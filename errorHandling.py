# Script to store, return, and identify the errors

#Lib for script and error codes
#... 101 = controlHardware
#... 100 = errorHandling/ main -> general errors
#... ... 00000 = The msg contains a general mistake
#... ... 00001 = Timeout
#... 011 = goalMapStorage
#... ... 00020 = failed to add a new goalMap
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

SCRIPTCODE_SWITCHCON = 0
SCRIPTCODE_MSGBUILD = 1
SCRIPTCODE_MAPFUNC = 2
SCRIPTCODE_GOALMAPSTORE = 3
SCRIPTCODE_ERROR = 4
SCRIPTCODE_HW = 5

ACTION_IGNORE = 1
ACTION_SENDERRORMSG = 2
ACTION_SENDPLSREPEATMSG = 3
ACTION_RESETROBOT = 4
ACTION_CORRECTSTH = 5
ACTION_SENDINITMSG = 6

ACTION_CORRECTSTH_RESTARTMAP = 1
ACTION_CORRECTSTH_TILEINCORRECT = 2

# CAN BE SEVERLY OPTIMIZED: NOT ALL ERRORS CAN BE SENT
# MISSING A WRONG MSG
def decodeErrorMsg(scriptCode, errorCode):
    if scriptCode == 0:
        # switchCon error
        if errorCode == 0: 
            return receiverIsBusy()
        elif errorCode == 1:
            return timeout()
        elif errorCode == 2:
            return olderTimestamp()
        elif errorCode == 3:
            # if switchCon.ROOT:
            #     return
            # hw.sendMsg(msgBuild.createPOSMsg())
            # hw.sendMsg(msgBuild.createFollowupMsg())
            return receiverIsROOT()
        else:
            errorMsgIncorrect()
    elif scriptCode == 1:
        # msgBuild error
        if errorCode == 0:
            return msgLengthIncorrect()
        elif errorCode == 1:
            return msgTypeIncorrect()
        elif errorCode == 2:
            return parityCheckIncorrect()
        else:
            return errorMsgIncorrect()
    elif scriptCode == 2:
        # mapFunc error
        if errorCode == 0:
            emptyMap()
            return None
        elif errorCode == 1:
            emptyGoalMap()
            return None # main creates a goalMap
        elif errorCode == 2:
            # input o that place on the map that it is incorrect !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # signal to user that it is incorrect
            pass
        elif errorCode == 3:
            mapTooLarge()
            return None
        else:
            return errorMsgIncorrect()
        pass
    elif scriptCode == 3:
        # goalMapStore error
        if errorCode == 0:
            failedToAddGoalMap()
            return None
        else:
            return errorMsgIncorrect() # there are no registered errors yet
    elif scriptCode == 4:
        # errorHandling error
        if errorCode == 0:
            return errorMsgIncorrect()
        elif errorCode == 1:
            return timeout()
        elif errorCode == 2:
            return wrongOrder()
        else:
            return errorMsgIncorrect()
    elif scriptCode == 5:
        # controlHardware error
        return errorMsgIncorrect()
    else:
        return msgTypeIncorrect()

#----- From errorHandling/ main -----
def errorMsgIncorrect():
    print(f"[ERROR] 1000000000000 The last error msg contains a general mistake")
    return {"scriptCode": SCRIPTCODE_ERROR, 
            "errorCode": 0,
            "action": ACTION_IGNORE,
            "actionCode": None}
    # send an ACK

def timeout():
    print(f"[ERROR] Timeout")
    return {"scriptCode": SCRIPTCODE_ERROR, 
            "errorCode": 1,
            "action": ACTION_IGNORE,
            "actionCode": None}
    # get a new communication partner

def unknownError():
    print(f"[ERROR] I dont know what error means or what to do with it. I will just ignore it :)")
    return {"scriptCode": None, 
            "errorCode": None,
            "action": ACTION_IGNORE,
            "actionCode": None}
    # do nothing but acknowledge it

def wrongOrder():
    print(f"[ERROR] I have not received crucial information ")
    print(f"[ERROR] Timeout")
    return {"scriptCode": SCRIPTCODE_ERROR, 
            "errorCode": 2,
            "action": ACTION_SENDPLSREPEATMSG,
            "actionCode": None}
    # request to send previous msg

