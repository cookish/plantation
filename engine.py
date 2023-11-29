from player import Player
from random_player_plus import RandomPlayerPlus
from typing import List
from include import get_player_restricted_board
import numpy as np

num_rows = 11
num_cols = 11
max_turns = 500

moves_required = {
    'fertilise': 1,
    'plant': 1,
    'colonise': 2,
    'spray': 2,
    'bomb': 2
}


def run_game(player_handler_p, player_handler_m, board):

    turn = 0
    while turn < max_turns:
        print()
        print("---------------------------------------------------------------")
        print(f"Turn {turn}")
        print("=========")
        run_turn(1, player_handler_p, board)
        print()
        run_turn(-1, player_handler_m, board)
        turn += 1

    print("Game over")
    print_board(board)


def score_board(board):
    total_m = abs(np.sum(board[board < 0]))
    total_p = np.sum(board[board > 0])
    print(f"Total for Plus: {total_p}")
    print(f"Total for Minus: {total_m}")
    if total_p > total_m:
        print(f"Plus wins by {total_p - total_m} points!")
    elif total_p < total_m:
        print(f"Minus wins by {total_m - total_p} points!")
    else:
        print("It's a draw!")


def run_turn(player: int, player_handler: Player, board: np.array):
    print_board(board)
    moves_remaining = 3
    name = "Plus" if player == 1 else "Minus"
    print(f"### {name} ###")
    while moves_remaining > 0:
        player_board = get_player_restricted_board(board, player)
        move, pos = player_handler.get_move(player_board, moves_remaining)
        print(f"Move: {move} ({','.join([str(p) for p in pos])})")
        result = do_move(move, pos, player, moves_remaining, board)
        print(f"Result: {result}")
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
        if 0 <= row + delta_r < num_rows and 0 <= col + delta_c < num_cols:
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
            if 0 <= row + delta_r < num_rows and 0 <= col + delta_c < num_cols:
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
        if 0 <= row + delta_r < num_rows and 0 <= col + delta_c < num_cols:
            if board[row + delta_r][col + delta_c] * player < 0:
                board[row + delta_r][col + delta_c] += player
                total += 1
    return f"OK {total}"


def do_bomb(pos: List[int], player: int, board: np.array) -> str:

    row, col = pos[0], pos[1]
    if board[row][col] * player > 0:

        print(f"do_bomb: target tile owned by player")
        return "error"
    else:
        levels_reduced = min(abs(board[row][col]), 3)
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
    if row < 0 or row >= num_rows or col < 0 or col >= num_cols:
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


def main():
    board = np.zeros((num_rows, num_cols), dtype=int)
    board[1][1] = 1
    board[4][4] = -1
    probs_p = {
        'fertilise': 0.3,
        'plant': 0.5,
        'colonise': 0.1,
        'spray': 0.05,
        'bomb': 0.05
    }
    # probs_m = {
    #     'fertilise': 0.1,
    #     'plant': 0.2,
    #     'colonise': 0.05,
    #     'spray': 0.4,
    #     'bomb': 0.25
    # }
    probs_m = {
        'plant': 0.1,
        'fertilise': 0.1,
        'spray': 0.7,
        'bomb': 0.1
    }
    player_handler_p = RandomPlayerPlus(1, probs_p)
    player_handler_m = RandomPlayerPlus(-1, probs_m)
    run_game(player_handler_p, player_handler_m, board)
    score_board(board)


if __name__ == "__main__":
    main()
