import random
import time
from typing import List, Tuple

import numpy as np

from plantation.player import Player
from plantation.include import get_player_restricted_board, display_board_text


class Engine:

    moves_required = {
        'fertilise': 1,
        'plant': 1,
        'scout': 1,
        'colonise': 2,
        'spray': 2,
        'bomb': 2
    }
    bomb_damage = 4
    output = "stdout"
    outfile = None

    def __init__(
            self,
            num_rows: int,
            num_cols: int,
            starting_tiles: int,
            starting_seconds: float,
            time_increment: float,
            max_turns: int
    ):
        self.num_rows = num_rows
        self.num_cols = num_cols
        self.starting_tiles = starting_tiles
        self.starting_seconds = starting_seconds
        self.time_increment = time_increment
        self.max_turns = max_turns
        self.board = None
        self.turn = 0

    def run_game(
            self,
            player_handler_p: Player,
            player_handler_m: Player,
    ) -> float:
        self.start_of_game(player_handler_p, player_handler_m)

        time_p = self.starting_seconds
        time_m = self.starting_seconds
        for self.turn in range(1, self.max_turns+1):
            self.vprint()
            self.vprint("--------------------------------------------------------------")
            self.vprint(f"Turn {self.turn}")
            self.vprint("=========")
            t = self.run_player_turn(1, player_handler_p, time_p)
            time_p = time_p - t + self.time_increment
            if time_p < 0:
                break
            self.vprint()
            t = self.run_player_turn(-1, player_handler_m, time_m)
            time_m = time_m - t + self.time_increment
            if time_m < 0:
                break

        m_score, p_score = self.score_game()
        self.end_of_game(p_score, m_score, player_handler_p, player_handler_m, time_p, time_m)

        return p_score + m_score

    def start_of_game(self, player_handler_p: Player, player_handler_m: Player):
        if self.output and self.output != "stdout":
            self.outfile = open(self.output, "w")

        self.initialise_board(self.starting_tiles)
        player_handler_m.start_game(self.board.shape, sign=-1)
        player_handler_p.start_game(self.board.shape, sign=1)
        self.at_start_of_game_action()

    def end_of_game(
            self,
            p_score: int,
            m_score: int,
            player_handler_p: Player,
            player_handler_m: Player,
            time_p: float,
            time_m: float
    ):
        self.vprint("********** Game over! **********")
        if time_p < 0:
            self.vprint(f"{player_handler_p.name} ran out of time!")
            return -100
        if time_m < 0:
            self.vprint(f"{player_handler_m.name} ran out of time!")
            return 100

        player_handler_m.end_game(m_score, p_score)
        player_handler_p.end_game(p_score, m_score)

        self.print_score(p_score, m_score, player_handler_p, player_handler_m)
        self.at_end_of_game_action()

    def initialise_board(self, starting_tiles: int) -> None:
        self.board = np.zeros((self.num_rows, self.num_cols), dtype=np.byte)
        random_rows = random.sample(range(self.board.shape[0]), starting_tiles)
        self.board[random_rows, 0] = 1

        random_rows = random.sample(range(self.board.shape[0]), starting_tiles)
        self.board[random_rows, -1] = -1

    def score_game(self) -> Tuple[int, int]:
        board = self.board
        m_score = sum(board[board < 0])
        p_score = sum(board[board > 0])
        return p_score, m_score

    def print_score(self, p_score: int, m_score: int, player_p: Player, player_m: Player) -> None:
        final_score = p_score + m_score

        self.vprint()
        self.vprint("================ Final score ================")
        self.vprint(f"{player_p.name}: {p_score:+}")
        self.vprint(f"{player_m.name}: {m_score:+}")
        if final_score == 0:
            self.vprint("It's a draw!")
        else:
            winner = player_p.name if final_score > 0 else player_m.name
            self.vprint(f"{winner} wins by {abs(final_score)} points!")

    def run_player_turn(
            self,
            sign: int,
            player_handler: Player,
            time_remaining: float
    ) -> float:
        board = self.board
        total_p = np.sum(board[board > 0])
        total_m = np.sum(board[board < 0])
        self.vprint(f"Score: {total_p:+}, {total_m:+}  ({total_p + total_m:+})")

        if self.output is not None:
            board_str = display_board_text(board)
            self.vprint(board_str)

        moves_remaining = 3

        self.vprint(f"### {player_handler.name} ({'+' if sign > 0 else '-'}) ###  (time={time_remaining:.2f})")
        total_turn_time = 0.
        while moves_remaining > 0:
            time_taken, moves_taken = self.run_player_move(player_handler, time_remaining, moves_remaining, sign)
            total_turn_time += time_taken
            moves_remaining -= moves_taken
        self.at_end_of_turn_action(sign)
        return total_turn_time

    def run_player_move(
            self,
            player_handler: Player,
            time_remaining: float,
            moves_remaining: int,
            sign: int
    ) -> Tuple[float, int]:
        board = self.board
        player_board = get_player_restricted_board(board, sign)
        start_time = time.time()
        move, pos = player_handler.get_move(
            player_board, self.turn, moves_remaining, time_remaining
        )
        time_taken = time.time() - start_time
        result = self.do_move(move, pos, sign, moves_remaining)
        move_str = f"{move} ({','.join([str(p) for p in pos])})"
        self.vprint(f"{move_str:<20}  |  {result}")
        player_handler.handle_move_result(move, self.turn, pos, result)
        self.after_move_action(move, pos, sign, moves_remaining, result)
        return time_taken, self.moves_required[move]

    def do_fertilise(self, pos: List[int], sign: int) -> str:
        board = self.board
        row, col = pos[0], pos[1]
        if sign * board[row][col] > 0:
            board[row][col] += sign
            return "OK"
        else:
            self.vprint("do_fertilise: tile not owned by player")
            return "error"

    def do_plant(self, pos: List[int], sign: int) -> str:
        board = self.board

        row, col = pos[0], pos[1]
        if board[row][col] * sign > 0:
            self.vprint("do_plant: target tile already owned by player")
            return "error"
        elif board[row][col] * sign < 0:
            return f"occupied {board[row][col]}"

        # now we know that board[row][col] == 0
        for delta_r, delta_c in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            test_row = row + delta_r
            test_col = col + delta_c
            if 0 <= test_row < board.shape[0] and 0 <= test_col < board.shape[1]:
                if board[row + delta_r][col + delta_c] * sign > 0:
                    board[row][col] = sign
                    return "OK"

        self.vprint("do_plant: no adjacent tiles owned by player")
        return "error"

    def do_scout(self, pos: List[int], _sign: int) -> str:
        board = self.board

        row, col = pos[0], pos[1]
        results = []
        for delta_r in (-1, 0, 1):
            for delta_c in (-1, 0, 1):
                test_row = row + delta_r
                test_col = col + delta_c
                if 0 <= test_row < board.shape[0] \
                        and 0 <= test_col < board.shape[1]:
                    results.append(board[row + delta_r][col + delta_c])
        return "OK " + ",".join([str(x) for x in results])

    def do_colonise(self, pos: List[int], sign: int) -> str:
        board = self.board

        row, col, source_row, source_col = pos[0], pos[1], pos[2], pos[3]
        if board[row][col] * sign > 0:
            self.vprint("do_colonise: target tile already owned by player")
            return "error"
        elif board[source_row][source_col] * sign < 2:
            self.vprint("do_colonise: source tile count less than 2")
            return "error"

        elif board[row][col] * sign < 0:
            return f"occupied {board[row][col]}"
        else:
            board[row][col] = sign
            board[source_row][source_col] -= sign
            return "OK"

    def do_spray(self, pos: List[int], sign: int) -> str:
        board = self.board

        row, col = pos[0], pos[1]
        total = 0
        for delta_r, delta_c in [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]:
            test_row = row + delta_r
            test_col = col + delta_c
            if 0 <= test_row < board.shape[0] and 0 <= test_col < board.shape[1]:
                if board[test_row][test_col] * sign < 0:
                    board[row + delta_r][col + delta_c] += sign
                    total += 1
        return f"OK {total}"

    def do_bomb(self, pos: List[int], sign: int) -> str:
        board = self.board

        row, col = pos[0], pos[1]
        if board[row][col] * sign > 0:

            self.vprint(f"do_bomb: target tile owned by player")
            return "error"
        else:
            levels_reduced = min(abs(board[row][col]), self.bomb_damage)
            board[row][col] += sign * levels_reduced
            return f"OK {levels_reduced}"

    def do_move(
            self,
            move: str,
            pos: List[int],
            sign: int,
            moves_remaining: int,
    ):
        board = self.board
        if len(pos) < 2:
            self.vprint(f"Invalid position: {pos}")
            return "error"
        row, col = pos[0], pos[1]
        if row < 0 or row >= board.shape[0] or col < 0 or col >= board.shape[1]:
            self.vprint(f"Invalid location: ({row}, {col})")
            return "error"
        if move not in self.moves_required.keys():
            self.vprint(f"Invalid move: {move}")
            return "error"
        if self.moves_required[move] > moves_remaining:
            self.vprint(f"Not enough moves remaining for {move}")
            return "error"

        if move == 'fertilise':
            return self.do_fertilise(pos, sign)
        elif move == 'plant':
            return self.do_plant(pos, sign)
        elif move == 'scout':
            return self.do_scout(pos, sign)
        elif move == 'colonise':
            return self.do_colonise(pos, sign)
        elif move == 'spray':
            return self.do_spray(pos, sign)
        else:  # move == 'bomb':
            return self.do_bomb(pos, sign)

    def vprint(self, *args, **kwargs):
        if not self.output:
            return
        elif self.output == "stdout":
            print(*args, **kwargs)
        else:
            kwargs['file'] = self.outfile
            print(*args, **kwargs)

    def at_start_of_game_action(self):
        pass

    def after_move_action(
            self,
            move: str,
            pos: List[int],
            sign: int,
            moves_remaining: int,
            result: str
    ):
        pass

    def at_end_of_turn_action(self, sign: int):
        pass

    def at_end_of_game_action(self):
        pass


