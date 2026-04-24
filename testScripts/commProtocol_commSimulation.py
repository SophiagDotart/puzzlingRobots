import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import random
import copy
import importlib

from messageBuild import Message
import main as main_code
import errorHandling as err

# VERY IMPORTANT: WHEN DONE TESTING, UNCOMMENT THIS LINE FROM MAIN-> DECODEMSG:
#msg = msgBuild.Message.checkIfCorrectLen(msg) 


# ============================================================
# STATES
# ============================================================
IDLE = "IDLE"
WAIT_ACK_INIT = "WAIT_ACK_INIT"
WAIT_POS_ACK = "WAIT_POS_ACK"
WAIT_FOLLOWUP_ACK = "WAIT_FOLLOWUP_ACK"
DONE = "DONE"

STEPS = 10
MAX_DELAY = 1                   # change it to more than 1 only when testing "TOO MUCH DELAY" scenario
PARITYERRORENABLED = False      # still in development!

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
        #Scenario("PACKET LOSS", packet_loss_fault),
        #Scenario("CORRUPTION", corruptedMsg_fault),
        #Scenario("WRONG ORDER", wrongOrder_fault),
        #Scenario("TOO MUCH DELAY", timeout_fault),
        #Scenario("PARITY ERROR", parityError_fault)  # still in development!
    ]


def no_errors(event):
    return event, "OK"

def packet_loss_fault(event):
    if random.random() < 0.3:
        return None, "DROPPED"
    return event, "OK"

