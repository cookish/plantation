from player import Player
from typing import Tuple, List, Dict
import random
import numpy as np


class RandomPlayer (Player):

    def __init__(
            self, sign: int,
            move_probabilities: Dict[str, float] = None
    ):
        super().__init__(sign)
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
            board: np.array,
            moves_remaining: int
    ) -> Tuple[str, List[int]]:

        attempts = 50
        rows = board.shape[0]
        cols = board.shape[1]

        # get a list of positions of tiles with a count > 1
        non_zero_tiles = np.argwhere(board != 0)
        multi_tiles = np.argwhere(np.abs(board) > 1)

        options = []
        if self.move_probabilities.get('plant', 0) > 0:
            options.append('plant')
        if len(non_zero_tiles) > 0 and \
                self.move_probabilities.get('fertilise', 0) > 0:
            options.append('fertilise')
        if moves_remaining > 1:
            for option in ('spray', 'bomb'):
                if self.move_probabilities.get(option, 0) > 0:
                    options.append(option)
            if len(multi_tiles) > 0:
                if self.move_probabilities.get('colonise', 0) > 0:
                    options.append('colonise')

        total_prob = sum({self.move_probabilities[k] for k in options})
        weights = [self.move_probabilities[k] / total_prob for k in options]

        while True:
            move = random.choices(options, weights=weights)[0]
            if move == 'fertilise':
                pos = random.choice(non_zero_tiles)
                return move, pos

            elif move == 'plant':
                if len(non_zero_tiles) == 0:
                    continue
                row, col = random.choice(non_zero_tiles)
                for delta_r, delta_c in [
                    (0, -1), (0, 1), (1, 0), (-1, 0)
                ]:
                    test_row = row + delta_r
                    test_col = col + delta_c
                    if 0 <= test_row < rows and 0 <= test_col < cols:
                        if board[test_row][test_col] == 0:
                            return move, [test_row, test_col]

            elif move == 'colonise':
                source_row, source_col = random.choice(multi_tiles)
                for i in range(attempts):
                    zero_tiles = np.argwhere(board == 0)
                    if len(zero_tiles) == 0:
                        continue
                    else:
                        row, col = random.choice(zero_tiles)
                        return move, [row, col, source_row, source_col]

            elif move == 'spray':
                row = random.randint(0, rows - 1)
                col = random.randint(0, cols - 1)
                return move, [row, col]

            else:  # move == 'bomb':
                for i in range(attempts):
                    row = random.randint(0, rows - 1)
                    col = random.randint(0, cols - 1)
                    if board[row][col] * self.sign == 0:
                        return move, [row, col]
