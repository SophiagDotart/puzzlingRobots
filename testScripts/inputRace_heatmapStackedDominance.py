import sys, os, random
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import switchingConditions as switchCon
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import matplotlib.patches as mpatches
import numpy as np


# =========================
# PARAMETERS
# =========================

NUM_NODES = 20
TIME_STEPS = 500
NUM_INPUTS = 12
RUNS = 2


# =========================
# SETUP
# =========================

def create_nodes(n):
    nodes = [switchCon.Node(i) for i in range(n)]

    for node in nodes:
        node.mode = 0
        node.timestamp = 0
        node.ROOT = False
        node.BUSY = False
        node.IDLE = True

    return nodes


def connect_limited(nodes, max_neighbors=4):
    edges = []
    neighbor_count = {node: 0 for node in nodes}

    pairs = [
        (nodes[i], nodes[j])
        for i in range(len(nodes))
        for j in range(i + 1, len(nodes))
    ]

    random.shuffle(pairs)

    for a, b in pairs:
        if neighbor_count[a] >= max_neighbors or neighbor_count[b] >= max_neighbors:
            continue

        edges.append((a, b))
        neighbor_count[a] += 1
        neighbor_count[b] += 1

    return edges


def generate_input_schedule():
    times = sorted(random.sample(range(TIME_STEPS), NUM_INPUTS))
    return [(t, i + 1) for i, t in enumerate(times)]


def generate_colormap(num_inputs):
    base_colors = plt.cm.get_cmap("tab20", num_inputs)

    colors = ["white"]
    for i in range(num_inputs):
        colors.append(base_colors(i))

    return ListedColormap(colors)


def draw_input_markers(schedule):
    for (t, _) in schedule:
        plt.axvline(x=t, linestyle="--", alpha=0.4)


# =========================
# METRICS
# =========================

def compute_metrics(state_matrix, schedule):

    metrics = {}
    T = len(state_matrix)

    for (t, input_id) in schedule:
        metrics[input_id] = {
            "introduced": t,
            "disappeared": None,
            "lifespan": 0,
            "max_nodes": 0,
        }

    for t in range(T):
        snapshot = state_matrix[t]

        counts = {}
        for m in snapshot:
            if m != 0:
                counts[m] = counts.get(m, 0) + 1

        for input_id in metrics:
            if input_id in counts:
                metrics[input_id]["lifespan"] += 1
                metrics[input_id]["max_nodes"] = max(
                    metrics[input_id]["max_nodes"],
                    counts[input_id]
                )
            else:
                if metrics[input_id]["disappeared"] is None and t > metrics[input_id]["introduced"]:
                    metrics[input_id]["disappeared"] = t

    for input_id in metrics:
        if metrics[input_id]["disappeared"] is None:
            metrics[input_id]["disappeared"] = T

    return metrics


def print_metrics_table(metrics):
    print("\n--- INPUT METRICS ---")
    print(f"{'Input':<8}{'Intro':<8}{'End':<8}{'Life':<8}{'MaxNodes':<10}")
    print("-" * 45)

    for i in sorted(metrics.keys()):
        m = metrics[i]
        print(f"{i:<8}{m['introduced']:<8}{m['disappeared']:<8}{m['lifespan']:<8}{m['max_nodes']:<10}")


# =========================
# SIMULATION CORE
# =========================

def simulate(nodes, edges, schedule):

    print("Schedule:", schedule)

    state_matrix = []
    dominance = []

    for t in range(TIME_STEPS):

        # ---- inject inputs properly ----
        for (time, input_id) in schedule:
            if t == time:
                empty_nodes = [n for n in nodes if n.mode == 0]

                if empty_nodes:
                    node = random.choice(empty_nodes)
                else:
                    node = random.choice(nodes)

                node.mode = input_id
                node.ROOT = True
                node.timestamp = t

        # ---- communication ----
        for current_node in nodes:

            neighbors = [b for (a, b) in edges if a == current_node] + \
                        [a for (a, b) in edges if b == current_node]

            if not neighbors:
                continue

            partner = random.choice(neighbors)

            if random.random() < 0.5:
                sender, receiver = current_node, partner
            else:
                sender, receiver = partner, current_node

            if sender.mode == 0:
                continue

            res = receiver.processInitMsg(sender.timestamp, sender.mode, sender.ROOT)

            if res == switchCon.RESULT_COMMUNICATIONACCEPTED:
                receiver.mode = sender.mode
                receiver.timestamp = sender.timestamp

        snapshot = [n.mode for n in nodes]
        state_matrix.append(snapshot)

        # ---- dominance ----
        counts = {}
        for m in snapshot:
            if m != 0:
                counts[m] = counts.get(m, 0) + 1

        if counts:
            dominant = max(counts, key=counts.get)
        else:
            dominant = 0

        dominance.append(dominant)

    return state_matrix, dominance


# =========================
# PLOTS
# =========================

def plot_stacked(state_matrix, schedule, run_id):

    T = len(state_matrix)
    inputs = sorted(set(v for row in state_matrix for v in row if v != 0))

    data = {i: [] for i in inputs}

    for t in range(T):
        counts = {i: 0 for i in inputs}
        total_active = 0

        for v in state_matrix[t]:
            if v in counts:
                counts[v] += 1
                total_active += 1

        for i in inputs:
            data[i].append(counts[i] / total_active if total_active > 0 else 0)

    bottom = [0] * T

    plt.figure()
    for i in inputs:
        plt.bar(range(T), data[i], bottom=bottom, label=f"Input {i}")
        bottom = [bottom[j] + data[i][j] for j in range(T)]

    draw_input_markers(schedule)
    plt.title(f"Run {run_id} - Relative Control")
    plt.xlabel("Time")
    plt.ylabel("Fraction")
    plt.legend()


def plot_dominance(state_matrix, schedule, run_id):

    strength = []

    for snapshot in state_matrix:
        counts = {}
        for m in snapshot:
            if m != 0:
                counts[m] = counts.get(m, 0) + 1

        if counts:
            strength.append(max(counts.values()) / sum(counts.values()))
        else:
            strength.append(0)

    plt.figure()
    plt.plot(strength)
    draw_input_markers(schedule)

    plt.title(f"Run {run_id} - Dominance Strength")
    plt.xlabel("Time")
    plt.ylabel("Dominance")


def plot_heatmap(state_matrix, schedule, run_id):

    N = len(state_matrix[0])
    T = len(state_matrix)

    mat = np.zeros((N, T))

    for t in range(T):
        for n in range(N):
            mat[n][t] = state_matrix[t][n]

    plt.figure()
    cmap = generate_colormap(NUM_INPUTS)
    plt.imshow(mat, aspect="auto", cmap=cmap, interpolation="nearest")

    draw_input_markers(schedule)
    plt.title(f"Run {run_id} - Heatmap")
    plt.xlabel("Time")
    plt.ylabel("Node ID")


# =========================
# RUNNER
# =========================

def run():
    for r in range(RUNS):

        print(f"\n=== RUN {r+1} ===")

        nodes = create_nodes(NUM_NODES)
        edges = connect_limited(nodes)
        schedule = generate_input_schedule()

        state_matrix, _ = simulate(nodes, edges, schedule)

        plot_stacked(state_matrix, schedule, r+1)
        plot_dominance(state_matrix, schedule, r+1)
        plot_heatmap(state_matrix, schedule, r+1)

        metrics = compute_metrics(state_matrix, schedule)
        print_metrics_table(metrics)

    plt.show()


if __name__ == "__main__":
    run()