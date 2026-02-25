# Main script for the behavior of node

import random
import switchingConditions as switchCon
import messageBuild as msgBuild
import controlHardware as hw
import errorHandling as err
import goalMapsStorage as goalMapStore
import mapFunctions as mapFunc

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
            if msgBuild.Message.getHeader(msg) == msgBuild.Message.ERROR_HEADER: # ERROR
                err.decodeErrorMsg()
                return True
            elif msgBuild.Message.getHeader(msg) == msgBuild.Message.ACK_HEADER: # ACK
                if msgBuild.Message.getACK(msg):
                    msgBuild.Message.decodeACK()
                    return True
                else:
                    return False
            else:
                errorCode, scriptCode = err.msgTypeIncorrect()
                hw.sendMsg(msgBuild.Message.createAckMsg(errorCode, scriptCode))   
                return False 
        listeningTime -= 1
    err.timeout()
    return False

def decodeMsg(node, goalMapLib, msg, sensorNumber):
    header = msgBuild.Message.getHeader(msg)
    if header == msgBuild.Message.INIT_HEADER:
        decodedMsg = msgBuild.Message.decodeINITMsg(msg)
        node.msgRcv(decodedMsg)
        # switchCon takes over and decides what to do
    elif header == msgBuild.Message.ACK_HEADER:
        decodedMsg = msgBuild.Message.decodeACKMsg(msg)  
        if decodedMsg['ACK']:
            lastMsg = msgBuild.Message.getLastMsgType()
            if lastMsg == msgBuild.Message.INIT_HEADER:
                hw.sendMsg(msgBuild.Message.createPosMsg(POSDONE = node.POSDONE, posX = node.posX, posY = node.posY))
            elif lastMsg == msgBuild.Message.POS_HEADER:
                hw.sendMsg(msgBuild.Message.createFollowUpMsg(orientation = node.orientation, DONE = node.DONE, mapData = node.mapData))
            else:
                return
        else:                       # they are asking me to resend last msg
            msgTypeToSend = decodedMsg['msgType']
            if msgTypeToSend == msgBuild.Message.INIT_HEADER:
                hw.sendMsg(msgBuild.Message.createInitMsg(senderID = NODE_ID, ROOT = node.ROOT, mode = node.mode,timestep = node.timestamp))
            elif msgTypeToSend == msgBuild.Message.FOLLOWUP_HEADER:
                hw.sendMsg(msgBuild.Message.createFollowUpMsg(orientation = node.orientation, DONE = node.DONE, mapData = node.mapData))
            elif msgTypeToSend == msgBuild.Message.ERROR_HEADER:
                hw.sendMsg(msgBuild.Message.createErrorMsg(node.scriptCode, node.errorCode))
            elif msgTypeToSend == msgBuild.Message.POS_HEADER:
                hw.sendMsg(msgBuild.Message.createPosMsg(POSDONE = node.POSDONE, posX = node.posX, posY = node.posY))
            elif msgTypeToSend == msgBuild.Message.INSTRUCT_HEADER:
                hw.sendMsg(msgBuild.Message.createInstructMsg(INSTDONE = node.INSTDONE, instructData = node.instructData, instMode = node.updateType))
            elif msgTypeToSend == msgBuild.Message.SYSUPDATE_HEADER:
                hw.sendMsg(msgBuild.Message.createSystemUpdateMsg(updateCode = node.updateCode, updateData = node.updateData))
            else:
                hw.sendMsg(msgBuild.Message.createAckMsg(ACK = False, msgType = decodedMsg['msgType']))
        # react to it and possibly resend a msg
    elif header == msgBuild.Message.POS_HEADER:
        decodedMsg = msgBuild.Message.decodePOSMsg(msg)
        delay(TIMER)
        hw.sendMsg(msgBuild.Message.createAckMsg(ACK = True, msgType = msgBuild.Message.POS_HEADER))
        listeningForMsg_onlyErrorAndAckAllowed(TIMER, sensorNumber) # keep listening for the next msg. 
        # Maybe put an error stopper in by defining that the msg received before this one had to be either an ACK, ERR, INIT
        # possible error msgs
    elif header == msgBuild.Message.FOLLOWUP_HEADER:
        decodedMsg = msgBuild.Message.decodeFOLLOWUPMsg(msg)
        if not decodedMsg['parityCheck']:
            err.parityCheckIncorrect()
            hw.sendMsg(msgBuild.Message.createAckMsg(ACK = False, msgType = msgBuild.Message.FOLLOWUP_HEADER))
        hw.sendMsg(msgBuild.Message.createAckMsg(ACK = True, msgType = msgBuild.Message.FOLLOWUP_HEADER))
        listeningForMsg_onlyErrorAndAckAllowed(TIMER, sensorNumber) #keep listening for the next msg. 
        # Maybe put an error stopper in by defining that the msg received before this one had to be either an ACK, ERR, POS
        # possible ERROR msgs
    elif header == msgBuild.Message.ERROR_HEADER:
        decodedMsg = msgBuild.Message.decodeErrorMsg(msg)
        # make a reaction function to all possible errors
    elif header == msgBuild.Message.INSTRUCT_HEADER:
        decodedMsg = msgBuild.Message.decodeInstructMsg(msg)
        node.ROOT = True
        hw.sendThroughRandomModule(node.createINITmsg(senderID = NODE_ID, ROOT = node.ROOT, mode = node.mode, timestamp = node.timestamp))
    elif header == msgBuild.Message.SYSUPDATE_HEADER:
        decodedMsg = msgBuild.Message.decodeSysUpdateMsg(msg)   # decodedMsg contains: updateType, INSTDONE, instructData
        if not decodedMsg['parityCheck']:
            err.parityCheckIncorrect()
            hw.sendMsg(msgBuild.Message.createAckMsg(False, msgBuild.Message.SYSUPDATE_HEADER))
        node.ROOT = True
        if decodedMsg['updateType'] == msgBuild.Message.SYSUPDATE_COMPLETEUPDATE:       # its a goalMap -> add it to the lib
            addedNewGoalMap = goalMapLib.addGoalMap(dictGoalMap = mapFunc.serialize(decodedMsg['updateData']) , name = 'xyz')   
            if addedNewGoalMap is None:
                errorCode, scriptCode = err.failedToAddGoalMap()
                hw.sendMsg(msgBuild.Message.createErrorMsg(errorCode, scriptCode))
                return
        elif decodedMsg['updateType'] == msgBuild.Message.SYSUPDATE_NEWGOALMAP:        
            # if it returns True then its a proper system update which is not implemented yet
            # i cant implement the system rewrite for thing, but if new mode, then possible
            print(f"[FYI] Feature not implemented yet. Please use another feature")
        
        if decodedMsg['INSTDONE']:
            hw.sendMsg(msgBuild.Message.createInstructMsg(INSTDONE = True, instructData = decodedMsg['instructData'], instMode = decodedMsg['updateType'])) #keep spreading the update!
        else:
            # sender is done transmitting all information yet. Wait and listen
            success = listeningForMsg_onlyErrorAndAckAllowed(TIMER, sensorNumber)
            if not success:
                errorCode, scriptCode = err.timeout()
                return
    else:
        errorCode, scriptCode = err.msgTypeIncorrect()              # I dont recognize this header
        hw.sendMsg(msgBuild.Message.createErrorMsg(errorCode, scriptCode))
        return

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
                    decodeMsg(node, goalMapLib, msg, sensorNumber)
        delay(TIMER)

        #the msg Im using here has to be fresh from the sender! Find a way
        # talking phase
        print(f"[FYI] Entering talking phase")
        module = hw.sendThroughRandomModule(msgBuild.Message.createINITMsg(senderID = NODE_ID, ROOT = node.ROOT, mode = node.mode, timestamp = node.timestamp))
        delay(TIMER)
        if not listeningForMsg_onlyErrorAndAckAllowed(TIMER, module):
            err.timeout()
        delay(TIMER)        
        hw.sendThroughModule(msgBuild.Message.createPOSMsg(POSDONE = node.POSDONE, posX = node.posX, posY = node.posY), module)
        delay(TIMER)
        if not listeningForMsg_onlyErrorAndAckAllowed(TIMER, module):
            err.timeout()
        delay(TIMER)
        hw.sendThroughModule((msgBuild.Message.createFollowUpMsg(orientation = node.orientation, DONE = node.DONE, mapData = node.mapData)), module)
        delay(TIMER)
        if not listeningForMsg_onlyErrorAndAckAllowed(TIMER, module):
            err.timeout()
        delay(TIMER)
        # Cycle has been completed -> stay in the while-loop

if __name__ == "__main__":
    main()