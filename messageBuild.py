# Script to create the actual message and convert it to a package that can be sent through RFID| 16bit message (msg) channel

#Lib for msg codes -> first Bit: does the input come from the user or from another robot? 0 comes from robot, 1 from user
#... 000 = free
#... 001 = Initiation msg (INIT)
#... 010 = Follow-up/ Answer msg (FOLLOWUP)
#... 011 = ERROR msg
#... 100 = free
#... 101 = User game instruction 
#... 110 = System Update
#... 111 = free

# For later implementation:
#... bigger senderId & versioned header so the swarm can have more than 8 nodes
#... implement proper checksum
#... compress map fragments so it can can have more than 64 spaces

import controlHardware as hw 
import errorHandling as err
import switchingConditions as switchCon

class Message:
    def __init__(self, senderID, receiverID, senderRootFlag, instructionComplete, instructionMode, positionDone, posX, posY, extraErrorBits,
                 senderMap, senderMode, senderSource, senderReplyFlag, senderUpdateFlag, senderRFIDOrientation, senderDoneFlag, senderTimestamp, senderParityErrorFlag, senderErrorCode, senderScriptCode, instructionUpdateCode, instructionUpdateData):
        self.senderID = senderID
        # flags
        self.REPLY = senderReplyFlag
        self.UPDATE = senderUpdateFlag
        self.ROOT = senderRootFlag
        self.DONE = senderDoneFlag
        # payload
        self.mode = senderMode
        self.timestamp = senderTimestamp
        self.orientation = senderRFIDOrientation
        self.map = senderMap
        self.scriptCode = senderScriptCode
        self.errorCode = senderErrorCode
        self.updateCode = instructionUpdateCode
        self.updateData = instructionUpdateData
        self.INSTDONE = instructionComplete
        self.instMode = instructionMode
        self.POSDONE = positionDone
        self.posX = posX
        self.posY = posY
        self.extraErrorBits = extraErrorBits
        
    #----- bit manipulation code -----
    @staticmethod
    def setBit(word: int, bitPos: int, value: int):
        value = 1 if value else 0   # make sure the value is definitely 100% 1 or 0
        return word | (1 << bitPos) if value else word & ~(1 << bitPos)
        # | = OR bitwise ;;; use it bc single bits can not be assigned, only bytes can be assigned. So, to change a single bit we can do that with OR. Add might lead to errors bc of the carry flag. Using OR is called "mask"

    @staticmethod
    def setSeveralBit(word: int, startBit: int, width: int, value: int) -> int:
        mask = ((1 << width) - 1) << startBit
        value = value & ((1 << width) - 1) << startBit
        return (word & ~mask) | value
        
    @staticmethod
    def getBit(word: int, bitPos: int) -> int:
        return (word >> bitPos) & 1
        
    @staticmethod
    def getSeveralBit(word: int, startBit: int, width: int) -> int:   
        return (word >> startBit) & ((1 << width) - 1)
        
    @staticmethod
    def calcParity(value: int) -> int:
        return bin(value).count("1") %4     # count the ones in the bitwise written msg and use only the last 2 numbers
        
    def createInitMsg(self):  
        msg = 0
        msg = Message.setSeveralBit(msg, 13, 3, 1) 
        msg = Message.setBit(msg, 10, self.REPLY) 
        msg = Message.setBit(msg, 9, self.UPDATE)
        msg = Message.setSeveralBit(msg, 7, 4, self.mode)
        msg = Message.setBit(msg, 3, self.ROOT)
        msg = Message.setSeveralBit(msg, 2, 3, self.timestamp)
        REPLY, BUSY, UPDATE, ROOT = 0
        return msg
            
    def createFollowUpMsg(self):
        msg = 0
        msg = Message.setSeveralBit(msg, 13, 3, 2)
        msg = Message.setSeveralBit(msg, 11, 2, self.orientation)
        msg = Message.setBit(msg, 8, self.DONE)
        msg = Message.setSeveralBit(msg, 7, 8, self.map)
        
        msg = Message.setSeveralBit(msg, 9, 2, Message.calcParity(msg))
        return msg
        
    def createErrorMsg(self):
        msg = 0 
        msg = Message.setSeveralBit(msg, 13, 3, 4)
        msg = Message.setSeveralBit(msg, 8, 3, self.scriptCode)  
        msg = Message.setSeveralBit(msg, 5, 5, self.errorCode)
        msg = Message.setSeveralBit(msg, 0, 5, self.extraErrorBits)
        return msg

    def createSystemUpdateMsg(self):
        msg = 0 
        msg = Message.setSeveralBit(msg, 13, 3, 6)
        msg = Message.setSeveralBit(msg, 8, 3, self.updateCode)  
        msg = Message.setSeveralBit(msg, 5, 5, self.updateData)
        msg = Message.setSeveralBit(msg, 9, 2, Message.calcParity(msg))
        return msg   
    
    def createInstructMsg(self):
        msg = 0
        msg = Message.setSeveralBit(msg, 13, 3, 5)
        msg = Message.setSeveralBit(msg, 9, 4, self.instMode)
        msg = Message.setBit(msg, 8, self.INSTDONE)
        msg = Message.setSeveralBit(msg, 7, 8, self.map)
        return msg
    
    def createPosMsg(self):
        msg = 0
        msg = Message.setSeveralBit(msg, 13, 3, 4) # header
        msg = self.setSeveralBit(msg, 9, 4, 0)                  # reserved is left empty
        msg = self.setBit(msg, 8, self.POSDONE)
        msg = self.setSeveralBit(msg, 4, 4, self.posX)
        msg = self.setSeveralBit(msg, 0, 4, self.posY)

    def createAckMsg(self):
        lastHeader = switchCon.lastRcvMsgHeader
        # implement rest of message!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        if

    @staticmethod    
    def serializeMsg(msg:int, word) -> bytearray:
        return bytearray([
            (word >> 8) & 0xFF,
            msg & 0xFF
        ])
        # use as message = createMsg then rfid_payload = Message.serializeMsg
        
    def decodeMsg(self, buf: bytearray):
        if len(buf) != 2:
            err.msgLengthIncorrect()
        word = (buf[0] << 8) | buf[1]
        #read header
        header = Message.getSeveralBit(word, 13, 3)
        if (header == 1):               # INIT msg
            senderID = self.getSeveralBit(word, 10, 3)
            REPLY = self.getBit(word, 7)
            UPDATE = self.getBit(word, 6)
            BUSY = self.getBit(word, 5)
            mode = self.getSeveralBit(word, 4, 3)
            ROOT = self.getBit(word, 3)
            timestamp = self.getSeveralBit(word, 2, 3)
            # listen only on that one module for a set time
        elif (header == 2):             # FOLLOWUP msg
            orientation = self.getSeveralBit(word, 11, 2)
            parity = self.getSeveralBit(word, 9, 2)
            DONE = self.getBit(word, 8)
            mapData = self.getSeveralBit(word, 0, 8)
            # verify parity
            word = self.setSeveralBit(word, 9, 2, 2)
            parityCalc = self.calcParity(word)
            if not (parity == parityCalc):
                err.parityCheckIncorrect()
            # listen only on that module for a set period of time
        elif (header == 4):             # ERROR msg
            scriptCode = self.getSeveralBit(word, 8, 5)
            errorCode = self.getSeveralBit(word, 5, 3)
            err.decodeErrorMsg()
        elif (header == 5):             # INSTRUCT msg
            ROOT = 1
            updateCode = self.getSeveralBit(word, 8, 3)
            updateData = self.getSeveralBit(word, 0, 8)
            # verify parity
            word = self.setSeveralBit(word, 11, 2, 0)
            parityCalc = self.calcParity(word)
            if not (parity == parityCalc):
                err.parityCheckIncorrect()
        elif (header == 6):             # SYSTEM UPDATE msg
            INSTDONE = self.getBit(word, 8)
            instructData = self.getSeveralBit(word, 0, 8)
            # i cant implement the system rewrite for thing, but if new mode, then possible
            hw.resetRobot()
            
        elif (header == 4):              # POS msg
            POSDONE = self.getBit(word, 8)
            posX = self.getSeveralBit(word, 4, 4)
            posY = self.getSeveralBit(word, 0, 4)
            # listen only on that module for a set period of time
        else:
            err.msgTypeIncorrect()

