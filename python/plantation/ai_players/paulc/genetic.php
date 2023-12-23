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
     *      - scorediff: int
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

    /** @var array Indexed by move type, then x then y */
    protected $friendlyDistanceWeights = [];
    protected $enemyDistanceWeights = [];

    protected $friendlyDistances = [];
    protected $enemyDistances = [];

    protected $moveTypeCounts = [];

    protected $moveTypes = ['plant', 'fertilise', 'scout', 'colonise', 'bomb', 'spray'];

    const NUM_SPECIES = 10;
    const GAMES_PER_EVOLVE = 10;

    function __construct($name, $sign) {
        $this->name = $name;
        $this->friendlyBoard = array_fill(0, 11, array_fill(0, 11, 0));
        $this->enemyBoard = array_fill(0, 11, array_fill(0, 11, null));
        foreach ($this->moveTypes as $move) {
            if ($move == 'spray') continue; //irrelevant
            $this->friendlyDistanceWeights[$move] = array_fill(0, 11, array_fill(0, 11, 0));
            $this->enemyDistanceWeights[$move] = array_fill(0, 11, array_fill(0, 11, 0));
        }
        $this->sign = $sign;
        foreach ($this->moveTypes as $move) {
            $this->moveTypeCounts[$move] = 0;
        }

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

    protected function setFriendlyBoard($x, $y, $points) {
        if ($this->friendlyBoard[$x][$y] != $points) {
            if ($this->friendlyBoard[$x][$y] == 0 || $points == 0) {
                $this->friendlyDistances = []; // reset distances, need to be recalc'ed
            }
            $change = $points - $this->friendlyBoard[$x][$y];
            // update weights
            for ($i = 0; $i <= 10; $i++) {
                for ($j = 0; $j <= 10; $j++) {
                    $dist = (abs($x - $i) + abs($y - $j));
                    foreach (array_keys($this->friendlyDistanceWeights) as $move) {
                        $this->friendlyDistanceWeights[$move][$i][$j] += pow($this->gene($move . 'FriendlyDistanceScale'), $dist) * $change;
                    }
                }
            }
            // update the rest
            $this->friendlyScore += $change;
            $this->friendlyBoard[$x][$y] = $points;
            if ($points > 0) {
                if ($this->enemyBoard[$x][$y] !== 0) {
                    $this->setEnemyBoard($x, $y, 0);
                }
                $this->knowledgeDate[$x][$y] = $this->turn;
            }
        }
    }

    protected function setEnemyBoard($x, $y, $points, $updateKnowledgeDate = true) {
        if ($this->enemyBoard[$x][$y] != $points) {
            if ($this->enemyBoard[$x][$y] == 0 || $points == 0) {
                $this->enemyDistances = []; // reset distances, need to be recalc'ed
            }
            $change = $points - $this->enemyBoard[$x][$y];
            // update weights
            for ($i = 0; $i <= 10; $i++) {
                for ($j = 0; $j <= 10; $j++) {
                    $dist = (abs($x - $i) + abs($y - $j));
                    foreach (array_keys($this->enemyDistanceWeights) as $move) {
                        $this->enemyDistanceWeights[$move][$i][$j] += pow($this->gene($move . 'EnemyDistanceScale'), $dist) * $change;
                    }
                }
            }
            // update the rest
            $this->enemyScore += $change;
            $this->enemyBoard[$x][$y] = $points;
        }
        if ($updateKnowledgeDate) {
            $this->knowledgeDate[$x][$y] = $this->turn;
        }
    }

    public function getMove($board, $turn, $movesRemaining, $timeRemaining) {
        $this->turn = $turn;
        $this->movesRemaining = $movesRemaining;
        $this->timeRemaining = $timeRemaining;
        $this->currentMove = null;
        $this->currentMoveWeight = 0;
        // handle board updates
        for ($x = 0; $x <= 10; $x++) {
            for ($y = 0; $y <= 10; $y++) {
                $points = $board[$x][$y];
                if ($points < 0) $points = -$points;
                if ($this->friendlyBoard[$x][$y] != $points) {
                    $this->setFriendlyBoard($x, $y, $points);
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
        if ($movesRemaining > 1) {
            $this->generateColoniseMoves();
            $this->generateSprayMoves();
            $this->generateBombMoves();
        }
        $this->moveTypeCounts[$this->currentMove[0]]++;
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
                        if (empty($this->enemyDistances)) $this->calcEnemyDistances();
                        $this->proposeMove('plant', [$x, $y],
                            $this->gene('plantWeight')
                            + $this->friendlyDistanceWeights['plant'][$x][$y] * $this->gene('plantFriendlyDistanceWeight')
                            + $this->enemyDistanceWeights['plant'][$x][$y] * $this->gene('plantEnemyDistanceWeight')
                            + $this->enemyDistances[$x][$y] * $this->gene('plantEnemyDistance')
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
                    if (empty($this->enemyDistances)) $this->calcEnemyDistances();
                    $this->proposeMove('fertilise', [$x, $y],
                        $this->gene('fertiliseWeight')
                        + $this->friendlyDistanceWeights['fertilise'][$x][$y] * $this->gene('fertiliseFriendlyDistanceWeight')
                        + $this->enemyDistanceWeights['fertilise'][$x][$y] * $this->gene('fertiliseEnemyDistanceWeight')
                        + $this->enemyDistances[$x][$y] * $this->gene('fertiliseEnemyDistance')
                        + ($this->myStartingColumn == 0 ? $y : 10-$y) * $this->gene('fertiliseYPositionFromMySide')
                        + ($this->myStartingColumn == 0 ? 10-$y : $y) * $this->gene('fertiliseYPositionFromEnemySide')
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
                if (empty($this->friendlyDistances)) $this->calcFriendlyDistances();
                if (empty($this->enemyDistances)) $this->calcEnemyDistances();
                $this->proposeMove('scout', [$x, $y],
                    $this->gene('scoutWeight')
                    + $unknownCount * $this->gene('scoutUnknownSquareCount')
                    + $knowledgeAge * $this->gene('scoutKnowledgeAge')
                    + $this->friendlyDistanceWeights['scout'][$x][$y] * $this->gene('scoutFriendlyDistanceWeight')
                    + $this->enemyDistanceWeights['scout'][$x][$y] * $this->gene('scoutEnemyDistanceWeight')
                    + $this->friendlyDistances[$x][$y] * $this->gene('scoutFriendlyDistance')
                    + $this->enemyDistances[$x][$y] * $this->gene('scoutEnemyDistance')
                    + ($this->myStartingColumn == 0 ? $y : 10-$y) * $this->gene('scoutYPositionFromMySide')
                    + ($this->myStartingColumn == 0 ? 10-$y : $y) * $this->gene('scoutYPositionFromEnemySide')
                );
            }
        }
    }

    public function generateColoniseMoves() {
        for ($x = 0; $x <= 10; $x++) {
            for ($y = 0; $y <= 10; $y++) {
                if ($this->friendlyBoard[$x][$y] == 0 && !$this->enemyBoard[$x][$y]) {
                    if (empty($this->friendlyDistances)) $this->calcFriendlyDistances();
                    if (empty($this->enemyDistances)) $this->calcEnemyDistances();
                    if ($this->friendlyDistances[$x][$y] > 1) { // no sense using colonise otherwise
                        $weighting =
                            $this->gene('coloniseWeight')
                            + $this->friendlyDistanceWeights['colonise'][$x][$y] * $this->gene('coloniseFriendlyDistanceWeight')
                            + $this->enemyDistanceWeights['colonise'][$x][$y] * $this->gene('coloniseEnemyDistanceWeight')
                            + $this->friendlyDistances[$x][$y] * $this->gene('coloniseFriendlyDistance')
                            + $this->enemyDistances[$x][$y] * $this->gene('coloniseEnemyDistance')
                            + ($this->myStartingColumn == 0 ? $y : 10-$y) * $this->gene('coloniseYPositionFromMySide')
                            + ($this->myStartingColumn == 0 ? 10-$y : $y) * $this->gene('coloniseYPositionFromEnemySide');
                        // find source square
                        for ($i = 0; $i <= 10; $i++) {
                            for ($j = 0; $j <= 10; $j++) {
                                if ($this->friendlyBoard[$i][$j] > 1) {
                                    $this->proposeMove('colonise', [$x, $y, $i, $j], $weighting
                                        + $this->friendlyBoard[$i][$j] * $this->gene('coloniseSourcePoints')
                                    );
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    public function generateSprayMoves() {
        for ($x = 0; $x <= 10; $x++) {
            for ($y = 0; $y <= 10; $y++) {
                $enemyScore = $this->enemyBoard[$x][$y];
                if ($x > 0) $enemyScore += $this->enemyBoard[$x-1][$y];
                if ($x < 10) $enemyScore += $this->enemyBoard[$x+1][$y];
                if ($y > 0) $enemyScore += $this->enemyBoard[$x][$y-1];
                if ($y < 10) $enemyScore += $this->enemyBoard[$x][$y+1];
                if ($enemyScore > 0) {
                    if (empty($this->friendlyDistances)) $this->calcFriendlyDistances();
                    $this->proposeMove('spray', [$x, $y],
                        $this->gene('sprayWeight')
                            + $enemyScore * $this->gene('sprayEnemyScore')
                            + $this->friendlyDistances[$x][$y] * $this->gene('sprayFriendlyDistance')
                            + ($this->myStartingColumn == 0 ? $y : 10-$y) * $this->gene('sprayYPositionFromMySide')
                            + ($this->myStartingColumn == 0 ? 10-$y : $y) * $this->gene('sprayYPositionFromEnemySide')
                    );
                }
            }
        }
    }

    public function generateBombMoves() {
        for ($x = 0; $x <= 10; $x++) {
            for ($y = 0; $y <= 10; $y++) {
                $enemyScore = $this->enemyBoard[$x][$y];
                if ($enemyScore > 0) {
                    $knowledgeAge = $this->turn - $this->knowledgeDate[$x][$y];
                    if (empty($this->friendlyDistances)) $this->calcFriendlyDistances();
                    $this->proposeMove('bomb', [$x, $y],
                        $this->gene('bombWeight')
                        + $enemyScore * $this->gene('bombEnemyScore')
                        + $knowledgeAge * $this->gene('bombKnowledgeAge')
                        + $this->friendlyDistances[$x][$y] * $this->gene('bombFriendlyDistance')
                        + $this->friendlyDistanceWeights['bomb'][$x][$y] * $this->gene('bombFriendlyDistanceWeight')
                        + $this->enemyDistanceWeights['bomb'][$x][$y] * $this->gene('bombEnemyDistanceWeight')
                        + ($this->myStartingColumn == 0 ? $y : 10-$y) * $this->gene('bombYPositionFromMySide')
                        + ($this->myStartingColumn == 0 ? 10-$y : $y) * $this->gene('bombYPositionFromEnemySide')
                    );
                }
            }
        }
    }

    public function handleMoveResult($move, $turn, $pos, $result) {
        if ($result == 'error') {
            throw new Exception('Error with move ' . json_encode($this->currentMove));
        }
        switch ($move) {
            case 'plant':
            case 'colonise':
                if (substr($result, 0, 9) == 'occupied ') {
                    $enemyScore = substr($result, 9);
                    $this->setEnemyBoard($pos[0], $pos[1], -1 * abs($enemyScore));
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
                            $this->setEnemyBoard($i, $j, $val);
                        } // no need to store friendly board as gets updated next turn
                    }
                }
                break;
            case 'spray':
                $x = $pos[0];
                $y = $pos[1];
                $this->setEnemyBoard($x, $y, max(0, $this->enemyBoard[$x][$y] - 1), false);
                if ($x > 0) $this->setEnemyBoard($x-1, $y, max(0, $this->enemyBoard[$x-1][$y] - 1), false);
                if ($x < 10) $this->setEnemyBoard($x+1, $y, max(0, $this->enemyBoard[$x+1][$y] - 1), false);
                if ($y > 0) $this->setEnemyBoard($x, $y-1, max(0, $this->enemyBoard[$x][$y-1] - 1), false);
                if ($y < 10) $this->setEnemyBoard($x, $y+1, max(0, $this->enemyBoard[$x][$y+1] - 1), false);
                break;
            case 'bomb':
                $x = $pos[0];
                $y = $pos[1];
                $reduction = substr($result, 3);
                $knowResultingScore = ($reduction < 4);
                $this->setEnemyBoard($x, $y, max(0, $this->enemyBoard[$x][$y] - 4), $knowResultingScore);
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
            $this->lineageJson['species'][$this->speciesNumber] = ['genes' => $this->genes, 'scorediff' => 0];
        }
        $yourScore = abs($yourScore);
        $opponentScore = abs($opponentScore);
        $scorediff = abs($yourScore) - abs($opponentScore);
        // adjust scorediff down if the player didn't use all moves at least once
        foreach ($this->moveTypes as $move) {
            if ($this->moveTypeCounts[$move] < 5) {
                $scorediff -= 10 * (5 - $this->moveTypeCounts[$move]);
            }
        }

        $this->lineageJson['species'][$this->speciesNumber]['scorediff'] += $scorediff;
        $this->lineageJson['nextSpeciesToPlay'] = 1 + ($this->lineageJson['nextSpeciesToPlay'] ?? 0);
        if ($this->lineageJson['nextSpeciesToPlay'] >= self::NUM_SPECIES) {
            $this->lineageJson['nextSpeciesToPlay'] = 0;
            $this->lineageJson['roundsPlayed'] = 1 + ($this->lineageJson['roundsPlayed'] ?? 0);
            if ($this->lineageJson['roundsPlayed'] >= self::GAMES_PER_EVOLVE) {
                $this->lineageJson['roundsPlayed'] = 0;

                // time to evolve!
                // sort by scorediff descending, i.e., top two species first, we'll keep them
                $top = $second = -1;
                $topScore = $secondScore = -999999;
                for ($i = 0; $i < self::NUM_SPECIES; $i++) {
                    if ($this->lineageJson['species'][$i]['scorediff'] > $secondScore) {
                        if ($this->lineageJson['species'][$i]['scorediff'] > $topScore) {
                            $secondScore = $topScore;
                            $second = $top;
                            $topScore = $this->lineageJson['species'][$i]['scorediff'];
                            $top = $i;
                        } else {
                            $secondScore = $this->lineageJson['species'][$i]['scorediff'];
                            $second = $i;
                        }
                    }
                }
                $this->lineageJson['generations']++;
                $this->log("Evolving {$this->name} to generation {$this->lineageJson['generations']}! Top species were $top and $second");
                $this->lineageJson['species'][0] = $this->lineageJson['species'][$top];
                $this->lineageJson['species'][1] = $this->lineageJson['species'][$second];
                for ($i = 1; $i < self::NUM_SPECIES / 2; $i++) {
                    $this->lineageJson['species'][$i * 2]['genes'] = $this->evolve($this->lineageJson['species'][0]['genes']);
                    $this->lineageJson['species'][$i * 2 + 1]['genes'] = $this->evolve($this->lineageJson['species'][1]['genes']);
                }
                for ($i = 0; $i < sizeof($this->lineageJson['species']); $i++) {
                    $this->lineageJson['species'][$i]['scorediff'] = 0;
                }
            }
        }
        $filename = __DIR__ . '/' . escapeshellcmd($this->name) . '.json';
        $f = fopen($filename, 'w');
        fwrite($f, json_encode($this->lineageJson, JSON_PRETTY_PRINT));
        fclose($f);

        // dump 4% of games, moves played
        if (mt_rand(0, 24) == 1) {
            $st = '';
            foreach ($this->moveTypeCounts as $move => $count) {
                $st .= "$move: $count; ";
            }
            $this->log($this->name . " snapshot of moves used: " . substr($st, 0, -2));
        }

        return '';
    }

    /**
     * Bias towards smaller over time, and allow changing sign
     *
     * @param $genes
     * @return mixed
     */
    public function evolve($genes) {
        foreach ($genes as $key => $val) {
            if (mt_rand(0,4) == 1) { //evolve ~20% of genes each run
                if (mt_rand(0,3) == 1) { // 75% small adjustment, 25% big adjustment
                    $genes[$key] *= (1 + mt_rand(-200, 100) / 100);
                } else {
                    $genes[$key] *= (1 + mt_rand(-33, 50) / 100);
                }
                if (abs($genes[$key]) < 1e-6) {
                    // behaviour is irrelevant, remove it entirely
                    $genes[$key] = 0;
                }
                //if (abs($genes[$key]) < 0.01) {
                //    $genes[$key] -= 1;
                //}
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

    protected function calcFriendlyDistances() {
        $this->friendlyDistances = array_fill(0, 11, array_fill(0, 11, 999));
        // initialise with my positions
        for ($x = 0; $x <= 10; $x++) {
            for ($y = 0; $y <= 10; $y++) {
                if ($this->friendlyBoard[$x][$y]) {
                    $this->friendlyDistances[$x][$y] = 0;
                }
            }
        }
        // diffuse out
        do {
            $changed = false;
            for ($x = 0; $x <= 10; $x++) {
                for ($y = 0; $y <= 10; $y++) {
                    $new = 1 + $this->friendlyDistances[$x][$y];
                    if ($new < 999) {
                        if ($x > 0 && $this->friendlyDistances[$x-1][$y] > $new) {
                            $this->friendlyDistances[$x-1][$y] = $new;
                            $changed = true;
                        }
                        if ($x < 10 && $this->friendlyDistances[$x+1][$y] > $new) {
                            $this->friendlyDistances[$x+1][$y] = $new;
                            $changed = true;
                        }
                        if ($y > 0 && $this->friendlyDistances[$x][$y-1] > $new) {
                            $this->friendlyDistances[$x][$y-1] = $new;
                            $changed = true;
                        }
                        if ($y < 10 && $this->friendlyDistances[$x][$y+1] > $new) {
                            $this->friendlyDistances[$x][$y+1] = $new;
                            $changed = true;
                        }
                    }
                }
            }
        } while ($changed);
    }

    protected function calcEnemyDistances() {
        $this->enemyDistances = array_fill(0, 11, array_fill(0, 11, 15)); //15 is a basic max plausible result
        // initialise with my positions
        for ($x = 0; $x <= 10; $x++) {
            for ($y = 0; $y <= 10; $y++) {
                if ($this->enemyBoard[$x][$y]) {
                    $this->enemyDistances[$x][$y] = 0;
                }
            }
        }
        // diffuse out
        do {
            $changed = false;
            for ($x = 0; $x <= 10; $x++) {
                for ($y = 0; $y <= 10; $y++) {
                    $new = 1 + $this->enemyDistances[$x][$y];
                    if ($new < 999) {
                        if ($x > 0 && $this->enemyDistances[$x-1][$y] > $new) {
                            $this->enemyDistances[$x-1][$y] = $new;
                            $changed = true;
                        }
                        if ($x < 10 && $this->enemyDistances[$x+1][$y] > $new) {
                            $this->enemyDistances[$x+1][$y] = $new;
                            $changed = true;
                        }
                        if ($y > 0 && $this->enemyDistances[$x][$y-1] > $new) {
                            $this->enemyDistances[$x][$y-1] = $new;
                            $changed = true;
                        }
                        if ($y < 10 && $this->enemyDistances[$x][$y+1] > $new) {
                            $this->enemyDistances[$x][$y+1] = $new;
                            $changed = true;
                        }
                    }
                }
            }
        } while ($changed);
    }

    protected function log($msg) {
        $debug = fopen('debug.log', 'a');
        fwrite($debug, $msg . "\n");
        fclose($debug);
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
            if (!$name) $name = $data['name'];
            break;
        case 'start_game':
            $sign = $data['sign'];
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
    $prevData = $data;
    fputs(STDOUT, json_encode($response) . "\n");
}

