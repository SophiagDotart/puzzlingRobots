# Main script for the behavior of node

import random
import switchingConditions as switchCon
import messageBuild as msgBuild
import mapFunctions as mapFunc

#----- General data -----
node_id = 1

#----- Listening phase variables -----
MIN_LISTEN_TIMESTEP = 500
MAX_LISTEN_TIMESTEP = 1000
AMOUNT_MODULES = 4          # 4 RFID modules

#----- INITIALIZATION -----
def init():
    pass

while True:
    # listening phase
    listeningTime = random.randint(MIN_LISTEN_TIMESTEP, MAX_LISTEN_TIMESTEP)
    print(f"[FYI] Entering listening phase")
    #if msgRcv:
     #   pass
    # delay here to give the rfid modules a chance to keep up
    # sending phase
    print(f"[FYI] Entering talking phase")
    for module in AMOUNT_MODULES:
        # dont forget the delay!
        pass
    pass
