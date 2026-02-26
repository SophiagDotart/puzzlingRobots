# Main script for the behavior of node

import random
import switchingConditions as switchCon
import messageBuild as msgBuild
import controlHardware as hw
import errorHandling as err
import goalMapsStorage as goalMapStore
import mapFunctions as mapFunc

#----- General data -----
NODE_ID = 1         # max 16 robots!!
TIMER = 50                          # test experimentally
GRADUALDELAY_DECREASE = 0.5         # test experimentally, has to be between 0 and 1
GRADUALDELAY_INIT = 3 * TIMER
nameOfNewGoalmap = 1

#----- Only True if debugging mode activated -----
DEBUG = True

#----- Listening phase variables -----
MIN_LISTEN_TIMESTEP = 500
MAX_LISTEN_TIMESTEP = 1000
EXTRA_LISTENING_TIME_IDLE = 2
LESS_LISTENING_TIME_ROOT = 2
AMOUNT_MODULES = 4          # 4 RFID modules

#----- Initialization -----
def init():
    node = switchCon.Node(NODE_ID)  # this is me, this robot
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
        return base / LESS_LISTENING_TIME_ROOT
    else:
        return base

def listeningForMsg_onlyErrorAndAckAllowed(node, listeningTime):
    while listeningTime > 0:
        msg = hw.listenThroughModule(node.moduleNumber)
        if msg is not None:
            if msgBuild.Message.getHeader(msg) == msgBuild.Message.ERROR_HEADER:        # ERROR
                errMsg = msgBuild.Message.decodeERRORMsg(msg)
                err.decodeErrorMsg(errMsg['errorCode'], errMsg['scriptCode'])
                return True
            elif msgBuild.Message.getHeader(msg) == msgBuild.Message.ACK_HEADER:        # ACK
                if msgBuild.Message.getACK(msg):        # this would mean its simply a "understood" -> no need to decode it
                    return True
                elif not msgBuild.Message.getACK(msg):  # then it is a pls repeat msg, has to be decoded and resend
                    askMsg = msgBuild.Message.decodeACK(msg)
                    resendLastMsg(node, askMsg['msgType'])
                    return False
                else:
                    handleError(node, err.msgTypeIncorrect())
                    return False
            else:
                handleError(node, err.msgTypeIncorrect())  
                return False 
        listeningTime -= 1
    handleError(node, err.timeout())
    return False

def politeGossip(node):
    delayTime = GRADUALDELAY_INIT
    while delayTime > 0:
        if listeningForMsg_onlyErrorAndAckAllowed(node, int(delayTime)):
            return True
        delayTime = int(delayTime* GRADUALDELAY_DECREASE)

def resendLastMsg(node, msgTypeToSend):
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
        hw.sendMsg(msgBuild.Message.createAckMsg(ACK = False, msgType = msgTypeToSend))

def areWeDoneYet(node):
    wereAreDone = mapFunc.compareMapToGoal(goalMapStore.loadGoalMap(node.mode))
    if not wereAreDone: 
        return False                # there were mistakes or mode not complete
    elif wereAreDone:
        # Mode completed!
        # maybe set timestamp to infinity and only send out the message 
        # maybe light up funny
        return True
    else:
        handleError(node, err.unknownError)

def resetFlags(node):
    msgBuild.Message.setPOSDONEAndDONELow()
    switchCon.INITDONE = False
    node.ROOT = switchCon.becomeRoot()
    node.BUSY = False
    node.IDLE = True

def validateFlags(node):
    if node.IDLE and node.BUSY:
        return False
    POSDONE = msgBuild.Message.getPOSDONE()
    if node.DONE and not (POSDONE or node.INITDONE):
        return False
    if POSDONE and not node.INITDONE:
        return False
    return True

