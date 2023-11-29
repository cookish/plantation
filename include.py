def get_player_restricted_board(board, player):
    """ Returns a copy of the board with only the player's tiles. """

    num_rows = len(board)
    num_cols = len(board[0])

    player_board = [[0 for _ in range(num_cols)] for _ in range(num_rows)]
    for row in range(num_rows):
        for col in range(num_cols):
            if board[row][col] * player > 0:
                player_board[row][col] = board[row][col]
    return player_board
