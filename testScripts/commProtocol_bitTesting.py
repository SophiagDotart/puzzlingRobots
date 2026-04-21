import sys, os, random
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from messageBuild import Message

# Helper functions
def check(field_name, expected, actual):
    if expected != actual:
        print(f"[FAIL] {field_name}: expected {expected}, got {actual}")
    else:
        print(f"[OK] {field_name}")


# Serial test of msgs
def test_init():
    msg = Message.createInitMsg(senderID=3, ROOT=1, mode=5, timestamp=9)
    decoded = Message.decodeINITMsg(Message.serializeMsg(msg))

    print("Decoded INIT:", decoded)

    check("senderID", 3, decoded['senderID'])
    check("ROOT", 1, decoded['ROOT'])
    check("mode", 5, decoded['mode'])
    check("timestamp", 9, decoded['timestamp'])

def test_followup():
    orientation = 2
    DONE = 1
    mapData = 173

    msg = Message.createFollowUpMsg(orientation, DONE, mapData)
    decoded = Message.decodeFOLLOWUPMsg(Message.serializeMsg(msg))

    print("\nDecoded FOLLOWUP:", decoded)

    check("FOLLOWUP orientation", orientation, decoded['orientation'])
    check("FOLLOWUP DONE", DONE, decoded['DONE'])
    check("FOLLOWUP mapData", mapData, decoded['mapData'])
    check("FOLLOWUP parity", True, decoded['parity'])

def test_error():
    scriptCode = 17
    errorCode = 5

    msg = Message.createErrorMsg(scriptCode, errorCode)
    decoded = Message.decodeERRORMsg(Message.serializeMsg(msg))

    print("\nDecoded ERROR:", decoded)

    check("ERROR scriptCode", scriptCode, decoded['scriptCode'])
    check("ERROR errorCode", errorCode, decoded['errorCode'])

def test_pos():
    POSDONE = 1
    posX = 7
    posY = 12

    msg = Message.createPosMsg(POSDONE, posX, posY)
    decoded = Message.decodePOSMsg(Message.serializeMsg(msg))

    print("\nDecoded POS:", decoded)

    check("POS POSDONE", POSDONE, decoded['POSDONE'])
    check("POS posX", posX, decoded['posX'])
    check("POS posY", posY, decoded['posY'])

def test_ack():
    ACK = 1
    msgType = Message.POS_HEADER

    msg = Message.createAckMsg(ACK, msgType)
    decoded = Message.decodeACKMsg(Message.serializeMsg(msg))

    print("\nDecoded ACK:", decoded)

    check("ACK value", ACK, decoded['ACK'])
    check("ACK msgType", msgType, decoded['msgType'])

def test_instruct():
    INSTDONE = 1
    instructData = 200
    instMode = 3

    msg = Message.createInstructMsg(INSTDONE, instructData, instMode)
    decoded = Message.decodeINSTRUCTMsg(Message.serializeMsg(msg))

    print("\nDecoded INSTRUCT:", decoded)

    check("INSTRUCT INSTDONE", INSTDONE, decoded['INSTDONE'])
    check("INSTRUCT data", instructData, decoded['instructData'])
    check("INSTRUCT mode", instMode, decoded['updateCode'])

def test_sysupdate():
    updateCode = Message.SYSUPDATE_COMPLETEUPDATE
    updateData = 155

    msg = Message.createSystemUpdateMsg(updateCode, updateData)
    decoded = Message.decodeSysUpdateMsg(Message.serializeMsg(msg))

    print("\nDecoded SYSUPDATE:", decoded)

    check("SYSUPDATE data", updateData, decoded['updateData'])
    check("SYSUPDATE parity", True, decoded['parityCheck'])

# Test for: incorrect values (too long/short, prohibited/ not defined), wrong order
# Test errors
def test_followup_badParity():
    msg = Message.createFollowUpMsg(2, 1, 173)
    msg ^= 1  # flip one bit

    decoded = Message.decodeFOLLOWUPMsg(Message.serializeMsg(msg))

    print("\nDecoded FOLLOWUP (bad parity):", decoded)

    check("FOLLOWUP bad parity", False, decoded['parity'])


def run():
    # tests to check correct bit (un)packing
    test_init()
    test_followup()
    test_error()
    test_pos()
    test_ack()
    test_instruct()
    test_sysupdate()
    # test_followup_badParity()

if __name__ == "__main__":
    run()
