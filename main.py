# Main script for the behavior of node

import random
import switchingConditions as switchCon
import messageBuild as msgBuild
import controlHardware as hw
import errorHandling as err
import goalMapsStorage as goalMapStore

#----- General data -----
NODE_ID = 1         #max 8 robots!!
TIMER = 50

#----- Listening phase variables -----
MIN_LISTEN_TIMESTEP = 500
MAX_LISTEN_TIMESTEP = 1000
EXTRA_LISTENING_TIME_IDLE = 2
LESS_LISTENING_TIME_ROOT = 2
AMOUNT_MODULES = 4          # 4 RFID modules

#----- Initialization -----
def init():
    node = switchCon.Node(NODE_ID)          # this is me, this robot
    goalMapManager = goalMapStore.GoalMapManager()   
    hw.initAllHw()
    print(f"[FYI] Robot is ready to play!")
    return node, goalMapManager

#----- Helper functions -----
def delay(steps):
    for _ in range(steps):
        pass

def calcListeningTime(node):
    base = random.randint(MIN_LISTEN_TIMESTEP, MAX_LISTEN_TIMESTEP)
    if node.IDLE:
        return base * EXTRA_LISTENING_TIME_IDLE
    elif node.ROOT:
        return base // LESS_LISTENING_TIME_ROOT
    else:
        return base

def listeningForMsg_onlyErrorAndAckAllowed(listeningTime, moduleNumber):
    while listeningTime > 0:
        msg = hw.listenThroughModule(moduleNumber)
        if msg is not None:
            if msgBuild.getHeader(msg) == msgBuild.ERROR_HEADER: # ERROR
                err.decodeErrorMsg()
            elif msgBuild.getHeader(msg) == msgBuild.ACK_HEADER: # ACK
                pass    
                if msgBuild.getACK(msg):
                    pass
                else:
                    msgBuild.decodeACK()
            else:
                err.msgTypeIncorrect()    
        listeningTime -= 1

def decodeMsg(node, goalMapLib, msg):
    header = msgBuild.getHeader(msg)
    if header == msgBuild.INIT_HEADER:
        decodedMsg = msgBuild.decodeINITMsg(msg)
        node.msgRcv(decodedMsg)
        # listen only on that module for a set period of time
    elif header == msgBuild.ACK_HEADER:
        decodedMsg = msgBuild.decodeACKMsg(msg)  
        # react to it and possibly resend a msg
    elif header == msgBuild.POS_HEADER:
        decodedMsg = msgBuild.decodePOSMsg(msg)
        # listen only on that module for a set period of time
    elif header == msgBuild.FOLLOWUP_HEADER:
        decodedMsg = msgBuild.decodeFOLLOWUPMsg(msg)
        # listen only on that module for a set period of time
    elif header == msgBuild.ERROR_HEADER:
        decodedMsg = msgBuild.decodeErrorMsg(msg)
    elif header == msgBuild.INSTRUCT_HEADER:
        decodedMsg = msgBuild.decodeInstructMsg(msg)
        node.ROOT = True
        # keep spreading the update!
    elif header == msgBuild.SYSUPDATE_HEADER:
        decodedMsg = msgBuild.decodeSysUpdateMsg(msg)
        # decodedMsg contains: updateType, INSTDONE, instructData
        node.ROOT = True
        if decodedMsg['updateType'] == msgBuild.SYSUPDATE_NEWGOALMAP:        # if it returns True then its a proper system update which is not implemented yet
            pass    # i cant implement the system rewrite for thing, but if new mode, then possible
        elif decodedMsg['updateType'] == msgBuild.SYSUPDATE_COMPLETEUPDATE:
            goalMapLib.addGoalMap(decodedMsg['instructData'])   # its a goalMap -> add it to the lib
        else:
            err.msgTypeIncorrect()              # I dont recognize this updateType
            hw.sendMsg(msgBuild.createErrorMsg(node.errorCode, node.scriptCode))
        if decodedMsg['INSTDONE']:
            hw.sendMsg(msgBuild.createSysUpdateMsg(True, decodedMsg['instructData'], decodedMsg['updateType'])) #keep spreading the update!
        else:
            #keep listening on that module only
            pass
            # if timers out: sendMsg(msgBuild.createAckMsg(please repeat the last msg))
       
    else:
        err.msgTypeIncorrect()

#----- Main loop -----
def main():
    node, goalMapLib = init()
    while True:
        # listening phase
        listeningTime = calcListeningTime(node)
        print(f"[FYI] Entering listening phase")
        for _ in range(listeningTime):
            for sensorNumber in range(AMOUNT_MODULES):
                msg = hw.listenThroughModule(sensorNumber) # the actual polling and reacting to the msg is in control hardware
                if msg is not None:
                    decodeMsg(node, goalMapLib, msg)
        delay(TIMER)

        #the msg Im using here has to be fresh from the sender! Find a way
        # talking phase
        print(f"[FYI] Entering talking phase")
        module = hw.sendThroughRandomModule(msgBuild.createINITMsg())
        delay(TIMER)
        listeningForMsg_onlyErrorAndAckAllowed(TIMER, module)
        delay(TIMER)        
        hw.sendThroughModule(msgBuild.createPOSMsg(), module)
        delay(TIMER)
        listeningForMsg_onlyErrorAndAckAllowed(TIMER, module)
        delay(TIMER)
        hw.sendThroughModule(msgBuild.createFollowUpMsg(), module)
        delay(TIMER)
        listeningForMsg_onlyErrorAndAckAllowed(TIMER, module)
        delay(TIMER)
        # Cycle has been completed -> stay in the while-loop

if __name__ == "__main__":
    main()