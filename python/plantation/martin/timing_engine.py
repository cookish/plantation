from typing import List

from plantation.engine import Engine
from plantation.martin.board_stats import BoardStats
from plantation.player import Player


class TimingEngine(Engine):

    def __init__(self, *args, **kwargs):
        self.times = {}
        super().__init__(*args, **kwargs)

    def at_end_of_game_action(self, player_p: Player, player_m: Player, time_p: float, time_m: float):
        # check if player_p.name in self.times keys
        # if not, add it with value 0
        if player_p.name not in self.times:
            self.times[player_p.name] = 0
        if player_m.name not in self.times:
            self.times[player_m.name] = 0

        self.times[player_p.name] += time_p
        self.times[player_m.name] += time_m

    def print_times(self):
        for key, val in self.times.items():
            print(f"Player {key}: {val:.2f} ms")
