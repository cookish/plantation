import numpy as np

from plantation.ai_players.random_player import RandomPlayer
from plantation.ai_players.random_player_dumb import RandomPlayerDumb
from plantation.ai_players.scry_and_die import ScryAndDie
from plantation.ai_players.paulc.php_player_wrapper import PHPPlayerWrapper

import plantation.engine as engine
import time


def main():
    # this should be even to allow players to each get the same number of first turns
    num_games_per_pair = 20

    players = [
        RandomPlayer(
            move_probabilities={
                'fertilise': 10,
                'plant': 10,
                'colonise': 1,
                'spray': 2,
                'bomb': 1
            }, name="CarlRogersRandom"),

        ScryAndDie(
            name="Vaarsuvius"
        ),

        PHPPlayerWrapper(
            name="Crocodilian",
            php_file="genetic.php"
        ),

        PHPPlayerWrapper(
            name="Coelacanth",
            php_file="genetic.php"
        ),

        PHPPlayerWrapper(
            name="AvianDinosaur",
            php_file="genetic.php"
        )
    ];
    engine.verbose = False
    wins = {}
    for p in players:
        wins[p.name] = []

    num_games = num_games_per_pair * len(players) * len(players)
    print(f"Running {num_games} games, being {num_games_per_pair} per pair between {len(players)} players, {num_games_per_pair*len(players)} games per player")
    print("Running games: [", end="")
    start_time = time.time()
    game = 0
    for iterations in range(num_games_per_pair // 2):
        for p1 in range(len(players)):
            for p2 in range(len(players)):
                # print progress bar
                game = game + 1
                if game % (num_games // 20) == 0:
                    print("=", end="")

                score = engine.run_game(
                    player_handler_p=players[p1],
                    player_handler_m=players[p2],
                    num_rows=11,
                    num_cols=11,
                    max_turns=100,
                    starting_tiles=3,
                    starting_seconds=1.0,
                    time_increment=0.1
                )

                if score > 0:
                    wins[players[p1].name].append(abs(score))
                elif score < 0:
                    wins[players[p2].name].append(abs(score))

                if score == 100:
                    print(players[p2].name, "ran out of time")
                elif score == -100:
                    print(players[p1].name, "ran out of time")

    print("]")
    print()

    for p in players:
        win_count = len(wins[p.name])
        print(f"{p.name} wins: {win_count} ({round(win_count/num_games*100, 2)} %)")
    print()

    # Calculate and print the duration
    end_time = time.time()
    duration = end_time - start_time
    print("Seconds:", duration)


if __name__ == '__main__':
    main()
