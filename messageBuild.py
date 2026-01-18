# Script to create the actual message and convert it to a package that can be sent through RFID| 16bit message (msg) channel

#Lib for msg codes
#... 001 = Initiation msg (INIT)
#... 010 = Follow-up/ Answer msg (FOLLOWUP)
#... 100 = ERROR msg

# For later implementation:
#... bigger senderId & versioned header so the swarm can have more than 8 nodes
#... implement proper checksum
#... compress map fragments so it can can have more than 64 spaces

# import controlhardware_testing.c as hw 
import errorHandeling.py as err

class Message:
    def __init__(self, senderID, receiverID, senderRootFlag, 
                 senderMap, senderMode, senderSource, 
                 senderBusyFlag, senderReplyFlag, senderUpdateFlag, senderRFIDOrientation, senderDoneFlag, senderTimestamp, senderParityErrorFlag, senderErrorCode, senderScriptCode):
        self.senderID = senderID
        # flags
        self.REPLY = senderReplyFlag
        self.UPDATE = senderUpdateFlag
        self.BUSY = senderBusyFlag
        self.ROOT = senderRootFlag
        self.DONE = senderDoneFlag
        self.PARITY = senderParityErrorFlag
        # payload
        self.mode = senderMode
        self.timestamp = senderTimestamp
        self.orientation = senderRFIDOrientation
        self.map = senderMap
        self.scriptCode = senderScriptCode
        self.errorCode = senderErrorCode
        
        
    @staticmethod
    def setBit(word: int, bitPos: int, value: int):
        value = 1 if value else 0   # make sure the value is definetely 100% 1 or 0
        return word | (1 << bitPos) if value else word & ~(1 << bitPos)
        # | = OR bitwise ;;; use it bc sinle bits can not be assigned, only bytes can be assigned. So, to change a single bit we can do that with OR. Add might lead to errors bc of the carry flag. Using OR is called "mask"

    @staticmethod
    def setSeveralBit(word: int, startBit: int, width: int, value: int) -> int:
        mask = ((1 << width) - 1) << startBit
        value = (value & ((1 << width) - 1) << startBit
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
        msg = Message.setSeveralBit(msg, 13, 3, self.header)
        msg = Message.setBit(msg, 10, self.REPLY) 
        msg = Message.setBit(msg, 9, self.UPDATE)
        msg = Message.setBit(msg, 8, self.BUSY)
        msg = Message.setSeveralBit(msg, 7, 3, self.mode)
        msg = Message.setBit(msg, 3, self.ROOT)
        msg = Message.setSeveralBit(msg, 2, 3, self.timestamp)
        return msg
            
    def createFollowUpMsg(self):
        msg = 0
        msg = Message.setSeveralBit(msg, 13, 3, self.header)
        msg = Message.setSeveralBit(msg, 11, 2, self.orientation)
        msg = Message.setBit(msg, 8, self.DONE)
        msg = Message.setSeveralBit(msg, 7, 8, self.map)
        
        msg = Message.setSeveralBit(msg, 9, 2, Message.calcParity(msg))
        return msg
        
    def createErrorMsg(self):
        msg = 0 
        msg = Message.setSeveralBit(msg, 13, 3, self.header)
        msg = Message.setSeveralBit(msg, 8, 5, self.scriptCode)  
        msg = Message.setSeveralBit(msg, 5, 3, self.errorCode)
        msg = Message.setSeveralBit(msg, 0, 5, 0)  #empty
                
    @staticmethod    
    def serializeMsg(msg:int) -> bytearray:
        return bytearray([
            (word >> 8) & 0xFF,
            msg & 0xFF
        ])
        # use as message = createMsg then rfid_payload = Message.serializeMsg
        
    @staticmethod
    def deserializeMsg(buf: bytearray) -> dict:
        if len(buf) != 2:
            print("[ERROR] 00001000 RFID message must be exactly 2 bytes")
            err.msgLengthIncorrect()

        word = (buf[0] << 8) | buf[1]
        
        #read header
        header = Message.getSeveralBit(word, 13, 3)
        
        if (header == 001):             # INIT msg
            senderID = getSeveralBit(word, 10, 3)
            REPLY = getBit(word, 7)
            UPDATE = getBit(word, 6)
            BUSY = getBit(word, 5)
            mode = getSeveralBit(word, 4, 3)
            ROOT = getBit(word, 3)
            timestamp = getSeveralBit(word, 2, 3)
        else if (header == 010):        # FOLLOWUP msg
            orientation = getSeveralBit(word, 11, 2)
            parity = Message.getSeveralBit(word, 9, 2)
            DONE = Message.getSeveralBit(word, 8, 1)
            mapData = Message.getSeveralBit(word, 0, 8)
            # verify parity
            word = Message.setSeveralBit(word, 9, 2, 0)
            parityCalc = Message.calcParity(word)
            if not (parity == paritycalc):
                print("[ERROR] 00001001 Parity Safety Check incorrect. Pls retry")
                err.parityCheckIncorrect()
        else if (header == 100):        # ERROR msg
            scriptCode = getSeveralBit(word, 8, 5)
            errorCode = getSeveralBit(word, 5, 3)
        else:
            print("[ERROR] 00001010 This message is not an INIT, FOLLOWUP, nor ERROR msg. Pls retry")
            err.msgTypeIncorrect()

        
       
