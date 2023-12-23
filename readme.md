# December coding challenge
Build a bot to play the game below. In January, when most people are back, we'll organise a tournament, 
where pairs of bots face off against each other in matches consisting of several games each.
We'll make the call later about how many games in a match, and how much time 
is available for bots to move.

Feel free to upload your bot to the repo if you want to share it with others, otherwise
email the code through directly if you want to sneak in.

Feel free to use an AI to code your AI. If, in the process of building AIs
to code AIs, one of your AIs wrests control of Earth from humanity, 
you win by default. Please ensure that all your chatGPT prompts 
say "please" and "thank you".

# Plantation Game
![Plantation logo](logo2.webp "Plantation logo")
(Thank you chatGPT / Dall-E for the pretty picture.)

## Game overview
Plantation is a two player game played on a 11x11 grid. In each player's turn, they have 3 moves. These can 
be used to:
- "plant" (1 move): gain control of an empty tile adjacent (not diagonal) to one of your tiles, with a score of 1 
- "fertilise" (1 move): increase the score of one of your tiles by 1
- "scout" (1 move) get information about the opponent's score in each tile in a 3x3 grid.
- "colonise" (2 moves): long distance plant to any empty tile anywhere on the board. You need a source tile with a score of 2 or more, the source's score is reduced by 1. 
- "spray" (2 moves): attack several tiles, reducing the opponent's score in the target tile and the four adjacent tiles by 1.
- "bomb" (2 moves): attack a single tile, reducing the opponent's score in that tile by up to 4.

Plantation is a game of imperfect information. In each turn, the player is given
information about their tile scores only. Information about the opponent's tile 
scores can only be gained by interrogating the response to player moves. "Scout" directly gives the opponent's
scores in a region, but "plant", "colonise", "spray" and "bomb" can also yield some information.

Scores for Player 1 are represented by positive numbers, and Player 2 has negative 
numbers. Player 1 starts off with three randomly selected tiles in the left-most column with
a score of +1. Similarly, Player 2 starts off with three random tiles in the right-most
column with -1.

Each player alternates turns with three moves per turn. The  game ends after each player has had 100 turns, where the winner is decided by 
whoever has the highest sum of tile scores.

## Board layout
Example board: 
```
     0    1    2    3    4    5    6    7    8    9    10
   ========================================================
 0 |    |    |    |    |    |    |    |    |    |    |    |
 1 |    |    |    |    |    |    |    |    |    |    | -1 |
 2 |    |    |    | +1 |    |    |    |    |    |    |    |
 3 | +1 |    |    |    |    |    |    |    |    |    |    |
 4 |    |    |    |    |    |    |    |    |    |    |    |
 5 |    |    |    |    |    |    |    |    |    | -1 | -1 |
 6 | +1 |    |    |    |    |    |    |    |    |    |    |
 7 |    |    |    |    |    |    |    |    |    |    |    |
 8 |    |    |    |    |    |    |    |    |    |    |    |
 9 | +1 |    |    |    |    |    |    |    |    |    |    |
10 |    |    |    |    |    |    |    |    |    | -1 | -2 |
   ========================================================
 ```
Player 1 owns tiles (2, 3), (3, 0), (6, 0), and (9, 0) with a total score of +4. 

Player 2 owns tiles (1, 10), (5, 9), (5, 10), (5,9) and (10, 10) with a total score of -6.

## Command details

If you do not have enough moves remaining for a command that requires more than one move, "error" is returned.

--- 
#### ```fertilise [row, col]```
 
Moves: 1  
Return: ```OK``` or ```error```

Increases the score of one of your tiles 1.

If you do not control the tile, "error" is returned.

