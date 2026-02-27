# Script to store, return, and identify the errors

#Lib for script and error codes:
#
#. 0 = switching conditions/ switchCon
#. 0 0 = receiver is busy. Retry later
#. 0 1 = receiver and sender’s mode are different
#. 0 2 = sender’s timestamp is older than receiver’s. Will now send my own FOLLOW-UP
#. 0 3 = receiver is ROOT
#
#. 1 = messageBuild
#. 1 1 = msg type was not recognized
#. 1 3 = the message received is the incorrect length
#. 1 4 = parity check is incorrect
#
#. 2 = mapFunctions
#. 2 0 = the map is missing
#. 2 1 = the goal map is missing
#. 2 2 = Forbidden position for tile
#. 2 3 = the size of the map is incorrect
#. 2 4 = the margins of the 2 maps differ
#. 2 5 = this tile does not belong in this position
#. 2 6 = this tile is outside the margins
#. 2 7 = this tile symbol is not recognized
#
#. 3 = goalMapStorage
#. 3 0 = failed to add a new goalMap
#
#. 4 = errorHandling/ main -> general errors
#. 4 0 = the received msg contains a mistake
#. 4 1 = time is up. I am sick of waiting, moving on
#. 4 2 = msgs have arrived in the wrong order
#. 4 3 = I have no idea what that error is, will ignore it
#. 4 4 = that flag combination is not possible. Please correct it
#. 4 5 = I have no idea what is happening and won't even try
#
#. 5 = hardware
#       nothing here yet. Add your own!

# Possible actions table:
# 1 = ignore 
# 2 = send an ERROR msg
# 3 = send an ACK msg asking to repeat the last message
# 4 = reset robot
# 5 = actually try to correct the mistake
# 5 1 = deletes and adds new map
# 5 2 = signals in map that this tile is in an incorrect position
# 5 3 = replaces whatever symbol that tile had with a ?
# 5 4 = resets the flags so communication can restart anew
# 6 = send an INIT msg to update their status instead
# 7 = signal to the user that they made a mistake

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
ACTION_SIGNALTOUSER = 7

ACTION_CORRECTSTH_RESTARTMAP = 1
ACTION_CORRECTSTH_TILEINCORRECT = 2
ACTION_CORRECTSTH_FIXTILESYMBOL = 3
ACTION_CORRECTSTH_MESSEDUPFLAGS = 4

def decodeErrorMsg(scriptCode, errorCode):
    if scriptCode == 0:
        # switchCon error
        if errorCode == 0: 
            return receiverIsBusy()
        elif errorCode == 2:
            return olderTimestamp()
        elif errorCode == 3:
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
        if errorCode == 2:
            return attachmentAtPosForbidden()
        elif errorCode == 3:
            return mapIncorrectLength()
        else:
            return errorMsgIncorrect()
        pass
    elif scriptCode == 3:
        # goalMapStore error
        if errorCode == 0:
            failedToAddGoalMap()
            return None
        else:
            return errorMsgIncorrect()      # there are no registered errors yet
    elif scriptCode == 4:
        # errorHandling error
        if errorCode == 0:
            return errorMsgIncorrect()
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
    print(f"[ERROR] The last error msg contains a general mistake")
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
    return {"scriptCode": SCRIPTCODE_ERROR, 
            "errorCode": 2,
            "action": ACTION_SENDPLSREPEATMSG,
            "actionCode": None}
    # request to send previous msg

def invalidFlagCombination():
    print(f"[ERROR] The flag combination does not work. Will restart.")
    return {"scriptCode": None, 
            "errorCode": None,
            "action": ACTION_CORRECTSTH,
            "actionCode": ACTION_CORRECTSTH_MESSEDUPFLAGS}
    # will restart the flags

def wtfIsHappening():
    print(f"[ERROR] Yeah, there is an error. Its prob a wrong scriptCode or errorCode. Will feign ignorance")

#----- From goalMapsStorage -----
def failedToAddGoalMap():
    print(f"[ERROR] Failed to add new goalMap")
    # ask to resend msg
    return {"scriptCode": SCRIPTCODE_GOALMAPSTORE, 
            "errorCode": 0,               
            "action": ACTION_SENDPLSREPEATMSG,
            "actionCode": None}

