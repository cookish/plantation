from typing import List

from plantation.martin.board_stats import BoardStats
from plantation.martin.timing_engine import TimingEngine
from plantation.player import Player


class BoardStatsEngine(TimingEngine):

    def __init__(self, board_stats: BoardStats, *args, **kwargs):
        self.board_stats = board_stats
        super().__init__(*args, **kwargs)
        self.game_count = 0
        self.save_every = 2

    def after_move_action(
            self,
            player: Player,
            move: str,
            pos: List[int],
            moves_remaining: int,
            result: str
    ):
        super().after_move_action(player, move, pos, moves_remaining, result)
        self.board_stats.record_move(player.sign, move, pos, result, self.turn)

    def at_end_of_turn_action(self, player: Player):
        super().at_end_of_turn_action(player)
        self.board_stats.end_turn(player.sign, self.turn, self.board)

    def at_end_of_game_action(self, player_p: Player, player_m: Player, time_p: float, time_m: float):
        super().at_end_of_game_action(player_p, player_m, time_p, time_m)
        self.game_count += 1
        if self.game_count % self.save_every == 0:
            self.board_stats.write_data()
