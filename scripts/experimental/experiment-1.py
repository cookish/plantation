"""Smoke test - teach a simple MPL the rules of Plantation."""

import json
from pathlib import Path
import random
import sys
from typing import BinaryIO, Self

import click
import equinox as eqx
import jax
import jax.lax as lax
import jax.numpy as jnp
import jax.random as jr
from jaxtyping import Array, Float, PRNGKeyArray, PyTree, Scalar, UInt
import optax
from optax import GradientTransformation, OptState

sys.path.insert(0, str(Path(__file__).parent / "lib"))
from v1.agxnt import (
    AbstractAgent,
    ExoState,
    Simulator,
    StateEnvelope,
    Trainer,
    TrainStepFn,
)
from v1.game import (  # type: ignore
    allowed_actions,
    BoardUInt,
    BOARD_HEIGHT,
    BOARD_WIDTH,
    NUM_ACTIONS,
)


type ActionPMF = Float[Array, "height width actions"]
"""The action probability mass function by which an agent expresses its will"""

type ActionPMFs = Float[Array, "sim_steps height width actions"]

type BoardUIntSeq = UInt[Array, "sim_steps height width"]

type BoardUIntBatch = UInt[Array, "batch_size height width"]

type BoardUIntSeqBatch = UInt[Array, "batch_size sim_steps height width"]


class LearningAgent[State](AbstractAgent[State, ActionPMF, BoardUInt]):
    trainable_map: PyTree # TODO How to say "callable Module"?
    hyperparams: dict = eqx.field(static=True)

    @classmethod
    def make_dev_agent(
        cls,
        *,
        board_height: int,
        board_width: int,
        num_actions: int,
        mlp_width: int,
        mlp_depth: int,
        key: PRNGKeyArray,
    ) -> Self:
        trainable_map = eqx.nn.Sequential([
            eqx.nn.Lambda(jnp.ravel),
            eqx.nn.MLP(
                in_size=board_height * board_width,
                out_size=board_height * board_width * num_actions,
                width_size=mlp_width,
                depth=mlp_depth,
                key=key,
            ),
            eqx.nn.Lambda(jax.nn.softmax),  # TODO Inspect
            eqx.nn.Lambda(
                lambda x: x.reshape(board_height, board_width, num_actions)
            ),
        ])

        return cls(
            trainable_map,
            hyperparams = {
                "board_height": board_height,
                "board_width": board_width,
                "num_actions": num_actions,
                "mlp_width": mlp_width,
                "mlp_depth": mlp_depth,
            }
        )
    
    @classmethod
    def load(cls, source: BinaryIO) -> Self:
        params = json.loads(source.readline().decode())
        agent = cls.make_dev_agent(**params, key=jr.PRNGKey(0))

        return eqx.tree_deserialise_leaves(source, agent)

    def save(self, target: BinaryIO):
        structure = (json.dumps(self.hyperparams) + "\n").encode()
        target.write(structure)
        eqx.tree_serialise_leaves(target, self)

    def react(
        self,
        state: State,
        exo_state: BoardUInt,
    ) -> ActionPMF:
        return self.trainable_map(exo_state)


def dynamics(
    state_envelope: StateEnvelope[None, ActionPMF],
    exo_state: BoardUInt,
) -> tuple[StateEnvelope[None, ActionPMF], ActionPMF]:
    agent: LearningAgent[None] = eqx.combine(
        state_envelope.agent_dynamic_tree,
        state_envelope.agent_static_tree,
    )
    new_state = state_envelope.state  # no-op
    action = agent.react(new_state, exo_state)

    return StateEnvelope[None, ActionPMF](
        *eqx.partition(agent, filter_spec=eqx.is_array), new_state, action
    ), state_envelope.action


def score_action_legal_uniform(
    action: ActionPMF,
    board: BoardUInt,
) -> Scalar:
    """Evaluates an action pmf for compliance with the rules of the game.

    Penalises
    - probabiliy mass on illegal moves
    - non-uniform density on legal moves

    TODO Devise a score less sensitive to then number of occupied cells.
    """
    legal_actions = allowed_actions(board)
    good_pm = jnp.where(legal_actions, action, 0.0)
    evil_pm = jnp.where(~legal_actions, action, 0.0)

    n = jnp.count_nonzero(legal_actions).astype(float)
    good_absdev = jnp.where(
        legal_actions,
        lax.abs(action - good_pm.sum() / n),
        0.0,
    )

    return 1.0 - evil_pm.sum() - good_absdev.mean()


