# ------ SCRIPT ROBOT LOGIC -----
# Script details the behaviour of the node -> root, polite gossip, busy logic and how to handle messages
# Any functions that explicitly deal with checking or comparing or creating maps in "mapFunctions"
# All direct hardware functions in different scripts

# Maybe have a flag description here?

import numpy as np
from mapFunctions import Map

# tested in input race simulation
timeToPassive = 50                  
INITIAL_ROOT_PROBABILITY = 0.8 
DECAY_RATE = 0.05 

#---- -----
RESULT_BUSY = 1
RESULT_ROOT = 2
RESULT_MODE = 3
RESULT_TIMESTEP = 4
RESULT_EQUAL = 5
RESULT_COMMUNICATIONACCEPTED = 6

#----- General functions -----
def expDecay(t, p0, dec): 
    return p0 * np.power((1- dec), t)   

#----- Robot identifiers ----
class Node:
    def __init__(self, nodeId):     # starting conditions
        self.id = nodeId
        self.IDLE = 1
        self.ROOT = 0
        self.timestamp = 0
        # For communications and priority
        self.mode = 0
        self.BUSY = 0
        self.lastRcvMsgHeader = None
        self.mapHandler = Map()
        self.moduleNumber = None
        print(f"[FYI] Node {self.id} was created")
        # For statistics
        self.lastUpdate = 0
        self.sentMsgs = 0
        self.rcvMsgs = 0

    #----- Auxiliary functions -----
    def becomeRoot(self):          
        # calculate if node will become a root
        return np.random.rand() < expDecay(self.timestamp, INITIAL_ROOT_PROBABILITY, DECAY_RATE)  

    def timeout(self):
        # if a node has not been updated for timeToPassive steps then become passive
        if self.lastUpdate > timeToPassive:
            self.IDLE = 1
            self.ROOT = 0
            self.delayIfBusy = 0
        print(f"[FYI] Am now in IDLE again bc timeout")

    # def printData(self):
    #     print(f"Robot {self.nodeId} is at position ({self.mapHandler.x}, {self.mapHandler.y})")
    #     print(f"Is ROOT: {self.ROOT}, is IDLE: {self.IDLE}")
    #     print(f"Current timestamp: {self.timestamp}")
    #     print(f"Current internal map: {mapFunc.printCompressedMap(self.compMap)}")
    #     print(f"Currently playing game: {self.mode}")
    #     print(f"Current goal/ mode map: {mapFunc.printCompressedMap(self.compGoalMap)}")
    #     #not printing waiting queue yet
    #     print(f"Statistical data")
    #     print(f"Amount of msg rcv: {self.rcvMsgs}") 
    #     print(f"Amount of sent msgs: {self.sentMsgs}")
    #     print(f"Timestamp of the last follow-up msg is: {self.lastUpdate}")

    #----- "How to manage msg way" functions -----
    def processInstructMsg(self, instructMode): # reacts to Instruct
        self.IDLE = 0
        self.ROOT = 1
        self.mode = instructMode
        self.timestamp += 1

    def processInitMsg(self, senderTimestep, senderMode, senderROOT):    # reacts to INIT
        # IDLE > BUSY > ROOT > MODE > TIMESTAMPS
        self.IDLE = 0
        self.ROOT = self.becomeRoot() 
        self.timestamp += 1
        if (self.IDLE):
            return RESULT_COMMUNICATIONACCEPTED
        else:
            if self.BUSY:
                return RESULT_BUSY # err.receiverIsBusy()
            else:
                self.BUSY = 1
                self.rcvMsgs += 1 
                if self.ROOT == 1:
                    self.BUSY = 0
                    return RESULT_ROOT # err.receiverIsROOT()
                elif senderROOT == 1 and self.ROOT == 0:
                    return RESULT_COMMUNICATIONACCEPTED
                else:
                    if(self.mode != senderMode):
                        self.BUSY = 0
                        return RESULT_MODE # err.modeIsDifferent()
                    else:
                        if senderTimestep > self.timestamp:
                            return RESULT_COMMUNICATIONACCEPTED
                        elif senderTimestep < self.timestamp:
                            self.BUSY = 0
                            return RESULT_TIMESTEP # err.olderTimestamp()
                        else:
                            print(f"[UPDATE] Communicating nodes have the same timestamps and modes, so no exchange")
                            self.BUSY = 0
                            return RESULT_EQUAL  
