# ------ SCRIPT ROBOT LOGIC -----
# Script details the behaviour of the node -> root, polite gossip, busy logic and how to handle messages
# Any functions that explicitly deal with checking or comparing or creating maps in "mapFunctions"
# All direct hardware functions in different scripts

# Maybe have a flag description here?

import numpy as np
import random
# import time
import mapFunctions as mapFunc
import messageBuild as msgBuild
import errorHandeling as err

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
        self.STATE = 0              # 0 = PASSIVE state, 1 = ACTIVE
        self.ROOT = 0
        self.t = 0
        self.map = []               
        self.goalMap = []
        # For communications and priority
        self.REPLY = 0
        self.mode = 0
        self.SOURCE = 1             # if it were a card this would be 0
        self.BUSY = 0
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
            self.STATE = 0
            self.ROOT = 0
            self.delayIfBusy = 0
        print(f"[UPDATE] Node {self.id} is now passive again bc timeout")
    
    def politeGossipWait(self, receiver, receiverState):
        if msgBuild.getBUSY():
            self.delayIfBusy = min(self.delayIfBusy +1, maxDelayIfBusy) + random.randint(0, 2)
            print(f"[UPDATE] receiving Node {receiver} is busy. Node {self.id} will retry later")
            err.receiverBusy()
            
        if self.delayIfBusy >= maxDelayIfBusy:      # resend msg when polite gossip delay is ready to retry
            print(f"[SEND] {self.id} has waited politely and will now resend the msg to {receiver}")
            self.delayIfBusy = 0
        elif self.delayIfBusy > 0:                  # wait before interrupting again
            return

    def printData(self):
        print(f"Robot "{self.nodeId}" is at position" {mapFunc.getCurrentPos()})
        print(f"Current state: "{self.STATE})
        print(f"Current root: "{self.ROOT})
        print(f"Current timestamp: "{self.t})
        print(f"Current internal map: "{mapFunc.printCompressedMap(self.map)})
        print(f"Currently playing game: " {self.mode})
        print(f"Current goal/ mode map: "{mapFunc.printCompressedMap(self.goalMap)})
        #not printing waiting queue yet
        print(f"Statistical data")
        print(f"Amount of msg rcv: "{self.rcvMsgs}) 
        print(f"Amount of sent msgs: "{sentMsgs})
        print(f"Timestamp of the last follow-up msg is: "{lastUpdate})

    #----- "How to manage msg way" functions -----
    def msgDetected(self, msg):
        if (msgBuild.getMsgSourceType() == 0):      # msg comes from another robot
            self.msgRcv(msg)
        elif (msgBuild.getMsgSourceType() == 1):    # msg comes from a user
            self.instructRcv(msg)
        else:
            err.messageSourceIncorrect()
    
    def instructRcv(self, msg):
        self.STATE = 1
        self.ROOT = 1
        mapFunc.createMap(msg)
        self.mode = msg["mode"]
        self.t += 1
        print(f"[UPDATE] Node {self.id} received instructions from card | mode = {self.mode}")

    def msgRcv(self, msg, receiver):
        if self.BUSY:
            print(f"[ERROR] Receiver is busy. Try again later")
            msgBuild.replyMsg_busy()
            self.msgQueue.append(msg)
        else:
            self.BUSY = 1
            self.rcvMsgs += 1 
            if(self.mode != msgBuild.getMode()):
                msgBuild.replyMsg_diffMode()
                print(f"[ERROR] Receiver has a different mode")
            else:
                print(f"[UPDATE] Node {self.id} received from Node {msg['sender']}")
                # check if either node root THEN go for the msg that is newer THEN check if they have same mode
                if self.ROOT == 1:
                    pass                                #what is meant is restart the process !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                elif msgBuild.getROOT() == 1:
                    self.overwriteMap(msgBuild.getMap(), msgBuild.getTimestep())
                    print(f"[UPDATE] Node {self.id} copied Node {msgBuild.getSenderId()} it is a ROOT")
                else:
                    if msgBuild.getTimestep() > self.t:
                        self.overwriteMap(msgBuild.getMap(), msgBuild.getTimestep())
                        print(f"[UPDATE] Node {self.id} copied Node {msgBuild.getSenderId()} bc newer data")
                    elif msgBuild.getTimestep() < self.t:
                        print(f"[ERROR] Sender's timestamp is lower than mine")
                        self.sendMsg(msgBuild.getSenderId())
                    else:
                        print(f"[UPDATE] Communicating nodes have the same timestamps, so no exchange")
            self.STATE = 1              
            self.ROOT = self.becomeRoot() 
            self.BUSY = 0
            self.delayIfBusy = 0
        self.lastUpdate = self.t
        self.t += 1
        if self.msgQueue and not self.busy:
            nextMsg = self.msgQueue.pop(0)
            print(f"[QUEUE] Node {self.id} now processing Node {nextMsg['sender']} msg")
            self.msgRcv(nextMsg)
            
                
