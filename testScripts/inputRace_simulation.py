import sys, os, random
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import switchingConditions as switchCon
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import matplotlib.colors as mc
import matplotlib.patches as mpatches
import numpy as np
import networkx as nx


# =========================
# PARAMETERS
# =========================

NUM_NODES = 1000
TIME_STEPS = 500
NUM_INPUTS = 10
RUNS = 100

# =========================
# SIMULATE REAL-LIFE USAGE
# =========================

def create_nodes(n):
    nodes = [switchCon.Node(i) for i in range(n)]

    for node in nodes:
        node.mode = 0
        node.timestamp = 0
        node.ROOT = False
        node.BUSY = False
        node.nodeIDLE = True

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

def generate_positions(nodes):
    return {
        node.nodeID: (random.uniform(0, 1), random.uniform(0, 1))
        for node in nodes
    }

def lighten_color(color, amount=0.5):
    try:
        c = mc.cnames[color]
    except:
        c = color
    c = mc.to_rgb(c)
    return tuple(1 - amount * (1 - x) for x in c)

# =========================
# METRICS
# =========================

def compute_metrics(state_matrix, schedule):

    metrics = {}
    T = len(state_matrix)
    for (intro_time, mode) in schedule:
        metrics[mode] = {
            "introduced": intro_time,
            "disappeared": None,
            "lifespan": 0,
            "max_nodes": 0,
            "max_percent": 0,
            "history": [],
            "domination_periods": [],
            "steps_to_domination": None
        }

    for t, snapshot in enumerate(state_matrix):
        counts = {}
        for mode in snapshot:
            if mode != 0:
                counts[mode] = counts.get(mode, 0) + 1
        #get metrics
        for input_id in metrics:
            count = counts.get(input_id, 0)
            metrics[input_id]["history"].append(count)
            if count > 0:
                metrics[input_id]["lifespan"] += 1
                metrics[input_id]["max_nodes"] = max(
                    metrics[input_id]["max_nodes"],
                    count)
            elif (
                metrics[input_id]["disappeared"] is None and t > metrics[input_id]["introduced"]):
                    metrics[input_id]["disappeared"] = t
    # Compute derived values
    for input_id in metrics:
        m = metrics[input_id]
        if m["disappeared"] is None:
            m["disappeared"] = T

        history = m["history"]
        m["max_percent"] = max(history) / NUM_NODES
        # find dominant periods
        periods = []
        inside = False
        for t, value in enumerate(history):
            if value == NUM_NODES and not inside:
                start = t
                inside = True
            elif value < NUM_NODES and inside:
                periods.append((start, t-1))
                inside = False
        if inside:
            periods.append((start, len(history)-1))
        m["domination_periods"] = periods
        # get steps from introduction to dominance (only if node was successful)
        if periods:
            first_dom = periods[0][0]
            m["steps_to_domination"] = (
                first_dom - m["introduced"]
            )
        else: None

    return metrics

def print_metrics_table(metrics): # skvbhiasfhbvgai a new category: avg time from introduction to dominance
    print("\n--- INPUT METRICS ---")
    print(f"{'Input':<8}{'Intro':<8}{'End':<8}{'Life':<8}{'MaxNodes':<10}{'Steps2Dom':<10}")
    print("-" * 60)
    steps = "-"
    
    for i in sorted(metrics.keys()):
        m = metrics[i]
        if m["steps_to_domination"] is None:
            steps = "-"
        else:
            steps = m["steps_to_domination"]
        print(f"{i:<8}{m['introduced']:<8}{m['disappeared']:<8}{m['lifespan']:<8}{m['max_nodes']:<10}{steps:<10}")

    avgSteps = averageDominationSteps(metrics)
    print(f"Avg. steps from introduction to domination : {avgSteps}")



def print_metrics_allRuns(avgDomSteps, onlyFirstInputDom, cases, rootCount):
    print(f"\n========== AVG METRICS OVER ALL RUNS  ==========")
    print(f"Runs: {RUNS}, Nodes: {NUM_NODES}, Modes: {NUM_INPUTS}")
    print()

    print_caseSummary_allRuns(cases, avgDomSteps, onlyFirstInputDom)
    if len(rootCount) == 0:
        print("Avg. total ROOTs : -")
    else:
        overallROOTs = sum(rootCount) / len(rootCount)
        print(f"Avg. total ROOTs: {overallROOTs:.2f}")
    print()




