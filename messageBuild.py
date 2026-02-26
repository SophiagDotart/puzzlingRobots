# Script to create the actual message and convert it to a package that can be sent through RFID| 16bit message (msg) channel

#Lib for msg codes -> first Bit: does the input come from the user or from another robot? 0 comes from robot, 1 from user
#... 000 = free
#... 001 = Initiation msg (INIT)
#... 010 = Follow-up/ Answer msg (FOLLOWUP)
#... 011 = ERROR msg (ERROR)
#... 100 = POS
#... 101 = User game instruction (INSTRUCT)
#... 110 = System Update (SYSUPDATE)
#... 111 = ACK

#Lib for sysupdate code
# 2 = complete update
# 3 = new mode/ new goalMap to be added


from mapFunctions import Map

class Message:

    # state system variables
    POSDONE = False
    DONE = False

    # header variables
    INIT_HEADER = 1
    FOLLOWUP_HEADER = 2
    ERROR_HEADER = 3
    POS_HEADER = 4
    INSTRUCT_HEADER = 5
    SYSUPDATE_HEADER = 6
    ACK_HEADER = 7

    SYSUPDATE_COMPLETEUPDATE = 2
    SYSUPDATE_NEWGOALMAP = 3

    def __init__(Message, senderID, senderRootFlag, instructionComplete, instructionMode, positionDone, posX, posY, extraErrorBits, senderACK, senderMsgType, 
                 senderMap, senderMode, senderRFIDOrientation, senderDoneFlag, senderTimestamp, senderErrorCode, senderScriptCode, instructionUpdateCode, instructionUpdateData):
        Message.senderID = senderID
        Message.ROOT = senderRootFlag
        Message.DONE = senderDoneFlag
        Message.mode = senderMode
        Message.timestamp = senderTimestamp
        Message.orientation = senderRFIDOrientation
        Message.map = senderMap
        Message.scriptCode = senderScriptCode
        Message.errorCode = senderErrorCode
        Message.updateCode = instructionUpdateCode
        Message.updateData = instructionUpdateData
        Message.INSTDONE = instructionComplete
        Message.instMode = instructionMode
        Message.POSDONE = positionDone
        Message.posX = posX
        Message.posY = posY
        Message.extraErrorBits = extraErrorBits
        Message.ACK = senderACK
        Message.lastMsgType = senderMsgType
        
    #----- bit manipulation code -----
    @staticmethod
    def setBit(msg: int, bitPos: int, value: int):
        value = 1 if value else 0   # make sure the value is definitely 100% 1 or 0
        return msg | (1 << bitPos) if value else msg & ~(1 << bitPos)
        # | = OR bitwise ;;; use it bc single bits can not be assigned, only bytes can be assigned. So, to change a single bit we can do that with OR. Add might lead to errors bc of the carry flag. Using OR is called "mask"

    @staticmethod
    def setSeveralBit(msg: int, startBit: int, width: int, value: int) -> int:
        mask = ((1 << width) - 1) << startBit
        value = value & ((1 << width) - 1) << startBit
        return (msg & ~mask) | value
        
    @staticmethod
    def getBit(msg: int, bitPos: int) -> int:
        return (msg >> bitPos) & 1
        
    @staticmethod
    def getSeveralBit(msg: int, startBit: int, width: int) -> int:   
        return (msg >> startBit) & ((1 << width) - 1)
        
    @staticmethod
    def calcParity(value: int) -> int:
        return bin(value).count("1") % 4     # count the ones in the bitwise written msg and use only the last 2 numbers

    #----- Create msgs ------  
    @staticmethod  
    def createInitMsg(senderID, ROOT, mode, timestamp):  
        msg = 0
        msg = Message.setSeveralBit(msg, 13, 3, Message.INIT_HEADER)
        msg = Message.setSeveralBit(msg, 9, 4, senderID)
        msg = Message.setBit(msg, 8, ROOT)
        msg = Message.setSeveralBit(msg, 4, 4, mode)
        msg = Message.setSeveralBit(msg, 0, 4, timestamp)
        return msg

    @staticmethod 
    def createFollowUpMsg(orientation, DONE, mapData):
        msg = 0
        msg = Message.setSeveralBit(msg, 13, 3, Message.FOLLOWUP_HEADER)
        msg = Message.setSeveralBit(msg, 11, 2, orientation)
        msg = Message.setBit(msg, 8, DONE)
        msg = Message.setSeveralBit(msg, 7, 8, mapData)
        # add parity
        msg = Message.setSeveralBit(msg, 9, 2, 0)          # make sure parity bits do not influence in the calc product
        msg = Message.setSeveralBit(msg, 9, 2, Message.calcParity(msg))
        return msg
        
    @staticmethod     
    def createErrorMsg(scriptCode, errorCode):
        msg = 0 
        msg = Message.setSeveralBit(msg, 13, 3, Message.ERROR_HEADER)
        msg = Message.setSeveralBit(msg, 8, 5, scriptCode)  
        msg = Message.setSeveralBit(msg, 5, 3, errorCode)
        return msg

    @staticmethod 
    def createSystemUpdateMsg(updateCode, updateData):
        msg = 0 
        msg = Message.setSeveralBit(msg, 13, 3, Message.SYSUPDATE_HEADER)
        msg = Message.setSeveralBit(msg, 8, 3, updateCode)  
        msg = Message.setSeveralBit(msg, 5, 8, updateData)
        # add parity
        msg = Message.setSeveralBit(msg, 11, 2, 0)          # make sure parity bits do not influence in the calc product
        msg = Message.setSeveralBit(msg, 11, 2, Message.calcParity(msg))
        return msg   
    
    @staticmethod 
    def createInstructMsg(INSTDONE, instructData, instMode):
        msg = 0
        msg = Message.setSeveralBit(msg, 13, 3, Message.INSTRUCT_HEADER)
        msg = Message.setSeveralBit(msg, 9, 4, instMode)
        msg = Message.setBit(msg, 8, INSTDONE)
        msg = Message.setSeveralBit(msg, 7, 8, instructData)
        return msg
    
    @staticmethod 
    def createPosMsg(POSDONE, posX, posY):
        msg = 0
        msg = Message.setSeveralBit(msg, 13, 3, Message.POS_HEADER) 
        msg = Message.setSeveralBit(msg, 9, 4, 0)           # reserved is empty
        msg = Message.setBit(msg, 8, POSDONE)
        msg = Message.setSeveralBit(msg, 4, 4, posX)
        msg = Message.setSeveralBit(msg, 0, 4, posY)
        return msg

    @staticmethod 
    def createAckMsg(ACK, msgType):
        msg = 0
        msg = Message.setSeveralBit(msg, 13, 3, Message.ACK_HEADER)
        msg = Message.setBit(msg, 12, ACK)
        msg = Message.setSeveralBit(msg, 5, 7, 0)           # free is empty
        msg = Message.setSeveralBit(msg, 0, 5, msgType)
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
            return False        # err.msgLengthIncorrect()
        return (buf[0] << 8) | buf[1]

    #----- decode msgs -----
    @staticmethod
    def decodeINITMsg(msg):
        msg = Message.checkIfCorrectLen(msg)
        if msg is not None:
            senderID = Message.getSenderID(msg)
            ROOT = Message.getROOT(msg)
            mode = Message.getMode(msg)
            timestamp = Message.getTimestep(msg)
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
    
    @staticmethod
    def decodeFOLLOWUPMsg(msg):
        msg = Message.checkIfCorrectLen(msg)
        if msg is not None:
            orientation = Message.getOrientation(msg)
            Map.DONE = Message.getDONE(msg)
            mapData = Message.getMap(msg)
            # verify parity
            parity = Message.getSeveralBit(msg, 11, 2)         # get the parity value
            msg = Message.setSeveralBit(msg, 11, 2, 0)         # zero that value s parity bits dont screw the parity check
            if not parity == Message.calcParity(msg):
                return {'type': 'FOLLOWUP',
                        'orientation': None,
                        'DONE': None,
                        'mapData': None,
                        'parity': False}                        #err.parityCheckIncorrect()
            return {'type': 'FOLLOWUP',
                    'orientation': orientation,
                    'DONE': Map.DONE,
                    'mapData': mapData,
                    'parity': True}
        return {'type': 'FOLLOWUP',
                'orientation': None,
                'DONE': None,
                'mapData': None,
                'parity': None}
    
    @staticmethod
    def decodePOSMsg(msg):
        msg = Message.checkIfCorrectLen(msg)
        if msg is not None:
            Map.POSDONE = Message.getPOSDONE(msg)
            posX = Message.getPosX(msg)
            posY = Message.getPosY(msg)
            return {'type': 'POS',
                    'POSDONE': Map.POSDONE,
                    'posX': posX,
                    'posY': posY}
        return {'type': 'POS',
                    'POSDONE': None,
                    'posX': None,
                    'posY': None}
    
    @staticmethod
    def decodeERRORMsg(msg):                 # decode the meaning of the error in err.decodeERR()
        msg = Message.checkIfCorrectLen(msg)
        if msg is not None:
            scriptCode = Message.getScriptCode(msg)
            errorCode = Message.getErrorCode(msg)
            return {'type': 'ERROR',
                    'scriptCode': scriptCode,
                    'errorCode': errorCode}
        return {'type': 'ERROR',
                'scriptCode': None,
                'errorCode': None}
    
    @staticmethod
    def decodeINSTRUCTMsg(msg):
        msg = Message.checkIfCorrectLen(msg)
        if msg is not None:
            instMode = Message.getInstMode(msg)
            INSTDONE = Message.getINSTDONE(msg)
            instructData = Message.getInstructData(msg)
            return {'type': 'INSTRUCT',
                    'updateCode': instMode,
                    'INSTDONE': INSTDONE,
                    'instructData': instructData}
        return {'type': 'INSTRUCT',
                'updateCode': None,
                'INSTDONE': None,
                'instructData': None}

    @staticmethod
    def decodeSysUpdateMsg(msg):
        msg = Message.checkIfCorrectLen(msg)
        if msg is not None:
            updateCode = Message.getUpdateCode(msg)
            updateData = Message.getUpdateData(msg)
            # verify parity
            parity = Message.getSeveralBit(msg, 11, 2)         # get the parity value
            msg = Message.setSeveralBit(msg, 11, 2, 0)         # zero that value s parity bits dont screw the parity check
            if not parity == Message.calcParity(msg):          # check if the value that was sent is the same as the one calculated on the msg I rcv
                return {'type': 'SYSUPDATE',
                        'updateCode': updateCode,
                        'updateData': updateData,
                        'parityCheck': False}
            if updateCode == Message.SYSUPDATE_NEWGOALMAP:     # check for updateCode
                updateType = 2
            elif updateCode == Message.SYSUPDATE_COMPLETEUPDATE:
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

    @staticmethod
    def decodeACKMsg(msg):
        msg = Message.checkIfCorrectLen(msg)
        if msg is not None:
            ACK = Message.getACK(msg)
            msgType = Message.getLastMsgType(msg)
            return {'type': 'ACK',
                    'ACK': ACK,
                    'msgType': msgType}
        return {'type': 'ACK',
                'ACK': None,
                'msgType': None}

