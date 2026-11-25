import itertools
import json
import math
import os
import sys

import networkx as nx
from networkx.algorithms import approximation as approx

REGIONS = {
    "north": {"A": (17, 23), "B": (0, 11), "C": (14, 0), "D": (40, 29), "E": (28, 20), "F": (30, 12), "G": (29, 15)},
    "west": {"H": (25, 4), "I": (1, 31), "J": (10, 1), "K": (45, 11), "L": (3, 22), "M": (35, 6)},
    "south": {"N": (11, 45), "O": (28, 40), "P": (29, 45), "Q": (34, 8), "R": (35, 30), "S": (16, 34), "T": (5, 41)},
    "east": {"U": (29, 25.5), "V": (6.5, 37.5), "W": (42.5, 10.5), "X": (10.5, 25.5), "Y": (21, 35.5), "Z": (32.5, 21)},
    "hub": {"1": (23, 23), "2": (45, 41), "3": (6, 20), "4": (26, 34), "5": (5, 33), "6": (20, 39)},
}


def build(stops):
    G = nx.Graph()
    names = list(stops)
    G.add_nodes_from(names)
    for u, v in itertools.combinations(names, 2):
        (x1, y1), (x2, y2) = stops[u], stops[v]
        G.add_edge(u, v, weight=round(math.hypot(x1 - x2, y1 - y2)))
    return G


def driven(stops, tour):
    return sum(math.hypot(stops[a][0] - stops[b][0], stops[a][1] - stops[b][1]) for a, b in zip(tour, tour[1:]))


def cost(G, tour):
    return sum(G[a][b]["weight"] for a, b in zip(tour, tour[1:]))


def shortest_loop(G):
    nodes = sorted(G)
    first, rest = nodes[0], nodes[1:]
    return min(cost(G, [first, *p, first]) for p in itertools.permutations(rest))


def main():
    label = os.environ.get("LABEL", "local")
    out = {"label": label, "python": sys.version.split()[0], "networkx": nx.__version__,
           "regions": {}}
    for name, stops in REGIONS.items():
        G = build(stops)
        tour = approx.traveling_salesman_problem(G)
        out["regions"][name] = {"loop": "-".join(tour), "planner_total": cost(G, tour),
                                "driven_km": round(driven(stops, tour), 2), "shortest_planner": shortest_loop(G)}
    print(json.dumps(out, indent=2))
    with open("fleet_%s.json" % label, "w") as f:
        json.dump(out, f, indent=2)


if __name__ == "__main__":
    main()
