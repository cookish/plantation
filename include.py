import numpy as np


def get_player_restricted_board(board: np.ndarray, player) -> np.array:
    """ Returns a copy of the board with only the player's tiles. """

    return board * (board * player > 0)
