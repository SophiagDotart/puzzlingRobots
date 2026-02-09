# Script to handle the error once they appear. It reacts to raise valueErrors
import messageBuild.py as msgBuild
import controlHardware.py as hw

#Lib for script and error codes
#... 00100 = mapFunctions
#... ..... 000 = the map is missing
#... ..... 001 = the goal map is missing
#... ..... 010 = the tile is trying to attach itself to a forbidden position within the map
#... ..... ... 00001 = forbidden position due to outside of the boundaries or 'has to be left empty' tile
#... 00001 = messageBuild
#... ..... 000 = the message received is the incorrect length
#... ..... 001 = the message is neither a INIT, FOLLOWUP, or ERROR message
#... ..... 010 = parity check is incorrect

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
    print("[ERROR] 00001000 RFID message must be exactly 2 bytes")
    Message.header = 0bx11      #ERROR
    Message.scriptCode = 0bx00001
    Message.errorCode = 0bx000
    hw.sendMsg(Message.createErrorMsg())
    
def msgTypeIncorrect():
    print("[ERROR] 00001010 This message is not an INIT, FOLLOWUP, nor ERROR msg. Pls retry")
    Message.header = 0bx11
    Message.scriptCode = 0bx00001
    Message.errorCode = 0bx001
    hw.sendMsg(Message.createErrorMsg())

def parityCheckIncorrect():
    print("[ERROR] 00001001 Parity Safety Check incorrect. Pls retry")
    Message.scriptCode = 0bx00001
    Message.errorCode = 0bx010
    hw.sendMsg(Message.createErrorMsg())

#----- From sxitchingConditions -----
def receiverIsBusy():
    pass

def messageSourceIncorrect():
    #light up in pls retry colours
    print("[ERROR] 00001010 The source of the msg can not be detected")
    pass
