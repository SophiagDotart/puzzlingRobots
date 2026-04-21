import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from messageBuild import Message
import main as main_code


# ---------------- CHANNEL ----------------
class FakeChannel:
    def __init__(self):
        self.messages = []

    def broadcast(self, sender_id, msg):
        self.messages.append((sender_id, msg))

    def receive(self, receiver_id):
        for i, (sender, msg) in enumerate(self.messages):
            if sender != receiver_id:
                return self.messages.pop(i)[1]
        return None


# ---------------- HARDWARE ----------------
class FakeHardware:
    def __init__(self, channel):
        self.channel = channel
        self.node_id = None

    def attach_node(self, node_id):
        self.node_id = node_id

    def sendThroughModule(self, msg, module=None):
        self.channel.broadcast(self.node_id, Message.serializeMsg(msg))
        return 0

    def sendThroughRandomModule(self, msg):
        self.channel.broadcast(self.node_id, Message.serializeMsg(msg))
        return 0

    def listenThroughModule(self, module):
        return self.channel.receive(self.node_id)

    def initAllHw(self):
        pass

    def resetRobot(self):
        print(f"[HW] Node {self.node_id} reset")


# ---------------- NODE RUNNER ----------------
class NodeRunner:
    def __init__(self, node_id, main_module, hw):
        self.main = main_module
        self.hw = hw

        self.hw.attach_node(node_id)
        self.main.hw = self.hw

        self.node, self.goalMap = self.main.init()
        self.sent_init = False

    def step(self):
        # listening
        for _ in range(5):
            msg = self.hw.listenThroughModule(0)
            if msg:
                print(f"[RECV] Node got msg: {msg}")
                self.main.decodeMsg(self.node, self.goalMap, msg)

        # talking
        if not self.sent_init:
            msg = self.main.msgBuild.Message.createInitMsg(
                senderID=self.node.nodeID,
                ROOT=self.node.ROOT,
                mode=self.node.mode,
                timestamp=self.node.timestamp
            )
            print(f"[SEND] Node sending INIT")
            self.hw.sendThroughRandomModule(msg)
            self.sent_init = True


# ---------------- TEST ----------------
def run(steps=10):
    channel = FakeChannel()

    node1 = NodeRunner(1, main_code, FakeHardware(channel))
    node2 = NodeRunner(2, main_code, FakeHardware(channel))

    print("=== START SIMULATION ===")

    for step in range(steps):
        print(f"\n--- STEP {step} ---")
        node1.step()
        node2.step()

    print("\n=== END SIMULATION ===")


if __name__ == "__main__":
    run()
    # test for collision, wrong oder, corruption