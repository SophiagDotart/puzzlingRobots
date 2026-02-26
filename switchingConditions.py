# ------ SCRIPT ROBOT LOGIC -----
# Script details the behaviour of the node -> root, polite gossip, busy logic and how to handle messages
# Any functions that explicitly deal with checking or comparing or creating maps in "mapFunctions"
# All direct hardware functions in different scripts

# Maybe have a flag description here?

import random
from mapFunctions import Map

# tested in input race simulation
timeToPassive = 50                  
INITIAL_ROOT_PROBABILITY = 0.8 
DECAY_RATE = 0.05 

#---- Possible issues in determining priority -----
RESULT_BUSY = 1
RESULT_ROOT = 2
RESULT_MODE = 3
RESULT_TIMESTEP = 4
RESULT_EQUAL = 5
RESULT_COMMUNICATIONACCEPTED = 6

#----- Handling communication order -----
INITDONE = False

#----- General functions -----
def expDecay(t, pFalse, dec): 
    return pFalse * (1- dec) ** t   

#----- Robot identifiers ----
class Node:
    def __init__(self, nodeID):     # starting conditions
        self.ID = nodeID
        self.IDLE = 1
        self.ROOT = False
        self.timestamp = 0
        # For communications and priority
        self.mode = 0
        self.BUSY = False
        self.lastRcvMsgHeader = None
        self.mapHandler = Map()
        self.moduleNumber = None
        print(f"[FYI] Node {self.ID} was created")
        # For statistics
        self.lastUpdate = 0
        self.sentMsgs = 0
        self.rcvMsgs = 0

    #----- Auxiliary functions -----
    def becomeRoot(self):          
        # calculate if node will become a root
        return random.random() < expDecay(self.timestamp, INITIAL_ROOT_PROBABILITY, DECAY_RATE)  

    def timeout(self):
        # if a node has not been updated for timeToPassive steps then become passive
        if self.lastUpdate > timeToPassive:
            self.IDLE = 1
            self.ROOT = False
            self.delayIfBusy = False
            self.INITDONE = False
            print(f"[FYI] Am now in IDLE again bc timeout")

    def printData(self):
        print(f"[DEBUG] Here is my current data")
        print(f"I am robot {self.nodeID}, at step {self.timestamp}, currently in mode {self.mode}")
        print(f"[DEBUG] Statistical data")
        print(f"Amount of msg rcv: {self.rcvMsgs}, Amount of sent msgs: {self.sentMsgs}, Timestamp of the last follow-up msg is: {self.lastUpdate}") 

    #----- "How to manage msg way" functions -----
    def processInstructMsg(self, instructMode):     # reacts to Instruct
        self.BUSY = True
        self.IDLE = not self.BUSY
        self.ROOT = True
        self.mode = instructMode
        self.timestamp += 1

    def processInitMsg(self, senderTimestep, senderMode, senderROOT):    # reacts to INIT
        # IDLE > BUSY > ROOT > MODE > TIMESTAMPS
        self.timestamp += 1
        if (self.IDLE):
            self.INITDONE = True
            return RESULT_COMMUNICATIONACCEPTED
        else:
            if self.BUSY:
                return RESULT_BUSY                  # err.receiverIsBusy()
            else:
                self.BUSY = True
                self.IDLE = not self.BUSY
                self.rcvMsgs += 1 
                if self.ROOT == True:
                    self.BUSY = False
                    self.IDLE = not self.BUSY
                    return RESULT_ROOT              # err.receiverIsROOT()
                elif senderROOT == True and self.ROOT == False:
                    self.INITDONE = True
                    return RESULT_COMMUNICATIONACCEPTED
                else:
                    if self.mode != senderMode:
                        self.ROOT = self.becomeRoot() 
                        self.BUSY = False
                        self.IDLE = not self.BUSY
                        return RESULT_MODE          # err.modeIsDifferent()
                    else:
                        if senderTimestep > self.timestamp:
                            self.INITDONE = True
                            return RESULT_COMMUNICATIONACCEPTED
                        elif senderTimestep < self.timestamp:
                            self.ROOT = self.becomeRoot() 
                            self.BUSY = False
                            self.IDLE = not self.BUSY
                            return RESULT_TIMESTEP  # err.olderTimestamp()
                        else:
                            print(f"[UPDATE] Communicating nodes have the same timestamps and modes, so no exchange")
                            self.ROOT = self.becomeRoot() 
                            self.BUSY = False
                            self.IDLE = not self.BUSY
                            return RESULT_EQUAL  
