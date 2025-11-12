import numpy as np
import random

#----- Parameters -----
PASSIVE = 0
ACTIVE = 1

timeToPassive = 50                  # same as in input race

#----- Robot identifiers ----
class Node:
    def __init__(self, nodeId):     # starting conditions
        self.id = nodeId
        self.state = PASSIVE
        self.root = False
        self.t = 0
        self.map = {}               # dictionary to store positions on map
        # For communications and priority
        self.reply = False
        self.mode = None
        self.source = 1
        self.busy = False
        self.msgQueue = []          # list of rcv messages -> might have to limit of stored amount later
        print(f"[NEW] Node {self.id} was created")
        # For statistics
        self.lastUpdate = 0
        self.sentMsgs = 0
        self.rcvMsgs = 0

    #----- Auxiliary functions -----
    def becomeRoot(self):          # from input race; take from there once codes combined
        return np.random.rand() < 0.2

    def timeout(self):
        # if a node has not been updated for timeToPassive steps then become passive
        if self.lastUpdate > timeToPassive:
            self.state = PASSIVE
            self.root = False
        print(f"[UPDATE] Node {self.id} is now passive again bc timeout")

    def sendMsg(self, receiver):
        msg = {"sender": self.id, "t": self.t, "root": self.root, "map": self.map, "mode": self.mode, "reply": False, "source": self.source}
        self.sentMsgs += 1
        print(f"[SEND] Node {self.id} sends msg to Node {receiver} | time = {self.t} | root = {self.root} | reply = False")

    def sendReply(self, receiver):
        msg = {"sender": self.id, "t": self.t, "root": self.root, "map": self.map, "mode": self.mode, "reply": True, "source": self.source}
        print(f"[RECV] Node {self.id} sends reply to Node {receiver} | time = {msg['t']} | reply = True")

    #----- Map functions ----- maybe outsource to the map functions script???????
    def createMap(self, receiverMap):
        return receiverMap

    def compareMap(self, receiver, receiverMap):
        print(f"[CMP] Node {receiver} map {receiverMap} vs Node {self.id} map {self.map}")

    def updateMap(self, receiver):
        print(f"[UPDATE] Node {self.id} map was updated according to Node {receiver} map")

    def overwrite(self, receiverMap, time):
        self.map = receiverMap
        self.t = time

    #----- Signal handling functions -----
    def instructRcv(self, msg):
        self.state = ACTIVE
        self.root = True
        self.createMap(msg)
        self.mode = msg["mode"]
        self.t += 1
        print(f"[UPDATE] Node {self.id} received instructions from card | mode = {self.mode}")

    def msgRcv(self, msg):
        self.rcvMsgs += 1 
        print(f"[RECV] Node {self.id} received from Node {msg['sender'].id} | time = {msg['t']} | root = {msg['root']} | mode = {msg['mode']}")
        # check if either node root THEN go for the msg that is newer THEN check if they have same mode
        if self.root == True:
            pass
        elif msg["root"] == True:
            self.overwrite(msg["map"], msg["t"])
            print(f"Node {self.id} copied Node {msg['sender'].id} | time = {msg['t']} bc root = {msg['root']}")
        else:
            if msg["t"] > self.t:
                self.overwrite(msg["map"], msg["t"])
                print(f"Node {self.id} copied Node {msg['sender'].id} | time = {msg['t']} bc newer data")
            elif msg["t"] < self.t:
                self.sendMsg(msg["sender"])
            else:
                if self.mode == msg["mode"]:
                    self.compareMap(msg["sender"], msg["map"])
                else:
                    print(f"Node {self.id} and Node {msg['sender'].id} have same time = {msg['t']} so no exchange")
        self.t += 1
        self.lastUpdate = self.t
        self.state = ACTIVE              
        self.root = self.becomeRoot()    
        self.t += 1
        self.lastUpdate = self.t

    def handleSignal(self, msg):
        if msg["source"] == "0":
            self.instructRcv(msg)       # the received msg comes from user through a card
        else:
            self.msgRcv(msg)            # the received msg sent comes from another robot


if __name__ == "__main__":
    A = Node(1)
    B = Node(2)
    C = Node(3)
    D = Node(4)
    E = Node(5)

    A.sendMsg(B)
    A.sendMsg(E)

    B.sendMsg(C)
    B.sendMsg(D)

    C.sendMsg(A)

    D.sendMsg(B)

    print(f"Final states: ")
    for node in [A, E]:             # print all stats at the end to survey each nodes progress
        print(f"Node = {node.id}," 
              f"state = {node.state},"
              f"root = {node.root},"
              f"mode = {node.mode},"
              f"t = {node.t}"
              f"sent msgs = {node.sentMsgs}"
              f"rcv msgs = {node.rcvMsgs}")
                