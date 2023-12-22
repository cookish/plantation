from plantation.ai_players.random_player import RandomPlayer
from plantation.ai_players.random_player_dumb import RandomPlayerDumb
from plantation.ai_players.scry_and_die import ScryAndDie
from plantation.ai_players.human import HumanPlayer

from plantation.engine import Engine


def main():
    engine = Engine()
    player_handler_a = HumanPlayer(name="NobbityBop")
    player_handler_b = ScryAndDie(name="Xykon")

    engine.output = 'output.txt'
    _score = engine.run_game(
        player_handler_a,
        player_handler_b,
        num_rows=11,
        num_cols=11,
        max_turns=100,
        starting_tiles=3,
        starting_seconds=1000.0,
        time_increment=1000
    )


if __name__ == '__main__':
    main()
