import numpy as np

from ai_players.random_player import RandomPlayer
from ai_players.random_player_dumb import RandomPlayerDumb


import engine


def main():

    num_games = 40
    player_a = RandomPlayer(
        1,
        move_probabilities={
            'fertilise': 6,
            'plant': 10,
            'colonise': 2,
            'spray': 1,
            'bomb': 1
        })
    # player_a = RandomPlayerDumb(1)
    player_b = RandomPlayer(
        -1,
        move_probabilities={
            'fertilise': 10,
            'plant': 20,
            'colonise': 1,
            'spray': 5,
            'bomb': 5
        })

    engine.verbose = False
    scores = []
    for game in range(num_games):
        player_a.set_sign(1)
        player_b.set_sign(-1)

        board = engine.run_game(
            player_handler_p=player_a,
            player_handler_m=player_b,
            num_rows=11,
            num_cols=11,
            max_turns=100,
            starting_tiles=3
        )

        score = engine.score_board(board)
        if game % 2 == 1:
            score = -score

        scores.append(score)
        player_a, player_b = player_b, player_a

    print(f"Scores: {scores}")
    print(f"Average score: {np.average(scores)}  (+-{np.std(scores):.2f})")


if __name__ == '__main__':
    main()
