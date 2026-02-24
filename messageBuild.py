# Script to create the actual message and convert it to a package that can be sent through RFID| 16bit message (msg) channel

#Lib for msg codes -> first Bit: does the input come from the user or from another robot? 0 comes from robot, 1 from user
#... 000 = free
#... 001 = Initiation msg (INIT)
#... 010 = Follow-up/ Answer msg (FOLLOWUP)
#... 011 = ERROR msg
#... 100 = POS
#... 101 = User game instruction 
#... 110 = System Update
#... 111 = ACK

#Lib for sysupdate code
#... .010 = complete update
#... .011 = new mode/ new goalMap to be added

# For later implementation:
#... bigger senderId & versioned header so the swarm can have more than 8 nodes
#... implement proper checksum
#... compress map fragments so it can can have more than 64 spaces

import controlHardware as hw 
import errorHandling as err

class Message:

    INIT_HEADER = 1
    FOLLOWUP_HEADER = 2
    ERROR_HEADER = 3
    POS_HEADER = 4
    INSTRUCT_HEADER = 5
    SYSUPDATE_HEADER = 6
    ACK_HEADER = 7

    SYSUPDATE_COMPLETEUPDATE = 2
    SYSUPDATE_NEWGOALMAP = 3

    def __init__(self, senderID, senderRootFlag, instructionComplete, instructionMode, positionDone, posX, posY, extraErrorBits, senderACK, senderMsgType, 
                 senderMap, senderMode, senderRFIDOrientation, senderDoneFlag, senderTimestamp, senderErrorCode, senderScriptCode, instructionUpdateCode, instructionUpdateData):
        self.senderID = senderID
        self.ROOT = senderRootFlag
        self.DONE = senderDoneFlag
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
        self.ACK = senderACK
        self.lastMsgType = senderMsgType
        
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
        return bin(value).count("1") % 4     # count the ones in the bitwise written msg and use only the last 2 numbers

    #----- Create msgs ------    
    def createInitMsg(self, senderID, ROOT, mode, timestamp):  
        msg = 0
        msg = Message.setSeveralBit(msg, 13, 3, self.INIT_HEADER)
        msg = self.setSeveralBit(msg, 9, 4, senderID)
        msg = Message.setBit(msg, 8, ROOT)
        msg = Message.setSeveralBit(msg, 4, 4, mode)
        msg = Message.setSeveralBit(msg, 0, 4, timestamp)
        return msg
            
    def createFollowUpMsg(self, orientation, DONE, mapData):
        msg = 0
        msg = Message.setSeveralBit(msg, 13, 3, self.FOLLOWUP_HEADER)
        msg = Message.setSeveralBit(msg, 11, 2, orientation)
        msg = Message.setBit(msg, 8, DONE)
        msg = Message.setSeveralBit(msg, 7, 8, mapData)
        
        msg = Message.setSeveralBit(msg, 9, 2, self.calcParity(msg))
        return msg
        
    def createErrorMsg(self, scriptCode, errorCode):
        msg = 0 
        msg = Message.setSeveralBit(msg, 13, 3, self.ERROR_HEADER)
        msg = Message.setSeveralBit(msg, 8, 3, scriptCode)  
        msg = Message.setSeveralBit(msg, 5, 5, errorCode)
        msg = Message.setSeveralBit(msg, 0, 5, self.extraErrorBits)
        return msg

    def createSystemUpdateMsg(self):
        msg = 0 
        msg = Message.setSeveralBit(msg, 13, 3, self.SYSUPDATE_HEADER)
        msg = Message.setSeveralBit(msg, 8, 3, self.updateCode)  
        msg = Message.setSeveralBit(msg, 5, 5, self.updateData)
        msg = Message.setSeveralBit(msg, 9, 2, self.calcParity(msg))
        return msg   
    
    def createInstructMsg(self, INSTDONE, instructData, updateType):
        msg = 0
        msg = Message.setSeveralBit(msg, 13, 3, self.INSTRUCT_HEADER)
        msg = Message.setSeveralBit(msg, 9, 4, updateType)
        msg = Message.setBit(msg, 8, INSTDONE)
        msg = Message.setSeveralBit(msg, 7, 8, instructData)
        return msg
    
    def createPosMsg(self, POSDONE, posX, posY):
        msg = 0
        msg = Message.setSeveralBit(msg, 13, 3, self.POS_HEADER) 
        msg = self.setSeveralBit(msg, 9, 4, 0)                  # reserved is empty
        msg = self.setBit(msg, 8, POSDONE)
        msg = self.setSeveralBit(msg, 4, 4, posX)
        msg = self.setSeveralBit(msg, 0, 4, posY)
        return msg

    def createAckMsg(self, ACK, msgType):
        msg = 0
        msg = self.setBit(msg, 8, self.ACK_HEADER)
        msg = self.setSeveralBit(msg, 5, 7, 0)                  # free is empty
        # ACK is missing !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        msg = self.setSeveralBit(msg, 0, 5, msgType)
        return msg

    @staticmethod    
    def serializeMsg(msg:int, word) -> bytearray:
        return bytearray([
            (word >> 8) & 0xFF,
            msg & 0xFF
        ])
        # use as message = createMsg then rfid_payload = Message.serializeMsg

    @staticmethod
    def checkIfCorrectLen(self, buf: bytearray):
        if len(buf) != 2:
            err.msgLengthIncorrect()
            return False, None
        msg = (buf[0] << 8) | buf[1]
        return True, msg

    #----- decode msgs -----
    def decodeINIT(self,msg):
        msg = self.checkIfCorrectLen(msg)
        if msg is not None:
            senderID = self.getSeveralBit(word, 10, 4)
            ROOT = self.getBit(word, 8)
            mode = self.getSeveralBit(word, 4, 4)
            timestamp = self.getSeveralBit(word, 0, 4)
            return senderID, ROOT, mode, timestamp
        return None, None, None, None
    
    def decodeFOLLOWUP(self, msg):
        msg = self.checkIfCorrectLen(msg)
        if msg is not None:
            orientation = self.getSeveralBit(msg, 11, 2)
            parity = self.getSeveralBit(msg, 9, 2)
            DONE = self.getBit(msg, 8)
            mapData = self.getSeveralBit(msg, 0, 8)
            # verify parity
            msg = self.getSeveralBit(msg, 9, 2, 2)
            parityCalc = self.calcParity(msg)
            if not (parity == parityCalc):
                err.parityCheckIncorrect()
            return orientation, DONE, mapData
        return None, None, None
        # listen only on that module for a set period of time
    
    def decodePOS(self, msg):
        msg = self.checkIfCorrectLen(msg)
        if msg is not None:
            POSDONE = self.getBit(msg, 8)
            posX = self.getSeveralBit(msg, 4, 4)
            posY = self.getSeveralBit(msg, 0, 4)
            return POSDONE, posX, posY
        return None, None, None
        # listen only on that module for a set period of time
    
    def decodeERROR(self, msg):
        msg = self.checkIfCorrectLen(msg)
        if msg is not None:
            scriptCode = self.getSeveralBit(word, 8, 5)
            errorCode = self.getSeveralBit(word, 5, 3)
            return scriptCode, errorCode
        return None, None
        # decode error in err.decodeERR()
    
    def decodeINSTRUCT(self, msg):
        msg = self.checkIfCorrectLen(msg)
        if msg is not None:
            ROOT = 1
            updateCode = self.getSeveralBit(word, 8, 3)
            updateData = self.getSeveralBit(word, 0, 8)
            # verify parity
            word = self.setSeveralBit(word, 11, 2, 0)
            parityCalc = self.calcParity(word)
            if not (parity == parityCalc):
                err.parityCheckIncorrect()
                return None, None
            else:
                return updateCode, updateData
        return None, None

    def decodeSysUpdateMsg(self, msg):
        msg = self.checkIfCorrectLen(msg)
        if msg is not None:
            # check whether really sysupmsg ? 
            INSTDONE = self.getBit(msg, 8)
            instructData = self.getSeveralBit(msg, 0, 8)
            scriptCode = self.getSeveralBit(msg, 9, 3)
            if scriptCode == self.SYSUPDATE_NEWGOALMAP:
                updateType = 2
            elif scriptCode == self.SYSUPDATE_COMPLETEUPDATE:
                updateType = 3
            else:
                None
            return INSTDONE, instructData, updateType
        return None, None, None

    def decodeACK(self, msg):
        msg = self.checkIfCorrectLen(msg)
        if msg is not None:
            ACK = self.getBit(msg, 12)
            msgType = self.getSeveralBit(msg, 0, 5)
            return ACK, msgType
        # all of this belongs in main!!!!!!!!!!
        msgTypeToSend = self.getLastMsgType()
        if msgTypeToSend == self.INIT_HEADER:
            hw.sendMsg(self.createInitMsg())
        elif msgTypeToSend == self.FOLLOWUP_HEADER:
            hw.sendMsg(self.createFollowUpMsg())
        elif msgTypeToSend == self.ERROR_HEADER:
            hw.sendMsg(self.createErrorMsg())
        elif msgTypeToSend == self.POS_HEADER:
            hw.sendMsg(self.createPosMsg())
        elif msgTypeToSend == self.INSTRUCT_HEADER:
            hw.sendMsg(self.createInstructMsg())
        elif msgTypeToSend == self.SYSUPDATE_HEADER:
            hw.sendMsg(self.createSystemUpdateMsg())
        else:
            hw.sendMsg(self.createAckMsg())
        return None, None

