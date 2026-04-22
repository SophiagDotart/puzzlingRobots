import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import random
import copy

from messageBuild import Message
import main as main_code
from switchingConditions import RESULT_COMMUNICATIONACCEPTED

# ============================================================
# STATES
# ============================================================
IDLE = "IDLE"
WAIT_ACK_INIT = "WAIT_ACK_INIT"
WAIT_POS_ACK = "WAIT_POS_ACK"
WAIT_FOLLOWUP_ACK = "WAIT_FOLLOWUP_ACK"
DONE = "DONE"

STEPS = 10
MAX_DELAY = 1

# ============================================================
# MESSAGE FORMAT DEBUG
# ============================================================
def format_msg(msg):
    try:
        header = Message.getHeader(msg)

        if header == Message.INIT_HEADER:
            d = Message.decodeINITMsg(msg)
            return f"INIT(sender={d['senderID']}, root={d['ROOT']}, mode={d['mode']}, t={d['timestamp']})"

        if header == Message.ACK_HEADER:
            d = Message.decodeACKMsg(msg)
            return f"ACK(ack={d['ACK']}, type={d['msgType']})"

        if header == Message.POS_HEADER:
            return "POS(...)"

        if header == Message.FOLLOWUP_HEADER:
            return "FOLLOWUP(...)"

        return f"UNKNOWN({msg})"
    except:
        return f"RAW({msg})"


# ============================================================
# SCENARIOS (FAULT DEFINITIONS)
# ============================================================
class Scenario:
    def __init__(self, name, fault_fn):
        self.name = name
        self.fault_fn = fault_fn

def build_scenarios():
    return [
        Scenario("NO ERRORS", no_errors),
        Scenario("PACKET LOSS", packet_loss_fault),
        Scenario("CORRUPTION", corruptedMsg_fault),
        Scenario("WRONG ORDER", wrongOrder_fault),
        Scenario("TOO MUCH DELAY", timeout_fault),
        Scenario("PARITY ERROR", parityError_fault)
    ]


def no_errors(event):
    return event, "OK"

def packet_loss_fault(event):
    if random.random() < 0.3:
        return None, "DROPPED"
    return event, "OK"

def corruptedMsg_fault(event):
    if random.random() < 0.2 and Message.getHeader(event.m) == Message.ACK_HEADER:
        new_event = copy.copy(event)
        d = Message.decodeACKMsg(event.m)
        new_event.m = Message.createAckMsg(not d["ACK"], d["type"])
        return new_event, "CORRUPTED"

    return event, "OK"

def wrongOrder_fault(event):
    if random.random() < 0.4:
        new_event = copy.copy(event)
        new_event.t = max(0, event.t - random.randint(1, 3))
        return new_event, "MSG ORDER REARRANGED"
    return event, "OK"

def timeout_fault(event):
    if random.random() < 0.3:
        event.t += random.randint(2, 5)
        return event, "DELAYED"
    return event, "OK"

def parityError_fault(event):
    if Message.getHeader(event.m) == Message.FOLLOWUP_HEADER:
        if random.random() < 0.5:
            new_event = copy.copy(event)

            # flip parity bits (bits 9–10)
            parity = Message.getSeveralBit(event.m, 9, 2)
            corrupted_parity = (parity + 1) % 4

            corrupted_msg = Message.setSeveralBit(event.m, 9, 2, corrupted_parity)
            new_event.m = corrupted_msg

            return new_event, "PARITY_ERROR"

    return event, "OK"

# ============================================================
# EVENT + BUS scheduling
# ============================================================
class Event:
    def __init__(self, t, r, s, m):
        self.t = t
        self.r = r
        self.s = s
        self.m = m

class EventLog: 
    def __init__(self): 
        self.entries = [] 
    
    def log(self, entry): 
        self.entries.append(entry) 
    
    def dump(self): 
        for e in self.entries: 
            print(e)

class EventBus:
    def __init__(self, log = None):
        self.time = 0
        self.q = []
        self.log = log

    def send(self, s, r, m, delay=1):
        delay = random.randint(1, MAX_DELAY)
        event = Event(self.time + delay, r, s, m)
        self.q.append(event)

        print(f"[SEND t={self.time}] {s}->{r} {format_msg(m)}")

        if self.log:
            self.log.log(f"[SEND t={self.time}] {s} → {r} | delay={delay} | msg={m}")

    def userInitiation(self):
        ready = [e for e in self.q if e.t <= self.time]
        self.q = [e for e in self.q if e.t > self.time]

        for e in ready:
            latency = self.time - e.t
            if self.log:
                self.log.log(
                    f"[DELIVER t={self.time}] {e.s} → {e.r} | latency={latency} | msg={e.m}"
                )
        return ready

    def deliver(self, time):
        ready = [e for e in self.q if e.t <= time]
        self.q = [e for e in self.q if e.t > time]
        return ready

    def tick(self):
        self.time += 1

# ============================================================
# Dummy Hardware
# ============================================================
class SimHW:
    def __init__(self, node, bus):
        self.node = node
        self.bus = bus

    def initAllHw(self):
        print("[SIM] initAllHw called")

    def sendMsg(self, msg):
        peer = 2 if self.node.id == 1 else 1
        self.bus.send(self.node.id, peer, msg)

    def sendThroughModule(self, msg, module=None):
        self.sendMsg(msg)
        return 0  # important: real code expects a module number!

    def sendThroughRandomModule(self, msg):
        self.sendMsg(msg)
        return 0  # same here

    def listenThroughModule(self, module):
        if self.node.hw_inbox:
            return self.node.hw_inbox[0]   # DO NOT POP
        return None


