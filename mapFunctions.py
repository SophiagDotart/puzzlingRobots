#----- Map functions ----- 
# Handles any functions that deal with the contents of the map
# Switching logic in script "switching conditions"
# Hardware functions in separate script

class MapCompression:
    # contains all functions related to the compression of the map (dictionary to bytearray and back)

    tileToByte = {
        # tile lookup table
        "-": 0,         # empty tile, default
        "+": 1,         # tile that is supposed to be filled
        "·": 2,         # tile that is supposed to be left empty -> alt 250
        "■": 3,         # full correct tile -> alt 254 ■ or alt 219 █?
        "X": 4,         # full wrong tile
        "?": 5          # not sure what is needed
    }

    byteToTile = {v: k for k, v in tileToByte.items()}

    def __init__(self):
        self.compMap = bytearray()  # compressed map storage
        self.margins = (0, 0, 0, 0) # min(x), min(y), width, height

    #----- (De)compress the maps -----
    def compressMap(self, ogMap: dict):
        if not ogMap:
            print(f"[ERROR] Node {self.id} has no map yet")
            self.compMap = bytearray()
            self.margins = (0, 0, 0, 0)
            return
        
        xs = [x for (x, y) in ogMap.keys()]
        ys = [y for (x, y) in ogMap.keys()]
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        width = maxx - minx + 1
        height = maxy - miny + 1

        arr = bytearray(width * height)
        for (x, y), tile in ogMap.items():
            idx = (y - miny) * width + (x - minx)
            arr[idx] = self.tileToByte.get(tile, 0)
        self.compMap = arr
        self.margins = (minx, miny, width, height)

    def decompressMap(self):
        dictMap = {}
        minx, miny, width, height = self.margins
        for j in range(height):
            for i in range(width):
                idx = j * width + i
                tile = self.compMap[idx]
                dictMap[(minx + i, miny + j)] = self.byteToTile.get(tile, "?")
        return dictMap
    
    def printCompressedMap(self):
        if not self.compMap:
            print("[ERROR] Map is empty")
            return
        arr = self.compMap
        minx, miny, width, height = self.margins
        for j in range(height):
            row = ""
            for i in range(width):
                idx = j * width + i
                row += self.byteToTile.get(self.compMap[idx], "?")
            print(row)


def printMap(self):
    if not self.map:
        print(f"[ERROR] Node {self.id} has no map yet")
        return
    x = [pos[0] for pos in self.map.keys()]
    y = [pos[1] for pos in self.map.keys()]
    print(f"[MAP] Node {self.id} map:")
    for cy in range(min(y), max(y)):
        row = ""
        for cx in range(min(x), max(x)):
            row += self.map.get((cx,cy), "-")
        print(row)

def getGoalMap(self, receiverMap):
    self.goalMap = dict(receiverMap)

def compareMap(self, receiver, receiverMap):
    # compare every single position of the map 
    print(f"[CMP] Node {receiver} map {receiverMap} vs Node {self.id} map {self.map}")
    diff = 0
    selfKeys = set(self.map.keys())
    receiverKeys = set(receiverMap.keys())
    onlyInSelfMap = selfKeys - receiverKeys                 # I can condense this to when positive is this and when negative, that. Maybe to  -> 
    onlyInReceiverMap = receiverKeys - selfKeys             # Avoid saving it by replacing it in the debugging message and use abs for the entries?
    for key in selfKeys + receiverKeys:
        if self.map[key] != receiverMap[key]:
            diff += 1
            print("X")          # change to insert the big X in the corresponding position
        else: 
            print("x")          # Compare to gameMap!
    for key in onlyInReceiverMap + onlyInSelfMap:
        print("M")              # change to just become an entry in disparity map
    print(f"[UPDATE] Amount of different entries in maps: {diff}, Amount of spots only in {self.id}: {onlyInSelfMap}, Amount of spots only in {receiver}: {onlyInReceiverMap}")

# To do: "whats left to do" map; "mistake map" in comparison to game map -> do I really need a map for that? How to tell the user that that one node is wrong?
# How to figure out own position? Maybe its the only one that never changes???? Should I directly merge the maps in the compare function?

def compareMapToGoal(self):
    # Essentially the same as compMap but with goalMap as comparison
    print(f"[CMP] Goal map vs Node {self.id} map")
    selfKeys = set(self.map.keys())
    receiverKeys = set(self.goalMap.keys())
    if selfKeys != receiverKeys:
        print("[UPDATE] Game has not been completed yet") 
        return
    for key in selfKeys + receiverKeys:
        if self.map[key] != self.goalMap[key]:
            print("[UPDATE] Game has not been completed yet") # add a reply msg with this pos is incorrect -> add a logic for that, too!
            return
    print(f"[UPDATE] Game has been completed. Congrats!")
        
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
