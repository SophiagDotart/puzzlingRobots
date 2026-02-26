#----- Map functions ----- 
# Handles any functions that deal with the contents of the map 
# create, (de)compress, change maps including figuring out where the user is on the map


class Map:
    # functions related to the compression of the map (dictionary to bytearray and back)

    MAX_MAP_SIZE = 2**8

    # sth does not exist
    MAPERROR_EMPTYMAP = 1
    MAPERROR_EMPTYGOALMAP = 2
    # sth went wrong with the map
    MAPERROR_INCORRECTLENGTH = 4
    MAPERROR_IAMAROOT = 5
    MAPERROR_MARGINSDIFFER = 6
    # sth went wrong attaching a tile
    MAPERROR_ATTACHMENTFORBIDDEN = 3
    MAPERROR_WRONGTILE = 7
    MAPERROR_OUTSIDEOFMARGINS = 8
    MAPERROR_UNRECOGNIZEDTILE = 9 
    

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
        self._compMap = bytearray()     # compressed map for storage
        self._compGoalMap = bytearray()
        self.margins = (0, 0, 0, 0)     # min(x), min(y), width, height
        self.goalMargins = (0, 0, 0, 0)

    def deleteCompMap(self):   
        self._compMap.clear()
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

    def updatePosition(self, senderX, senderY):
        # root status do not get overwritten
        if self.ROOT:
            return False # err.receiverIsROOT()
        self.overwritePos(senderX, senderY)
        print(f"[FYI] Node {self.id} updated it's position to ({senderX}, {senderY})")
        return True
        
    #----- (De)compress the maps -----
    @staticmethod
    def compressMapToByteArray(ogMap: dict):    # only the cards have a dict
        if not ogMap:
            return Map.MAPERROR_EMPTYMAP        # err.emptyMap()
        xs = [x for (x, y) in ogMap.keys()]
        ys = [y for (x, y) in ogMap.keys()]
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        width = maxx - minx + 1
        height = maxy - miny + 1
        if width * height > Map.MAX_MAP_SIZE:  
            return Map.MAPERROR_INCORRECTLENGTH # err.mapTooLarge()
        arr = bytearray(width * height)
        for (x, y), tile in ogMap.items():
            idx = (y - miny) * width + (x - minx)
            arr[idx] = Map.tileToByte.get(tile, 0)
        margins = (minx, miny, width, height)
        return arr, margins
    
    def printCompressedMap(self):
        print(f"[DEBUG] This is my current compressed map:")
        if not self._compMap:
            return self.MAPERROR_EMPTYMAP       # err.emptyMap()
        minx, miny, width, height = self.margins
        for j in range(height):
            row = ""
            for i in range(width):
                idx = j * width + i
                row += self.byteToTile.get(self._compMap[idx], "?")
            print(row)

#----- Compare maps -----
    def overwriteCompressedMap(self, newMap, margins): # throw all caution out the window
        self._compMap = newMap
        self.margins = margins
        return True

    def overwriteGoalMap(self, newGoalMap, margins):
        self.compGoalMap = newGoalMap
        self.goalMargins = margins
        return True

    def compareMaps(self, senderMap, goalMaps, goalMapMargins):
        if not self._compMap:
            return self.MAPERROR_EMPTYMAP           # err.emptyMap
        elif not senderMap:
            return self.MAPERROR_EMPTYGOALMAP       # err.emptyGoalMap
        elif self.margins != goalMapMargins:
            return self.MAPERROR_MARGINSDIFFER      # err.marginsDiffer
        elif len(self._compMap) >= len(senderMap):
            return self.MAPERROR_INCORRECTLENGTH    # err.mapIncorrectLength
        else:
            minX, minY, width, height = self.margins
            if len(self._compMap) != width * height:
                return self.MAPERROR_INCORRECTLENGTH
            for i in range(len(self._compMap)):
                posX = minX + i % width             # modulo to get the remainder of row -> got column
                posY = minY + i // width            # integer division to get row
                entry = self._compMap[i]
                if entry != senderMap[i]:
                    if not self.checkTileIsCorrect(posX, posY, entry, goalMapMargins):
                        return self.MAPERROR_WRONGTILE                  # err.wrongTile
                    if not self.setTileInCompressedMap(posX, posY, entry):
                        return self.MAPERROR_ATTACHMENTFORBIDDEN        # err.forbidden attachment
                    # update that tile and move to the next position
                else: 
                    pass        # they are the same, we can just continue testing next position
        return True             # maps are the same

    def compareMapToGoal(self, goalMap):
        # Essentially the same as compMap but with goalMap as comparison
        if not self._compMap:
            return self.MAPERROR_EMPTYMAP           # err.emptyMap
        if not goalMap:
            return self.MAPERROR_EMPTYGOALMAP       # err.emptyGoalMap
        if len(self._compMap) != len(goalMap):
            print("[FYI] Mode has not been completed yet")
            return False
        for i in range(len(self._compMap)):
            if self._compMap[i] != goalMap[i]:
                print(f"[FYI] There is an error in the current mode map")
                return self.MAPERROR_WRONGTILE      # err.wrongTile
            else: 
                pass        # they are the same, we can just continue testing next position
        print(f"[FYI] Mode has been completed. Congrats!")
        return True         # maps are the same

    def setTileInCompressedMap(self, posX, posY, tile):
        if not self._compMap:
            return self.MAPERROR_EMPTYMAP           # err.empty map
        if tile not in self.tileToByte:
            return self.MAPERROR_UNRECOGNIZEDTILE   # err.unrecognized tile
        index = self.getIndex(posX, posY)
        if index is not True:
            return self.MAPERROR_OUTSIDEOFMARGINS   # err.outside margins
        self._compMap[index] = self.tileToByte[tile]
        return True

#----- Check that everything is alright functions -----
    def checkTileIsCorrect(self, posX, posY, goalMap):
        if self._compMap[posX, posY] != goalMap[posX, posY]:
            return self.MAPERROR_WRONGTILE          # err.wrong tile
        else:
            return True
        
    def checkIfCompressedMapIsCorrect(self):        # length correct? values within expected bounds? correct dimensions?
        expectedSize = self.width * self.height
        if len(self._compMap) != expectedSize:
            return False
        for i in range(len(self._compMap)):
            value = self._compMap[i]
            if value not in self.tileToByte:
                return False
        return True

#----- Getters -----
    def getIndex(self, posX, posY):
        minx, miny, width, height = self.margins
        if not (minx <= posX < minx + width and miny <= posY < miny + height):
            return None                                     # err.outside margins
        else:
            index = (posY - miny) * width + (posX - minx)   # Convert (x, y) → flat array index
            return index
        
    def getTileInCompressedMap(self, posX, posY):
        if not self._compMap:
            return self.MAPERROR_EMPTYMAP           # err.empty map
        minx, miny, width, height = self.margins
        if not (minx <= posX < minx + width and miny <= posY < miny + height):
            return self.MAPERROR_OUTSIDEOFMARGINS   # err.outside margins
        tile = self._compMap[self.getIndex(posX, posY)]
        if tile not in self.tileToByte:
            return self.MAPERROR_UNRECOGNIZEDTILE   # err.unrecognized tile
        index = self.getIndex(posX, posY)
        if index is not True:
            return self.MAPERROR_OUTSIDEOFMARGINS   # err.outside margins
        return self._compMap[index]
