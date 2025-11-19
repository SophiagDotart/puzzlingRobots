#----- Map functions ----- 
# Handles any functions that deal with the contents of the map
# Switching logic in script "switching conditions"
# Hardware functions in separate script

def printMap(self, receiverMap):
    if not self.map:
        print(f"[ERROR] Node {self.id} has no map yet")
        return
    x = [pos[0] for pos in self.map.keys()]
    y = [pos[1] for pos in self.map.keys()]
    print(f"[MAP] Node {self.id} map:")
    for y in range(min(y), max(y+1)):
        row = ""
        for x in range(min(x), max(x+1)):
            row += self.map.get((x,y), "-")
        print(row)

def createMap(self, receiverMap):
    self.map = dict(receiverMap)

def compareMap(self, receiver, receiverMap):
    # compare every single position of the map 
    print(f"[CMP] Node {receiver} map {receiverMap} vs Node {self.id} map {self.map}")
    diff = 0
    selfKeys = set(self.map.keys())
    receiverKeys = set(receiverMap.keys())
    onlyInSelfMap = selfKeys - receiverKeys                 # I can condense this to when positive is this and when negative, that. Maybe to  -> 
    onlyInReceiverMap = receiverKeys - selfKeys             # Avoid saving it by replacing it in the debugging message and use Betrag for the entries?
    for key in selfKeys & receiverKeys:
        if self.map[key] != receiverMap:
            diff += 1
            print("X")          # change to insert the big X in the corresponding position
        else: 
            print("x")          # change for the actual entry -> what do I do in actual map??? Compare to gameMap!
    for key in onlyInReceiverMap & onlyInSelfMap:
        print("M")              # change to just become an entry in disparity map
    print(f"[UPDATE] Amount of different entries in maps: {diff}, Amount of spots only in {self.id}: {onlyInSelfMap}, Amount of spots only in {receiver}: {onlyInReceiverMap}")

# To do: "whats left to do" map; "mistake map" in comparison to game map -> do I really need a map for that? How to tell the user that that one node is wrong?
# How to figure out own position? Maybe its the only one that never changes???? Should I directly merge the maps in the compare function?
        
def overwriteMap(self, receiverMap, time):
    self.map = receiverMap
    self.t = time

# def mergeMaps(self, receiverMap):
#     mergedMap = {self,map}
#     for key, value in receiverMap.items():
#         mergedMap[key] = value
#    return mergedMap

def checkIfMapComplete(self, receiver, receiverMap):
    #if the amount of entries is not the same, abort instantly
    pass