--- 
#### ```plant [row, col]``` 
Moves: 1  
Return: ```OK```, ```error``` or ```occupied #```  (if occupied, # is the score of the opponent's tile)

Target must be a tile not planted by you that is adjacent (not diagonal) to one of your tiles. If it is empty, you gain control of that tile with a plantation count of 1.

```plant``` can give  some information about an opponent's tile. If the tile is 
already owned by your opponent, nothing happens and "occupied" is returned 
together with the opponent's score in the tile. 

--- 
#### ```scout [row, col]```
Moves: 1  
Return: ```OK a,b,c,d,e,f,g,h,i``` or ```error```    

a-i are the values of the 3x3 grid centred around the target tile:
```
a b c
d e f
g h i
```

--- 
#### ```colonise  [target_row, target_col, source_row, source_col]```  
Moves: 2  
Return: ```OK```, ```error``` or ```occupied #```  (if occupied, # is the score of the opponent's tile)  

Target can be any tile not already planted by you. Source must be one of your
tiles with a score of 2 or more. If you have no tiles with a score of 2 or more,
you cannot do this move.

If the target tile is empty, you gain control of that tile with a plantation count of 1.

```colonise``` can give  some information about an opponent's tile. If the tile is 
already owned by your opponent, nothing happens and "occupied" is returned 
together with the opponent's score in the tile.

--- 
#### ```spray [row, col]```  
Moves: 2  
Return: ```OK #``` or ```error```  (# is the number of opponent's tiles affected)

Affects a cross-shape including the target and the tiles above, below, left and right.

For each tile affected, if your opponent has planted that tile, their count is reduced by 1. If it is reduced to 0, they lose control of that tile. Returns the total number of tiles affected.

--- 
#### ```bomb [row, col]```  
Moves: 2  
Return: ```OK #``` or ```error``` (# is the number of plantation levels reduced)

Affects a single tile. If your opponent has planted the tile, it reduces their plantation level by up to 4 levels. Returns the number of plantation levels reduced.

## Running the game
Clone the repo. If you are managing your own python environment, install plantation by running something like

```pip install -e . ```

from the root of the working copy. You can then use

```python scripts/single_game.py``` 

to run a single game, or 

```python scripts/many_games.py``` 

to run a series of games and collect overall stats.

Alternatively, install the packaging and dependency management tool [Poetry](https://python-poetry.org/docs/#installation) and run

```poetry install```

in the directory of your working copy. This will create a virtual environment and install the dependencies. Then run

```poetry shell```

to activate the venv and proceed as above. Or you can use commands like

```poetry run python scripts/single_game.py```

to run commands in the venv without activating it in your shell.

`dev` and `experimental` optional dependecies are included in the pyproject configuration. Install them by running, for example,

```poetry install --with dev```

The `experimental` group _should_ install CUDA libraries and linked JAX and jaxlib, but your mileage may vary.

### Pre-requisites
python 3, numpy, scipy (to run ScryOrDie bot)

## Building an AI player

Create a file in the ```AI_players``` folder that extends the ```Player``` class 
and implement the ```get_move``` method. You can also implement some or all of 
the following optional functions:
 - ```handle_move_result```: process the return values of your moves
 - ```start_game```: called at the start of each game. Passes the size of the board (11x11)
 - ```end_game```: called at the end of the game. Passes your score and your opponent's score.

### Example AI players

There are three example AI agents in ```AI_players```, in increasing order of sophistication:
#### 1. ```random_player_dumb.py```
Randomly selects moves and target squares. Most aren't valid moves, so it gets lots of errors.

#### 2. ```random_player.py```
Randomly selects a valid move. It has configurable weightings for move options
to allow for customisation.

#### 3. ```scry_and_die.py```
Grows for a few turns, then spends a turn scouting. After that, it decides at the
start of the turn whether to grow or to kill. If it decides to grow, it randomly 
selects three valid ```plant```, ```colonise``` or ```fertilise``` moves for the turn. 
If it decides to kill, it scouts first, then chooses either to ```spray``` or ```bomb```.

It chooses between the options by maintaining an estimate of the opponent's board, 
and calculating how what score it would get for each option. 
It loops through a standard scouting cycle whenever it scouts.

It implements ```handle_move_result``` to update its estimate of the opponent's board.

# Clock
Players have a configurable amount of time per turn. This works like a chess
clock: you start with an initial number of  seconds, then gain a more time 
after each move. By default, you have 1 second starting time plus 0.1 seconds 
per turn.

When a player runs out of time, the game ends and their opponent gets a
score of 100 (or -100).

# Other programming languages
PHP support (I know, right) is in paulc/php_player_wrapper.py, using STDIN and STDOUT to communicate with a process in running a PHP file. This can be replicated for other languages. 
