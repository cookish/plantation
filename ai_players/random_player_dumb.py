import numpy as np

from player import Player
from typing import Tuple, List
import random


class RandomPlayerDumb (Player):

    def get_move(
            self,
            board: np.array,
            turn: int,
            moves_remaining: int,
            time_remaining: float,
    ) -> Tuple[str, List[int]]:

        if moves_remaining > 1:
            options = ['fertilise', 'plant', 'colonise', 'spray', 'bomb']
        else:
            options = ['fertilise', 'plant']

        # generate a random number between 0 and num_rows - 1
        row = random.randint(0, board.shape[0] - 1)
        col = random.randint(0, board.shape[1] - 1)

        # select a random value from options List
        move = random.choice(options)

        if move == 'colonise':
            source_row = random.randint(0, board.shape[0] - 1)
            source_col = random.randint(0, board.shape[1] - 1)

            return move, [row, col, source_row, source_col]

        else:
            return move, [row, col]
