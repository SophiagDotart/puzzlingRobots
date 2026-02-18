# Example goalMaps for a swarm of 6
import errorHandling as err

class GoalMapManager():
    def __init__(self, singleMap):
        self.singleMap = singleMap   
        self.goalMaps = {}          # name = (compressedMap, margins) to satisfy map architecture from mapFunc

    def addGoalMap(self, name, dictGoalMap):
        compressedGoalMap, margins = self.singleMap.compressMapToByteArray(dictGoalMap) # here we also get the margins from the mapFunc
        self.goalMaps[name] = (compressedGoalMap[:], margins)

    def loadGoalMap(self, name):
        if name not in self.goalMaps:
            err.goalMapNonExistent()
            return None
        return self.goalMaps[name]


# Test pyramid
# mode 001
#   _____
#  | --+ |
#  | -++ |
#  | +++ |
#  |_____|
# x->; y up; bottom left is start
pyramid = { (0, 0): "+", #key: value
            (1, 0): "+",
            (2, 0): "+",
            (1, 1): "+",
            (2, 1): "+",
            (2, 2): "+"}

# Test square 
# -> this shape should cause errors 
#   and possibly infinite rows!
# mode = 010
#   _____
#  | +++ |
#  | --- |
#  | +++ |
#  |_____|
# x->; y up; bottom left is start
errorSquare = { (0, 0): "+", #key: value
                (1, 0): "+",
                (2, 0): "+",
                (0, 2): "+",
                (1, 2): "+",
                (2, 2): "+"}

# Test Z 
# -> not all robots are used
# mode = 011
#   _____
#  | -++ |
#  | -+- |
#  | ++- |
#  |_____|
# x->; y up; bottom left is start
smallZ = {  (0, 0): "+", #key: value
            (1, 0): "+",
            (1, 1): "+",
            (2, 1): "+",
            (2, 2): "+"}
