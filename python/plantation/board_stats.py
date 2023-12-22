from typing import List
import numpy as np
import h5py
from datetime import datetime
import os

from plantation.include import get_player_restricted_board


def create_or_append_hdf5(filename, data, dataset_name):
    with h5py.File(filename, "a") as f:  # 'a' mode for read/write access and create file if it doesn't exist
        if dataset_name in f:
            # Append to the existing dataset
            dataset = f[dataset_name]
            dataset.resize((dataset.shape[0] + 1,) + dataset.shape[1:])
            dataset[-1] = data
        else:
            # Create a new dataset
            # 'maxshape' is set to None for unlimited dimensions
            f.create_dataset(dataset_name, data=data, maxshape=(None,) + data.shape)


class BoardStats:
    board_info = None
    out_dir = ''
    results = {}

    def __init__(self):
        self.board_info = {
            -1: np.zeros((11, 11, 11), "byte"),
            1: np.zeros((11, 11, 11), "byte")
        }
        self.init_results()

        # 0: player board
        # 1: known tiles of opponent board
        # 2: turn when known
        # 3: most recent bomb damage
        # 4: turn when the bomb was deployed
        # 5: second most recent bomb damage
        # 6: turn when the second recent bomb was deployed
        # 7: most recent spray damage
        # 8: turn when the spray was deployed
        # 9: second most recent spray damage
        # 10: turn when the second recent spray was deployed

    def init_results(self):
        self.results = {
            'board_info': np.empty((11, 11, 11, 0), dtype=np.byte),
            'turn': np.empty((0, ), dtype=np.byte),
            'sign': np.empty((0, ), dtype=np.byte),
            'opp_board': np.empty((11, 11, 0), dtype=np.byte),
        }

    def record_move(self, sign: int, move: str, pos: List[int], result: str, turn: int):
        board = self.board_info[sign]
        result_code, result_remainder = result.split(' ', maxsplit=1) if ' ' in result else (result, None)
        if result_code == 'error':
            return
        if move == 'scout':
            vals_str = result.split(' ')[1]
            vals = np.array([int(n) for n in vals_str.split(',')])
            vals[vals * sign > 0] = 0  # only record opponent's squares
            board[pos[0] - 1:pos[0] + 2, pos[1] - 1:pos[1] + 2, 1] \
                = abs(vals.reshape((3, 3)))
            board[pos[0] - 1:pos[0] + 2, pos[1] - 1:pos[1] + 2, 2] = turn
        elif move == 'spray':
            board[pos[0], pos[1], 9] = board[pos[0], pos[1], 7]
            board[pos[0], pos[1], 10] = board[pos[0], pos[1], 8]
            board[pos[0], pos[1], 7] = int(result_remainder)
            board[pos[0], pos[1], 8] = turn
        elif move == 'bomb':
            board[pos[0], pos[1], 5] = board[pos[0], pos[1], 3]
            board[pos[0], pos[1], 6] = board[pos[0], pos[1], 4]
            board[pos[0], pos[1], 3] = int(result_remainder)
            board[pos[0], pos[1], 4] = turn
        elif move in ('plant', 'colonise'):
            if result_remainder is not None and result_remainder[0:2] == "oc":
                val = int(result_remainder.split(' ')[1])
                board[pos[0], pos[1], 1] = val
                board[pos[0], pos[1], 2] = turn
        elif move == 'fertilise':
            pass

    def end_turn(self, sign, turn, full_board: np.ndarray) -> None:
        player_board = get_player_restricted_board(full_board, sign)
        opp_board = get_player_restricted_board(full_board, -1*sign)
        board = self.board_info[sign]

        board[:, :, 0] = np.abs(player_board)

        # we know opponent has zero score where we have non-zero score
        board[player_board > 0, 1] = 0
        board[player_board > 0, 2] = turn

        out_board_info = board

        # if sign is positive, that means opponent is on the right.
        # we want to flip: always put the opponent on the left
        if sign == 1:
            out_board_info = board[:, ::-1, :]

        out_board_info = np.expand_dims(out_board_info, axis=-1)
        self.results['board_info'] = np.concatenate((self.results['board_info'], out_board_info), axis=-1)

        self.results['turn'] = np.append(self.results['turn'], turn)
        self.results['sign'] = np.append(self.results['sign'], sign)

        opp_board = np.expand_dims(opp_board, axis=-1)
        self.results['opp_board'] = np.concatenate((self.results['opp_board'], opp_board), axis=-1)

    def end_game(self):
        nw = datetime.now()
        out_dir = f'out/{nw}'
        os.makedirs(out_dir)
        for k, v in self.results.items():
            np.save(f'{out_dir}/{k}.npy', v)
        self.init_results()
