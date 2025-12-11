# import controlhardware_testing.c as hw

class Message:
    def __init__(self, senderID, receiverID, 
                 senderState, senderRootStatus, 
                 senderMap, senderMode, senderSource, 
                 senderBusyStatus, senderRFIDOrientation):
        self.senderID = senderID
        self.receiverID = receiverID
        # fields to be send as 16bits each
        self.state = senderState
        self.root = senderRootStatus
        self.map = senderMap
        self.mode = senderMode      # reply?
        self.source = senderSource
        self.busy = senderBusyStatus
        self.orientation = senderRFIDOrientation

    def serialize(self) -> bytearray:
        # extracts upper byte and then the lower one of the int to be able to send data through rfid
        buf = bytearray()

        # explain this further in thesis with bit logic? extract upper bit, then lower bit
        # -> CHANGE TO DIFFERENT LENGTHS ACCORDING TO MAP TRANSFER:PY!!!!!!!!!"!!!!!!!!!!"
        for field in (
            self.senderID,
            self.state, self.root, self.map,
            self.mode, self.source, self.busy,
            self.orientation):
            buf.append((field >> 8) & 0xFF)
            buf.append(field & 0xFF)

        payload_length = (len(buf) - 4)
        buf.append(payload_length)

        checksum = sum(buf) & 0xFF      # error recognition help
        buf.append(checksum)

        return buf
    
    @staticmethod
    def deserialize(buf: bytearray):
        # check for correctness
        if len(buf) < 6:
            print(f"[ERROR] The message is too short")

        checksum = buf[-1]
        calc = sum(buf[:-1]) & 0xFF
        if checksum != calc:
            print(f"[ERROR] Checksum mismatch")

        payloadLength = buf[-2]
        if payloadLength != len(buf) - 6:
            print(f"[ERROR] The message is not the right length")

        # decode the message
        senderID = (buf[0] << 8) | buf[1]
        receiverID = (buf[2] << 8) | buf[3]

        fields = []
        idx = 4
        end = idx + payloadLength
        while idx < end:
            val = (buf[idx] << 8) | buf[idx+1]
            fields.append(val)
            idx += 2

        return Message(senderID, receiverID)
    
    def send(self, msgContent):
        #hw_sendMsg(self.serialize(msgContent))
        pass

    @staticmethod
    def receive(rawMsg):
        return Message.deserialize(rawMsg)

