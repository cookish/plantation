from itertools import cycle
import random
from typing import Tuple, List, Optional

import numpy as np
from scipy.signal import convolve2d

from plantation.player import Player


class ScryAndDie (Player):
    opp_board = None
    turn_scouted = None
    mode = ''
    scry_locations = None
    cross_coords = np.array([
        [-1, 0], [0, -1], [0, 0], [0, 1], [1, 0]
    ])

    def __init__(
            self, sign: int,
            name: Optional[str] = None
    ):
        super().__init__(sign, name)

    def start_game(self, board_shape: Tuple[int]):
        self.opp_board = np.zeros(board_shape)
        self.turn_scouted = np.zeros(board_shape)
        self.scry_locations = cycle(
            [(r, c) for c in [1, 3, 6, 9] for r in [1, 4, 7, 9]]
        )

    def get_move(
            self,
            board: np.ndarray,
            turn: int,
            moves_remaining: int,
            time_remaining: float,
    ) -> Tuple[str, List[int]]:

        first_move = moves_remaining == 3

        # spend some time in the beginning growing
        if turn <= 5:
            return self.get_grow(board, moves_remaining)

        # enough of this pacifist nonsense, let's get some eyes on the prey
        if turn == 6:
            if first_move:
                # start with estimated score for the opponent's first two cols
                av_last_col = 8/11
                av_second_last_col = 5/11
                if self.sign > 0:
                    self.opp_board[:, -1] = av_last_col
                    self.opp_board[:, -2] = av_second_last_col
                else:
                    self.opp_board[:, 0] = av_last_col
                    self.opp_board[:, 1] = av_second_last_col

            # all three moves are a scout
            return self.get_scry()

        else:  # self.turn >= 7
            # set the strategy for the rest of this turn
            if first_move:
                attack_score, _best_move, _best_score = \
                    self.get_best_offensive_move(board, turn)

                grow_score = 3
                grow_prob = grow_score / (grow_score + attack_score)

                # adjust the probability using an S-curve to make it more likely
                # to select the option it thinks is optimal
                if grow_prob != 1:
                    # from https://stats.stackexchange.com/a/289477
                    grow_prob = 1 / (1 + (grow_prob / (1 - grow_prob))**-3)

                if random.random() < grow_prob:
                    self.mode = 'grow'
                else:
                    self.mode = 'kill'

            if self.mode == 'grow':
                return self.get_grow(board, moves_remaining)
            else:
                return self.get_scry_and_die(board, turn, moves_remaining)

    def get_best_offensive_move(
            self, board: np.ndarray, turn: int
    ) -> Tuple[float, str, List[int]]:
        estimated_board = self.opp_board + \
                          (turn - self.turn_scouted) * 1.5 / 121.
        estimated_board[board != 0] = 0

        bomb_score = min(np.max(estimated_board), 4)

        spray_board = np.where(estimated_board > 1, 1, estimated_board)
        spray_kernel = np.array([[0, 1, 0],
                                 [1, 1, 1],
                                 [0, 1, 0]])

        spray_scores = convolve2d(spray_board, spray_kernel,
                                  mode='same', boundary='fill', fillvalue=0)
        spray_score = np.max(spray_scores)
        if bomb_score > spray_score:
            bomb_pos = np.unravel_index(
                np.argmax(estimated_board), estimated_board.shape)

            return bomb_score, 'bomb', list(bomb_pos)
        else:   # spray_score >= bomb_score
            spray_pos = np.unravel_index(
                np.argmax(spray_scores), spray_scores.shape)
            return spray_score, 'spray', list(spray_pos)

    def get_scry_and_die(
            self, board: np.ndarray, turn: int, moves_remaining: int
    ) -> Tuple[str, List[int]]:
        if moves_remaining == 3:  # we must scout
            return self.get_scry()
        else:  # we must kill
            best_offensive_score, best_offensive_move, best_offensive_pos = \
                self.get_best_offensive_move(board, turn)
            return best_offensive_move, best_offensive_pos

    def get_scry(self) -> Tuple[str, List[int]]:
        scry_row, scry_col = next(self.scry_locations)
        return 'scout', [scry_row, scry_col]

    def get_grow(
            self, board: np.ndarray, moves_remaining: int
    ) -> Tuple[str, List[int]]:
        zero_tiles = np.argwhere(board == 0)
        multi_tiles = np.argwhere(np.abs(board) > 1)
        move_probabilities = {'fertilise': 5}
        if len(zero_tiles) > 0:
            move_probabilities['plant'] = 5
            if moves_remaining > 1 and len(multi_tiles) > 0:
                move_probabilities['colonise'] = 1

        move = random.choices(
            list(move_probabilities.keys()),
            weights=list(move_probabilities.values()))[0]

        rows = board.shape[0]
        cols = board.shape[1]

        # pick a random tile empty tile adjacent to a non-zero tile
        if move == 'plant':
            non_zero_tiles = np.argwhere(board != 0)
            row, col = random.choice(non_zero_tiles)
            plant_options = []
            for delta_r, delta_c in [(0, -1), (0, 1), (1, 0), (-1, 0)]:
                test_row = row + delta_r
                test_col = col + delta_c
                if 0 <= test_row < rows and 0 <= test_col < cols:
                    if board[test_row][test_col] == 0:
                        plant_options.append([test_row, test_col])
            if len(plant_options) > 0:
                return move, random.choice(plant_options)
            else:
                move = 'fertilise'  # fall back to this option

        # pick a random non-zero tile to fertilise
        if move == 'fertilise':
            non_zero_tiles = np.argwhere(board != 0)
            if len(non_zero_tiles) > 0:
                return move, random.choice(non_zero_tiles)

        if move == 'colonise':
            if len(multi_tiles) > 0 and len(zero_tiles) > 0:
                source_row, source_col = random.choice(multi_tiles)
                target_row, target_col = random.choice(zero_tiles)
                return move, [target_row, target_col, source_row, source_col]

        # there is nowhere we can move...
        return 'scout', [0, 0]

    def handle_move_result(self, move, turn, pos, result):
        code = result.split(' ')[0]

        if move == 'scout':
            if code == 'OK':
                vals_str = result.split(' ')[1]
                vals = np.array([int(n) for n in vals_str.split(',')])
                vals[vals * self.sign > 0] = 0  # only record opponent's squares
                self.opp_board[pos[0]-1:pos[0]+2, pos[1]-1:pos[1]+2] \
                    = abs(vals.reshape((3, 3)))
                self.turn_scouted[
                    pos[0]-1:pos[0]+2, pos[1]-1:pos[1]+2
                ] = turn
        if move in ('plant', 'colonise'):
            if code == 'occupied':
                val = abs(int(result.split(' ')[1]))
                self.opp_board[pos[0], pos[1]] = val
                self.turn_scouted[pos[0], pos[1]] = turn

        if move in ('spray', 'bomb'):
            if code == 'OK':
                if move == 'bomb':
                    # subtract at most 4
                    val_to_subtract = min(self.opp_board[pos[0], pos[1]], 4)
                    self.opp_board[pos[0], pos[1]] -= val_to_subtract
                else:  # move = 'spray'
                    for row, col in self.cross_coords + [pos[0], pos[1]]:
                        if 0 <= row < self.opp_board.shape[0] and \
                                0 <= col < self.opp_board.shape[1]:
                            # subtract at most 1
                            val_to_subtract = min(self.opp_board[row, col], 1)
                            self.opp_board[row, col] -= val_to_subtract
