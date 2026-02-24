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

from mapFunctions import Map

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
        # add parity
        msg = self.setSeveralBit(msg, 9, 2, 0)          # make sure parity bits do not influence in the calc product
        msg = self.setSeveralBit(msg, 9, 2, self.calcParity(msg))
        return msg
        
    def createErrorMsg(self, scriptCode, errorCode):
        msg = 0 
        msg = Message.setSeveralBit(msg, 13, 3, self.ERROR_HEADER)
        msg = Message.setSeveralBit(msg, 8, 5, scriptCode)  
        msg = Message.setSeveralBit(msg, 5, 3, errorCode)
        msg = Message.setSeveralBit(msg, 0, 5, self.extraErrorBits)
        return msg

    def createSystemUpdateMsg(self, updateCode, updateData):
        msg = 0 
        msg = Message.setSeveralBit(msg, 13, 3, self.SYSUPDATE_HEADER)
        msg = Message.setSeveralBit(msg, 8, 3, updateCode)  
        msg = Message.setSeveralBit(msg, 5, 8, updateData)
        # add parity
        msg = self.setSeveralBit(msg, 11, 2, 0)          # make sure parity bits do not influence in the calc product
        msg = self.setSeveralBit(msg, 11, 2, self.calcParity(msg))
        return msg   
    
    def createInstructMsg(self, INSTDONE, instructData, instMode):
        msg = 0
        msg = Message.setSeveralBit(msg, 13, 3, self.INSTRUCT_HEADER)
        msg = Message.setSeveralBit(msg, 9, 4, instMode)
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
        msg = self.setSeveralBit(msg, 13, 3, self.ACK_HEADER)
        msg = self.setBit(msg, 12)
        msg = self.setSeveralBit(msg, 5, 7, 0)                  # free is empty
        msg = self.setSeveralBit(msg, 0, 5, msgType)
        return msg

    @staticmethod    
    def serializeMsg(msg:int) -> bytearray:
        return bytearray([
            (msg >> 8) & 0xFF,
            msg & 0xFF
        ])
        # use as message = createMsg then rfid_payload = Message.serializeMsg

    @staticmethod
    def checkIfCorrectLen(buf: bytearray):
        if len(buf) != 2:
            return None  # err.msgLengthIncorrect()
        return (buf[0] << 8) | buf[1]

    #----- decode msgs -----
    def decodeINIT(self,msg):
        msg = self.checkIfCorrectLen(msg)
        if msg is not None:
            senderID = self.getSenderID(msg)
            ROOT = self.getROOT(msg)
            mode = self.getMode(msg)
            timestamp = self.getTimestep(msg)
            return {'type' : 'INIT',
                    'senderId': senderID,
                    'ROOT': ROOT,
                    'mode': mode,
                    'timestamp': timestamp}
        return {'type': None,
                'senderID': None,
                'ROOT': None,
                'mode': None,
                'timestamp': None}
    
    def decodeFOLLOWUP(self, msg):
        msg = self.checkIfCorrectLen(msg)
        if msg is not None:
            orientation = self.getOrientation(msg)
            DONE = self.getDONE(msg)
            mapData = self.getMap(msg)
            # verify parity
            parity = self.getSeveralBit(msg, 11, 2)         # get the parity value
            msg = self.setSeveralBit(msg, 11, 2, 0)         # zero that value s parity bits dont screw the parity check
            if not parity == self.calcParity(msg):
                #err.parityCheckIncorrect()
                return {'type': 'FOLLOWUP',
                        'orientation': None,
                        'DONE': None,
                        'mapData': None,
                        'parity': False}
            return {'type': 'FOLLOWUP',
                    'orientation': orientation,
                    'DONE':DONE,
                    'mapData': mapData,
                    'parity': True}
        return {'type': 'FOLLOWUP',
                'orientation': None,
                'DONE': None,
                'mapData': None,
                'parity': None}
    
    def decodePOS(self, msg):
        msg = self.checkIfCorrectLen(msg)
        if msg is not None:
            POSDONE = self.getPOSDONE(msg)
            posX = self.getPosX(msg)
            posY = self.getPosY(msg)
            return {'type': 'POS',
                    'POSDONE': POSDONE,
                    'posX': posX,
                    'posY': posY}
        return {'type': 'POS',
                    'POSDONE': None,
                    'posX': None,
                    'posY': None}
    
    def decodeERROR(self, msg):                 # decode the meaning of the error in err.decodeERR()
        msg = self.checkIfCorrectLen(msg)
        if msg is not None:
            scriptCode = self.getScriptCode(msg)
            errorCode = self.getErrorCode(msg)
            return {'type': 'ERROR',
                    'scriptCode': scriptCode,
                    'errorCode': errorCode}
        return {'type': 'ERROR',
                'scriptCode': None,
                'errorCode': None}
    
    def decodeINSTRUCT(self, msg):
        msg = self.checkIfCorrectLen(msg)
        if msg is not None:
            instMode = self.getInstMode(msg)
            INSTDONE = self.getINSTDONE(msg)
            instructData = self.getInstructData(msg)
            return {'type': 'INSTRUCT',
                    'updateCode': instMode,
                    'INSTDONE': INSTDONE,
                    'instructData': instructData}
        return {'type': 'INSTRUCT',
                'updateCode': None,
                'INSTDONE': None,
                'instructData': None}

    def decodeSysUpdateMsg(self, msg):
        msg = self.checkIfCorrectLen(msg)
        if msg is not None:
            updateCode = self.getUpdateCode(msg)
            updateData = self.getUpdateData(msg)
            # verify parity
            parity = self.getSeveralBit(msg, 11, 2)         # get the parity value
            msg = self.setSeveralBit(msg, 11, 2, 0)         # zero that value s parity bits dont screw the parity check
            if not parity == self.calcParity(msg):          # check if the value that was sent is the same as the one calculated on the msg I rcv
                return {'type': 'SYSUPDATE',
                        'updateCode': updateCode,
                        'updateData': updateData,
                        'parityCheck': False}
            if updateCode == self.SYSUPDATE_NEWGOALMAP:     # check for updateCode
                updateType = 2
            elif updateCode == self.SYSUPDATE_COMPLETEUPDATE:
                updateType = 3
            else:
                return {'type': 'SYSUPDATE',
                        'updateType': None,
                        'parityCheck': True}
            return {'type': 'SYSUPDATE',
                    'updateType': updateType,
                    'updateData': updateData,
                    'parityCheck': True}
        return {'type': 'SYSUPDATE',
                'updateCode': None,
                'updateData': None,
                'parityCheck': None}

    def decodeACK(self, msg):
        msg = self.checkIfCorrectLen(msg)
        if msg is not None:
            ACK = self.getACK(msg)
            msgType = self.getMsgType(msg)
            return {'type': 'ACK',
                    'ACK': ACK,
                    'msgType': msgType}
        return {'type': 'ACK',
                'ACK': None,
                'msgType': None}

