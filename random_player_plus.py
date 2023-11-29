from player import Player
from typing import Tuple, List
import random


class RandomPlayerPlus (Player):

    def get_move(
            self,
            board: List[List[int]],
            moves_remaining: int
    ) -> Tuple[str, List[int]]:

        attempts = 50

        if moves_remaining > 1:
            options = ['fertilise', 'plant', 'colonise', 'spray', 'bomb']
        else:
            options = ['fertilise', 'plant']

        while True:
            move = random.choice(options)
            if move == 'fertilise':
                for i in range(attempts):

                    row = random.randint(0, self.num_rows - 1)
                    col = random.randint(0, self.num_cols - 1)
                    if board[row][col] * self.player > 0:
                        return move, [row, col]

            elif move == 'plant':
                for i in range(attempts):
                    row = random.randint(0, self.num_rows - 1)
                    col = random.randint(0, self.num_cols - 1)
                    if board[row][col] == 0:
                        for delta_r, delta_c in [
                            (0, -1), (0, 1), (1, 0), (-1, 0)
                        ]:
                            if 0 <= row + delta_r < self.num_rows \
                                    and 0 <= col + delta_c < self.num_cols:
                                if board[row + delta_r][col + delta_c] \
                                        * self.player > 0:
                                    return move, [row, col]

            elif move == 'colonise':
                found_source = False
                source_row = -1
                source_col = -1
                for i in range(attempts):
                    source_col = random.randint(0, self.num_cols - 1)
                    source_row = random.randint(0, self.num_rows - 1)
                    if board[source_row][source_col] * self.player > 1:
                        found_source = True
                        break

                if found_source:
                    for i in range(attempts):
                        row = random.randint(0, self.num_rows - 1)
                        col = random.randint(0, self.num_cols - 1)
                        if board[row][col] == 0:
                            return move, [row, col, source_row, source_col]

            elif move == 'spray':
                row = random.randint(0, self.num_rows - 1)
                col = random.randint(0, self.num_cols - 1)
                return move, [row, col]

            else:  # move == 'bomb':
                for i in range(attempts):
                    row = random.randint(0, self.num_rows - 1)
                    col = random.randint(0, self.num_cols - 1)
                    if board[row][col] * self.player == 0:
                        return move, [row, col]
