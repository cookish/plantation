<?php

class Genetic
{
    /** @var float[] name-indexed genes where each is a float, geometric scaling */
    protected $genes = [];
    protected $name = '';
    protected $sign;

    protected $speciesNumber = 0;
    /**
     * Data on the entire lineage (i.e the population of species in this instance by name)
     *
     * Fields:
     * - nextSpeciesToPlay: int
     * - species: array {
     *      - genes: dictionary
     *      - netWins: int
     * - roundsPlayed: int
     *
     * @var mixed|null JSON
     */
    protected $lineageJson = null;

    protected $friendlyBoard = [];
    protected $turn;
    protected $movesRemaining;
    protected $timeRemaining;

    protected $currentMove = null;
    protected $currentMoveWeight = 0;

    /** @var array[] Negative values when the enemy is there */
    protected $enemyBoard = [];
    protected $knowledgeDate = [];
    /** @var int[][] Squares until nearest friendly square */
    protected $friendlyScore = 0;
    protected $enemyScore = 0;

    protected $myStartingColumn = null;

    const NUM_SPECIES = 10;
    const GAMES_PER_EVOLVE = 10;

    function __construct($name, $sign) {
        $this->name = $name;
        $this->enemyBoard = array_fill(0, 11, array_fill(0, 11, null));
        $this->sign = $sign;

        // load weights
        $filename = __DIR__ . '/' . escapeshellcmd($name) . '.json';
        if (file_exists($filename)) {
            $data = file_get_contents($filename);
            $this->lineageJson = json_decode($data, true);
            $this->speciesNumber = $this->lineageJson['nextSpeciesToPlay'];
            $this->lineageJson['species'] = (array)$this->lineageJson['species'];
            if (isset($this->lineageJson['species'][$this->speciesNumber])) {
                $this->genes = (array)$this->lineageJson['species'][$this->speciesNumber]['genes'];
            }
        } else {
            $this->lineageJson = ['nextSpeciesToPlay' => 0, 'roundsPlayed' => 0, 'species' => [], 'generations' => 0];
        }
    }

    public function getMove($board, $turn, $movesRemaining, $timeRemaining) {
        $this->friendlyBoard = $board;
        $this->turn = $turn;
        $this->movesRemaining = $movesRemaining;
        $this->timeRemaining = $timeRemaining;
        $this->currentMove = null;
        $this->currentMoveWeight = 0;
        //analyse the board somewhat
        $this->friendlyScore = 0;
        $this->enemyScore = 0;
        for ($x = 0; $x <= 10; $x++) {
            for ($y = 0; $y <= 10; $y++) {
                $this->friendlyBoard[$x][$y] = abs($this->friendlyBoard[$x][$y]);
                if ($this->friendlyBoard[$x][$y] > 0) {
                    $this->friendlyScore += $this->friendlyBoard[$x][$y];
                    $this->enemyBoard[$x][$y] = 0;
                    $this->knowledgeDate[$x][$y] = $turn;
                } else {
                    $this->enemyScore += abs($this->enemyBoard[$x][$y]);
                }
            }
        }
        if (is_null($this->myStartingColumn)) {
            for ($x = 0; $x <= 10; $x++) {
                if ($this->friendlyBoard[$x][0] > 0) {
                    $this->myStartingColumn = 0;
                    break;
                }
                if ($this->friendlyBoard[$x][10] > 0) {
                    $this->myStartingColumn = 10;
                    break;
                }
            }
        }

        // find best move
        $this->generatePlantMoves();
        $this->generateFertiliseMoves();
        $this->generateScoutMoves();
        return $this->currentMove;
    }

