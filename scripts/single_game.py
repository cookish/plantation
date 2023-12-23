from plantation.ai_players.random_player import RandomPlayer
from plantation.ai_players.scry_and_die import ScryAndDie
from plantation.ai_players.paulc.php_player_wrapper import PHPPlayerWrapper
from plantation.martin.ai_players.scry_and_die_T800 import ScryAndDieT800
from plantation.engine import Engine


def main():

    engine = Engine(
        num_rows=11,
        num_cols=11,
        max_turns=100,
        starting_tiles=3,
        starting_seconds=1000.0,
        time_increment=1000
    )
    # player_handler_a = RandomPlayer(
    #     1,
    #     move_probabilities={
    #         'fertilise': 0.3,
    #         'plant': 0.5,
    #         'colonise': 0.1,
    #         'spray': 0.05,
    #         'bomb': 0.05
    #     }, name="DukeNukem")
    # player_handler_b = RandomPlayer(
    #     1,
    #     move_probabilities={
    #         'fertilise': 10,
    #         'plant': 10,
    #         'colonise': 1,
    #         'spray': 2,
    #         'bomb': 1
    #     }, name="CarlRogers")
    # player_handler_b = RandomPlayerDumb(-1, name="Dumb")
    player_handler_a = ScryAndDie(name="Xykon")
    player_handler_b = ScryAndDieT800(name="Arnie")
    # player_handler_b = PHPPlayerWrapper(name="Crocodilian", php_file="genetic.php")

    engine.output = 'stdout'
    _score = engine.run_game(
        player_handler_a,
        player_handler_b
    )


if __name__ == '__main__':
    main()