# ----- getters -----
    def getSenderSourceType(self, word):
        return self.getBit(word, 15)
    
    def getMsgType(self, word):
        if(self.getSenderSourceType(word,16) == 0): # sent by a robot
            if(self.getSeveralBit(word, 14, 2) == 0x10): # follow up
                pass
            elif(self.getSeveralBit(word, 14, 2) == 0x11): # error
                pass
            elif(self.getSeveralBit(word, 14, 2) == 0x01):   # init
                pass
            else:
                err.msgTypeIncorrect()
        elif(self.getSenderSourceType(word,16) == 0):        # sent by the user
            if(self.getSeveralBit(word, 14, 2) == 0x01):     # instruction
                pass
            elif(self.getSeveralBit(word, 14, 2) == 0x10):   # system update
                pass
            else:
                err.msgTypeIncorrect()
        else:
            err.msgTypeIncorrect()        

    def getHeader(self, word):
        return self.getSeveralBit(word, 13, 3)

    def getSenderID(self, word):
        if self.getHeader is not 1:
            err.msgTypeIncorrect()
        return self.getSeveralBit(word, 10, 3)
    
    def getREPLY(self, word):
        if self.getHeader is not 1:
            err.msgTypeIncorrect()
        return self.getBit(word, 7)
        
    def getUPDATE(self, word):
        if self.getHeader is not 1:
            err.msgTypeIncorrect()
        return self.getBit(word, 6)
        
    def getROOT(self, word):
        if self.getHeader is not 1:
            err.msgTypeIncorrect()
        return self.getBit(word, 3)
        
    def getDONE(self, word):
        if self.getHeader is not 2:
            err.msgTypeIncorrect()
        return self.getBit(word, 8)
        
    def getMode(self, word):
        if self.getHeader is not 1:
            err.msgTypeIncorrect()
        return self.getSeveralBit(word, 4, 3)    
    
    def getTimestep(self, word):
        if self.getHeader is not 1:
            err.msgTypeIncorrect()
        return self.getSeveralBit(word, 2, 3)

    def getOrientation(self, word):
        if self.getHeader is not 2:
            err.msgTypeIncorrect()
        return self.getSeveralBit(word, 11, 2)
        
    def getMap(self, word):
        if self.getHeader is not 2:
            err.msgTypeIncorrect()
        return self.deserialize(self.getSeveralBit(word, 0, 8))
        
    def getScriptCode(self, word):
        if self.getHeader is not 3:
            err.msgTypeIncorrect()
        return self.getSeveralBit(word, 8, 5)
        
    def getErrorCode(self, word):
        if self.getHeader is not 3:
            err.msgTypeIncorrect()
        return self.getSeveralBit(word, 5, 3)
    
    # Message.setSeveralBit(msg, 0, 5, self.extraErrorBits)
    def getExtraErrorBits(self, word):
        if self.getHeader is not 3:
            err.msgTypeIncorrect()
        return self.getSeveralBit(word, 0, 5)
    
    def getUpdateCode(self, word):
        if self.getHeader is not 6:
            err.msgTypeIncorrect()
        return self.getSeveralBit(word, 8, 3)
    
    def getUpdateData(self, word):
        if self.getHeader is not 6:
            err.msgTypeIncorrect()
        return self.getSeveralBit(word, 0, 8)
    
    def getInstMode(self, word):
        if self.getHeader is not 5:
            err.msgTypeIncorrect()
        return self.getSeveralBit(word, 9, 4)
    
    def getINSTDONE(self, word):
        if self.getHeader is not 5:
            err.msgTypeIncorrect()
        return self.getBit(word, 8)
    
    def getInstructData(self, word):
        if self.getHeader is not 5:
            err.msgTypeIncorrect()
        return self.getSeveralBit(word, 0, 8)

    def getPOSDONE(self, word):
        if self.getHeader is not 4:
            err.msgTypeIncorrect()
        return self.getBit(word, 8)
    
    def getPosX(self, word):
        if self.getHeader is not 4:
            err.msgTypeIncorrect()
        return self.getSeveralBit(word, 4, 4)
    
    def getPosY(self, word):
        if self.getHeader is not 4:
            err.msgTypeIncorrect()
        return self.getSeveralBit(word, 0, 4)
    