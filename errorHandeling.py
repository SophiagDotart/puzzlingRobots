# Script to handle the error once they appear. It reacts to raise valueErrors
import messageBuild.py
import xx.py

#Lib for script and error codes
#... 00001 = messageBuild
#... ..... 000 = the message received is the incorrect length
#... ..... 001 = the message is neither a INIT, FOLLOWUP, or ERROR message
#... ..... 002 = parity check is incorrect

# From messageBuild
def msgLengthIncorrect():
    Message.header = 0bx11
    Message.scriptCode = 0bx00001
    Message.errorCode = 0bx000
    Message.createErrorMsg()
    #send errorMsg
    return
    
def msgTypeIncorrect():
    Message.header = 0bx11
    Message.errorCode = 0bx001
    Message.createErrorMsg()
    #send error msg
    return

def parityCheckIncorrect():
    Message.scriptCode = 0bx00001
    Message.errorCode = 0bx010
    Message.createErrorMsg()
    # send msg
    return