def make_train_step(
    agent: LearningAgent[None],
    sim_fn: Simulator[
        None, ActionPMF, BoardUInt, BoardUIntSeq, ActionPMF, ActionPMFs
    ],
    optimiser: GradientTransformation,
    sim_steps: int,
    batch_size: int,
    lam: float,
) -> tuple[
        TrainStepFn[OptState, None, ActionPMF, BoardUInt],
        OptState
    ]:
    @eqx.filter_grad
    def compute_loss(
        agent: LearningAgent[None],
        exo_state: ExoState[BoardUIntBatch, BoardUIntSeqBatch],
    ) -> Scalar:
        actions = eqx.filter_vmap(
            sim_fn, in_axes=(None, None, 0)
        )(agent, None, exo_state)

        boards = jnp.roll(exo_state.sequence, shift=1, axis=1)
        boards = boards.at[:, 0].set(exo_state.initial)

        # Merge batch and sequence dims
        actions = actions.reshape(-1, *actions.shape[-3:])
        boards = boards.reshape(-1, *boards.shape[-2:])

        scores = jax.vmap(score_action_legal_uniform)(actions, boards)

        return -scores.mean()

    @eqx.filter_jit
    def train_step(
        agent: LearningAgent[None],
        train_state: OptState,
        rng_key: PRNGKeyArray,
    ) -> tuple[LearningAgent[None], OptState]:
        k1, k2 = jr.split(rng_key)

        exo_state = ExoState[BoardUIntBatch, BoardUIntSeqBatch](
            initial=jr.poisson(
                k1,
                lam=lam,
                shape=(batch_size, BOARD_HEIGHT, BOARD_WIDTH),
            ),
            sequence=jr.poisson(
                k2,
                lam=lam,
                shape=(batch_size, sim_steps, BOARD_HEIGHT, BOARD_WIDTH),
            ),
        )

        grads = compute_loss(agent, exo_state)

        updates, train_state = optimiser.update(
            grads, train_state, params=agent  # type: ignore  # FIXME
        )
        agent = eqx.apply_updates(agent, updates)

        return agent, train_state

    opt_state = optimiser.init(eqx.filter(agent, eqx.is_array))

    return train_step, opt_state  # type: ignore  # FIXME


def test(
    agent: LearningAgent[None],
    lam: float,
    rng_key: PRNGKeyArray,
    batch_size: int = 10000,
):
    boards = jr.poisson(
        rng_key, lam=lam, shape=(batch_size, BOARD_HEIGHT, BOARD_WIDTH)
    )

    actions = eqx.filter_vmap(
        agent.react, in_axes=(None, 0),
    )(None, boards)

    scores = jax.vmap(score_action_legal_uniform)(actions, boards)

    return scores.mean()


TRAIN_STEPS = 100
LEARNING_RATE = 1e-3
SIM_STEPS = 1
BATCH_SIZE = 1024
LAMBDA = 0.25
MLP_WIDTH = 128
MLP_DEPTH = 1


@click.command
@click.option(
    "--load",
    type=click.File("rb"),
)
@click.option(
    "--save",
    type=click.File("wb"),
)
@click.option(
    "--train-steps",
    type=click.IntRange(min=0),
    default=TRAIN_STEPS,
)
@click.option(
    "--learning-rate",
    type=click.FloatRange(min=0.0, min_open=True),
    default=LEARNING_RATE,
)
@click.option(
    "--sim-steps",
    type=click.IntRange(min=0),  # FIXME Fails at bound
    default=SIM_STEPS,
)
@click.option(
    "--batch-size",
    type=click.IntRange(min=0),  # TODO Check behaviour at bound
    default=BATCH_SIZE,
)
@click.option(
    "--lambda", "lambda_",
    type=click.FloatRange(min=0.0, min_open=True),
    default=LAMBDA,
)
@click.option(
    "--mlp-width",
    type=click.IntRange(min=0, min_open=True),
    default=MLP_WIDTH,
)
@click.option(
    "--mlp-depth",
    type=click.IntRange(min=0, min_open=True),
    default=MLP_DEPTH,
)
@click.option(
    "--rng-seed",
    type=click.IntRange(min=0),
    default=lambda: random.SystemRandom().randint(0, 2**32 - 1),
)
def train_cmd(
    *,
    load,
    save,
    train_steps,
    learning_rate,
    sim_steps,
    batch_size,
    lambda_,
    mlp_width,
    mlp_depth,
    rng_seed,
):
    key = jr.PRNGKey(rng_seed)

    if load is None:
        hyperparams = {
            "board_height": BOARD_HEIGHT,
            "board_width": BOARD_WIDTH,
            "num_actions": NUM_ACTIONS,
            "mlp_width": mlp_width,
            "mlp_depth": mlp_depth,
        }
        key, subkey = jr.split(key)
        agent = LearningAgent[None].make_dev_agent(**hyperparams, key=subkey)
    else:
        agent = LearningAgent[None].load(load)

    key, subkey = jr.split(key)
    metric = test(agent, lambda_, subkey)
    print(f"{'Before training:':16}", f"{metric:4.6f}")

    simulate = Simulator[
        None, ActionPMF, BoardUInt, BoardUIntSeq, ActionPMF, ActionPMFs
    ](dynamics)

    optimiser = optax.adamw(learning_rate)
    train_step, opt_state = make_train_step(
        agent,
        simulate,
        optimiser,
        sim_steps,
        batch_size,
        lam=lambda_,
    )

    train = Trainer[
        PyTree, None, ActionPMF, BoardUInt,
    ](train_step)

    key, subkey = jr.split(key)
    agent, opt_state = train(agent, opt_state, train_steps, subkey)

    if save is not None:
        agent.save(save)  # type: ignore  # TODO Bad design by me anyway

    key, subkey = jr.split(key)
    metric = test(agent, lambda_, subkey)  # type: ignore  # TODO
    print(f"{'After training:':16}", f"{metric:4.6f}")


if __name__ == "__main__":
    train_cmd()
