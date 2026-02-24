# Script to handle the error once they appear.
import messageBuild as msgBuild
import controlHardware as hw
import switchingConditions as switchCon
import mapFunctions as mapFunc

#Lib for script and error codes
#... 101 = controlHardware
#... 100 = errorHandling
#... ... 00000 = The msg contains a general mistake
#... 011 = goalMapStorage
#... ... 00000 = non existent goalMap
#... 010 = mapFunctions
#... ... 00000 = the map is missing
#... ... 00001 = the goal map is missing
#... ... 00010 = the tile is trying to attach itself to a forbidden position within the map
#... ... ..... 00001 = forbidden position due to outside of the boundaries or 'has to be left empty' tile
#... ... 00011 = the size of the map is too big
#... 001 = messageBuild
#... ... 00000 = the message received is the incorrect length
#... ... 00001 = the message is neither a INIT, POS, FOLLOWUP, SYSTEM UPDATE, INSTRUCTION or ERROR message
#... ... 00010 = parity check is incorrect
#... 000 = switching conditions
#... ... 00000 = receiver is busy. Retry later
#... ... 00001 = receiver and sender’s mode are different
#... ... 00010 = sender’s timestamp is older than receiver’s. Will now send my own FOLLOW-UP
#... ... 00011 = receiver is ROOT

def raiseError(result):
    if result == errorCode.modeDifferent:
        modeIsDifferent()
    pass

def decodeErrorMsg(msg):
    header = msgBuild.getHeader(msg)
    errorCode = msgBuild.getErrorCode(msg)
    extra = msgBuild.getExtraErrorBits(msg)
    if header == 0:
        # switchCon error
        if errorCode == 0: 
            switchCon.politeGossipWait()
        elif errorCode == 1:
            return # to the main loop
        elif errorCode == 2:
            hw.sendMsg(msgBuild.createPOSMsg())
            hw.sendMsg(msgBuild.createFollowupMsg())
        elif errorCode == 3:
            if switchCon.ROOT:
                return
            hw.sendMsg(msgBuild.createPOSMsg())
            hw.sendMsg(msgBuild.createFollowupMsg())
        else:
            errorMsgIncorrect()
    elif header == 1:
        # msgBuild error
        if errorCode == 0:
            hw.sendMsg(msgBuild.createAckMsg())
        elif errorCode == 1:
            hw.sendMsg(msgBuild.createAckMsg())
        elif errorCode == 2:
            hw.sendMsg(msgBuild.createAckMsg())
        else:
            errorMsgIncorrect()
    elif header == 2:
        # mapFunc error
        if errorCode == 0:
            return # Abbruch
        elif errorCode == 1:
            return # Abbruch
        elif errorCode == 2:
            # input o that place on the map that it is incorrect !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # signal to user that it is incorrect
            if extra == 0:
                pass
            elif extra == 1:
                pass
            else: 
                errorMsgIncorrect()
        elif errorCode == 3:
            return # Abbruch
        else:
            errorMsgIncorrect()
        pass
    elif header == 3:
        # goalMapStore error
        errorMsgIncorrect()
    elif header == 4:
        # errorHandling error
        if errorCode == 0:
            hw.sendMsg(msgBuild.createAckMsg())
        else:
            errorMsgIncorrect()
    elif header == 5:
        # controlHardware error
        errorMsgIncorrect()
    else:
        msgTypeIncorrect()
    # if busy then initiate polite gossip from switchCon

#----- From errorHandling -----
def errorMsgIncorrect():
    print(f"[ERROR] 1000000000000 The last msg contains a general mistake")
    msgBuild.ACK = 0
    hw.sendMsg(msgBuild.createACKMsg())

#----- From goalMapsStorage -----

#----- From mapFunctions -----
def emptyMap():         #head 11 script 00100 error 000
    print(f"[ERROR] 0100000000000 Empty map. Will create an empty new one")
    mapFunc.createMap()
    return None
    
def emptyGoalMap():     #head 11 script 00100 error 001
    print(f"[ERROR] 0100000100000 Empty goal map")
    return None
    
def attachmentAtPosForbidden(posx, posy):   #head 11 script 00100 error 010 extra 00001
    # light up in error
    print(f"[ERROR] 0100001000000 ({posx}|{posy}) is not a valid position for this game")
    # maybe add th extra field and use those bits as well?
    return None

def mapTooLarge():
    print(f"[ERROR] 0110001100000 The size of the map is too big")
    return None


#----- From messageBuild -----
def msgLengthIncorrect():
    print("[ERROR] 0010000000000 RFID message must be exactly 2 bytes")
    msgBuild.Message.header = 3      #ERROR
    msgBuild.scriptCode = 1
    msgBuild.errorCode = 0
    hw.sendMsg(msgBuild.createErrorMsg())
    
def msgTypeIncorrect():
    print("[ERROR] 0010000100000 This message is not an INIT, FOLLOWUP, nor ERROR msg. Pls retry")
    msgBuild.header = 3
    msgBuild.scriptCode = 1
    msgBuild.errorCode = 1
    hw.sendMsg(msgBuild.createErrorMsg())

def parityCheckIncorrect():
    print("[ERROR] 0010001000000 Parity Safety Check incorrect. Pls retry")
    msgBuild.Message.scriptCode = 1
    msgBuild.Message.errorCode = 1
    hw.sendMsg(msgBuild.createErrorMsg())

#----- From switchingConditions -----
def receiverIsBusy():
    print("[ERROR] 0000000000000 Receiver is busy. Please retry again later")
    msgBuild.scriptCode = 0
    msgBuild.errorCode = 0
    hw.sendMsg(msgBuild.serializeMsg(msgBuild.createErrorMsg()))

def modeIsDifferent():
    print("[ERROR] 0000000100000 Receiver and sender's mode are different")
    msgBuild.scriptCode = 0
    msgBuild.errorCode = 1 
    hw.sendMsg(msgBuild.serializeMsg(msgBuild.createErrorMsg())) 

def olderTimestamp():
    print("[ERROR] 0000001000000 Sender's timestamp is older than receiver's. Will now send my own timestamp")
    msgBuild.scriptCode = 0
    msgBuild.errorCode = 2
    msgBuild.sendMsg(msgBuild.serializeMsg(msgBuild.createErrorMsg()))

def receiverIsROOT():
    print(f"[] 0000001100000 Receiver is ROOT")
    msgBuild.scriptCode = 0
    msgBuild.errorCode = 3
    msgBuild.sendMsg(msgBuild.serializeMsg(msgBuild.createErrorMsg()))
