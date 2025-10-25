//mapCenteredFunctions


//Global variables
int amtNodesHorizontal = 3;
int amtNodesVertical = 3;
int *ownMap[amtNodesHorizontal][amtNodesVertical]


void getTheirMap(){
    pass;
}
//dictonary with gameGoalMaps

int* generateMap(){
    return ownMap;
}

void updateMap(){ //problem: O(n^2) Laufzeit
    for (int i : amtNodesHorizontal){
        for(int j : amtNodesVertical){
            if(ownMap[i][j]!=theirMap[i][j]){
                switch(theirMap[i][j]==)
                    case: 1 {
                        *ownMap[i][j] <- 1;
                    }
                    case: 0 {
                        *ownMap[i][j] <- 0;
                    }
                    case: default {
                        pass;
                    }
            }
            else{
                pass;
            }
        }
    }
}

bool gameCheck(int[][] ownMap, int[][] gameMap){ //problem: if the game is indeed complete, then this operation will take =(n^2)
    //if the vertical and horizontal amount is not the same as in the game return 0
    for (int i : amtNodesHorizontal){
        for(int j : amtNodesVertical){
            if (ownMap[i][j]!=gameMap[i][j]){
                return 0;
            }//what about errors????????????????????????
        }
    }
    return 1;
}