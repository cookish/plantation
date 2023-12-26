from typing import List

from plantation.engine import Engine
from plantation.martin.board_stats import BoardStats
from plantation.player import Player


class BoardStatsEngine(Engine):

    def __init__(self, board_stats: BoardStats, *args, **kwargs):
        self.board_stats = board_stats
        super().__init__(*args, **kwargs)

    def at_start_of_game_action(self, player_p: Player, player_m: Player):
        pass

    def after_get_move_action(self, move: str, post: List[int]):
        pass

    def after_move_action(
            self,
            player: Player,
            move: str,
            pos: List[int],
            moves_remaining: int,
            result: str
    ):
        self.board_stats.record_move(player.sign, move, pos, result, self.turn)

    def at_end_of_turn_action(self, sign: int, player: Player):
        self.board_stats.end_turn(sign, self.turn, self.board)

    def at_end_of_game_action(self, player_p: Player, player_m: Player, time_p: float, time_m: float):
        self.board_stats.end_game()
