# Script to handle the error once they appear. It reacts to raise valueErrors
import messageBuild.py as msgBuild
import controlHardware.py as hw

#Lib for script and error codes
#... 010 = mapFunctions
#... ... 00000 = the map is missing
#... ... 00001 = the goal map is missing
#... ... 00010 = the tile is trying to attach itself to a forbidden position within the map
#... ... ..... 00001 = forbidden position due to outside of the boundaries or 'has to be left empty' tile
#... 001 = messageBuild
#... ... 00000 = the message received is the incorrect length
#... ... 00001 = the message is neither a INIT, FOLLOWUP, or ERROR message
#... ... 00010 = parity check is incorrect
#... 000 = switching conditions
#... ... 00000 = receiver is busy. Retry later
#... ... 00001 = receiver and sender’s mode are different
#... ... 00010 = sender’s timestamp is older than receiver’s. Will now send my own FOLLOW-UP

#----- From mapFunctions -----
def emptyMap():         #head 11 script 00100 error 000
    print(f"[ERROR] Empty map")
    return
    
def emptyGoalMap():     #head 11 script 00100 error 001
    print(f"[ERROR] Empty goal map. Nothing to compare")
    return
    
def attachmentAtPosForbidden(posx, posy):   #head 11 script 00100 error 010 extra 00001
    # light up in error
    print(f"[ERROR] ("{posx}"|" {posy} " is not a valid position for this game")
    # maybe add th extra field and use those bits as well?
    return


#----- From messageBuild -----
def msgLengthIncorrect():
    print("[ERROR] 0010000000000 RFID message must be exactly 2 bytes")
    msgBuild.Message.header = 3      #ERROR
    msgBuild.scriptCode = 1
    msgBuild.errorCode = 0
    hw.sendMsg(Message.createErrorMsg())
    
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