    /** Used to propose a possible move. Will use the weight to either replace the previous best move, or not */
    protected function proposeMove($move, $params, $weight) {
        $weight = $weight
            + $this->turn * $this->gene($move . 'TurnsPlayed')
            + (100 - $this->turn) * $this->gene($move . 'TurnsLeft')
            + $this->friendlyScore * $this->gene($move . 'FriendlyScore')
            + $this->enemyScore * $this->gene($move . 'EnemyScore')
            + ($this->friendlyScore > 0 ? $this->enemyScore / $this->friendlyScore : 99999) * $this->gene($move . 'ScoreRatio');
        $weight += $this->getRandomFactor(2);
        if ($this->currentMoveWeight == 0 || $this->currentMoveWeight < $weight) {
            $this->currentMove = [$move, $params];
            $this->currentMoveWeight = $weight;
        }
    }

    function generatePlantMoves() {
        for ($x = 0; $x <= 10; $x++) {
            for ($y = 0; $y <= 10; $y++) {
                if ($this->friendlyBoard[$x][$y] == 0 && !$this->enemyBoard[$x][$y]) {
                    if (
                        ($x > 0 && $this->friendlyBoard[$x-1][$y]) ||
                        ($x < 10 && $this->friendlyBoard[$x+1][$y]) ||
                        ($y > 0 && $this->friendlyBoard[$x][$y-1]) ||
                        ($y < 10 && $this->friendlyBoard[$x][$y+1])
                    ) {
                        list($friendlyWeight, $enemyWeight, $friendlyDistance, $enemyDistance) = $this->getDistanceWeights($x, $y, $this->gene('plantFriendlyDistanceScale'), $this->gene('plantEnemyDistanceScale'));
                        $this->proposeMove('plant', [$x, $y],
                            $this->gene('plantWeight')
                            + $friendlyWeight * $this->gene('plantFriendlyDistanceWeight')
                            + $enemyWeight * $this->gene('plantEnemyDistanceWeight')
                            + $enemyDistance * $this->gene('plantEnemyDistance')
                            + ($this->myStartingColumn == 0 ? $y : 10-$y) * $this->gene('plantYPositionFromMySide')
                            + ($this->myStartingColumn == 0 ? 10-$y : $y) * $this->gene('plantYPositionFromEnemySide')
                        );
                    }
                }
            }
        }
    }

    function generateFertiliseMoves() {
        for ($x = 0; $x <= 10; $x++) {
            for ($y = 0; $y <= 10; $y++) {
                if ($this->friendlyBoard[$x][$y] > 0) {
                    list($friendlyWeight, $enemyWeight, $friendlyDistance, $enemyDistance) = $this->getDistanceWeights($x, $y, $this->gene('fertiliseFriendlyDistanceScale'), $this->gene('fertiliseEnemyDistanceScale'));
                    $this->proposeMove('fertilise', [$x, $y],
                        $this->gene('fertiliseWeight')
                        + $friendlyWeight * $this->gene('fertiliseFriendlyDistanceWeight')
                        + $enemyWeight * $this->gene('fertiliseEnemyDistanceWeight')
                        + $enemyDistance * $this->gene('fertiliseEnemyDistance')
                        + ($this->myStartingColumn == 0 ? $y : 10-$y) * $this->gene('plantYPositionFromMySide')
                        + ($this->myStartingColumn == 0 ? 10-$y : $y) * $this->gene('plantYPositionFromEnemySide')
                    );
                }
            }
        }
    }

    function generateScoutMoves() {
        for ($x = 1; $x <= 9; $x++) {
            for ($y = 1; $y <= 9; $y++) {
                $unknownCount = 0;
                $knowledgeAge = 0;
                for ($i = $x-1; $i <= $x+1; $i++) {
                    for ($j = $y - 1; $j <= $y + 1; $j++) {
                        if ($this->friendlyBoard[$i][$j] == 0) {
                            if ($this->enemyBoard[$i][$j]) {
                                $knowledgeAge += $this->turn - $this->knowledgeDate[$i][$j];
                            } else {
                                $unknownCount++;
                            }
                        }
                    }
                }
                list($friendlyWeight, $enemyWeight, $friendlyDistance, $enemyDistance) = $this->getDistanceWeights($x, $y, $this->gene('scoutFriendlyDistanceScale'), $this->gene('scoutEnemyDistanceScale'));
                $this->proposeMove('scout', [$x, $y],
                    $this->gene('scoutWeight')
                    + $unknownCount * $this->gene('scoutUnknownSquareCount')
                    + $knowledgeAge * $this->gene('scoutKnowledgeAge')
                    + $friendlyWeight * $this->gene('scoutFriendlyDistanceWeight')
                    + $enemyWeight * $this->gene('scoutEnemyDistanceWeight')
                    + $friendlyDistance * $this->gene('scoutFriendlyDistance')
                    + $enemyDistance * $this->gene('scoutEnemyDistance')
                    + ($this->myStartingColumn == 0 ? $y : 10-$y) * $this->gene('scoutYPositionFromMySide')
                    + ($this->myStartingColumn == 0 ? 10-$y : $y) * $this->gene('scoutYPositionFromEnemySide')
                );
            }
        }
    }

