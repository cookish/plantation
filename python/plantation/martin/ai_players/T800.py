import random
from typing import Tuple, List, Optional, Any

import numpy as np
from scipy.signal import convolve2d

from plantation.player import Player


def s_curve(x, factor: float = 3):
    # from https://stats.stackexchange.com/a/289477
    if x == 1 or x == 0:
        return x
    else:
        return 1 / (1 + (x / (1 - x)) ** (-factor))


def s_curve_probs(probs: List[float], factor: float = 3):
    # from https://stats.stackexchange.com/a/289477
    total = sum(probs)
    scaled_probs = [s_curve(p / total, factor) for p in probs]
    new_total = sum(scaled_probs)
    new_probs = [p / new_total for p in scaled_probs]
    return new_probs


class T800 (Player):
    opp_board = None
    turn_scouted = None
    cross_coords = np.array([
        [-1, 0], [0, -1], [0, 0], [0, 1], [1, 0]
    ])
    spray_kernel = np.array([[0, 1, 0],
                             [1, 1, 1],
                             [0, 1, 0]])
    scout_kernel = np.array([[1, 1, 1],
                             [1, 1, 1],
                             [1, 1, 1]])

    def __init__(
            self,
            name: Optional[str] = None,
            scout_propensity: float = 1,
            initial_turns_of_growth: int = 7,
            s_curve_factor: float = 3,
            relative_plant_propensity: float = 5,
            relative_fertilise_propensity: float = 5,
            relative_colonise_propensity: float = 1,

    ):
        super().__init__(name)
        self.scout_score_normalisation = 5 * 9 * 10 / scout_propensity
        self.initial_turns_of_growth = initial_turns_of_growth
        self.s_curve_factor = s_curve_factor
        self.relative_plant_propensity = relative_plant_propensity
        self.relative_fertilise_propensity = relative_fertilise_propensity
        self.relative_colonise_propensity = relative_colonise_propensity

    def start_game(self, board_shape: Tuple[int], sign: int):
        super().start_game(board_shape, sign)
        self.opp_board = np.zeros(board_shape)
        self.turn_scouted = np.zeros(board_shape)

    def get_move(
            self,
            board: np.ndarray,
            turn: int,
            moves_remaining: int,
            time_remaining: float,
    ) -> Tuple[str, List[int]]:

        # spend some time in the beginning growing
        if turn <= self.initial_turns_of_growth:
            return self.get_grow(board, moves_remaining)

        else:  # self.turn >= self.turns_of_growth
            attack_score, attack_move, attack_targets = \
                self.get_best_offensive_move(self.opp_board)

            # Our course is clear: kill where possible.
            # If only one move remaining, plant to kill time, then we can kill next turn
            if attack_score >= 3:
                if moves_remaining >= 2:
                    return attack_move, random.choice(attack_targets)
                else:
                    return self.get_grow(board, moves_remaining)

            else:
                scout_payoff, scout_targets = self.get_scout_payoff(board, moves_remaining, turn)
                grow_payoff = 1
                attack_payoff = attack_score / 2.  # two moves for spray and bomb
                if moves_remaining < 2:
                    attack_payoff = 0

                scout_chance, grow_chance, attack_chance = s_curve_probs(
                    [scout_payoff, grow_payoff, attack_payoff], self.s_curve_factor)

                r = random.random()
                if r < scout_chance:
                    scout_coords = random.choice(scout_targets)
                    # never scout in the edges -- waste of info
                    scout_coords[0] = max(scout_coords[0], 1)
                    scout_coords[0] = min(scout_coords[0], board.shape[0] - 2)
                    scout_coords[1] = max(scout_coords[1], 1)
                    scout_coords[1] = min(scout_coords[1], board.shape[1] - 2)
                    return 'scout', scout_coords
                elif r < scout_chance + grow_chance:
                    return self.get_grow(board, moves_remaining)
                else:
                    return attack_move, random.choice(attack_targets)

    def get_scout_payoff(self, board: np.ndarray, moves_remaining: int, turn: int
                         ) -> Tuple[float, List[List[int]]]:

        rows, cols = board.shape
        gradient = (101. - turn) / 100.
        row = np.array([5 + (c - 4) * gradient for c in range(cols)])
        scout_board = np.tile(row, (rows, 1))

        if self.sign < 0:
            # reverse scout_board
            scout_board = scout_board[:, ::-1]

        # if board is controlled by player, no need to scout
        scout_board = np.where(board == 0, scout_board, 0)

        # multiply value by number of turns since scouted
        scout_board = scout_board * (turn - self.turn_scouted)

        # convolve with a 3x3 scout kernel
        scout_scores = convolve2d(scout_board, self.scout_kernel,
                                  mode='same', boundary='fill', fillvalue=0)

        best_score = np.max(scout_scores)
        best_scouts = np.argwhere(scout_scores == best_score).tolist()
        scout_payoff = best_score / self.scout_score_normalisation
        # prefer scouting at start of turn: 3->1, 2->0.8, 1->0.6
        scout_payoff *= 0.2 * moves_remaining + 0.4
        return scout_payoff, best_scouts

    def get_best_offensive_move(
            self, board: np.ndarray
    ) -> Tuple[float, str, List[List[Any]]]:
        abs_board = abs(board)
        max_tile = np.max(abs_board)
        bomb_score = min(max_tile, 4)

        spray_board = np.where(abs_board > 1, 1, abs_board)

        spray_scores = convolve2d(spray_board, self.spray_kernel,
                                  mode='same', boundary='fill', fillvalue=0)
        spray_score = np.max(spray_scores)
        if bomb_score > spray_score:
            bomb_coords = np.argwhere(abs_board == max_tile).tolist()
            return bomb_score, 'bomb', bomb_coords

        else:   # spray_score >= bomb_score
            spray_coords = np.argwhere(spray_scores == spray_score).tolist()
            return spray_score, 'spray', spray_coords

    def get_grow(
            self, board: np.ndarray, moves_remaining: int
    ) -> Tuple[str, List[int]]:
        # zero_tiles = np.argwhere(board == 0)
        # multi_tiles = np.argwhere(np.abs(board) > 1)
        move_probabilities = {'fertilise': self.relative_fertilise_propensity}
        if np.any(board == 0):
            move_probabilities['plant'] = self.relative_plant_propensity
            if moves_remaining > 1 and np.any(np.abs(board) > 1):
                move_probabilities['colonise'] = self.relative_colonise_propensity

        move = random.choices(
            list(move_probabilities.keys()),
            weights=list(move_probabilities.values()))[0]

        rows = board.shape[0]
        cols = board.shape[1]

        # pick a random tile empty tile adjacent to a non-zero tile
        if move == 'plant':
            non_zero_tiles = np.argwhere(board != 0).tolist()
            plant_options = set()
            for row, col in non_zero_tiles:
                for delta_r, delta_c in [(0, -1), (0, 1), (1, 0), (-1, 0)]:
                    test_row = row + delta_r
                    test_col = col + delta_c
                    if 0 <= test_row < rows and 0 <= test_col < cols:
                        if board[test_row][test_col] == 0:
                            plant_options.add((test_row, test_col))

            if len(plant_options) > 0:

                # exclude squares we know belong to opponent
                known_opp_tiles = set(tuple(k) for k in np.argwhere(self.opp_board != 0))
                filtered_options = plant_options - known_opp_tiles

                if len(filtered_options) > 0:
                    # now we want to sort by the maximum damage our opponent could do to us with a spray
                    # count 1, 2 and 3 as the same (don't want to discourage a line) but penalise 4 and 5
                    spray_board = np.where(board != 0, 1, board)
                    spray_damage_board = convolve2d(spray_board, self.spray_kernel,
                                                    mode='same', boundary='fill', fillvalue=0)

                    max_damage_scores = [
                        max(
                            spray_damage_board[option[0] + offset[0], option[1] + offset[1]]
                            for offset in self.cross_coords
                            if 0 <= option[0] + offset[0] < rows and 0 <= option[1] + offset[1] < cols
                        )
                        for option in filtered_options
                    ]

                    # if opponent can currently do 2 damage with a spray, once we plant here it will increase to 3. This
                    # is the ceiling: anything more than this we want to discourage
                    max_allowable_damage = 2
                    max_damage_scores = [max(s, max_allowable_damage) for s in max_damage_scores]
                    best_max_damage_score = min(max_damage_scores)
                    filtered_options = [c[0] for c in zip(filtered_options, max_damage_scores)
                                        if c[1] == best_max_damage_score]

                    if len(filtered_options) > 0:
                        return move, random.choice(list(filtered_options))

        if move == 'grow':
            move = 'fertilise'

        # pick a random non-zero tile to fertilise
        if move == 'fertilise':
            non_zero_tiles = np.argwhere(board != 0).tolist()
            if len(non_zero_tiles) > 0:
                # we want to sort by score mod 4 (ascending)
                mod_scores = [abs(board[c[0], c[1]]) % 4 for c in non_zero_tiles]
                best_score = min(mod_scores)
                filtered_non_zero_tiles = [c[0] for c in zip(non_zero_tiles, mod_scores) if c[1] == best_score]
                return move, random.choice(filtered_non_zero_tiles)

        if move == 'colonise':
            multi_tiles = np.argwhere(np.abs(board) > 1)
            if len(multi_tiles) > 0:
                combined_board = board + self.opp_board
                target_options = np.argwhere(np.abs(combined_board) == 0).tolist()
                if len(target_options) > 0:

                    # prioritise targets that don't have existing player tiles close by
                    dist_1_kernel = self.scout_kernel
                    dist_2_kernel = np.array([
                        [0, 0, 1, 0, 0],
                        [0, 1, 1, 1, 0],
                        [1, 1, 1, 1, 1],
                        [0, 1, 1, 1, 0],
                        [0, 0, 1, 0, 0],
                    ])
                    score_dist_1 = convolve2d(abs(board), dist_1_kernel,
                                              mode='same', boundary='fill', fillvalue=0)
                    score_dist_2 = convolve2d(abs(board), dist_2_kernel,
                                              mode='same', boundary='fill', fillvalue=0)
                    combined_score = score_dist_1 * 10 + score_dist_2
                    best_target_score = np.min([combined_score[*c] for c in target_options])
                    best_target_options = [c for c in target_options if combined_score[*c] == best_target_score]

                    source_scores = [abs(board[*c]) % 4 for c in multi_tiles]
                    best_source_score = np.min(source_scores)
                    best_source_options = [c[0] for c in zip(multi_tiles, source_scores) if c[1] == best_source_score]

                    source_row, source_col = random.choice(best_source_options)
                    target_row, target_col = random.choice(best_target_options)
                    return move, [target_row, target_col, source_row, source_col]

        # there is nowhere we can move...
        return 'scout', [5, 5]

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
