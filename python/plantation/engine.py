import random
import time
from typing import List

import numpy as np

from plantation.board_stats import BoardStats
from plantation.player import Player
from plantation.include import get_player_restricted_board, display_board_text

board_stats = BoardStats()


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

    def run_game(
            self,
            player_handler_p: Player,
            player_handler_m: Player,
            num_rows: int,
            num_cols: int,
            max_turns: int,
            starting_tiles: int,
            starting_seconds: float,
            time_increment: float
    ) -> float:

        if self.output and self.output != "stdout":
            self.outfile = open(self.output, "w")

        board = np.zeros((num_rows, num_cols), dtype=np.byte)
        self.initialise_board(board, starting_tiles)
        player_handler_m.start_game(board.shape, sign=-1)
        player_handler_p.start_game(board.shape, sign=1)

        time_p = starting_seconds
        time_m = starting_seconds
        for turn in range(1, max_turns+1):
            self.vprint()
            self.vprint("--------------------------------------------------------------")
            self.vprint(f"Turn {turn}")
            self.vprint("=========")
            t = self.run_turn(1, player_handler_p, board, time_p, turn)
            time_p = time_p - t + time_increment
            if time_p < 0:
                break
            self.vprint()
            t = self.run_turn(-1, player_handler_m, board, time_m, turn)
            time_m = time_m - t + time_increment
            if time_m < 0:
                break

        board_stats.end_game()

        self.vprint("********** Game over! **********")
        if time_p < 0:
            self.vprint(f"{player_handler_p.name} ran out of time!")
            return -100
        if time_m < 0:
            self.vprint(f"{player_handler_m.name} ran out of time!")
            return 100

        m_score = sum(board[board < 0])
        p_score = sum(board[board > 0])
        player_handler_m.end_game(m_score, p_score)
        player_handler_p.end_game(p_score, m_score)

        self.print_score(p_score, m_score, player_handler_p, player_handler_m)
        return p_score + m_score

    def initialise_board(self, board: np.ndarray, starting_tiles: int) -> None:
        random_rows = random.sample(range(board.shape[0]), starting_tiles)
        board[random_rows, 0] = 1

        random_rows = random.sample(range(board.shape[0]), starting_tiles)
        board[random_rows, -1] = -1

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

    def run_turn(
            self,
            sign: int,
            player_handler: Player,
            board: np.ndarray,
            time_remaining: float,
            turn: int
    ) -> float:
        global board_stats

        total_p = np.sum(board[board > 0])
        total_m = np.sum(board[board < 0])
        self.vprint(f"Score: {total_p:+}, {total_m:+}  ({total_p + total_m:+})")

        if self.output is not None:
            board_str = display_board_text(board)
            self.vprint(board_str)

        moves_remaining = 3

        self.vprint(f"### {player_handler.name} ({'+' if sign > 0 else '-'}) ###  (time={time_remaining:.2f})")
        time_taken = 0.
        while moves_remaining > 0:
            player_board = get_player_restricted_board(board, sign)
            start_time = time.time()
            move, pos = player_handler.get_move(
                player_board, turn, moves_remaining, time_remaining
            )
            time_taken += time.time() - start_time
            result = self.do_move(move, pos, sign, moves_remaining, board)
            move_str = f"{move} ({','.join([str(p) for p in pos])})"
            self.vprint(f"{move_str:<20}  |  {result}")
            player_handler.handle_move_result(move, turn, pos, result)
            board_stats.record_move(sign, move, pos, result, turn)
            moves_remaining -= self.moves_required[move]
        board_stats.end_turn(sign, turn, board)
        return time_taken

    def do_fertilise(self, pos: List[int], sign: int, board: np.ndarray) -> str:

        row, col = pos[0], pos[1]
        if sign * board[row][col] > 0:
            board[row][col] += sign
            return "OK"
        else:
            self.vprint("do_fertilise: tile not owned by player")
            return "error"

    def do_plant(self, pos: List[int], sign: int, board: np.ndarray) -> str:

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

    def do_scout(self, pos: List[int], _sign: int, board: np.ndarray) -> str:

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

    def do_colonise(self, pos: List[int], sign: int, board: np.ndarray) -> str:

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

    def do_spray(self, pos: List[int], sign: int, board: np.ndarray) -> str:

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

    def do_bomb(self, pos: List[int], sign: int, board: np.ndarray) -> str:

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
            board: np.ndarray
    ):
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
            return self.do_fertilise(pos, sign, board)
        elif move == 'plant':
            return self.do_plant(pos, sign, board)
        elif move == 'scout':
            return self.do_scout(pos, sign, board)
        elif move == 'colonise':
            return self.do_colonise(pos, sign, board)
        elif move == 'spray':
            return self.do_spray(pos, sign, board)
        else:  # move == 'bomb':
            return self.do_bomb(pos, sign, board)

    def vprint(self, *args, **kwargs):
        if not self.output:
            return
        elif self.output == "stdout":
            print(*args, **kwargs)
        else:
            kwargs['file'] = self.outfile
            print(*args, **kwargs)
