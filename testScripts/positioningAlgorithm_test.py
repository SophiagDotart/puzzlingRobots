import sys, os, random
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import mapFunctions as mapFunc


class SimNode:
    def __init__(self, node_id):
        self.id = node_id
        self.pos = None
        self.neighbors = []

    def receive_position(self, sender_pos, orientation):
        newX, newY = mapFunc.Map.getOwnPos(
            sender_pos[0], sender_pos[1],
            orientation[0], orientation[1]
        )

        if self.pos is None:
            self.pos = (newX, newY)
            return True
        elif self.pos != (newX, newY):
            print(f"[CONFLICT] Node {self.id}: {self.pos} vs {(newX,newY)}")
            return False
        return True


# ---- Simulation ----
def simulate(nodes, steps=30):
    if nodes[0].pos is None:
        nodes[0].pos = (0, 0)

    for _ in range(steps):
        messages = []

        for node in nodes:
            if node.pos is not None:
                for neighbor, orientation in node.neighbors:
                    messages.append((neighbor, node.pos, orientation))

        random.shuffle(messages)

        for receiver, sender_pos, orientation in messages:
            if not receiver.receive_position(sender_pos, orientation):
                return False

    return True


# ---- Pretty printing ----
def print_node_positions(nodes):
    print("Final Node Positions:")
    for node in nodes:
        print(f"  Node {node.id}: {node.pos}")
    print()


def print_map(nodes):
    coords = [n.pos for n in nodes if n.pos is not None]
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    grid = {}
    for node in nodes:
        if node.pos:
            grid[node.pos] = str(node.id)

    print("Map Representation:")
    for y in range(max_y, min_y - 1, -1):
        row = ""
        for x in range(min_x, max_x + 1):
            row += grid.get((x, y), ".").rjust(3)
        print(row)
    print()


# ---- Scenario runner ----
def run_scenario(name, builder, n=5, runs=5):
    successes = 0
    example_nodes = None
    failed_example = None

    for _ in range(runs):
        nodes = builder(n)
        result = simulate(nodes)

        if result:
            successes += 1
            if example_nodes is None:
                example_nodes = nodes
        else:
            if failed_example is None:
                failed_example = nodes

    success_rate = (successes / runs) * 100

    print(f"=== {name} ({n} Nodes) ===")
    print(f"Runs: {runs}")
    print(f"Success: {successes}")
    print(f"Failure: {runs - successes}")
    print(f"Success Rate: {success_rate:.1f}%")
    print()

    if example_nodes:
        print("[SUCCESSFUL RUN]")
        print_node_positions(example_nodes)
        print_map(example_nodes)

    if failed_example:
        print("[FAILED RUN]")
        print_node_positions(failed_example)
        print_map(failed_example)


# ---- Topologies ----

def build_chain(n):
    nodes = [SimNode(i) for i in range(n)]
    for i in range(n - 1):
        nodes[i].neighbors.append((nodes[i+1], (1,0)))
        nodes[i+1].neighbors.append((nodes[i], (-1,0)))
    return nodes


def build_loop(n):
    nodes = [SimNode(i) for i in range(n)]

    # create rectangle dimensions
    width = max(2, n // 4)
    height = max(2, n // width)

    coords = []
    # bottom row →
    for x in range(width):
        coords.append((x, 0))
    # right column ↑
    for y in range(1, height):
        coords.append((width-1, y))
    # top row ←
    for x in range(width-2, -1, -1):
        coords.append((x, height-1))
    # left column ↓
    for y in range(height-2, 0, -1):
        coords.append((0, y))

    # trim or extend to n nodes
    coords = coords[:n]

    # connect nodes based on coordinates
    pos_to_node = {coords[i]: nodes[i] for i in range(len(coords))}

    directions = [(1,0), (-1,0), (0,1), (0,-1)]

    for (x,y), node in pos_to_node.items():
        for dx,dy in directions:
            neighbor_pos = (x+dx, y+dy)
            if neighbor_pos in pos_to_node:
                neighbor = pos_to_node[neighbor_pos]
                node.neighbors.append((neighbor, (dx,dy)))

    return nodes


def build_L_shape(n):
    nodes = [SimNode(i) for i in range(n)]

    # split into horizontal + vertical
    split = n // 2

    for i in range(split - 1):
        nodes[i].neighbors.append((nodes[i+1], (1,0)))
        nodes[i+1].neighbors.append((nodes[i], (-1,0)))

    for i in range(split - 1, n - 1):
        nodes[i].neighbors.append((nodes[i+1], (0,1)))
        nodes[i+1].neighbors.append((nodes[i], (0,-1)))

    return nodes


def build_dual_root_plus(n):
    nodes = [SimNode(i) for i in range(n)]

    # two fixed roots
    nodes[0].pos = (0, 0)
    nodes[1].pos = (2, 0)

    # connect others in + shape around them
    center_nodes = [0, 1]
    directions = [(1,0), (-1,0), (0,1), (0,-1)]

    idx = 2
    for center in center_nodes:
        for dx,dy in directions:
            if idx >= n:
                break
            nodes[center].neighbors.append((nodes[idx], (dx,dy)))
            nodes[idx].neighbors.append((nodes[center], (-dx,-dy)))
            idx += 1

    return nodes

def build_broken_loop(n):
    nodes = [SimNode(i) for i in range(n)]

    for i in range(n):
        next_i = (i + 1) % n
        nodes[i].neighbors.append((nodes[next_i], (1,0)))
        nodes[next_i].neighbors.append((nodes[i], (-1,0)))

    return nodes

# ---- Main ----
if __name__ == "__main__":
    print()
    print("=== Positioning Simulation Results ===\n")

    NODE_COUNT = 16  # current max: 16
    print(f"{NODE_COUNT} nodes")
    print()

    run_scenario("Chain", build_chain, NODE_COUNT)
    print()
    run_scenario("L-Shape", build_L_shape, NODE_COUNT)
    print()
    run_scenario("Loop", build_loop, NODE_COUNT)
    print()
    run_scenario("Dual Root", build_dual_root_plus, NODE_COUNT)
    print()
    run_scenario("Broken Loop (Conflict Expected)", build_broken_loop, NODE_COUNT)
    print()