def debugIt(node, Map):
    switchCon.printData()
    print(f"[DEBUG] Current flags: ROOT: {node.ROOT}, BUSY: {node.BUSY}, IDLE: {node.IDLE}, INITDONE {node.INITDONE}, POSDONE: {Map.POSDONE}, DONE {Map.DONE}")
    if validateFlags():
        print(f"[DEBUG] No contradictions in flags")
    msgBuild.Message.printCompressedMap()
    if msgBuild.checkIfCompressedMapIsCorrect():
        print(f"[DEBUG] No issues in the current map")
    print(f"[DEBUG] Current pos: {msgBuild.Message.getPosX()}, {msgBuild.Message.getPosY()}")

#----- Behavioral functions -----
def decodeMsg(node, goalMapLib, msg):
    if not msgBuild.Message.checkIfCorrectLen(msg):
        handleError(node, err.msgLengthIncorrect())
        return
    header = msgBuild.Message.getHeader(msg)

    if header == msgBuild.Message.INIT_HEADER:
        decodedMsg = msgBuild.Message.decodeINITMsg(msg)
        if not handleInitMsg_establishingContact(node, decodedMsg['timestamp'], decodedMsg['mode'], decodedMsg['ROOT']):
            return      # deny communication request
        if not validateFlags():
            handleError(node, err.invalidFlagCombination())
        if DEBUG:
           debugIt(node) 
    elif header == msgBuild.Message.ACK_HEADER:
        decodedMsg = msgBuild.Message.decodeACKMsg(msg)  
        if decodedMsg['ACK']:
            lastMsg = msgBuild.Message.getLastMsgType(msg)
            if lastMsg == msgBuild.Message.INIT_HEADER:
                hw.sendMsg(msgBuild.Message.createPosMsg(POSDONE = node.POSDONE, posX = node.posX, posY = node.posY))
            elif lastMsg == msgBuild.Message.POS_HEADER:
                hw.sendMsg(msgBuild.Message.createFollowUpMsg(orientation = node.orientation, DONE = node.DONE, mapData = node.mapData))
            else:
                return  # I have no more information to send you
        else:           # they are asking me to resend last msg
            resendLastMsg(node, decodedMsg['msgType'])

    elif header == msgBuild.Message.POS_HEADER:
        if not switchCon.INITDONE:
            handleError(node, err.wrongOrder())
        decodedMsg = msgBuild.Message.decodePOSMsg(msg)
        if decodedMsg['POSDONE']:
            senderX, senderY = decodedMsg['posX'], decodedMsg['posY']
            orientationX, orientationY = msgBuild.Message.getOrientationX(msg), msgBuild.Message.getOrientationY(msg)
        else:
            return      # will never happen, because current map size can always be sent within a message
        if validateFlags():
            handleError(node, err.invalidFlagCombination())
        delay(TIMER)
        hw.sendMsg(msgBuild.Message.createAckMsg(ACK = True, msgType = msgBuild.Message.POS_HEADER))
        if DEBUG:
           debugIt(node) 

    elif header == msgBuild.Message.FOLLOWUP_HEADER:
        decodedMsg = msgBuild.Message.decodeFOLLOWUPMsg(msg)
        if msgBuild.Message.getPOSDONE(decodedMsg) or not switchCon.INITDONE:
            handleError(node, err.wrongOrder())
        # decode senders orientation
        mapFunc.getOwnPos(senderX, senderY, orientationX, orientationY)     # the variables will always be set because of the set order of msgs
        mapFunc.overrideMap(decodedMsg['senderMap'])
        if not decodedMsg['parityCheck']:
            handleError(node, err.parityCheckIncorrect())
        hw.sendMsg(msgBuild.Message.createAckMsg(ACK = True, msgType = msgBuild.Message.FOLLOWUP_HEADER))
        areWeDoneYet(node)
        resetFlags(node)
        if DEBUG:
           debugIt(node) 

    elif header == msgBuild.Message.ERROR_HEADER:
        decodedMsg = msgBuild.Message.decodeErrorMsg(msg)
        handleError(node, err.decodeErrorMsg(decodedMsg['scriptcode']), decodedMsg['errorCode'])
        if DEBUG:
           debugIt(node) 

    elif header == msgBuild.Message.INSTRUCT_HEADER:
        decodedMsg = msgBuild.Message.decodeInstructMsg(msg)
        node.goalMapLib.goalMap = goalMapLib.loadGoalMap(switchCon.processInstructMsg(decodedMsg['mode']))
        node.mapHandler.compMap = mapFunc.createEmptyMap()
        switchCon.processInstructMsg(decodedMsg['mode'])
        # now keep spreading the instruction
        hw.sendThroughRandomModule(node.createINITmsg(senderID = NODE_ID, ROOT = node.ROOT, mode = node.mode, timestamp = node.timestamp))
        if DEBUG:
           debugIt(node) 

    elif header == msgBuild.Message.SYSUPDATE_HEADER:
        decodedMsg = msgBuild.Message.decodeSysUpdateMsg(msg)       # decodedMsg contains: updateType, INSTDONE, instructData
        if not decodedMsg['parityCheck']:
            handleError(node, err.parityCheckIncorrect()) 
        if decodedMsg['updateType'] == msgBuild.Message.SYSUPDATE_COMPLETEUPDATE:       # its a goalMap -> add it to the lib
            addedNewGoalMap = goalMapLib.addGoalMap(dictGoalMap = mapFunc.serialize(decodedMsg['updateData']) , name = nameOfNewGoalMap)
            nameOfNewGoalMap += 1   
            if addedNewGoalMap is None:
                handleError(node, err.failedToAddGoalMap())
                return False
        elif decodedMsg['updateType'] == msgBuild.Message.SYSUPDATE_NEWGOALMAP:        
            # if it returns True then its a proper system update which is not implemented yet
            # i cant implement the system rewrite for thing, but if new mode, then possible
            print(f"[FYI] Feature not implemented yet. Please use another feature")
            return True         # so that it does not stop doing its job
        if decodedMsg['INSTDONE']:
            hw.sendMsg(msgBuild.Message.createInstructMsg(INSTDONE = True, instructData = decodedMsg['instructData'], instMode = decodedMsg['updateType'])) #keep spreading the update!
            # spread the user instruction
            if DEBUG:
                debugIt(node) 
            return True
        else:
            # sender is done transmitting all information yet. Wait and listen
            if not listeningForMsg_onlyErrorAndAckAllowed(node, TIMER):
                handleError(node, err.timeout())
                return False
            
    else:
        handleError(node, err.msgTypeIncorrect())
        return

