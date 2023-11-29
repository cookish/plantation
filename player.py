from typing import Tuple, List
import numpy as np


class Player:
    num_rows = 0
    num_cols = 0
    player = 0

    def __init__(self, player: int):
        self.player = player

    def get_move(
            self,
            board: np.array,
            moves_remaining: int
    ) -> Tuple[str, List[int]]:

        return "", []

    def handle_move_result(self, move, pos, result):
        pass
