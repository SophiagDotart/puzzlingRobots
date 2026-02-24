# goalMapStorage (aka goalMapStore)
# Tasks:
#   - store all goalMaps
#   - return goalMaps in a way that is directly comparable to the current map
#   - add goalMaps to the library when received via communication modules
# Example goalMaps for a swarm of at least 6 members

from mapFunctions import Map        # ONLY to use it's staticmethod utility functions

class GoalMapManager():
    def __init__(self):
        self.goalMaps = {}          # name = (compressedMap, margins) to satisfy map architecture from mapFunc

    def addGoalMap(self, name, dictGoalMap):
        newGoalMap, margins = Map.compressMapToByteArray(dictGoalMap)
        if newGoalMap is None or margins is None:
            return False            # compression failed, ERROR - failed to add new goalMap
        self.goalMaps[name] = (newGoalMap[:], margins)
        print(f"[FYI] A new goalMap was added called {name}")
        return True                 # added map successful

    def loadGoalMap(self, name):
        if name not in self.goalMaps:
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
