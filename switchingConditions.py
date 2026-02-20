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
import errorHandling as err
from mapFunctions import Map

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
        self.IDLE = 1
        self.ROOT = 0
        self.t = 0
        # For communications and priority
        self.REPLY = 0
        self.mode = 0
        self.SOURCE = 1             # if it were a card this would be 0
        self.BUSY = 0
        self.delayIfBusy = 0
        self.updateCode = 1 
        self.lastRcvMsgHeader = None
        print(f"[NEW] Node {self.id} was created")
        # For statistics
        self.lastUpdate = 0
        self.sentMsgs = 0
        self.rcvMsgs = 0
        self.mapHandler = Map()

    #----- Auxiliary functions -----
    def becomeRoot(self):          
        # calculate if node will become a root
        return np.random.rand() < expDecay(self.t, initRootProb, decayRate)  

    def timeout(self):
        # if a node has not been updated for timeToPassive steps then become passive
        if self.lastUpdate > timeToPassive:
            self.IDLE = 1
            self.ROOT = 0
            self.delayIfBusy = 0
        print(f"[FYI] Node {self.id} is now IDLE again bc timeout")
    
    def politeGossipWait(self, receiver):
        if msgBuild.getBUSY():
            self.delayIfBusy = min(self.delayIfBusy +1, maxDelayIfBusy) + random.randint(0, 2)
            print(f"[FYI] receiving Node {receiver} is busy. Node {self.id} will retry later")
            err.receiverBusy()
        if self.delayIfBusy >= maxDelayIfBusy:      # resend msg when polite gossip delay is ready to retry
            print(f"[FIY] {self.id} has waited politely and will now resend the msg to {receiver}")
            self.delayIfBusy = 0
        elif self.delayIfBusy > 0:                  # wait before interrupting again
            return

    def printData(self):
        print(f"Robot {self.nodeId} is at position ({self.mapHandler.x}, {self.mapHandler.y})")
        print(f"Is ROOT: {self.ROOT}, is IDLE: {self.IDLE}")
        print(f"Current timestamp: {self.t}")
        print(f"Current internal map: {mapFunc.printCompressedMap(self.compMap)}")
        print(f"Currently playing game: {self.mode}")
        print(f"Current goal/ mode map: {mapFunc.printCompressedMap(self.compGoalMap)}")
        #not printing waiting queue yet
        print(f"Statistical data")
        print(f"Amount of msg rcv: {self.rcvMsgs}") 
        print(f"Amount of sent msgs: {self.sentMsgs}")
        print(f"Timestamp of the last follow-up msg is: {self.lastUpdate}")

    #----- "How to manage msg way" functions -----
    def msgDetected(self, msg):
        if (msgBuild.getMsgSourceType() == 0):      # msg comes from another robot
            self.msgRcv(msg)
        elif (msgBuild.getMsgSourceType() == 1):    # msg comes from a user
            self.instructRcv(msg)
        else:
            err.messageSourceIncorrect()
    
    def instructRcv(self, msg):
        self.IDLE = 0
        self.ROOT = 1
        mapFunc.createMap(msg)
        self.mode = msg["mode"]
        self.t += 1
        print(f"[FYI] Node {self.id} received instructions from card, mode = {self.mode}")

    def msgRcv(self, msg, receiver):
        # UPDATE > IDLE > BUSY > ROOT > MODE > TIMESTAMPS
        if msgBuild.getUpdateCode()> self.updateCode:
            print(f"[ERROR] Update structure not implemented")
            pass
        elif (self.IDLE):
            self.overwriteMap(msgBuild.getMap(), msgBuild.getTimestep())
            print(f"[FYI] Node {self.id} copied Node {msgBuild.getSenderId()}")
        else:
            if self.BUSY:
                self.msgQueue.append(msg)
                err.receiverIsBusy()
            else:
                self.BUSY = 1
                self.rcvMsgs += 1 
                if self.ROOT == 1:
                    err.receiverIsROOT()
                elif msgBuild.getROOT() == 1 and self.ROOT == 0:
                    self.overwriteMap(msgBuild.getMap(), msgBuild.getTimestep())
                    print(f"[FYI] Node {self.id} copied Node {msgBuild.getSenderId()}")
                    
                else:
                    if(self.mode != msgBuild.getMode()):
                        err.modeIsDifferent()
                    else:
                        if msgBuild.getTimestep() > self.t:
                            self.overwriteMap(msgBuild.getMap(), msgBuild.getTimestep())
                            print(f"[FYI] Node {self.id} copied Node {msgBuild.getSenderId()} bc newer data")
                        elif msgBuild.getTimestep() < self.t:
                            err.olderTimestamp()
                        else:
                            print(f"[UPDATE] Communicating nodes have the same timestamps and modes, so no exchange")
                self.IDLE = 1              
                self.ROOT = self.becomeRoot() 
                self.BUSY = 0
                self.delayIfBusy = 0
            self.lastUpdate = self.t
            self.t += 1
        self.IDLE = 0