def handleError(node, error):
    action = error['action']
    if action == err.ACTION_SENDERRORMSG:
        if error['scriptCode'] is not None and error['errorCode'] is not None:
            hw.sendThroughModule(msgBuild.Message.createErrorMsg(errorCode = error['errorCode'], scriptCode = error['scriptCode']), node.moduleNumber)
            print(f"[FYI] Sent the error to the sender")
        else:
            err.wtfIsHappening()
    elif action == err.ACTION_SENDPLSREPEATMSG:
        if error['scriptCode'] is not None and error['errorCode'] is not None:
            hw.sendThroughModule(msgBuild.Message.createAckMsg(ACK = False, msgType = error['scriptERROR']), node.moduleNumber)
            print(f"[FYI] Sent an ACk msg to the sender to please resend the last msg")
        else:
            err.wtfIsHappening()   
    elif action == err.ACTION_IGNORE:
        print(f"[FYI] I ignored the error.Returning to main")   
    elif action == err.ACTION_SENDINITMSG:
        hw.sendThroughModule(msgBuild.Message.createInitMsg(senderID = NODE_ID, ROOT = node.ROOT, mode = node.mode, timestamp = node.timestamp), node.moduleNumber) 
    elif action == err.ACTION_RESETROBOT:
        print(f"[FYI] Will restart the robot now")
        hw.resetRobot()
    elif action == err.ACTION_CORRECTSTH:
        thatSth = error['actionCode']
        if thatSth == err.ACTION_CORRECTSTH_RESTARTMAP:
            node.mapData = bytearray()
            print(f"[FYI] Restarted the map and the timestep")
        elif signalThat == err.ACTION_CORRECTSTH_FIXTILESYMBOL:
            mapFunc.setTileInCompressedMap(node.posX, node.posY, mapFunc.tileToByte["?"]) 
        elif signalThat == err.ACTION_CORRECTSTH_MESSEDUPFLAGS:
            resetFlags()           
        else:
            err.wtfIsHappening()   
    elif action == err.ACTION_SIGNALTOUSER:
        signalThat = error['actionCode']
        if signalThat == err.ACTION_CORRECTSTH_TILEINCORRECT:
            hw.signalThatsWrong()
        else: 
            err.wtfIsHappening()
    else:
        err.wtfIsHappening()

