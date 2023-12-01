from player import Player
from typing import List
from include import get_player_restricted_board
import numpy as np
import random

moves_required = {
    'fertilise': 1,
    'plant': 1,
    'colonise': 2,
    'spray': 2,
    'bomb': 2
}
bomb_damage = 4


def run_game(
        player_handler_p: Player,
        player_handler_m: Player,
        num_rows: int,
        num_cols: int,
        max_turns: int,
        starting_tiles: int
) -> np.array:

    board = np.zeros((num_rows, num_cols), dtype=int)
    initialise_board(board, starting_tiles)
    for turn in range(1, max_turns+1):
        print()
        print("---------------------------------------------------------------")
        print(f"Turn {turn}")
        print("=========")
        run_turn(1, player_handler_p, board)
        print()
        run_turn(-1, player_handler_m, board)

    print("********** Game over! **********")
    return board


def initialise_board(board: np.array, starting_tiles: int) -> None:
    random_rows = random.sample(range(board.shape[0]), starting_tiles)
    board[random_rows, 0] = 1

    random_rows = random.sample(range(board.shape[0]), starting_tiles)
    board[random_rows, -1] = -1


def score_board(board):
    total_m = np.sum(board[board < 0])
    total_p = np.sum(board[board > 0])
    final_score = total_p + total_m

    print()
    print("================ Final score ================")
    print(f"Plus: {total_p:+}")
    print(f"Minus: {total_m:+}")
    if final_score == 0:
        print("It's a draw!")
    else:
        print(f"{'Plus' if final_score > 0 else 'Minus'} "
              f"wins by {abs(final_score)} points!")
    return final_score


def run_turn(player: int, player_handler: Player, board: np.array):
    print_board(board)
    moves_remaining = 3
    name = "Plus" if player == 1 else "Minus"
    print(f"### {name} ###")
    while moves_remaining > 0:
        player_board = get_player_restricted_board(board, player)
        move, pos = player_handler.get_move(player_board, moves_remaining)
        result = do_move(move, pos, player, moves_remaining, board)
        move_str = f"{move} ({','.join([str(p) for p in pos])})"
        print(f"{move_str:<20}  |  {result}")
        player_handler.handle_move_result(move, pos, result)
        moves_remaining -= moves_required[move]


def do_fertilise(pos: List[int], player: int, board: np.array) -> str:

    row, col = pos[0], pos[1]
    if player * board[row][col] > 0:
        board[row][col] += player
        return "OK"
    else:
        print("do_fertilise: tile not owned by player")
        return "error"


def do_plant(pos: List[int], player: int, board: np.array) -> str:

    row, col = pos[0], pos[1]
    if board[row][col] * player > 0:
        print("do_plant: target tile already owned by player")
        return "error"
    elif board[row][col] * player < 0:
        return f"occupied {board[row][col]}"

    # now we know that board[row][col] == 0
    for delta_r, delta_c in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        test_row = row + delta_r
        test_col = col + delta_c
        if 0 <= test_row < board.shape[0] and 0 <= test_col < board.shape[1]:
            if board[row + delta_r][col + delta_c] * player > 0:
                board[row][col] = player
                return "OK"

    print("do_plant: no adjacent tiles owned by player")
    return "error"


def do_scout(pos: List[int], _player: int, board: np.array) -> str:

    row, col = pos[0], pos[1]
    results = []
    for delta_c in (-1, 0, 1):
        for delta_r in (-1, 0, 1):
            test_row = row + delta_r
            test_col = col + delta_c
            if 0 <= test_row < board.shape[0] \
                    and 0 <= test_col < board.shape[1]:
                results.append(board[row + delta_r][col + delta_c])
    return "OK " + ",".join([str(x) for x in results])


def do_colonise(pos: List[int], player: int, board: np.array) -> str:

    row, col, source_row, source_col = pos[0], pos[1], pos[2], pos[3]
    if board[row][col] * player > 0:
        print("do_colonise: target tile already owned by player")
        return "error"
    elif board[source_row][source_col] * player < 2:
        print("do_colonise: source tile count less than 2")
        return "error"

    elif board[row][col] * player < 0:
        return f"occupied {board[row][col]}"
    else:
        board[row][col] = player
        board[source_row][source_col] -= player
        return "OK"


def do_spray(pos: List[int], player: int, board: np.array) -> str:

    row, col = pos[0], pos[1]
    total = 0
    for delta_r, delta_c in [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]:
        test_row = row + delta_r
        test_col = col + delta_c
        if 0 <= test_row < board.shape[0] and 0 <= test_col < board.shape[1]:
            if board[test_row][test_col] * player < 0:
                board[row + delta_r][col + delta_c] += player
                total += 1
    return f"OK {total}"


def do_bomb(pos: List[int], player: int, board: np.array) -> str:

    row, col = pos[0], pos[1]
    if board[row][col] * player > 0:

        print(f"do_bomb: target tile owned by player")
        return "error"
    else:
        levels_reduced = min(abs(board[row][col]), bomb_damage)
        board[row][col] += player * levels_reduced
        return f"OK {levels_reduced}"


def do_move(
        move: str,
        pos: List[int],
        player: int,
        moves_remaining: int,
        board: np.array
):
    if len(pos) < 2:
        print(f"Invalid position: {pos}")
        return "error"
    row, col = pos[0], pos[1]
    if row < 0 or row >= board.shape[0] or col < 0 or col >= board.shape[1]:
        print(f"Invalid location: ({row}, {col})")
        return "error"
    if move not in moves_required.keys():
        print(f"Invalid move: {move}")
        return "error"
    if moves_required[move] > moves_remaining:
        print(f"Not enough moves remaining for {move}")
        return "error"

    if move == 'fertilise':
        return do_fertilise(pos, player, board)
    elif move == 'plant':
        return do_plant(pos, player, board)
    elif move == 'scout':
        return do_scout(pos, player, board)
    elif move == 'colonise':
        return do_colonise(pos, player, board)
    elif move == 'spray':
        return do_spray(pos, player, board)
    else:  # move == 'bomb':
        return do_bomb(pos, player, board)


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
