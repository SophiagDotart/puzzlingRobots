# Script to create the actual message and convert it to a package that can be sent through RFID| 16bit message channel

# For later implementation:
#... bigger senderId & versioned header so the swarm can have more than 8 nodes
#... implement proper checksum
#... compress map fragments so it can can have more than 64 spaces

# import controlhardware_testing.c as hw 

class Message:
    def __init__(self, senderID, receiverID, senderRootFlag, 
                 senderMap, senderMode, senderSource, 
                 senderBusyFlag, senderReplyFlag, senderUpdateFlag, senderRFIDOrientation, senderDoneFlag):
        self.senderID = senderID
        # flags
        self.REPLY = senderReplyFlag
        self.UPDATE = senderUpdateFlag
        self.BUSY = senderBusyFlag
        self.ROOT = senderRootFlag
        self.DONE = senderDoneFlag
        # payload
        self.mode = senderMode
        self.timestamp = senderTimestamp
        self.orientation = senderRFIDOrientation
        self.map = senderMap
        
        
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
            
    def createFollowUpMsg(self) -> int:
        msg = 0
        msg = Message.setSeveralBit(msg, 13, 3, self.header)
        msg = Message.setSeveralBit(msg, 11, 2, self.orientation)
        msg = Message.setSeveralBit(msg, 9, 2, Message.calcParity(msg))
        msg = Message.setBit(msg, 8, self.DONE)
        msg = Message.setSeveralBit(msg, 7, 8, self.map)
        return msg
        
    @staticmethod    
    def serializeMsg(msg:int) -> bytearray:
        return bytearray([
            (word >> 8) & 0xFF,
            word & 0xFF
        ])
        # use as message = createMsg then rfid_payload = Message.serializeMsg
        
    @staticmethod
    def deserializeMsg(msgInByteArray: bytearray) -> int:
        return msg
