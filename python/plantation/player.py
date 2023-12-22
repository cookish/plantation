from typing import Tuple, List, Optional
import numpy as np
import random
import string


class Player:
    sign = 0
    name = "Player"

    def __init__(self, name: Optional[str] = None):
        if name is not None:
            self.name = name
        else:
            self.name = "Player " + random.choice(string.ascii_lowercase)

    def end_game(self, your_score: int, opponent_score: int):
        pass

    def start_game(self, board_shape: Tuple[int], sign: int):
        self.sign = sign

    def get_move(
            self,
            board: np.ndarray,
            turn: int,
            moves_remaining: int,
            time_remaining: float,
    ) -> Tuple[str, List[int]]:

        return "", []

    def handle_move_result(self, move, turn, pos, result):
        pass
