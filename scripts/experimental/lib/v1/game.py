"""Elements of Plantation amenable to JAX autograd and jit."""

from enum import IntEnum

import jax.lax as lax
import jax.numpy as jnp
from jaxtyping import Array, Bool, UInt


BOARD_HEIGHT = 11
BOARD_WIDTH = 11

BOARD_SHAPE = (BOARD_HEIGHT, BOARD_WIDTH)

type BoardBool = Bool[Array, "height width"]
type BoardUInt = UInt[Array, "height width"]

NUM_ACTIONS = 2

type ActionBool = Bool[Array, "height width actions"]


class Act(IntEnum):
    """Index of an action type in the `actions` dimension of `ActionBool`"""
    FR = 0
    """Fertilise"""
    PL = 1
    """Plant"""
    SC = 2
    """Scout"""
    BM = 3
    """Bomb"""
    SP = 4
    """Spray"""
    # CO = 5  # FIXME What about this, son?


def allowed_actions(player_board: BoardUInt) -> ActionBool:
    """Actions allowed according to the state of ONE PLAYER's pieces.

    Actions are considered allowed even if their direct effect on the board is
    ultimately blocked due to the opponent's position.
    """
    # NOTE Maintain the correct order in the stack, as in enum `Act`.
    return jnp.stack(
        (
            allowed_fertilise(player_board),
            allowed_plant(player_board),
        ),
        axis=-1,
    )


def allowed_fertilise(player_board: BoardUInt) -> BoardBool:
    return player_board.astype('bool')


def allowed_plant(player_board: BoardUInt) -> BoardBool:
    occupied = player_board.astype('bool')

    return lax.full_like(
        occupied, False
    ).at[:, 1:].set(
        occupied[:, :-1]
    ).at[:, :-1].set(
        occupied[:, 1:]
    ).at[:-1, :].set(
        occupied[1:, :]
    ).at[1:, :].set(
        occupied[:-1, :]
    ) & ~occupied