# ----- Getters -----    
    @staticmethod
    def getHeader(msg):
        return Message.getSeveralBit(msg, 13, 3)

    @staticmethod
    def getSenderID(msg):
        if Message.getHeader(msg) != Message.INIT_HEADER:
            return None         # err.msgTypeIncorrect()
        return Message.getSeveralBit(msg, 9, 4)

    @staticmethod  
    def getROOT(msg):
        if Message.getHeader(msg) != Message.INIT_HEADER:
            return None         # err.msgTypeIncorrect()
        return Message.getBit(msg, 8)
    
    @staticmethod
    def getMode(msg):
        if Message.getHeader(msg) != Message.INIT_HEADER:
            return None         # err.msgTypeIncorrect()
        return Message.getSeveralBit(msg, 4, 4)    
    
    @staticmethod
    def getTimestep(msg):
        if Message.getHeader(msg) != Message.INIT_HEADER:
            return None         # err.msgTypeIncorrect()
        return Message.getSeveralBit(msg, 0, 4)  

    @staticmethod
    def getPOSDONE(msg):
        if Message.getHeader(msg) != Message.POS_HEADER:
            return None         # err.msgTypeIncorrect()
        return Map.POSDONE
    
    @staticmethod
    def getPosX(msg):
        if Message.getHeader(msg) != Message.POS_HEADER:
            return None         # err.msgTypeIncorrect()
        return Message.getSeveralBit(msg, 4, 4)
    
    @staticmethod
    def getPosY(msg):
        if Message.getHeader(msg) != Message.POS_HEADER:
            return None         # err.msgTypeIncorrect()
        return Message.getSeveralBit(msg, 0, 4)
    
    @staticmethod
    def getOrientation(msg):
        if Message.getHeader(msg) != Message.FOLLOWUP_HEADER:
            return None         # err.msgTypeIncorrect()
        return Message.getSeveralBit(msg, 11, 2)  

    @staticmethod
    def getOrientationX(msg):
        return Message.getBit(msg, 12)  
    
    @staticmethod
    def getOrientationY(msg):
        return Message.getBit(msg, 11)  

    @staticmethod
    def getDONE(msg):
        if Message.getHeader(msg) != Message.FOLLOWUP_HEADER:
            return None         # err.msgTypeIncorrect()
        return Map.POSDONE

    @staticmethod    
    def getMap(msg):
        if Message.getHeader(msg) != Message.FOLLOWUP_HEADER:
            return None         # err.msgTypeIncorrect()
        return Map.deserialize(Message.getSeveralBit(msg, 0, 8))

    @staticmethod    
    def getScriptCode(msg):
        if Message.getHeader(msg) != Message.ERROR_HEADER:
            return None         # err.msgTypeIncorrect()
        return Message.getSeveralBit(msg, 8, 5)

    @staticmethod    
    def getErrorCode(msg):
        if Message.getHeader(msg) != Message.ERROR_HEADER:
            return None         # err.msgTypeIncorrect()
        return Message.getSeveralBit(msg, 5, 3)

    @staticmethod
    def getExtraErrorBits(msg):
        if Message.getHeader(msg) != Message.ERROR_HEADER:
            return None         # err.msgTypeIncorrect()
        return Message.getSeveralBit(msg, 0, 5)
    
    @staticmethod
    def getACK(msg):
        if Message.getHeader(msg) != Message.ACK_HEADER:
            return None         # err.msgTypeIncorrect()
        return Message.getBit(msg, 12)
    
    @staticmethod
    def getLastMsgType(msg):
        if Message.getHeader(msg) != Message.ACK_HEADER:
            return None         # err.msgTypeIncorrect()
        return Message.getSeveralBit(msg, 0, 5)

    @staticmethod
    def getUpdateCode(msg):
        if Message.getHeader(msg) != Message.SYSUPDATE_HEADER:
            return None         # err.msgTypeIncorrect()
        return Message.getSeveralBit(msg, 8, 3)
    
    @staticmethod
    def getUpdateData(msg):
        if Message.getHeader(msg) != Message.SYSUPDATE_HEADER:
            return None         # err.msgTypeIncorrect()
        return Message.getSeveralBit(msg, 0, 8)
    
    @staticmethod
    def getInstMode(msg):
        if Message.getHeader(msg) != Message.INSTRUCT_HEADER:
            return None         # err.msgTypeIncorrect()
        return Message.getSeveralBit(msg, 9, 4)
    
    @staticmethod
    def getINSTDONE(msg):
        if Message.getHeader(msg) != Message.INSTRUCT_HEADER:
            return None         # err.msgTypeIncorrect()
        return Message.getBit(msg, 8)
    
    @staticmethod
    def getInstructData(msg):
        if Message.getHeader(msg) != Message.INSTRUCT_HEADER:
            return None         # err.msgTypeIncorrect()
        return Message.getSeveralBit(msg, 0, 8)
