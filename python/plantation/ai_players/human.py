from typing import Tuple, List
import numpy as np
from time import sleep

from plantation.player import Player
from plantation.include import display_board_text


class HumanPlayer (Player):

    prev_board = None

    def get_move(
            self,
            board: np.ndarray,
            turn: int,
            moves_remaining: int,
            time_remaining: float,
    ) -> Tuple[str, List[int]]:

        moves = {
            's': 'scout',
            'c': 'colonise',
            'f': 'fertilise',
            'p': 'plant',
            'b': 'bomb',
            'y': 'spray'
        }

        board_has_changed = not (board == self.prev_board).all()
        if moves_remaining == 3:
            print()
            print("#############################################################")
            if not board_has_changed and turn != 1:
                print("(Board has not changed since last turn)")

        if board_has_changed:
            print(display_board_text(board))
            self.prev_board = board

        print(f"{turn=} {moves_remaining=} {time_remaining=}")

        while True:
            inp = input("## Move [ (s)cout, (c)olonise, (f)ertilise, (p)lant, (b)omb, spra(y) ]: ")
            try:
                move, coords = inp.split(maxsplit=1)
                if move not in moves.keys() and move not in moves.values():
                    print(f"Invalid move: {move}, please try again")
                    continue
                coords = [int(a) for a in coords.split(',')]
                if (not (len(coords) == 4 and move == 'colonise')
                        and not (len(coords) == 2) and move != 'colonise'):
                    print(f"Coordinates not understood, please try again")
                    continue
            except ValueError:
                continue

            break

        if len(move) == 1:
            move = moves[move]
        return move, coords

    def handle_move_result(self, move, turn, pos, result):
        print(f"Result: {result}")
        sleep(0.15)