def corruptedMsg_fault(event):
    if not isinstance(event.m, int):
        return event, "CORRUPTED_INVALID_TYPE"
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
            new_event = copy.copy(event)

            # flip parity bits (bits 9–10)
            parity = Message.getSeveralBit(event.m, 9, 2)
            corrupted_parity = (parity + 1) % 4
            print(f"[DEBUG] Corrupted parity: {corrupted_parity}")

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
    def __init__(self, node, bus, sim):
        self.node = node
        self.bus = bus
        self.sim = sim

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
            return self.node.hw_inbox.pop(0)
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
    def __init__(self, nid, logic, bus, sim, initiator):
        self.id = nid
        self.bus = bus
        self.logic = importlib.reload(logic)
        self.hw = SimHW(self, bus, sim)
        self.logic.hw = self.hw
        self.initiatorSIM = initiator
        self.INITDONE = False
        self.POSDONE = False

        self.state, self.goalMapLib = logic.init()
        self.inbox = []

        self.state_name = IDLE
        self.started = False
        self.last_time_from = {}

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
        self.logic.decodeMsg(self.state, self.goalMapLib, msg)

    def fakeSendErrorMsg(errorCode, scriptCode):
        SimHW.sendThroughModule(Message.createErrorMsg(
                                    errorCode,
                                    scriptCode,
                                    None)
                                )
        
    def fakeSendAckMsg(ACK, msgType):
        SimHW.sendThroughModule(Message.createErrorMsg(
                                    ACK,
                                    msgType,
                                    None)
                                )

    def fakeHandleError(self, node, error):
        action = error['action']
        notScriptCode = error['scriptCode']
        notErrorCode = error['errorCode']
        if action == err.ACTION_SENDERRORMSG:
            if notScriptCode is not None and notErrorCode is not None:
                self.fakeSendErrorMsg(notErrorCode, notScriptCode)
                print(f"[FYI] Sent the error to the sender")
            else:
                err.wtfIsHappening()
        elif action == err.ACTION_SENDPLSREPEATMSG:
            if notScriptCode is not None and notErrorCode is not None:
                self.fakeSendAckMsg(False, notScriptCode)
                print(f"[FYI] Sent an ACK msg to the sender to please resend the last msg")
            else:
                err.wtfIsHappening()   
        elif action == err.ACTION_IGNORE:
            print(f"[FYI] I ignored the error.Returning to main")   
        elif action == err.ACTION_SENDINITMSG:
            print(f"[FYI] The normal response to this error would be to send INIT, but I am not implemnting it here unless necessary") 
        elif action == err.ACTION_RESETROBOT:
            print(f"[FYI] Would restart the robot now but this is a simulation so this case does not appear")
        elif action == err.ACTION_CORRECTSTH:
            thatSth = error['actionCode']
            if thatSth == err.ACTION_CORRECTSTH_RESTARTMAP:
                print(f"[FYI] Irl this error would have been corrected")
            elif thatSth == err.ACTION_CORRECTSTH_FIXTILESYMBOL:
                print(f"[FYI] Irl this error would have been corrected")
            elif thatSth == err.ACTION_CORRECTSTH_MESSEDUPFLAGS:
                print(f"[FYI] Irl this error would have been corrected")           
            else:
                err.wtfIsHappening()   
        elif action == err.ACTION_SIGNALTOUSER:
            print(f"[FYI] This should signal sth to user. So here it is: you, the player, made a mistake")
        else:
            err.wtfIsHappening()

    def sendAMsg(self):
        if self.id == 1:
            self.initiatorSIM = True
            peer = 2
        else:
            self.initiatorSIM = False
            peer = 1

        if self.id == 1:
            # INIT
            if self.initiatorSIM and not self.POSDONE and not self.INITDONE:
                print(f"[FYI] NODE {self.id} sends INIT")
                msg = Message.createInitMsg(self.id, False, 0, self.state.timestamp)
                self.send(peer, msg)
                self.state_name = WAIT_ACK_INIT
                self.started = True
                self.state.initiatorSIM = True
                print(f"Node {self.id}'s INIT msg: {msg}")
                return

            # POS
            if self.initiatorSIM and self.INITDONE and not self.POSDONE:
                print(f"[FYI] NODE {self.id} sends POS")
                msg = Message.createPosMsg(True, 0, 0)
                self.send(peer, msg)
                self.POSDONE = True
                print(f"Node {self.id}'s POS msg: {msg}")
                return

            # FOLLOWUP
            if self.initiatorSIM and self.INITDONE and self.POSDONE:
                print(f"[FYI]NODE {self.id} sends FOLLOWUP")
                msg = Message.createFollowUpMsg(0, True, 0)
                if PARITYERRORENABLED:
                    parityCorrect = Message.getSeveralBit(msg, 9, 2)
                    print(f"[DEBUG] Correct parity: {parityCorrect}")
                self.send(peer, msg)
                print(f"Node {self.id}'s FOLLOWUP msg: {msg}")
                return
            
        elif self.id == 2:
            print(f"[DEBUG] Nvm, Im node {self.id} and I am not allowed to send a message.")

    def run_step(self):
        node = self.state
        print(f"[DEBUG] POV Node {self.id}")
        # ---- LISTENING PHASE ----
        msg = None 
        for _ in range(20):
            for module in range(4):
                temp = self.hw.listenThroughModule(module)
                if temp is not None:
                    msg = temp
                    self.logic.decodeMsg(node, self.goalMapLib, msg)
                    break
            if msg is not None:
                break
        
              

        if msg is not None:
            print(f"[DEBUG] msg: {msg}")
            header = Message.getHeader(msg)
            if PARITYERRORENABLED:
                if header == Message.FOLLOWUP_HEADER:
                    print(f"[DEBUG] Node {self.id} received the FOLLOWUP msg")
                    followUpMsg = Message.decodeFOLLOWUPMsg(msg)
                    parity = followUpMsg["parity"]
                    print(f"[DEBUG] Parity: {parity}")
                    if parity is False:
                        self.fakeHandleError(node, err.parityCheckIncorrect())  

            if self.initiatorSIM and self.started: # new only ACK and ERROR allowed
                if header == Message.ACK_HEADER:
                    ackData = Message.decodeACKMsg(msg)
                    ack = ackData["ACK"]
                    ackType = ackData["msgType"]
                    print(f"[DEBUG] ACK Type: {ackType}")            
                    if ackType != None: 
                        if ackType == Message.INIT_HEADER:
                            self.hw.sendThroughModule(
                                Message.createPosMsg(True, 0, 0),
                                node.moduleNumber
                            )
                        elif ackType == Message.POS_HEADER:
                            self.hw.sendThroughModule(
                                Message.createFollowUpMsg(0, True, 0),
                                node.moduleNumber
                            )
                elif header == Message.ERROR_HEADER_HEADER:
                    print(f"[DEBUG] Node {self.id} received an ERROR message")
                    errMsg = Message.decodeERRORMsg(msg)
                    self.fakeHandleError(node, err.decodeErrorMsg(errMsg['errorCode'], errMsg['scriptCode']))
                else:
                    print(f"[DEBUG] That msg is not recognized")
        elif msg is None: 
            # ---- TALKING PHASE ----
            print(f"No message received, so I, node {self.id} (Initiator: {self.initiatorSIM}), will send a message")
            self.sendAMsg()


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

                if bus.time % 2 == 0:
                    for n in nodes:
                        n.run_step()

                bus.tick()

        except Exception as e:
            print(f"[SCENARIO CRASH] {scenario.name}: {e}")

        print(f"\n[SCENARIO END] {scenario.name}\n")


# ============================================================
# RUNNER
# ============================================================
def factory(bus):
    sim = Simulation(None)  # temporary
    nodes = [
        Node(1, main_code, bus, sim, 1),
        Node(2, main_code, bus, sim, 0)
    ]
    sim.nodes = nodes
    return nodes

def run_sim():
    log = EventLog()

    sim = Simulation(factory)

    # inject log into bus inside Simulation
    sim.run(STEPS, scenario=Scenario("NO ERRORS", no_errors))

    print("\n=== EVENT LOG ===") 
    log.dump()

def run_faulty():
    scenarios = build_scenarios()
    sim = Simulation(factory)

    for sc in scenarios:
        sim.run(STEPS, sc)


if __name__ == "__main__":
    # run_sim()
    run_faulty()