#----- From goalMapsStorage -----
def failedToAddGoalMap():
    print(f"[ERROR] 0110000000000 Failed to add new goalMap")
    # ask to resend msg
    return {"scriptCode": SCRIPTCODE_GOALMAPSTORE, 
            "errorCode": 2,                 # check if correct!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            "action": ACTION_SENDPLSREPEATMSG,
            "actionCode": None}

#----- From mapFunctions -----
def emptyMap():         #head 11 script 00100 error 000
    print(f"[ERROR] 0100000000000 Empty map. Will create an empty new one")
    # just create a new map
    return {"scriptCode": None, 
            "errorCode": None,
            "action": ACTION_CORRECTSTH,
            "actionCode": ACTION_CORRECTSTH_RESTARTMAP}
    
def emptyGoalMap():     #head 11 script 00100 error 001
    print(f"[ERROR] 0100000100000 Empty goal map") # INSTRUCTMsg, errorCode 1
    return {"scriptCode": None, 
            "errorCode": None,
            "action": ACTION_IGNORE,
            "actionCode": None}
    
def attachmentAtPosForbidden(posx, posy):   #head 11 script 00100 error 010
    # light up in error
    print(f"[ERROR] 0100001000000 ({posx}|{posy}) is not a valid position for this game")
    # maybe add th extra field and use those bits as well?
    return {"scriptCode": None, 
            "errorCode": None,
            "action": ACTION_CORRECTSTH,
            "actionCode": ACTION_CORRECTSTH_TILEINCORRECT}

def mapTooLarge():
    print(f"[ERROR] 0110001100000 The size of the map is too big")
    # pls resend the map
    return {"scriptCode": SCRIPTCODE_MSGBUILD, #PLease resend followUpmsg !!!!!!!!!!!!!!!!!!!!!
            "errorCode": None,
            "action": ACTION_SENDPLSREPEATMSG,
            "actionCode": None}


#----- From messageBuild -----
def msgTypeIncorrect():
    print("[ERROR] 0010000100000 This message type is not valid. Pls retry")
    return {"scriptCode": SCRIPTCODE_MSGBUILD, 
            "errorCode": 1,
            "action": ACTION_SENDPLSREPEATMSG,
            "actionCode": None}

def msgLengthIncorrect():
    print("[ERROR] 0010000000000 RFID message must be exactly 2 bytes")
    return {"scriptCode": SCRIPTCODE_MSGBUILD, 
            "errorCode": 3,
            "action": ACTION_SENDPLSREPEATMSG,
            "actionCode": None}

def parityCheckIncorrect():
    print("[ERROR] 0010001000000 Parity Safety Check incorrect. Pls retry")
    return {"scriptCode": SCRIPTCODE_MSGBUILD, 
            "errorCode": 4,
            "action": ACTION_SENDPLSREPEATMSG,
            "actionCode": None}

#----- From switchingConditions -----
def receiverIsBusy():
    print("[ERROR] 0000000000000 Receiver is busy. Please retry again later")
    return {"scriptCode": SCRIPTCODE_SWITCHCON, 
            "errorCode": 0,
            "action": ACTION_SENDERRORMSG,
            "actionCode": None}

def modeIsDifferent():
    print("[ERROR] 0000000100000 Receiver and sender's mode are different")
    return {"scriptCode": SCRIPTCODE_SWITCHCON, 
            "errorCode": 1,
            "action": ACTION_SENDERRORMSG,
            "actionCode": None}

def olderTimestamp():
    print("[ERROR] 0000001000000 Sender's timestamp is older than receiver's. Will now send my own timestamp")
    return {"scriptCode": SCRIPTCODE_SWITCHCON, 
            "errorCode": 2,
            "action": ACTION_SENDINITMSG,
            "actionCode": None}

def receiverIsROOT():
    print(f"[] 0000001100000 Receiver is ROOT")
    return {"scriptCode": SCRIPTCODE_SWITCHCON, 
            "errorCode": 3,
            "action": ACTION_SENDERRORMSG,
            "actionCode": None}
