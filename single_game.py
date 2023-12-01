from ai_players.random_player import RandomPlayer
from ai_players.random_player_dumb import RandomPlayerDumb


from engine import run_game, score_board


def main():

    player_handler_a = RandomPlayer(
        1,
        move_probabilities={
            'fertilise': 0.3,
            'plant': 0.5,
            'colonise': 0.1,
            'spray': 0.05,
            'bomb': 0.05
        })
    player_handler_b = RandomPlayerDumb(-1)

    board = run_game(
        player_handler_a,
        player_handler_b,
        num_rows=11,
        num_cols=11,
        max_turns=10,
        starting_tiles=3
    )
    _score = score_board(board)


if __name__ == '__main__':
    main()