    public function handleMoveResult($move, $turn, $pos, $result) {
        if ($result == 'error') {
            throw new Exception('Error with move ' . json_encode($this->currentMove));
        }
        switch ($move) {
            case 'plant':
                if (substr($result, 0, 9) == 'occupied ') {
                    $enemyScore = substr($result, 9);
                    $this->enemyBoard[$pos[0]][$pos[1]] = -1 * abs($enemyScore);
                    $this->knowledgeDate[$pos[0]][$pos[1]] = $turn;
                }
                break;
            case 'fertilise':
                // no action, board will update next turn
                break;
            case 'scout':
                $arr = explode(',',substr($result, 3));
                for ($i = $pos[0]-1; $i <= $pos[0]+1; $i++) {
                    for ($j = $pos[1] - 1; $j <= $pos[1] + 1; $j++) {
                        $val = current($arr);
                        next($arr);
                        $val *= $this->sign;
                        if ($val <= 0) {
                            $this->enemyBoard[$i][$j] = $val;
                            $this->knowledgeDate[$i][$j] = $turn;
                        } // no need to store friendly board as gets updated next turn
                    }
                }
                break;
        }
    }

    /**
     * Run at the end of the game. Where we store the species, and maybe evolve the lineage
     *
     * @param $yourScore
     * @param $opponentScore
     * @return void
     */
    public function endGame($yourScore, $opponentScore) : string {
        if (!isset($this->lineageJson['species'][$this->speciesNumber])) {
            if (!isset($this->lineageJson['species'])) $this->lineageJson['species'] = [];
            $this->lineageJson['species'][$this->speciesNumber] = ['genes' => $this->genes, 'netWins' => 0];
        }
        $yourScore = abs($yourScore);
        $opponentScore = abs($opponentScore);
        $netWin = ($opponentScore > $yourScore ? -1 : ($opponentScore < $yourScore ? 1 : 0));
        $this->lineageJson['species'][$this->speciesNumber]['netWins'] += $netWin;
        $this->lineageJson['nextSpeciesToPlay'] = 1 + ($this->lineageJson['nextSpeciesToPlay'] ?? 0);
        if ($this->lineageJson['nextSpeciesToPlay'] >= self::NUM_SPECIES) {
            $this->lineageJson['nextSpeciesToPlay'] = 0;
            $this->lineageJson['roundsPlayed'] = 1 + ($this->lineageJson['roundsPlayed'] ?? 0);
            if ($this->lineageJson['roundsPlayed'] >= self::GAMES_PER_EVOLVE) {
                $this->lineageJson['roundsPlayed'] = 0;

                // time to evolve!
                // sort by netWins descending, i.e., top two species first, we'll keep them
                usort($this->lineageJson['species'], function($a, $b) {
                    return ($a['netWins'] > $b['netWins'] ? -1 : ($a['netWins'] < $b['netWins'] ? 1 : 0));
                });
                for ($i = 1; $i < self::NUM_SPECIES / 2; $i++) {
                    $this->lineageJson['species'][$i * 2]['genes'] = $this->evolve($this->lineageJson['species'][0]['genes']);
                    $this->lineageJson['species'][$i * 2 + 1]['genes'] = $this->evolve($this->lineageJson['species'][1]['genes']);
                }
                for ($i = 0; $i < sizeof($this->lineageJson['species']); $i++) {
                    $this->lineageJson['species'][$i]['netWins'] = 0;
                }
                $this->lineageJson['generations']++;
            }
        }
        $filename = __DIR__ . '/' . escapeshellcmd($this->name) . '.json';
        $f = fopen($filename, 'w');
        fwrite($f, json_encode($this->lineageJson, JSON_PRETTY_PRINT));
        fclose($f);
        return '';
    }

