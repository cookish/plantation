import numpy as np
import io
from contextlib import redirect_stdout


def get_player_restricted_board(board: np.ndarray, player: int) -> np.ndarray:
    """ Returns a copy of the board with only the player's tiles. """

    return board * (board * player > 0)


def display_board_text(board):
    f = io.StringIO()
    with redirect_stdout(f):
        num_rows = board.shape[0]
        num_cols = board.shape[1]
        print("     " + "    ".join([str(i) for i in range(num_cols)]))
        print("   " + "=" * (num_cols * 5 + 1))
        for row in range(num_rows):

            print(f"{row:>2} |", end="")

            for col in range(num_cols):
                if board[row][col] == 0:
                    display = ""
                else:
                    display = "-" if board[row][col] < 0 else "+"
                    display += str(abs(board[row][col]))

                # print display with string padding up to length 3
                # print(display.center(4) + "|", end="")
                print(f"{display:^4}|", end="")

            print()
        print("   " + "=" * (num_cols * 5 + 1))

    return f.getvalue()