# ----- Getters -----    
    def getHeader(self, word):
        return self.getSeveralBit(word, 13, 3)

    def getSenderID(self, word):
        if self.getHeader(word) != self.INIT_HEADER:
            return None #err.msgTypeIncorrect()
        return self.getSeveralBit(word, 9, 4)
        
    def getROOT(self, word):
        if self.getHeader(word) != self.INIT_HEADER:
            return None #err.msgTypeIncorrect()
        return self.getBit(word, 8)
    
    def getMode(self, word):
        if self.getHeader(word) != self.INIT_HEADER:
            return None #err.msgTypeIncorrect()
        return self.getSeveralBit(word, 4, 4)    
    
    def getTimestep(self, word):
        if self.getHeader(word) != self.INIT_HEADER:
            return None #err.msgTypeIncorrect()
        return self.getSeveralBit(word, 0, 4)  

    def getPOSDONE(self, word):
        if self.getHeader(word) != self.POS_HEADER:
            return None #err.msgTypeIncorrect()
        return self.getBit(word, 8)
    
    def getPosX(self, word):
        if self.getHeader(word) != self.POS_HEADER:
            return None #err.msgTypeIncorrect()
        return self.getSeveralBit(word, 4, 4)
    
    def getPosY(self, word):
        if self.getHeader(word) != self.POS_HEADER:
            return None #err.msgTypeIncorrect()
        return self.getSeveralBit(word, 0, 4)
    
    def getOrientation(self, word):
        if self.getHeader(word) != self.FOLLOWUP_HEADER:
            return None #err.msgTypeIncorrect()
        return self.getSeveralBit(word, 11, 2)  

    def getDONE(self, word):
        if self.getHeader(word) != self.FOLLOWUP_HEADER:
            return None #err.msgTypeIncorrect()
        return self.getBit(word, 8)
        
    def getMap(self, word):
        if self.getHeader(word) != self.FOLLOWUP_HEADER:
            return None #err.msgTypeIncorrect()
        return Map.deserialize(self.getSeveralBit(word, 0, 8))
        
    def getScriptCode(self, word):
        if self.getHeader(word) != self.ERROR_HEADER:
            return None #err.msgTypeIncorrect()
        return self.getSeveralBit(word, 8, 5)
        
    def getErrorCode(self, word):
        if self.getHeader(word) != self.ERROR_HEADER:
            return None #err.msgTypeIncorrect()
        return self.getSeveralBit(word, 5, 3)

    def getExtraErrorBits(self, word):
        if self.getHeader(word) != self.ERROR_HEADER:
            return None #err.msgTypeIncorrect()
        return self.getSeveralBit(word, 0, 5)
    
    def getACK(self, word):
        if self.getHeader(word) != self.ACK_HEADER:
            return None #err.msgTypeIncorrect()
        return self.getBit(word, 12)
    
    def getLastMsgType(self, word):
        if self.getHeader(word) != self.ACK_HEADER:
            return None #err.msgTypeIncorrect()
        return self.getSeveralBit(word, 0, 5)

    def getUpdateCode(self, word):
        if self.getHeader(word) != self.SYSUPDATE_HEADER:
            return None #err.msgTypeIncorrect()
        return self.getSeveralBit(word, 8, 3)
    
    def getUpdateData(self, word):
        if self.getHeader(word) != self.SYSUPDATE_HEADER:
            return None #err.msgTypeIncorrect()
        return self.getSeveralBit(word, 0, 8)
    
    def getInstMode(self, word):
        if self.getHeader(word) != self.INSTRUCT_HEADER:
            return None #err.msgTypeIncorrect()
        return self.getSeveralBit(word, 9, 4)
    
    def getINSTDONE(self, word):
        if self.getHeader(word) != self.INSTRUCT_HEADER:
            return None #err.msgTypeIncorrect()
        return self.getBit(word, 8)
    
    def getInstructData(self, word):
        if self.getHeader(word) != self.INSTRUCT_HEADER:
            return None #err.msgTypeIncorrect()
        return self.getSeveralBit(word, 0, 8)
