import random
import time
from typing import List

import numpy as np

from plantation.board_stats import BoardStats
from plantation.player import Player
from plantation.include import get_player_restricted_board

board_stats = BoardStats()


moves_required = {
    'fertilise': 1,
    'plant': 1,
    'scout': 1,
    'colonise': 2,
    'spray': 2,
    'bomb': 2
}
bomb_damage = 4
verbose = True


def run_game(
        player_handler_p: Player,
        player_handler_m: Player,
        num_rows: int,
        num_cols: int,
        max_turns: int,
        starting_tiles: int,
        starting_seconds: float,
        time_increment: float
) -> float:

    board = np.zeros((num_rows, num_cols), dtype=np.byte)
    initialise_board(board, starting_tiles)
    player_handler_m.start_game(board.shape, sign=-1)
    player_handler_p.start_game(board.shape, sign=1)

    time_p = starting_seconds
    time_m = starting_seconds
    for turn in range(1, max_turns+1):
        vprint()
        vprint("--------------------------------------------------------------")
        vprint(f"Turn {turn}")
        vprint("=========")
        t = run_turn(1, player_handler_p, board, time_p, turn)
        time_p = time_p - t + time_increment
        if time_p < 0:
            break
        vprint()
        t = run_turn(-1, player_handler_m, board, time_m, turn)
        time_m = time_m - t + time_increment
        if time_m < 0:
            break

    board_stats.end_game()

    vprint("********** Game over! **********")
    if time_p < 0:
        vprint(f"{player_handler_p.name} ran out of time!")
        return -100
    if time_m < 0:
        vprint(f"{player_handler_m.name} ran out of time!")
        return 100

    m_score = sum(board[board < 0])
    p_score = sum(board[board > 0])
    player_handler_m.end_game(m_score, p_score)
    player_handler_p.end_game(p_score, m_score)

    print_score(p_score, m_score, player_handler_p, player_handler_m)
    return p_score + m_score


def initialise_board(board: np.ndarray, starting_tiles: int) -> None:
    random_rows = random.sample(range(board.shape[0]), starting_tiles)
    board[random_rows, 0] = 1

    random_rows = random.sample(range(board.shape[0]), starting_tiles)
    board[random_rows, -1] = -1


def print_score(p_score: int, m_score: int, player_p: Player, player_m: Player) -> None:
    final_score = p_score + m_score

    vprint()
    vprint("================ Final score ================")
    vprint(f"{player_p.name}: {p_score:+}")
    vprint(f"{player_m.name}: {m_score:+}")
    if final_score == 0:
        vprint("It's a draw!")
    else:
        winner = player_p.name if final_score > 0 else player_m.name
        vprint(f"{winner} wins by {abs(final_score)} points!")


def run_turn(
        sign: int,
        player_handler: Player,
        board: np.ndarray,
        time_remaining: float,
        turn: int
) -> float:
    global board_stats

    if verbose:
        print_board(board)
    moves_remaining = 3

    vprint(f"### {player_handler.name} ({'+' if sign > 0 else '-'}) ###  (time={time_remaining:.2f})")
    time_taken = 0.
    while moves_remaining > 0:
        player_board = get_player_restricted_board(board, sign)
        start_time = time.time()
        move, pos = player_handler.get_move(
            player_board, turn, moves_remaining, time_remaining
        )
        time_taken += time.time() - start_time
        result = do_move(move, pos, sign, moves_remaining, board)
        move_str = f"{move} ({','.join([str(p) for p in pos])})"
        vprint(f"{move_str:<20}  |  {result}")
        player_handler.handle_move_result(move, turn, pos, result)
        board_stats.record_move(sign, move, pos, result, turn)
        moves_remaining -= moves_required[move]
    board_stats.end_turn(sign, turn, board)
    return time_taken


def do_fertilise(pos: List[int], sign: int, board: np.ndarray) -> str:

    row, col = pos[0], pos[1]
    if sign * board[row][col] > 0:
        board[row][col] += sign
        return "OK"
    else:
        vprint("do_fertilise: tile not owned by player")
        return "error"


def do_plant(pos: List[int], sign: int, board: np.ndarray) -> str:

    row, col = pos[0], pos[1]
    if board[row][col] * sign > 0:
        vprint("do_plant: target tile already owned by player")
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

    vprint("do_plant: no adjacent tiles owned by player")
    return "error"


def do_scout(pos: List[int], _sign: int, board: np.ndarray) -> str:

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


def do_colonise(pos: List[int], sign: int, board: np.ndarray) -> str:

    row, col, source_row, source_col = pos[0], pos[1], pos[2], pos[3]
    if board[row][col] * sign > 0:
        vprint("do_colonise: target tile already owned by player")
        return "error"
    elif board[source_row][source_col] * sign < 2:
        vprint("do_colonise: source tile count less than 2")
        return "error"

    elif board[row][col] * sign < 0:
        return f"occupied {board[row][col]}"
    else:
        board[row][col] = sign
        board[source_row][source_col] -= sign
        return "OK"


def do_spray(pos: List[int], sign: int, board: np.ndarray) -> str:

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


def do_bomb(pos: List[int], sign: int, board: np.ndarray) -> str:

    row, col = pos[0], pos[1]
    if board[row][col] * sign > 0:

        vprint(f"do_bomb: target tile owned by player")
        return "error"
    else:
        levels_reduced = min(abs(board[row][col]), bomb_damage)
        board[row][col] += sign * levels_reduced
        return f"OK {levels_reduced}"


def do_move(
        move: str,
        pos: List[int],
        sign: int,
        moves_remaining: int,
        board: np.ndarray
):
    if len(pos) < 2:
        vprint(f"Invalid position: {pos}")
        return "error"
    row, col = pos[0], pos[1]
    if row < 0 or row >= board.shape[0] or col < 0 or col >= board.shape[1]:
        vprint(f"Invalid location: ({row}, {col})")
        return "error"
    if move not in moves_required.keys():
        vprint(f"Invalid move: {move}")
        return "error"
    if moves_required[move] > moves_remaining:
        vprint(f"Not enough moves remaining for {move}")
        return "error"

    if move == 'fertilise':
        return do_fertilise(pos, sign, board)
    elif move == 'plant':
        return do_plant(pos, sign, board)
    elif move == 'scout':
        return do_scout(pos, sign, board)
    elif move == 'colonise':
        return do_colonise(pos, sign, board)
    elif move == 'spray':
        return do_spray(pos, sign, board)
    else:  # move == 'bomb':
        return do_bomb(pos, sign, board)


def print_board(board):
    num_rows = board.shape[0]
    num_cols = board.shape[1]
    total_p = np.sum(board[board > 0])
    total_m = np.sum(board[board < 0])
    print(f"Score: {total_p:+}, {total_m:+}  ({total_p + total_m:+})")
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


def vprint(*args, **kwargs):
    if verbose:
        print(*args, **kwargs)