def handleInitMsg_establishingContact(node, senderTimestep, senderMode, senderROOT):
    result = switchCon.processInitMsg(senderTimestep, senderMode, senderROOT)
    if validateFlags():
        handleError(node, err.invalidFlagCombination())
    if result == switchCon.RESULT_ROOT:
        handleError(node, err.receiverIsROOT())
        return False
    elif result == switchCon.RESULT_BUSY:
        politeGossip(node)
    elif result == switchCon.RESULT_MODE:
        handleError(node, err.modeIsDifferent())
        return False
    elif result == switchCon.RESULT_TIMESTEP:
        handleError(node, err.olderTimestamp())
        return False
    elif result == switchCon.RESULT_COMMUNICATIONACCEPTED:
        return True
    elif result == switchCon.RESULT_EQUAL:
        return False        # this is irrelevant. Nothing needs to happen
    else:
        handleError(node, err.unknownError)
        return None

def handleMapErrors(node, error):
    if error == mapFunc.MAPERROR_EMPTYMAP:
        handleError(err.emptyMap())
    elif error == mapFunc.MAPERROR_EMPTYGOALMAP:
        handleError(err.emptyGoalMap())
    elif error == mapFunc.MAPERROR_INCORRECTLENGTH:
        handleError(err.mapIncorrectLength())
    elif error == mapFunc.IAMAROOT:
        handleError(err.receiverIsROOT())
    elif error == mapFunc.MARGINSDIFFER:
        handleError(err.marginsDiffer())
    elif error == mapFunc.ATTACHMENTFORBIDDEN:
        handleError(err.attachmentAtPosForbidden())
    elif error == mapFunc.WRONGTILE:
        handleError(err.wrongTile())
    elif error == mapFunc.OUTSIDEOFMARGINS:
        handleError(err.outsideOfMargins())
    elif error == mapFunc.UNRECOGNIZEDTILE:
        handleError(err.tileNotRecognized())
    else:
        handleError(err.unknownError())

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
        # talking phase
        print(f"[FYI] Entering talking phase")
        node.moduleNumber = hw.sendThroughRandomModule(msgBuild.Message.createInitMsg(senderID = NODE_ID, ROOT = node.ROOT, mode = node.mode, timestamp = node.timestamp))
        delay(TIMER)
        if not listeningForMsg_onlyErrorAndAckAllowed(node, TIMER):
            handleError(node, err.timeout())
            node.timeout()
        delay(TIMER)        
        hw.sendThroughModule(msgBuild.Message.createPOSMsg(POSDONE = node.POSDONE, posX = node.posX, posY = node.posY), node.moduleNumber)
        delay(TIMER)
        if not listeningForMsg_onlyErrorAndAckAllowed(node, TIMER):
            handleError(node, err.timeout())
        delay(TIMER)
        hw.sendThroughModule((msgBuild.Message.createFollowUpMsg(orientation = node.orientation, DONE = node.DONE, mapData = node.mapData)), node.moduleNumber)
        delay(TIMER)
        if not listeningForMsg_onlyErrorAndAckAllowed(node, TIMER):
            handleError(node, err.timeout())
        delay(TIMER)
        # Cycle has been completed -> stay in the while-loop

if __name__ == "__main__":
    main()