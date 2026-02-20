# Main script for the behavior of node

import random
import switchingConditions as switchCon
import messageBuild as msgBuild
import controlHardware as hw
import errorHandling as err

#----- General data -----
NODE_ID = 1         #max 8 robots!!
TIMER = 50

#----- Listening phase variables -----
MIN_LISTEN_TIMESTEP = 500
MAX_LISTEN_TIMESTEP = 1000
AMOUNT_MODULES = 4          # 4 RFID modules

#----- INITIALIZATION -----
def init():
    node = switchCon.Node(NODE_ID)
    hw.initAllHw()
    print(f"[FYI] Robot is ready to play!")
    return node

def delay(steps):
    for _ in range(steps):
        pass

def calcListeningTime():
    # maybe alter the listening time length depending on IDLE and ROOT?
    return random.randint(MIN_LISTEN_TIMESTEP, MAX_LISTEN_TIMESTEP)

def listeningForMsg_onlyErrorAllowed(listeningTime, moduleNumber):
    while listeningTime > 0:
        msg = hw.listenThroughModule(moduleNumber)
        if msg is not None:
            if msgBuild.getHeader(msg) == 3: # ERROR
                err.decodeErrorMsg()
                # Abbruch of the think and restart?
            else:
                err.msgTypeIncorrect()    
        listeningTime -= 1

def main():
    node = init()
    while True:
        # listening phase
        listeningTime = calcListeningTime()
        print(f"[FYI] Entering listening phase")
        for _ in range(listeningTime):
            for sensorNumber in range(AMOUNT_MODULES):
                msg = hw.listenThroughModule(sensorNumber) # the actual polling and reacting to the msg is in control hardware
                if msg is not None:
                    switchCon.lastRcvMsgHeader = msgBuild.getHeader(msg)
                    msgBuild.decodeMsg(msg) # rest of the stuff the receiver will take care of as seen in talking phase
                #msgDetected = 1
        delay(TIMER)

        #the msg Im using here has to be fresh from the sender! Find a way
        # talking phase
        print(f"[FYI] Entering talking phase")
        module = hw.sendThroughRandomModule(msgBuild.createINITMsg())
        delay(TIMER)
        listeningForMsg_onlyErrorAllowed(TIMER, module)
        delay(TIMER)        
        hw.sendThroughModule(msgBuild.createPOSMsg(), module)
        delay(TIMER)
        listeningForMsg_onlyErrorAllowed(TIMER, module)
        delay(TIMER)
        hw.sendThroughModule(msgBuild.createFollowUpMsg(), module)
        delay(TIMER)
        listeningForMsg_onlyErrorAllowed(TIMER, module)
        delay(TIMER)
        # Cycle has been completed -> stay in the while-loop

if __name__ == "__main__":
    main()