def getSpecialCases(metrics):
    cases = {
        "failedProp" :0,
        "delayedTakeover" :0,
        "limitedProp" :0,
        "successProp" :0,
        "softRev": 0,
        "rev" : 0, 
        "limitedPropRate": [],
        "maxCoverageRate": 0,
        "peakCoverageTotal": [],
    }
    for mode in range(1, NUM_INPUTS + 1):
        m = metrics[mode]
        cases["peakCoverageTotal"].append( m["max_nodes"]/NUM_NODES)
        if m["max_nodes"] == 0:
            cases['failedProp'] += 1
            continue
        elif m["max_nodes"] < NUM_NODES:
            cases['limitedProp'] += 1
            cases["limitedPropRate"].append(m["max_nodes"]/NUM_NODES)
            continue
        elif m["max_nodes"] == NUM_NODES:
            cases['successProp'] += 1
            # special cases: delayed prop
            if getMaxInfectedNodesDuringInterval(mode, metrics, 0, 0.05) <= 0.1:
                cases['delayedTakeover'] += 1
                continue
            # special cases: revival
            periods = m["domination_periods"]
            if len(periods) >= 2: 
                first_end = periods[0][1]
                second_start = periods[1][0]
                gap = m["history"][first_end+1:second_start]
                if len(gap):
                    if min(gap) < 0.5 * NUM_NODES:
                        cases["rev"] += 1
                    else:
                        cases["softRev"] += 1
        else:
            continue
    return cases

def print_specialCases_summary(cases):
    print(f"\n--- CASES SUMMARY: {NUM_INPUTS} modes ---")
    print()
    print(f"Failed introduction : {cases['failedProp']}")
    print(f"Limited propagation: {cases['limitedProp']}")
    print(f"Successful propagation: {cases['successProp']}")
    
    print(f"Soft revivals      : {cases['softRev']}")
    print(f"Revivals           : {cases['rev']}")
    print(f"Delayed Takeover: {cases['delayedTakeover']}")

    if len(cases["limitedPropRate"]) == 0:
        print("Avg. max unsuccessful coverage: -")
    else:
        avg = sum(cases["limitedPropRate"]) / len(cases["limitedPropRate"])
        print(f"Avg. max unsuccessful coverage: {100*avg:.1f}%")

def print_caseSummary_allRuns(cases, avgDomSteps, onlyFirstInputDom):
    total_failedProp = 0
    total_limitedProp = 0
    total_successProp = 0
    total_softRevs = 0
    total_revs = 0
    total_delayedTakeover = 0

    limitedPropRateSum = 0
    limitedPropRateCount = 0
    highestCoverage = 0
    allPeaks = []

    coverageHistogram = {
        "<10%": 0,
        "10-25%": 0,
        "25-50%": 0,
        "50-75%": 0,
        "75-99%": 0,
    }

    for r in range(RUNS):
        total_failedProp += cases[r]["failedProp"]
        total_limitedProp += cases[r]["limitedProp"]
        total_successProp += cases[r]["successProp"]
        total_softRevs += cases[r]["softRev"]
        total_revs += cases[r]["rev"]
        total_delayedTakeover += cases[r]["delayedTakeover"]
        limitedPropRateSum += sum(cases[r]["limitedPropRate"])
        limitedPropRateCount += len(cases[r]["limitedPropRate"])
        if len(cases[r]["limitedPropRate"]):
            highestCoverage = max(
                highestCoverage,
                max(cases[r]["limitedPropRate"])
            )
            allPeaks.extend(cases[r]["peakCoverageTotal"])
        coverageHistogram = createCoverageHistogram(cases[r], coverageHistogram)
    print()

    print("Propagation statistics")
    print(f"Avg. Successful propagation: {total_successProp/RUNS}")
    print(f"Avg. Limited propagation: {total_limitedProp/RUNS}")
    print(f"Avg. Failed introduction : {total_failedProp/RUNS}")
    print()

    print("Special cases")
    print(f"Total Soft revivals      : {total_softRevs}")
    print(f"Total Revivals           : {total_revs}")
    print(f"Total Delayed Takeover   : {total_delayedTakeover}")
    print()

    print("Metrics: Successful takeovers")
    successRateIgnoreFailedIntros = total_successProp/ ((NUM_INPUTS*RUNS) - (total_failedProp))
    print(f"Input take over success rate: {100* total_successProp/(NUM_INPUTS * RUNS)} %")
    print(f"Input takeover success rate without failed propagation cases: {100*successRateIgnoreFailedIntros:.1f} %")
    print(f"Percentage of runs where only Input 1 dominated: {(onlyFirstInputDom/RUNS)*100} %")
    if len(avgDomSteps) == 0:
        print("Avg. steps from introduction to domination : -")
    else:
        overall = sum(avgDomSteps) / len(avgDomSteps)
        print(f"Avg. steps from introduction to domination : {overall:.2f}")
    # print(coverageHistogram)
    print()

    print("Metrics: Unsuccessful takeovers")
    if limitedPropRateCount == 0:
        print("Avg. maximum unsuccessful coverage: -")
    else:
        avgCoverage = limitedPropRateSum / limitedPropRateCount
        print(f"Avg. maximum unsuccessful coverage: {100*avgCoverage:.1f}%")
    print(f"Maximum coverage of unsuccessful takeover: {100*highestCoverage:.1f}%")
    print()

    print("Metrics: Additional Data")
    if allPeaks:
        avgPeak = sum(allPeaks) / len(allPeaks)
        print(f"Average peak coverage of all inputs: {100*avgPeak:.1f}%")
    

