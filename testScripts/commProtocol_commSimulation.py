import sys, os, random
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from messageBuild import Message

# Helper functions
def check(field_name, expected, actual):
    if expected != actual:
        print(f"[FAIL] {field_name}: expected {expected}, got {actual}")
    else:
        print(f"[OK] {field_name}")

# Fake nodes that communicate
class FakeChannel:
    def __init__(self, node_id, channel):
        self.id = node_id
        self.channel = channel

    def send_init(self):
        msg = Message.createInitMsg(self.id, 0, 1, 5)
        self.channel.send(Message.serializeMsg(msg))

    def listen(self):
        msg = self.channel.receive()
        if msg:
            return Message.decodeINITMsg(msg)

    def test_init_through_channel():
        channel = FakeChannel()

        # sender
        sent_msg = Message.createInitMsg(senderID=3, ROOT=1, mode=5, timestamp=9)
        channel.send(Message.serializeMsg(sent_msg))

        # receiver
        received = channel.receive()
        decoded = Message.decodeINITMsg(received)

        assert decoded['senderId'] == 3
        assert decoded['ROOT'] == 1
        assert decoded['mode'] == 5
        assert decoded['timestamp'] == 9

        print("INIT CHANNEL OK")

    def test_two_nodes():
        channel = FakeChannel()

        nodeA = FakeNode(1, channel)
        nodeB = FakeNode(2, channel)

        nodeA.send_init()
        decoded = nodeB.listen()

        assert decoded['senderId'] == 1

        print("TWO NODE TEST OK")

def run():
    # test wrong order and interpretation
    pass

if __name__ == "__main__":
    run()
