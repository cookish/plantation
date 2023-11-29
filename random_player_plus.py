from player import Player
from typing import Tuple, List
import random
import numpy as np


class RandomPlayerPlus (Player):

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

        options = ['plant']
        if len(non_zero_tiles) > 0:
            options.append('fertilise')
        if moves_remaining > 1:
            options.extend(['spray', 'bomb'])
            if len(multi_tiles) > 0:
                options.append('colonise')

        while True:
            move = random.choice(options)
            if move == 'fertilise':
                pos = random.choice(non_zero_tiles)
                return move, pos

            elif move == 'plant':
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
                    if board[row][col] * self.player == 0:
                        return move, [row, col]
