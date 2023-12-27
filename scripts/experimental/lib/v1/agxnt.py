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
    Agent: AbstractAgent, State, Action,
    ScanX, ScanXS, ScanY, ScanYS
](Module, strict=True):
    dynamics: DynamicsFn[State, Action, ScanX, ScanY]

    def __call__(
        self,
        agent: Agent,
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


type TrainStepFn[Agent: AbstractAgent, TrainState] = Callable[
    [Agent, TrainState, PRNGKeyArray | None],
    tuple[Agent, TrainState],
]


# TODO Maybe this could just be a function `train` that receives train_step
class Trainer[Agent: AbstractAgent, TrainState](Module, strict=True):
    train_step: TrainStepFn[Agent, TrainState]

    def __call__(
        self,
        agent: Agent,
        train_state: TrainState,
        steps: int,
        rng_key: PRNGKeyArray | None,
    ) -> tuple[Agent, TrainState]:
        if rng_key is None:
            step_keys = [None] * steps
        else:
            step_keys = jr.split(rng_key, steps)

        # TODO Implement something like `lax.scan`'s YS to extract a record
        # TODO Would it be crazy to `lax.scan` over batches?

        for step_key in step_keys:
            agent, train_state = self.train_step(agent, train_state, step_key)

        return agent, train_state
