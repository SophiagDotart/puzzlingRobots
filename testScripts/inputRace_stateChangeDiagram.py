import sys, os, random
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import switchingConditions as switchCon


# ---- Parameters ----
NUM_NODES = 20
TIME_STEPS = 50
NUM_INPUTS = 3
RUNS = 1


# ---- Setup ----
def create_nodes(n):
    nodes = [switchCon.Node(i) for i in range(n)]

    for node in nodes:
        node.mode = 0
        node.timestamp = 0
        node.ROOT = False
        node.BUSY = False
        node.IDLE = True

    return nodes


# ---- Topology ----
def connect_limited(nodes, max_neighbors=4):
    edges = []
    neighbor_count = {node: 0 for node in nodes}

    possible_pairs = [
        (nodes[i], nodes[j])
        for i in range(len(nodes))
        for j in range(i + 1, len(nodes))
    ]

    random.shuffle(possible_pairs)

    for a, b in possible_pairs:
        if neighbor_count[a] >= max_neighbors or neighbor_count[b] >= max_neighbors:
            continue

        edges.append((a, b))
        neighbor_count[a] += 1
        neighbor_count[b] += 1

    return edges


# ---- Input schedule ----
def generate_input_schedule():
    times = sorted(random.sample(range(TIME_STEPS), NUM_INPUTS))
    return [(t, i + 1) for i, t in enumerate(times)]


# ---- Simulation ----
def simulate(nodes, edges):
    schedule = generate_input_schedule()

    history = []
    dominance_history = []

    for t in range(TIME_STEPS):

        # ---- inject inputs ----
        active_inputs = []
        for (time, input_id) in schedule:
            if t == time:
                node = random.choice(nodes)

                node.mode = input_id
                node.ROOT = True
                node.BUSY = True
                node.IDLE = False
                node.timestamp = t

                active_inputs.append(input_id)

        random.shuffle(edges)

        # ---- propagation (NO logic changes) ----
        for a, b in edges:
            if a.mode == 0:
                continue

            res = b.processInitMsg(a.timestamp, a.mode, a.ROOT)

            if res == switchCon.RESULT_COMMUNICATIONACCEPTED:
                b.mode = a.mode

        # ---- count modes ----
        counts = {i: 0 for i in range(1, NUM_INPUTS + 1)}

        for n in nodes:
            if n.mode in counts:
                counts[n.mode] += 1

        dominant = max(counts, key=counts.get)

        dominance_history.append(dominant)

        history.append({
            "t": t,
            "counts": counts,
            "dominant": dominant
        })

    return history, schedule, dominance_history


# =========================
# METRICS
# =========================

def compute_metrics(history, schedule, dominance_history):

    metrics = {}

    T = len(history)

    for input_id in range(1, NUM_INPUTS + 1):

        counts = [h["counts"][input_id] for h in history]

        # ---- introduction time ----
        intro_time = next((i for i, v in enumerate(counts) if v > 0), None)

        # ---- disappearance time ----
        disappearance_time = None
        for i in range(len(counts)-1, -1, -1):
            if counts[i] > 0:
                disappearance_time = i
                break

        # ---- time alive ----
        if intro_time is None:
            alive_time = 0
        else:
            alive_time = disappearance_time - intro_time

        # ---- max nodes ----
        max_nodes = max(counts)

        # ---- dominance switch timing ----
        switch_times = [
            i for i in range(1, len(dominance_history))
            if dominance_history[i] != dominance_history[i-1]
            and dominance_history[i] == input_id
        ]

        avg_switch_time = (
            sum(switch_times) / len(switch_times)
            if switch_times else None
        )

        metrics[input_id] = {
            "intro_time": intro_time,
            "disappearance_time": disappearance_time,
            "alive_time": alive_time,
            "max_nodes": max_nodes,
            "avg_dominance_entry_time": avg_switch_time
        }

    return metrics


# =========================
# GRAPH (FIXED X AXIS)
# =========================

def print_vertical_graph(history):
    print("\n=== INPUT PROPAGATION ===\n")

    T = len(history)

    milestone_step = 5

    for input_id in range(1, NUM_INPUTS + 1):

        print(f"Input {input_id}\n")

        values = [h["counts"][input_id] for h in history]

        for y in range(NUM_NODES, 0, -1):
            row = f"{y:3} |"
            for v in values:
                row += " █" if v >= y else "  "
            print(row)

        # ---- milestone x-axis ----
        print("    +" + "──" * T + "> Timesteps")

        label_row = "     "

        for i in range(T):
            if (i + 1) % milestone_step == 0:
                label_row += f"{i+1:2d}"
            else:
                label_row += "  "

            if i < T - 1:
                label_row += " "

        print(label_row)
        print()


# =========================
# STATS PRINT
# =========================

def print_statistics(metrics):

    print("\n--- STATISTICS ---\n")

    for i, m in metrics.items():
        print(f"Input {i}:")
        print(f"  Introduction time:        {m['intro_time']}")
        print(f"  Disappearance time:       {m['disappearance_time']}")
        print(f"  Time alive:               {m['alive_time']}")
        print(f"  Max nodes simultaneously: {m['max_nodes']}")
        print(f"  Avg dominance entry time: {m['avg_dominance_entry_time']}")
        print()


# =========================
# RUNNER
# =========================

def run():
    for r in range(RUNS):

        print("\n==============================")
        print(f"RUN {r + 1}")
        print("==============================\n")

        nodes = create_nodes(NUM_NODES)
        edges = connect_limited(nodes)

        history, schedule, dominance_history = simulate(nodes, edges)

        print_vertical_graph(history)

        metrics = compute_metrics(history, schedule, dominance_history)

        print_statistics(metrics)


if __name__ == "__main__":
    run()