#----- From mapFunctions -----
def emptyMap():         #head 11 script 00100 error 000
    print(f"[ERROR] Empty map. Will create an empty new one")
    # just create a new map
    return {"scriptCode": None, 
            "errorCode": None,
            "action": ACTION_CORRECTSTH,
            "actionCode": ACTION_CORRECTSTH_RESTARTMAP}
    
def emptyGoalMap():     #head 11 script 00100 error 001
    print(f"[ERROR] Empty goal map") # INSTRUCTMsg, errorCode 1
    return {"scriptCode": None, 
            "errorCode": None,
            "action": ACTION_IGNORE,
            "actionCode": None}
    
def attachmentAtPosForbidden():   #head 11 script 00100 error 010
    # light up in error
    print(f"[ERROR] This position is not a valid position for this game")
    # maybe add th extra field and use those bits as well?
    return {"scriptCode": None, 
            "errorCode": None,
            "action": ACTION_CORRECTSTH,
            "actionCode": ACTION_CORRECTSTH_TILEINCORRECT}

def mapIncorrectLength():
    print(f"[ERROR] The size of the map is incorrect")
    # pls resend the map
    return {"scriptCode": SCRIPTCODE_MSGBUILD, #PLease resend followUpmsg !!!!!!!!!!!!!!!!!!!!!
            "errorCode": None,
            "action": ACTION_SENDPLSREPEATMSG,
            "actionCode": None}

def marginsDiffer():
    # signal to the user sth is wrong bc these do not seem to mash
    print(f"[ERROR] The margins of the maps are different")
    return {"scriptCode": None,
            "errorCode": None,
            "action": ACTION_SIGNALTOUSER,
            "actionCode": None}

def wrongTile():
    # signal to user that that tile is incorrect
    print(f"[ERROR] That tile does not belong there, try a different one")
    return {"scriptCode": None,
            "errorCode": None,
            "action": ACTION_SIGNALTOUSER,
            "actionCode": None}

def outsideOfMargins():
    # signal to user that tile is incorrect
    print(f"[ERROR] That tile does not belong here. Try putting it somewhere else")
    return {"scriptCode": None,
            "errorCode": None,
            "action": ACTION_SIGNALTOUSER,
            "actionCode": None}

def tileNotRecognized():
    # this symbol is not whitelisted
    print(f"[ERROR] I do not recognize this tile")
    return {"scriptCode": None,
            "errorCode": None,
            "action": ACTION_CORRECTSTH,
            "actionCode": ACTION_CORRECTSTH_FIXTILESYMBOL}

#----- From messageBuild -----
def msgTypeIncorrect():
    print("[ERROR] This message type is not valid. Pls retry")
    return {"scriptCode": SCRIPTCODE_MSGBUILD, 
            "errorCode": 1,
            "action": ACTION_SENDPLSREPEATMSG,
            "actionCode": None}

def msgLengthIncorrect():
    print("[ERROR] RFID message must be exactly 2 bytes")
    return {"scriptCode": SCRIPTCODE_MSGBUILD, 
            "errorCode": 3,
            "action": ACTION_SENDPLSREPEATMSG,
            "actionCode": None}

def parityCheckIncorrect():
    print("[ERROR] Parity Safety Check incorrect. Pls retry")
    return {"scriptCode": SCRIPTCODE_MSGBUILD, 
            "errorCode": 4,
            "action": ACTION_SENDPLSREPEATMSG,
            "actionCode": None}

#----- From switchingConditions -----
def receiverIsBusy():
    print("[ERROR] Receiver is busy. Please retry again later")
    return {"scriptCode": SCRIPTCODE_SWITCHCON, 
            "errorCode": 0,
            "action": ACTION_SENDERRORMSG,
            "actionCode": None}

def modeIsDifferent():
    print("[ERROR] Receiver and sender's mode are different")
    return {"scriptCode": SCRIPTCODE_SWITCHCON, 
            "errorCode": 1,
            "action": ACTION_SENDERRORMSG,
            "actionCode": None}

def olderTimestamp():
    print("[ERROR] Sender's timestamp is older than receiver's. Will now send my own timestamp")
    return {"scriptCode": SCRIPTCODE_SWITCHCON, 
            "errorCode": 2,
            "action": ACTION_SENDINITMSG,
            "actionCode": None}

def receiverIsROOT():
    print(f"[ERROR] Receiver is ROOT")
    return {"scriptCode": SCRIPTCODE_SWITCHCON, 
            "errorCode": 3,
            "action": ACTION_SENDERRORMSG,
            "actionCode": None}
