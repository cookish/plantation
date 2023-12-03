from typing import Tuple, List, Optional
import numpy as np


class Player:
    sign = 0
    name = "Player"

    def __init__(self, sign: int, name: Optional[str] = None):
        self.sign = sign
        if name is not None:
            self.name = name
        else:
            self.name = "Plus" if sign > 0 else "Minus"

    def set_sign(self, sign):
        self.sign = sign

    def get_move(
            self,
            board: np.array,
            turn: int,
            moves_remaining: int,
            time_remaining: float,
    ) -> Tuple[str, List[int]]:

        return "", []

    def handle_move_result(self, move, turn, pos, result):
        pass
