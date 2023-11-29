# Board layout
```
     1    2    3    4  
   =====================
 A | o1 | x3 |    |    |
 B | o1 |    |    |    |
 C |    | x3 |    |    |
 D | o1 | x1 |    | x2 |
   =====================
```

# Commands

If you do not have enough moves remaining for a command that requires more than one move, "error" is returned.

### ```fertilise```
 
Moves: 1  
Return: ```OK``` or ```error```

Increases the plantation count of one of your tiles 1.

If you do not control the tile, "error" is returned


### ```plant``` 
Moves: 1  
Return: ```OK```, ```error``` or ```occupied #```  (# is the opponent's plantation count)

Target must be a tile not planted by you that is adjacent to one of your tiles. If it is empty, you gain control of that tile with a plantation count of 1.

If it is already planted by your opponent, nothing happens and "occupied" is returned.

### ```scout```
Moves: 1
Return: ```OK a,b,c,d,e,f,g,h,i``` or ```error```  
(a-i are the values of the 3x3 centred around the target tile

### ```colonise```  
Moves: 2  
Return: ```OK```, ```error``` or ```occupied #```  (# is the opponent's plantation count)  

Target can be any tile not already planted by you.

If it is empty, you gain control of that tile with a plantation count of 1.


### ```spray```  
Moves: 2  
Return: ```OK #``` or ```error```  (# is the number of opponent's tiles affected)

Affects a cross-shape including the target and the tiles above, below, left and right.

For each tile affected, if your opponent has planted that tile, their count is reduced by 1. If it is reduced to 0, they lose control of that tile. Returns the total number of tiles affected.


### ```bomb```  
Moves: 2  
Return: ```OK #``` or ```error``` (# is the number of plantation levels reduced)

Affects a single tile. If your opponent has planted the tile, it reduces their plantation level by up to 3 levels. Returns the number of plantation levels reduced.