# ============================================================
# FAULT ENGINE
# ============================================================
class FaultEngine:
    def __init__(self, scenario):
        self.scenario = scenario

    def apply(self, event):
        return self.scenario.fault_fn(event)


# ============================================================
# NODE
# ============================================================
class Node:
    def __init__(self, nid, logic, bus):
        self.id = nid
        self.bus = bus
        self.logic = logic

        self.state, _ = logic.init()
        self.inbox = []

        self.state_name = IDLE
        self.started = False
        self.last_time_from = {}

        self.hw = SimHW(self, bus)
        main_code.hw = self.hw
        self.hw_inbox = []

    def send(self, r, m):
        self.bus.send(self.id, r, m)

    def receive(self, m, sender=None, bus_time=None):

        # ORDER DETECTION
        if sender is not None:
            last = self.last_time_from.get(sender, -1)

            if bus_time is not None and bus_time < last:
                print(f"[NODE {self.id}] WRONG ORDER from {sender} (t={bus_time}, last={last})")

            self.last_time_from[sender] = bus_time

        self.inbox.append(m)

    def process(self):
        while self.inbox:
            self.handle(self.inbox.pop(0))

    def handle(self, msg):
        old_hw = main_code.hw
        main_code.hw = self.hw
        main_code.decodeMsg(self.state, None, msg)
        main_code.hw = old_hw

    def step(self):
        peer = 2 if self.id == 1 else 1

        # INIT
        if self.id == 1 and not self.started:
            print(f"[NODE {self.id} t={self.bus.time}] INIT")
            msg = Message.createInitMsg(self.id, False, 0, self.state.timestamp)
            self.send(peer, msg)
            self.state_name = WAIT_ACK_INIT
            self.started = True
            return

        # POS
        if self.id == 1 and self.state_name == WAIT_POS_ACK:
            print(f"[NODE {self.id} t={self.bus.time}] SEND POS")
            msg = Message.createPosMsg(True, 0, 0)
            self.send(peer, msg)
            self.state_name = "POS_IN_FLIGHT"
            return

        # FOLLOWUP
        if self.id == 1 and self.state_name == WAIT_FOLLOWUP_ACK:
            print(f"[NODE {self.id} t={self.bus.time}] SEND FOLLOWUP")
            msg = Message.createFollowUpMsg(0, True, 0)
            self.send(peer, msg)
            self.state_name = "FOLLOWUP_IN_FLIGHT"
            return

    def run_step(self):
        node = self.state

        # Listening phase (shortened for simulation)
        for _ in range(5):
            for module in range(4):
                msg = self.hw.listenThroughModule(module)
                if msg is not None:
                    main_code.decodeMsg(node, None, msg)
                    
        # Talking phase
        if self.id == 1 and not self.started:
            msg = Message.createInitMsg(
                senderID=self.id,
                ROOT=node.ROOT,
                mode=node.mode,
                timestamp=node.timestamp
            )
            self.hw.sendThroughRandomModule(msg)
            self.started = True

        self.hw_inbox.clear()

# ============================================================
# SIMULATION ENGINE (owns delivery loop)
# ============================================================
class Simulation:
    def __init__(self, nodes_factory):
        self.nodes_factory = nodes_factory

    def run(self, steps, scenario):

        print("\n" + "=" * 60)
        print(f"SCENARIO: {scenario.name}")
        print("=" * 60)

        try:
            bus = EventBus(log=EventLog())
            fault = FaultEngine(scenario)
            nodes = self.nodes_factory(bus)

            for _ in range(steps):

                print(f"\n=== TIME {bus.time} ===")

                events = bus.deliver(bus.time)

                for e in events:
                    result, status = fault.apply(e)
                    print(f"[LINK] {e.s}->{e.r} STATUS={status}")

                    if result is None:
                        print(f"[FAULT] DROPPED {e.s}->{e.r} | {format_msg(e.m)}")
                        continue

                    for n in nodes:
                        if n.id == result.r:
                            n.hw_inbox.append(result.m)

                for n in nodes:
                    n.run_step()

                bus.tick()

        except Exception as e:
            print(f"[SCENARIO CRASH] {scenario.name}: {e}")

        print(f"\n[SCENARIO END] {scenario.name}\n")


# ============================================================
# RUNNER
# ============================================================
def run_sim():
    log = EventLog()

    def factory(bus):
        return [
            Node(1, main_code, bus),
            Node(2, main_code, bus)
        ]

    sim = Simulation(factory)

    # inject log into bus inside Simulation
    sim.run(STEPS, scenario=Scenario("NO ERRORS", no_errors))

    print("\n=== EVENT LOG ===") 
    log.dump()

def run_faulty():
    scenarios = build_scenarios()

    sim = Simulation(lambda bus: [
        Node(1, main_code, bus),
        Node(2, main_code, bus)
    ])

    for sc in scenarios:
        sim.run(STEPS, sc)


if __name__ == "__main__":
    # run_sim()
    run_faulty()