# ----- Getters -----
    #def getSenderSourceType(self, word):
    #    return self.getBit(word, 15)
    
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
        if self.getHeader(word) is not self.INIT_HEADER:
            err.msgTypeIncorrect()
        return self.getSeveralBit(word, 9, 4)
        
    def getROOT(self, word):
        if self.getHeader(word) is not self.INIT_HEADER:
            err.msgTypeIncorrect()
        return self.getBit(word, 8)
        
    def getDONE(self, word):
        if self.getHeader(word) is not self.FOLLOWUP_HEADER:
            err.msgTypeIncorrect()
        return self.getBit(word, 8)
        
    def getMode(self, word):
        if self.getHeader(word) is not self.INIT_HEADER:
            err.msgTypeIncorrect()
        return self.getSeveralBit(word, 4, 4)    
    
    def getTimestep(self, word):
        if self.getHeader(word) is not self.INIT_HEADER:
            err.msgTypeIncorrect()
        return self.getSeveralBit(word, 0, 4)

    def getOrientation(self, word):
        if self.getHeader(word) is not self.FOLLOWUP_HEADER:
            err.msgTypeIncorrect()
        return self.getSeveralBit(word, 11, 2)
        
    def getMap(self, word):
        if self.getHeader(word) is not self.FOLLOWUP_HEADER:
            err.msgTypeIncorrect()
        return self.deserialize(self.getSeveralBit(word, 0, 8))
        
    def getScriptCode(self, word):
        if self.getHeader(word) is not self.ERROR_HEADER:
            err.msgTypeIncorrect()
        return self.getSeveralBit(word, 8, 5)
        
    def getErrorCode(self, word):
        if self.getHeader(word) is not self.ERROR_HEADER:
            err.msgTypeIncorrect()
        return self.getSeveralBit(word, 5, 3)
    
    # Message.setSeveralBit(msg, 0, 5, self.extraErrorBits)

    def getExtraErrorBits(self, word):
        if self.getHeader(word) is not self.ERROR_HEADER:
            err.msgTypeIncorrect()
        return self.getSeveralBit(word, 0, 5)
    
    def getUpdateCode(self, word):
        if self.getHeader(word) is not self.SYSUPDATE_HEADER:
            err.msgTypeIncorrect()
        return self.getSeveralBit(word, 8, 3)
    
    def getUpdateData(self, word):
        if self.getHeader(word) is not self.SYSUPDATE_HEADER:
            err.msgTypeIncorrect()
        return self.getSeveralBit(word, 0, 8)
    
    def getInstMode(self, word):
        if self.getHeader(word) is not self.INSTRUCT_HEADER:
            err.msgTypeIncorrect()
        return self.getSeveralBit(word, 9, 4)
    
    def getINSTDONE(self, word):
        if self.getHeader(word) is not self.INSTRUCT_HEADER:
            err.msgTypeIncorrect()
        return self.getBit(word, 8)
    
    def getInstructData(self, word):
        if self.getHeader(word) is not self.INSTRUCT_HEADER:
            err.msgTypeIncorrect()
        return self.getSeveralBit(word, 0, 8)

    def getPOSDONE(self, word):
        if self.getHeader(word) is not self.POS_HEADER:
            err.msgTypeIncorrect()
        return self.getBit(word, 8)
    
    def getPosX(self, word):
        if self.getHeader(word) is not self.POS_HEADER:
            err.msgTypeIncorrect()
        return self.getSeveralBit(word, 4, 4)
    
    def getPosY(self, word):
        if self.getHeader(word) is not self.POS_HEADER:
            err.msgTypeIncorrect()
        return self.getSeveralBit(word, 0, 4)
    
    def getACK(self, word):
        if self.getHeader(word) is not self.ACK_HEADER:
            err.msgTypeIncorrect()
        return self.getBit(word, 8)
    
    def getLastMsgType(self, word):
        if self.getHeader(word) is not self.ACK_HEADER:
            err.msgTypeIncorrect()
        return self.getSeveralBit(word, 0, 5)
    