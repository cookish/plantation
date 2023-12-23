from typing import List

from plantation.engine import Engine
from plantation.martin.board_stats import BoardStats


class BoardStatsEngine(Engine):

    def __init__(self, board_stats: BoardStats, *args, **kwargs):
        self.board_stats = board_stats
        super().__init__(*args, **kwargs)

    def at_start_of_game_action(self):
        pass

    def after_get_move_action(self, move: str, post: List[int]):
        pass

    def after_move_action(
            self,
            move: str,
            pos: List[int],
            sign: int,
            moves_remaining: int,
            result: str
    ):
        self.board_stats.record_move(sign, move, pos, result, self.turn)

    def at_end_of_turn_action(self, sign: int):
        self.board_stats.end_turn(sign, self.turn, self.board)

    def at_end_of_game_action(self):
        self.board_stats.end_game()