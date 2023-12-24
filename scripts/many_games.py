import numpy as np

from plantation.ai_players.random_player import RandomPlayer
from plantation.ai_players.scry_and_die import ScryAndDie
from plantation.ai_players.paulc.php_player_wrapper import PHPPlayerWrapper
from plantation.martin.ai_players.T800 import T800
from plantation.engine import Engine
import time


def main():
    num_games = 200

    # player_a = RandomPlayer(
    #     move_probabilities={
    #         'fertilise': 3,
    #         'plant': 4,
    #         'colonise': 2,
    #         'spray': 15,
    #         'bomb': 8
    #     },
    #     name="DukeNukem"
    # )

    # player_b = RandomPlayer(
    #     1,
    #     move_probabilities={
    #         'fertilise': 10,
    #         'plant': 10,
    #         'colonise': 1,
    #         'spray': 2,
    #         'bomb': 1
    #     }, name="CarlRogers")

    player_b = T800(name="Arnie fertilise", scout_propensity=0.2, initial_turns_of_growth=5, s_curve_factor=3,
                    relative_colonise_propensity=1,
                    relative_fertilise_propensity=2,
                    relative_plant_propensity=18,)
    # best parameters so far:
    player_a = T800(name="Arnie plant", scout_propensity=0.2, initial_turns_of_growth=5, s_curve_factor=3,
                    relative_colonise_propensity=0,
                    relative_fertilise_propensity=0,
                    relative_plant_propensity=18,)

    engine = Engine(
        num_rows=11,
        num_cols=11,
        max_turns=100,
        starting_tiles=3,
        starting_seconds=1.0,
        time_increment=0.5
    )

    engine.output = None
    wins = {
        player_a.name: [],
        player_b.name: [],
        'draw': []
    }

    print("Running games: [", end="", flush=True)
    start_time = time.time()
    for game in range(num_games):
        # print progress bar
        if game % max((num_games // 20), 1) == 0:
            print("=", end="", flush=True)

        score = engine.run_game(
            player_handler_p=player_a,
            player_handler_m=player_b
        )

        if score > 0:
            wins[player_a.name].append(abs(score))
        elif score < 0:
            wins[player_b.name].append(abs(score))
        else:
            wins['draw'].append(0)

        if score == 100:
            print(player_b.name, "ran out of time")
        elif score == -100:
            print(player_a.name, "ran out of time")

        player_a, player_b = player_b, player_a

    print("]")
    print()
    signed_scores = wins[player_a.name] + [-x for x in wins[player_b.name]]

    a_wins = len(wins[player_a.name])
    b_wins = len(wins[player_b.name])
    if a_wins > b_wins:
        print(f"{player_a.name} is the winner!!")
    elif b_wins > a_wins:
        print(f"{player_b.name} is the winner!!")
    else:
        print(f"It is a draw")

    print(f"{player_a.name} wins: {a_wins}")
    print(f"{player_b.name} wins: {b_wins}")
    print(f"Draws: {len(wins['draw'])}")
    print()
    print("Detailed results:")
    print(f"{player_a.name} wins: \n{wins[player_a.name]}\n")
    print(f"{player_b.name} wins: \n{wins[player_b.name]}")

    print(f"Average score, if we count scores for {player_b.name} as negative: "
          f"{np.mean(signed_scores):.2f}, (sigma: {np.std(signed_scores):.2f})")

    # Calculate and print the duration
    end_time = time.time()
    duration = end_time - start_time
    print("Seconds:", duration)


if __name__ == '__main__':
    main()
