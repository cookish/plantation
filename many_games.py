import numpy as np

from ai_players.random_player import RandomPlayer
from ai_players.random_player_dumb import RandomPlayerDumb


import engine


def main():
    name_a = "Duke Nukem"
    name_b = "Grower"
    num_games = 100
    player_a = RandomPlayer(
        sign=1,
        move_probabilities={
            'fertilise': 3,
            'plant': 4,
            'colonise': 2,
            'spray': 15,
            'bomb': 8
        },
        name=name_a
    )
    # player_a = RandomPlayerDumb(1, name="Dumb")
    player_b = RandomPlayer(
        sign=-1,
        move_probabilities={
            'fertilise': 10,
            'plant': 20,
            'colonise': 4,
            'spray': 3,
            'bomb': 2
        },
        name=name_b
    )

    engine.verbose = False
    wins = {
        player_a.name: [],
        player_b.name: [],
        'draw': []
    }

    print("Running games: [", end="")
    for game in range(num_games):
        # print progress bar
        if game % (num_games // 20) == 0:
            print("=", end="")

        player_a.set_sign(1)
        player_b.set_sign(-1)

        score = engine.run_game(
            player_handler_p=player_a,
            player_handler_m=player_b,
            num_rows=11,
            num_cols=11,
            max_turns=100,
            starting_tiles=3,
            starting_seconds=1.0,
            time_increment=0.1
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
    scores = wins[player_a.name] + [-x for x in wins[player_b.name]]
    print(f"{player_a.name} wins: {len(wins[player_a.name])}  "
          f"{wins[player_a.name]}")
    print(f"{player_b.name} wins: {len(wins[player_b.name])}  "
          f"{wins[player_b.name]}")
    print(f"Draws: {len(wins['draw'])}")
    print(f"Scores: {scores}")
    print(f"Average score, ({player_a.name} is positive): "
          f"{np.mean(scores):.2f}, (sigma: {np.std(scores):.2f})")
    print(f"There were {len(wins['draw'])} draws")


if __name__ == '__main__':
    main()
