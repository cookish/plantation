"""Scaffold for reinforcement learning with differentiable dynamics."""

from abc import abstractmethod
from typing import Callable

import equinox as eqx
from equinox import Module
import jax.lax as lax
import jax.random as jr
from jaxtyping import PRNGKeyArray, PyTree


class AbstractAgent[State, Action, ScanX](Module, strict=True):
    @abstractmethod
    def react(
        self,
        state: State,
        exo_state: ScanX,
    ) -> Action: ...


type Agent[State, Action, ScanX] = AbstractAgent[State, Action, ScanX]


class StateEnvelope[State, Action](Module, strict=True):
    agent_dynamic_tree: PyTree
    agent_static_tree: PyTree = eqx.field(static=True)
    state: State
    action: Action


class ExoState[ScanX, ScanXS](Module, strict=True):
    initial: ScanX
    sequence: ScanXS


type DynamicsFn[State, Action, ScanX, ScanY] = Callable[
    [StateEnvelope[State, Action], ScanX],
    tuple[StateEnvelope[State, Action], ScanY],
]


class Simulator[
    State, Action, ScanX, ScanXS, ScanY, ScanYS
](Module, strict=True):
    dynamics: DynamicsFn[State, Action, ScanX, ScanY]

    def __call__(
        self,
        agent: Agent[State, Action, ScanX],
        state: State,
        exo_state: ExoState[ScanX, ScanXS],
    ) -> ScanYS:
        action = agent.react(state, exo_state.initial)
        dynamic_tree, static_tree = eqx.partition(agent, eqx.is_array)
        _, result = lax.scan(
            self.dynamics,  # type: ignore
            init=StateEnvelope[State, Action](
                dynamic_tree, static_tree, state, action
            ),
            xs=exo_state.sequence,
        )

        return result  # type: ignore


type TrainStepFn[TrainState, State, Action, ScanX] = Callable[
    [Agent[State, Action, ScanX], TrainState, PRNGKeyArray | None],
    tuple[Agent[State, Action, ScanX], TrainState],
]


# TODO Maybe this could just be a function `train` that receives train_step
class Trainer[TrainState, State, Action, ScanX](Module, strict=True):
    train_step: TrainStepFn[TrainState, State, Action, ScanX]

    def __call__(
        self,
        agent: Agent[State, Action, ScanX],
        train_state: TrainState,
        steps: int,
        rng_key: PRNGKeyArray | None,
    ) -> tuple[Agent[State, Action, ScanX], TrainState]:
        if rng_key is None:
            step_keys = [None] * steps
        else:
            step_keys = jr.split(rng_key, steps)

        # TODO Implement something like `lax.scan`'s YS to extract a record
        # TODO Would it be crazy to `lax.scan` over batches?

        for step_key in step_keys:
            agent, train_state = self.train_step(agent, train_state, step_key)

        return agent, train_state
