# Game overview
Plantation is a game between two players, "Plus" and "Minus". It is played on a 
11x11 grid. In each player's turn, they have 3 moves. These can be used to:
- "plant" (1 move): gain control of an empty tile adjacent to one of your tiles, with a score of 1 
- "fertilise" (1 move): increase the score of one of your tiles by 1
- "scout" (1 move) get information about the opponent's score in each tile in a 3x3 grid.
- "colonise" (2 moves): long distance plant to any empty tile anywhere on the board. You need a source tile with a score of 2 or more, the source's score is reduced by 1. 
- "spray" (2 moves): attack several tiles, reducing the opponent's score in the target tile and any adjacent tiles by 1.
- "bomb" (2 moves): attack a single tile, reducing the opponent's score in that tile by up to 4.

Plantation is a game of imperfect information. In each turn, the player is given
information about their tile scores only. Information about the opponent's tile 
scores can only be received by moves. "Scout" directly gives scores in a region, 
but "plant", "colonise", "spray" and "bomb" can also yield some information.

Scores for Plus are represented by positive numbers, scores for Minus by negative.
Plus starts off with three randomly selected tiles in the left-most column with
a score of +1. Similarly, Minus starts off with three random tiles in the right-most
column with -1.

Plus moves first, then each player alternates turns with three moves per turn. The
game ends after each player has had 100 turns, where the winner is decided by 
whoever has the highest sum of tile scores.

# Board layout
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
Plus owns tiles (2, 3), (3, 0), (6, 0), and (9, 0) with a total score of +4. 

Minus owns tiles (1, 10), (5, 9), (5, 10), (5,9) and (10, 10) with a total score of -6.

# Command details

If you do not have enough moves remaining for a command that requires more than one move, "error" is returned.

### ```fertilise [row, col]```
 
Moves: 1  
Return: ```OK``` or ```error```

Increases the score of one of your tiles 1.

If you do not control the tile, "error" is returned.

### ```plant [row, col]``` 
Moves: 1  
Return: ```OK```, ```error``` or ```occupied #```  (if occupied, # is the score of the opponent's tile)

Target must be a tile not planted by you that is adjacent to one of your tiles. 
If it is empty, you gain control of that tile with a plantation count of 1.

```plant``` can give  some information about an opponent's tile. If the tile is 
already owned by your opponent, nothing happens and "occupied" is returned 
together with the opponent's score in the tile. 

### ```scout [row, col]```
Moves: 1  
Return: ```OK a,b,c,d,e,f,g,h,i``` or ```error```    

a-i are the values of the 3x3 grid centred around the target tile.

### ```colonise  [target_row, target_col, source_row, source_col]```  
Moves: 2  
Return: ```OK```, ```error``` or ```occupied #```  (if occupied, # is the score of the opponent's tile)  

Target can be any tile not already planted by you. Source must be one of your
tiles with a score of 2 or more. If you have no tiles with a score of 2 or more,
you cannot do this move.

If the target tile is empty, you gain control of that tile with a plantation count of 1.

```colonise``` can give  some information about an opponent's tile. If the tile is 
already owned by your opponent, nothing happens and "occupied" is returned 
together with the opponent's score in the tile.


### ```spray [row, col]```  
Moves: 2  
Return: ```OK #``` or ```error```  (# is the number of opponent's tiles affected)

Affects a cross-shape including the target and the tiles above, below, left and right.

For each tile affected, if your opponent has planted that tile, their count is reduced by 1. If it is reduced to 0, they lose control of that tile. Returns the total number of tiles affected.


### ```bomb [row, col]```  
Moves: 2  
Return: ```OK #``` or ```error``` (# is the number of plantation levels reduced)

Affects a single tile. If your opponent has planted the tile, it reduces their plantation level by up to 3 levels. Returns the number of plantation levels reduced.

# Building an AI player

Create a file in the AI_players folder that extends the ```Player``` class 
and implement the ```get_move``` method and optionally the ```handle_move_result```
method if you want to learn from the return values of your moves. 

There are two example AI agents in random_player.py and random_player_dumb.py.

RandomPlayerDumb randomly makes random moves, but doesn't check if they are valid
first, so gets lots of errors.

RandomPlayer makes a weighted random choice of valid moves each turn.

# Todo
- Make a chess clock
- Make two modes, one for single game, one for bulk running games