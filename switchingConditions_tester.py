# ------ SCRIPT ROBOT LOGIC -----
# Script details the behaviour of the node -> root, polite gossip, busy logic and how to handle messages
# Any functions that explicitly deal with checking or comparing or creating maps in "mapFunctions"
# All direct hardware functions in different scripts

import numpy as np
import random
# import time
import mapFunctions as mapFunc
import positioningAlgorithm as posGet

#----- Parameters -----
PASSIVE = 0
ACTIVE = 1

# tested in input race simulation
timeToPassive = 50                  
initRootProb = 0.8 
decayRate = 0.05 

# to test here
maxDelayIfBusy = 10

#----- General functions -----
def expDecay(t, p0, dec): 
    return p0 * np.power((1- dec), t)   

#----- Robot identifiers ----
class Node:
    def __init__(self, nodeId):     # starting conditions
        self.id = nodeId
        self.state = PASSIVE
        self.root = False
        self.t = 0
        self.map = []               
        self.goalMap = []
        # For communications and priority
        self.reply = False
        self.mode = None
        self.source = 1             # if it were a card this would be 0
        self.busy = False
        self.msgQueue = []          # list of rcv messages -> might have to limit of stored amount later
        self.delayIfBusy = 0
        print(f"[NEW] Node {self.id} was created")
        # For statistics
        self.lastUpdate = 0
        self.sentMsgs = 0
        self.rcvMsgs = 0

    #----- Auxiliary functions -----
    def becomeRoot(self):          
        # calculate if node will become a root
        return np.random.rand() < expDecay(self.t, initRootProb, decayRate)  

    def timeout(self):
        # if a node has not been updated for timeToPassive steps then become passive
        if self.lastUpdate > timeToPassive:
            self.state = PASSIVE
            self.root = False
            self.delayIfBusy = 0
        print(f"[UPDATE] Node {self.id} is now passive again bc timeout")
    
    def politeGossipWait(self, receiver, receiverState):
        if receiverState:
            self.delayIfBusy = min(self.delayIfBusy +1, maxDelayIfBusy) + random.randint(0, 2)
            print(f"[UPDATE] receiving Node {receiver} is busy. Node {self.id} will retry later")
            if self.delayIfBusy >= maxDelayIfBusy:      # resend msg when polite gossip delay is ready to retry
                print(f"[SEND] {self.id} has waited politely and will now resend the msg to {receiver}")
                self.delayIfBusy = 0
            elif self.delayIfBusy > 0:                  # wait before interrupting again
                return

    #----- Sending functions -----
    def sendMsg(self, receiver):
        msg = {"sender": self.id, "t": self.t, "root": self.root, "map": self.map, "mode": self.mode, "reply": False, "source": self.source, "busy": self.busy}
        self.sentMsgs += 1
        print(f"[SEND] Node {self.id} sends msg to Node {receiver}")

    def sendReply(self, receiver):
        msg = {"sender": self.id, "t": self.t, "root": self.root, "map": self.map, "mode": self.mode, "reply": True, "source": self.source}
        print(f"[RECV] Node {self.id} sends reply to Node {receiver}")

    def sendBusyReply(self, receiver):
        msg = {"sender": self.id, "t": self.t, "reply": True, "busy": self.busy}
        print(f"[BUSY] Node {receiver} tried gossiping with busy node {self.id}")
        receiver.handleSignal(msg)

    def sendErrorReply(self, receiver):
        msg = {"sender": self.id, "t": self.t, "reply": True}
        print(f"[ERROR] Node {receiver} is in an invalid positioned")

    #----- "How to manage msg way" functions -----
    def instructRcv(self, msg):
        self.state = ACTIVE
        self.root = True
        self.createMap(msg)
        self.mode = msg["mode"]
        self.t += 1
        print(f"[UPDATE] Node {self.id} received instructions from card | mode = {self.mode}")

    def msgRcv(self, msg, receiver):
        if self.busy:
            self.sendBusyReply(msg['sender'])
            self.msgQueue.append(msg)
        else:
            self.busy = True
            self.rcvMsgs += 1 
            print(f"[RECV] Node {self.id} received from Node {msg['sender']} | time = {msg['t']} | root = {msg['root']} | mode = {msg['mode']}")
            # check if either node root THEN go for the msg that is newer THEN check if they have same mode
            if self.root == True:
                return 
            elif msg["root"] == True:
                self.overwriteMap(msg["map"], msg["t"])
                print(f"Node {self.id} copied Node {msg['sender']} bc root = {msg['root']}")
            else:
                if msg["t"] > self.t:
                    self.overwriteMap(msg["map"], msg["t"])
                    print(f"Node {self.id} copied Node {msg['sender']} bc newer data")
                elif msg["t"] < self.t:
                    self.sendMsg(msg["sender"])
                else:
                    if self.mode == msg["mode"]:
                        self.compareMap(msg["sender"], msg["map"])
                    else:
                        print(f"Node {self.id} and Node {msg['sender']} have same time = {msg['t']} so no exchange")
            self.state = ACTIVE              
            self.root = self.becomeRoot() 
            self.busy = False
            self.delayIfBusy = 0
        receiver.handleSignal(msg)
        self.lastUpdate = self.t
        self.t += 1
        if self.msgQueue and not self.busy:
            nextMsg = self.msgQueue.pop(0)
            print(f"[QUEUE] Node {self.id} now processing Node {nextMsg['sender']} msg")
            self.msgRcv(nextMsg)
            
    def handleSignal(self, msg):
        if msg["source"] == 0:
            self.instructRcv(msg)                       # the received msg comes from user through a card
        else:
            self.msgRcv(msg, msg["sender"])             # the received msg sent comes from another robot


if __name__ == "__main__":                              # Testing function "it switches"
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
    for node in [A, B, C, D, E]:                 # print all stats at the end to survey each nodes progress
        print(f"Node = {node.id}, state = {node.state}, root = {node.root}, mode = {node.mode}, t = {node.t}, sent msgs = {node.sentMsgs}, rcv msgs = {node.rcvMsgs}")

# if __name__ == "__main__":                  # Testing function "does the polite gossip delay stabilize communication functions and minimize interactions?"
#     # create swarm
#     nodes = {i: Node(i) for i in range(1, 6)}
#     A, B, C, D, E = nodes.values()

#     # simulate steps
#     print("\n--- Simulation start ---\n")
#     for step in range(10):
#         print(f"\n=== Step {step} ===")
#         # decay politeness delay gradually
#         for n in nodes.values():
#             n.decayDelay()

#         # simple random communication pattern
#         sender, receiver = random.sample(list(nodes.values()), 2)
#         sender.sendMsg(receiver)

#     print("\n--- Final stats ---")
#     for n in nodes.values():
#         print(f"Node {n.id}: sent={n.sentMsgs}, received={n.rcvMsgs}, delay={n.delayIfBusy:.1f}, queue={len(n.msgQueue)}")
                