def analyze_topology(nodes, edges):
    G = nx.Graph()
    for node in nodes:
        G.add_node(node.nodeID)
    for a, b in edges:
        G.add_edge(a.nodeID, b.nodeID)

    degree = nx.degree_centrality(G)
    centrality = nx.betweenness_centrality(G)

    print("\n--- TOPOLOGY ANALYSIS ---")
    for n in G.nodes:
        print(f"Node {n}: degree={degree[n]:.2f}, centrality={centrality[n]:.2f}")

# Helpers
def getLifetime(input, metrics):
    m = metrics[input]
    return m["history"][m["introduced"]:m["disappeared"]]

def getMaxInfectedNodesDuringInterval(mode, metrics, startFraction, endFraction):
    history = getLifetime(mode, metrics)
    if len(history) == 0:
        return 0
    start = int(startFraction * len(history))
    end = max(start + 1, int(endFraction * len(history)))
    return max(history[start:end]) / NUM_NODES

def getMinInfectedNodesDuringInterval(mode, metrics, startFraction, endFraction):
    history = getLifetime(mode, metrics)
    if len(history) == 0:
        return 0
    start = int(startFraction * len(history))
    end = max(start + 1, int(endFraction * len(history)))
    return min(history[start:end]) / NUM_NODES

def averageDominationSteps(metrics):
    values = []
    for m in metrics.values():
        if m["steps_to_domination"] is not None:
            values.append(m["steps_to_domination"])
    if not values:
        return None
    return sum(values)/len(values)

def createCoverageHistogram(runCases, coverageHistogram):
    for coverage in runCases["limitedPropRate"]:
        if coverage < 0.10:
            coverageHistogram["<10%"] += 1
        elif coverage < 0.25:
            coverageHistogram["10-25%"] += 1
        elif coverage < 0.50:
            coverageHistogram["25-50%"] += 1
        elif coverage < 0.75:
            coverageHistogram["50-75%"] += 1
        else:
            coverageHistogram["75-99%"] += 1
    return coverageHistogram

# =========================
# SIMULATION CORE
# =========================

def simulate(nodes, edges, schedule):

    #print("Schedule:", schedule)

    state_matrix = []
    dominance = []
    input_origins = {}
    transmissions = []
    rootCount = 0

    for t in range(TIME_STEPS):

        # ---- inject inputs ----
        for (time, mode) in schedule:
            if t == time:
                empty_nodes = [n for n in nodes if n.mode == 0]

                if empty_nodes:
                    node = random.choice(empty_nodes)
                else:
                    node = random.choice(nodes)

                node.mode = mode
                node.ROOT = True
                node.timestamp = t
                input_origins[mode] = node.nodeID

        # ---- communication ----
        for current_node in nodes:
            if current_node.ROOT == True:
                rootCount += 1

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
                transmissions.append((t, sender.nodeID, receiver.nodeID, sender.mode))

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

    return state_matrix, dominance, input_origins, transmissions, rootCount

# =========================
# PLOTS
# =========================

def plot_stacked(state_matrix, schedule, run_nodeID):

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
    plt.title(f"Run {run_nodeID} - Relative Control")
    plt.xlabel("Time")
    plt.ylabel("Fraction")
    plt.legend()

def plot_dominance(state_matrix, schedule, run_nodeID):

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

    plt.title(f"Run {run_nodeID} - Dominance Strength")
    plt.xlabel("Time")
    plt.ylabel("Dominance")

def plot_heatmap(state_matrix, schedule, run_nodeID):

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
    plt.title(f"Run {run_nodeID} - Heatmap")
    plt.xlabel("Time")
    plt.ylabel("Node nodeID")