    public function evolve($genes) {
        foreach ($genes as $key => $val) {
            $genes[$key] *= (1 + mt_rand(-150, 100) / 100);
            if (abs($genes[$key]) < 0.01) {
                $genes[$key] -= 1;
            }
        }
        return $genes;
    }

    //---------------------------------------------------------------------------------------------------------------------------

    /** Returns a random factor between 0.1 and 10, positive or negative */
    protected function getRandomFactor($max = 10) {
        $r = mt_rand(-1000, 1000);
        $sign = mt_rand(0, 1);
        if ($sign == 0) $sign = -1;
        return pow(10, ($r / 1000)) * ($max / 10) * $sign;
    }

    /** Returns the give gene factor value, by name */
    protected function gene($name) {
        if (!array_key_exists($name, $this->genes)) {
            $this->genes[$name] = $this->getRandomFactor();
        }
        return $this->genes[$name];
    }

    /**
     * Returns array of four floats, being the distance-weighted point value of the square, [FriendlyWeight, EnemyWeight], and the distances in square, [friendlyDistance, EnemyDistance]
     *
     * This is the sum of all friendly (enemy) points on the board, multiplied by friendlyDistanceScale^distance (ie reduced by friendlyDistanceScale factor for each square)
     *
     * @param $x
     * @param $y
     * @param float $friendlyDistanceScale
     * @param float $enemyDistanceScale
     * @return float[]
     */
    protected function getDistanceWeights($x, $y, $friendlyDistanceScale, $enemyDistanceScale) {
        $friendlyWeight = 0;
        $enemyWeight = 0;
        $friendlyDistance = 99999;
        $enemyDistance = 99999;
        for ($i = 0; $i <= 10; $i++) {
            for ($j = 0; $j <= 10; $j++) {
                $dist = (abs($x - $i) + abs($y - $j));
                if ($this->friendlyBoard[$i][$j] > 0) {
                    $friendlyWeight += $friendlyDistanceScale ^ $dist * $this->friendlyBoard[$i][$j];
                    $friendlyDistance = min($friendlyDistance, $dist);
                }
                if ($this->enemyBoard[$i][$j] > 0) {
                    $enemyWeight += $enemyDistanceScale ^ $dist * $this->enemyBoard[$i][$j];
                    $enemyDistance = min($enemyDistance, $dist);
                }
            }
        }
        return [$friendlyWeight, $enemyWeight, $friendlyDistance, $enemyDistance];
    }
}

#$debug = fopen('debug.log', 'w');
$name = $sign = null;
// A simple loop to continuously read from STDIN
while ($line = fgets(STDIN)) {
    #fwrite($debug, $line);
    $data = json_decode($line, true);
    $response = '';
    switch ($data['function']) {
        case 'init':
        case 'start_game':
            if (!$name) $name = $data['name'];
            if (!$sign) $sign = $data['sign'];
            $player = new Genetic($name, $sign);
            break;
        case 'get_move':
            $response = $player->getMove($data['board'], $data['turn'], $data['moves_remaining'], $data['time_remaining']);
            break;
        case 'handle_move_result':
            $player->handleMoveResult($data['move'], $data['turn'], $data['pos'], $data['result']);
            break;
        case 'end_game':
            $player->endGame($data['your_score'], $data['opponent_score']);
            break;
    }
    fputs(STDOUT, json_encode($response) . "\n");
}

