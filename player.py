from typing import Tuple, List


class Player:
    num_rows = 0
    num_cols = 0
    player = 0

    def __init__(self, num_rows: int, num_cols: int, player: int):
        self.num_rows = num_rows
        self.num_cols = num_cols
        self.player = player

    def get_move(
            self,
            board: List[List[int]],
            moves_remaining: int
    ) -> Tuple[str, List[int]]:

        return "", []

    def handle_move_result(self, move, pos, result):
        pass