def plot_topology(nodes, edges, run_nodeID, input_origins, pos):

    G = nx.Graph()

    for node in nodes:
        G.add_node(node.nodeID, mode=node.mode)

    for a, b in edges:
        G.add_edge(a.nodeID, b.nodeID)

    plt.figure(figsize=(6,6))

    node_colors = [G.nodes[n]['mode'] for n in G.nodes]
    cmap = plt.cm.get_cmap("tab20", NUM_INPUTS + 1)

    for mode, node_nodeID in input_origins.items():
        nx.draw_networkx_nodes(
            G, pos,
            nodelist=[node_nodeID],
            node_color="yellow",
            node_size=900,
            edgecolors="black"
        )

    plt.title(f"Run {run_nodeID} - Topology + Input Origins")
    plt.tight_layout() 

def plot_topology_snapshot(state_matrix, edges, transmissions, input_origins, schedule, t, run_nodeID, pos):

    G = nx.Graph()

    num_nodes = len(state_matrix[0])

    for i in range(num_nodes):
        G.add_node(i, mode=state_matrix[t][i])

    for a, b in edges:
        G.add_edge(a.nodeID, b.nodeID)

    plt.figure(figsize=(7,7))

    cmap = plt.cm.get_cmap("tab20", NUM_INPUTS + 1)

    node_colors = []
    node_borders = []

    for n in G.nodes:
        mode = G.nodes[n]['mode']

        if mode == 0:
            node_colors.append("white")
            node_borders.append("black")
        else:
            base_color = cmap(mode)

            # ORIGIN NODE (strong color)
            if mode in input_origins and input_origins[mode] == n:
                node_colors.append(base_color)
                node_borders.append("black")
            else:
                # INFECTED NODE (lighter fill, colored border)
                node_colors.append(lighten_color(base_color, 0.6))
                node_borders.append(base_color)

    # ---- DRAW NODES ----
    nx.draw_networkx_nodes(
        G, pos,
        node_color=node_colors,
        edgecolors=node_borders,
        node_size=600,
        linewnodeIDths=1.5
    )

    nx.draw_networkx_labels(G, pos)

    # ---- EDGES ----
    nx.draw_networkx_edges(G, pos, edge_color="lightgray")

    active_edges = [
        (s, r) for (time, s, r, _) in transmissions if time <= t
    ]

    nx.draw_networkx_edges(
        G, pos,
        edgelist=active_edges,
        edge_color="red",
        wnodeIDth=2
    )

    # ---- LEGEND ----
    import matplotlib.patches as mpatches

    legend_elements = [
        mpatches.Patch(facecolor="white", edgecolor="black", label="Uninfected node"),
        mpatches.Patch(facecolor="gray", edgecolor="gray", label="Infected node (generic)"),
        mpatches.Patch(facecolor="gray", edgecolor="black", label="Origin node"),
        mpatches.Patch(facecolor="none", edgecolor="red", label="Transmission path")
    ]

    plt.legend(handles=legend_elements, loc="upper right", fontsize=8)

    # ---- TITLE ----
    plt.title(f"Run {run_nodeID} — Spread at timestep t = {t}")

    plt.tight_layout()

# =========================
# RUNNER
# =========================
def run():
    metrics = None
    specialCases = None
    onlyFirstInputDom = 0
    caseCount = []
    avgDomStep = []
    avgTotalROOTCount = []
    for r in range(RUNS):
        print(f"\n=== RUN {r+1} ===")

        nodes = create_nodes(NUM_NODES)
        edges = connect_limited(nodes)
        schedule = generate_input_schedule()
        pos = generate_positions(nodes)

        state_matrix, _, input_origins, transmissions, rootCount = simulate(nodes, edges, schedule)

        #plot_stacked(state_matrix, schedule, r+1)
        #plot_dominance(state_matrix, schedule, r+1)
        #plot_heatmap(state_matrix, schedule, r+1)
        # plot_topology(nodes, edges, r+1, input_origins, pos)

        # snapshot_times = [t for (t, _) in schedule]
        #for t in snapshot_times:
        #    plot_topology_snapshot(state_matrix, edges, transmissions, input_origins, schedule, t, r+1, pos)

        metrics = compute_metrics(state_matrix, schedule)
        avg = averageDominationSteps(metrics)
        if avg is not None:
            avgDomStep.append(avg)
        specialCases = getSpecialCases(metrics)
        caseCount.append(specialCases)

        #print_metrics_table(metrics)
        #print_specialCases_summary(specialCases)

        # check if only first input was able to dominate
        if metrics[1]["max_nodes"] == NUM_NODES and specialCases["successProp"] == 1:
            onlyFirstInputDom += 1

        #analyze_topology(nodes, edges)

        print(f"Total amount of ROOTs during run: {rootCount}")
        avgTotalROOTCount.append(rootCount)




    #plt.show()
    print_metrics_allRuns(avgDomStep, onlyFirstInputDom, caseCount, avgTotalROOTCount)


if __name__ == "__main__":
    run()