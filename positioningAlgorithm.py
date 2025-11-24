#----- Coordinate functions ----- 
# Handles any functions that deal with the position of the node within the map
# required information from msg: senderPosition, senderModule, senderID, root,

orientation = {
    1: (-1, 0),     # left
    2: (0, +1),     # up
    3: (+1, 0),     # right
    4: (0, -1)      # down
}

def getOwnPos(self, msg):
    # when the node first enters the swarm, it gets assigned a coordinate by its neighbour
    senderX, senderY = msg["senderPos"]
    moduleNumber = msg["senderModule"]
    dx, dy = orientation[moduleNumber]      # it is calculated "Im sending on module 1" and "Im receiving on module 3"
    return senderX + dx, senderY + dy       # add the difference to the neighbour's position

def overwritePos(self, msg):
    self.x, self.y = getOwnPos(msg)

def updatePosition(self, msg):
    # root status do not get overwritten
    if self.root:
        print(f"[UPDATE] This node is a root, it will keep its position")
        return
    overwritePos(msg)
    senderX, senderY = msg["senderPos"]
    print(f"[UPDATE] Node {self.id} updated it's position to ({senderX}, {senderY})")

# def printAsciiMap(tileMap: dict):
#     if not tileMap:
#         print("[ERROR] There is no map to display")
#         return
#     xs = [x for (x, y) in tileMap.keys()]
#     ys = [y for (x, y) in tileMap.keys()]
#     minx, maxx = min(xs), max(xs)
#     miny, maxy = min(ys), max(ys)

#     print("\n[ASCII MAP]")
#     for y in range(maxy, miny - 1, -1):     # print highest Y first
#         row = []
#         for x in range(minx, maxx + 1):
#             row.append(tileMap.get((x, y), "-"))
#         print(" ".join(row))
