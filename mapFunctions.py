#----- Map functions ----- 
# Handles any functions that deal with the contents of the map 
# create, (de)compress, change maps including figuring out where the user is on the map


class Map:
    # functions related to the compression of the map (dictionary to bytearray and back)

    MAX_MAP_SIZE = 2**8

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
    
    orientation = {
        1: (-1, 0),     # left
        2: (0, +1),     # up
        3: (+1, 0),     # right
        4: (0, -1)      # down
    }

    def __init__(self):
        self.compMap = bytearray()  # compressed map for storage
        self.compGoalMap = bytearray()
        self.margins = (0, 0, 0, 0) # min(x), min(y), width, height
        self.goalMargins = (0, 0, 0, 0)
        
    def deleteCompMap(self):   
        self.compMap.clear()
        self.margins = (0, 0, 0, 0)
        print(f"[FYI] compressed map has been deleted") 
        
    #----- Find and update own position in map -----
    @staticmethod
    def getOwnPos(senderX, senderY, orientationX, orientationY):
        # when the node first enters the swarm, it gets assigned a coordinate by its neighbour
        # it is calculated "Im sending on module 1" and "Im receiving on module 3"  
        return senderX + orientationX, senderY + orientationY       # add the difference to the neighbour's position

    def overwritePos(self, newX, newY):
        self.x, self.y = newX, newY

    def updatePosition(node, senderX, senderY):
        # root status do not get overwritten
        if node.ROOT:
            return False # err.receiverIsROOT()
        Map.overwritePos(senderX, senderY)
        print(f"[FYI] Node {node.id} updated it's position to ({senderX}, {senderY})")
        return True
        
    #----- (De)compress the maps -----
    @staticmethod
    def compressMapToByteArray(ogMap: dict):      # only the cards have a dict
        if not ogMap:
            return None # err.emptyMap()
        xs = [x for (x, y) in ogMap.keys()]
        ys = [y for (x, y) in ogMap.keys()]
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        width = maxx - minx + 1
        height = maxy - miny + 1
        if width * height > Map.MAX_MAP_SIZE:          # safety check
            return False # err.mapTooLarge()
        arr = bytearray(width * height)
        for (x, y), tile in ogMap.items():
            idx = (y - miny) * width + (x - minx)
            arr[idx] = Map.tileToByte.get(tile, 0)
        margins = (minx, miny, width, height)
        return arr, margins
    
    def printCompressedMap(self):
        if not self.compMap:
            return False # err.emptyMap()
        minx, miny, width, height = self.margins
        for j in range(height):
            row = ""
            for i in range(width):
                idx = j * width + i
                row += self.byteToTile.get(self.compMap[idx], "?")
            print(row)

    def compareMap(self, node, receiver, receiverMap):
        # compare every single position of the map 
        diff = 0
        selfKeys = set(self.compMap.keys())
        receiverKeys = set(receiverMap.keys())
        onlyInSelfMap = selfKeys - receiverKeys                 # I can condense this to when positive is this and when negative, that. Maybe to  -> 
        onlyInReceiverMap = receiverKeys - selfKeys             # Avoid saving it by replacing it in the debugging message and use abs for the entries?
        for key in (selfKeys | receiverKeys):
            if self.compMap.get(key) != receiverMap.get(key):
                diff += 1
                print("X")          # change to insert the big X in the corresponding position
            else: 
                print("x")          # Compare to gameMap!
        for key in onlyInReceiverMap | onlyInSelfMap:
            print("M")              # change to just become an entry in disparity map
        print(f"[FYI] Amount of different entries in maps: {diff}, Amount of spots only in {node.id}: {onlyInSelfMap}, Amount of spots only in {receiver}: {onlyInReceiverMap}")

    # def getDifferencesBetween2Maps(self, receiverMap):
    #     pass

    def compareMapToGoal(self, goalMap):
        # Essentially the same as compMap but with goalMap as comparison
        selfKeys = set(self.compMap.keys())
        receiverKeys = set(goalMap.keys())
        if selfKeys != receiverKeys:                                #if the amount of entries is not the same, abort instantly
            print("[FYI] Mode has not been completed yet") 
            return False
        for key in (selfKeys | receiverKeys):
            if self.compMap[key] != goalMap[key]:
                print("[FYI] Mode has not been completed yet")   # add a reply msg with this pos is incorrect -> add a logic for that, too!
                return False
        print(f"[FYI] Mode has been completed. Congrats!")
        return True

    def getTileFromCompressedMap(self, xPos, yPos):
        if not self.compMap:
            return False # err.emptyGoalMap
        minx, miny, width, height = self.margins
        if not (minx <= xPos < minx + width and miny <= yPos < miny + height):
            return None # err.mapTooLarge
        idx = (yPos - miny) * width + (xPos - minx)       # Convert (x, y) → flat array index
        byte = self.compMap[idx]
        return self.byteToTile.get(byte, "?")

    def setTileInCompressedMap(self, posX, posY):
        #if correct then attach the square, incorrect is X, else err.wrongPosition()
        pass

    def createEmptyMap():
        return bytearray()

    def attachmentAttempt(self, senderX, senderY, orientationX, orientationY):      
        # to check if the node is not being attached in a forbidden position
        if not self.compMap:
            return None # err.emptyMap()
        newX, newY = self.getOwnPos(senderX, senderY, orientationX, orientationY)
        allowedPos = {"+", "■"}
        tile = self.getTileFromCompressedMap(newX, newY)
        if tile in allowedPos: 
            print(f"[FYI] Node will be added to swarm function at this {newX}, {newY} position")
            # activate a certain color?
            # start the whole map cycle
            return True
        else:
            return False # err.attachmentPosForbidden(self.pos(newX), self.pos(newY))
            
    def overwriteMap(self, node, receiverMap, time):
        self.compMap = receiverMap
        node.timestamp = time

    # def mergeMaps(self, receiverMap):
    #     mergedMap = {self,map}
    #     for key, value in receiverMap.items():
    #         mergedMap[key] = value
    #    return mergedMap
