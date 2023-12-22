import random
from typing import Tuple, List, Dict, Optional

import numpy as np

from plantation.player import Player


class RandomPlayer (Player):

    def __init__(
            self,
            move_probabilities: Dict[str, float],
            name: Optional[str] = None
    ):
        super().__init__(name)
        if move_probabilities is None:
            self.move_probabilities = {
                'fertilise': 0.2,
                'plant': 0.2,
                'colonise': 0.2,
                'spray': 0.2,
                'bomb': 0.2
            }
        self.move_probabilities = move_probabilities

    def get_move(
            self,
            board: np.ndarray,
            turn: int,
            moves_remaining: int,
            time_remaining: float,
    ) -> Tuple[str, List[int]]:
        rows = board.shape[0]
        cols = board.shape[1]

        zero_tiles = np.argwhere(board == 0)
        non_zero_tiles = np.argwhere(board != 0)
        multi_tiles = np.argwhere(np.abs(board) > 1)

        options = []

        if len(non_zero_tiles) > 0:
            if self.move_probabilities.get('fertilise', 0) > 0:
                options.append('fertilise')
            if self.move_probabilities.get('plant', 0) > 0 \
                    and len(zero_tiles) > 0:
                options.append('plant')

        if moves_remaining > 1 and len(zero_tiles) > 0:
            for option in ('spray', 'bomb'):
                if self.move_probabilities.get(option, 0) > 0:
                    options.append(option)
            if len(multi_tiles) > 0:
                if self.move_probabilities.get('colonise', 0) > 0:
                    options.append('colonise')

        total_prob = sum({self.move_probabilities[k] for k in options})
        weights = [self.move_probabilities[k] / total_prob for k in options]

        move = random.choices(options, weights=weights)[0]
        if move == 'fertilise':
            pos = random.choice(non_zero_tiles)
            return move, pos

        elif move == 'plant':
            plant_attempts = 10
            for i in range(plant_attempts):
                plant_options = []
                row, col = random.choice(non_zero_tiles)
                for dr, dc in [
                    (0, -1), (0, 1), (1, 0), (-1, 0)
                ]:
                    test_row = row + dr
                    test_col = col + dc
                    if 0 <= test_row < rows and 0 <= test_col < cols:
                        if board[test_row, test_col] == 0:
                            plant_options.append((test_row, test_col))
                if len(plant_options) > 0:
                    return move, random.choice(plant_options)

        elif move == 'colonise':
            source_row, source_col = random.choice(multi_tiles)
            row, col = random.choice(zero_tiles)
            return move, [row, col, source_row, source_col]

        elif move in ('spray', 'bomb'):
            # don't target one of our own squares
            zero_tiles = np.argwhere(board == 0)
            row, col = random.choice(zero_tiles)
            if board[row][col] * self.sign == 0:
                return move, [row, col]

        else:
            print("Unknown move: ", move)

        # default: do nothing useful
        return 'scout', [0, 0]
