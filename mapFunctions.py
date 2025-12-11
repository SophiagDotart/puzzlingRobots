#----- Map functions ----- 
# Handles any functions that deal with the contents of the map
# Switching logic in script "switching conditions"
# Hardware functions in separate script

import switchingConditions_tester as switchCon
import positioningAlgorithm as posGet

class MapCompression:
    # contains all functions related to the compression of the map (dictionary to bytearray and back)

    MAX_MAP_SIZE = 1024

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
        self.compMap = bytearray()  # compressed map for storage
        self.compGoalMap = bytearray()
        self.margins = (0, 0, 0, 0) # min(x), min(y), width, height
        self.goalMargins = (0, 0, 0, 0)

    #----- (De)compress the maps -----
    def compressMapToByteArray(self, ogMap: dict):      # only the cards have a dict
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

    # def decompressMapToDict(self):
    #     dictMap = {}
    #     minx, miny, width, height = self.margins
    #     for j in range(height):
    #         for i in range(width):
    #             idx = j * width + i
    #             tile = self.compMap[idx]
    #             dictMap[(minx + i, miny + j)] = self.byteToTile.get(tile, "?")
    #     return dictMap
    
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


    def printDictMap(self):
        if not self.map:
            print(f"[ERROR] Node {self.id} has no map yet")
            return
        x = [pos[0] for pos in self.map.keys()]
        y = [pos[1] for pos in self.map.keys()]
        print(f"[MAP] Node {self.id} map:")
        for cy in range(min(y), max(y)+1):
            row = ""
            for cx in range(min(x), max(x)):
                row += self.map.get((cx,cy), "-")
            print(row)

    def getGoalMap(self, receiverMap):
        self.goalMap = self.mapCompression.compressMap(receiverMap)
        print(f"[UPDATE] Node {self.id} now has a map with game/ state {self.state}")

    def compareMap(self, receiver, receiverMap):
        # compare every single position of the map 
        print(f"[CMP] Node {receiver} map {receiverMap} vs Node {self.id} map {self.map}")
        diff = 0
        selfKeys = set(self.map.keys())
        receiverKeys = set(receiverMap.keys())
        onlyInSelfMap = selfKeys - receiverKeys                 # I can condense this to when positive is this and when negative, that. Maybe to  -> 
        onlyInReceiverMap = receiverKeys - selfKeys             # Avoid saving it by replacing it in the debugging message and use abs for the entries?
        for key in (selfKeys | receiverKeys):
            if self.map[key] != receiverMap[key]:
                diff += 1
                print("X")          # change to insert the big X in the corresponding position
            else: 
                print("x")          # Compare to gameMap!
        for key in onlyInReceiverMap | onlyInSelfMap:
            print("M")              # change to just become an entry in disparity map
        print(f"[UPDATE] Amount of different entries in maps: {diff}, Amount of spots only in {self.id}: {onlyInSelfMap}, Amount of spots only in {receiver}: {onlyInReceiverMap}")

    # def getDifferencesBetween2Maps(self, receiverMap):
    #     pass

    def compareMapToGoal(self):
        # Essentially the same as compMap but with goalMap as comparison
        print(f"[CMP] Goal map vs Node {self.id} map")
        selfKeys = set(self.map.keys())
        receiverKeys = set(self.goalMap.keys())
        if selfKeys != receiverKeys:                                #if the amount of entries is not the same, abort instantly
            print("[UPDATE] Game has not been completed yet") 
            return False
        for key in (selfKeys | receiverKeys):
            if self.map[key] != self.goalMap[key]:
                print("[UPDATE] Game has not been completed yet")   # add a reply msg with this pos is incorrect -> add a logic for that, too!
                return False
        print(f"[UPDATE] Game has been completed. Congrats!")
        return True

    def getTileFromCompressedMap(self, xPos, yPos):
        if not self.compMap:
            return None
        minx, miny, width, height = self.margins
        if not (minx <= xPos < minx + width and miny <= yPos < miny + height):
            return None 
        idx = (yPos - miny) * width + (xPos - minx)       # Convert (x, y) → flat array index
        byte = self.compMap[idx]
        return MapCompression.byteToTile.get(byte, "?")

    def attachmentAttempt(self, msg):      
        # to check if the node is not being attached in a forbidden position
        if not hasattr(self, "goalMap") or not self.goalMap:
            print(f"[ERROR] There is no game/ goalMap defined yet")
            return False
        newX, newY = self.getOwnPos(msg)
        allowedPos = {"+", "■"}
        tile = self.goalMap.get((newX, newY), None)
        if tile in allowedPos: 
            print(f"[UPDATE] Node will be added to swarm function at this position")
            # activate a certain color?
            # start the whole map cycle
            return True
        else:
            print(f"[ERROR] This is not a valid position for this game")
            switchCon.sendErrorReply(msg["id"])
            # maybe send a reply specifying why this attachment attempt was shut down?
            # send signal to user that this action is incorrect
            return False

    # def findMistakesInMap():        # to create a map where all positions that do not correspond with the goalMap; required?
    #     pass
            
    def overwriteMap(self, receiverMap, time):
        self.map = receiverMap
        self.t = time

    # def mergeMaps(self, receiverMap):
    #     mergedMap = {self,map}
    #     for key, value in receiverMap.items():
    #         mergedMap[key] = value
    #    return mergedMap
