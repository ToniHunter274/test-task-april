import itertools
import json
import math
import os
import sys

import networkx as nx
import numpy as np
import scipy
from networkx.algorithms import approximation as approx
from scipy.sparse.csgraph import shortest_path

REGIONS = {
    "north": {"A": (17, 23), "B": (0, 11), "C": (14, 0), "D": (40, 29), "E": (28, 20), "F": (30, 12), "G": (29, 15)},
    "west": {"H": (19, 6), "I": (19, 3), "J": (30, 11), "K": (16, 35), "L": (13, 8), "M": (2, 43)},
    "south": {"N": (11, 45), "O": (28, 40), "P": (29, 45), "Q": (34, 8), "R": (35, 30), "S": (16, 34), "T": (5, 41)},
    "east": {"U": (6, 8), "V": (32, 1), "W": (31, 28), "X": (16, 20), "Y": (18, 13), "Z": (18, 25)},
}
LINKS = [(1, 2, 4), (1, 3, 0), (2, 3, 3), (3, 4, 6), (4, 5, 2), (2, 4, 5), (5, 6, 0), (6, 4, 1), (2, 1, 2), (7, 7, 1)]


def build(stops):
    G = nx.Graph()
    names = sorted(stops)
    G.add_nodes_from(names)
    for u, v in itertools.combinations(names, 2):
        (x1, y1), (x2, y2) = stops[u], stops[v]
        G.add_edge(u, v, weight=round(math.hypot(x1 - x2, y1 - y2)))
    return G


def cost(G, tour):
    return sum(G[a][b]["weight"] for a, b in zip(tour, tour[1:]))


def shortest_loop(G):
    nodes = sorted(G)
    first, rest = nodes[0], nodes[1:]
    return min(cost(G, [first, *p, first]) for p in itertools.permutations(rest))


def main():
    label = os.environ.get("LABEL", "local")
    out = {"label": label, "python": sys.version.split()[0], "networkx": nx.__version__,
           "scipy": scipy.__version__, "regions": {}}
    for name, stops in REGIONS.items():
        G = build(stops)
        tour = approx.traveling_salesman_problem(G)
        out["regions"][name] = {"loop": "-".join(tour), "length": cost(G, tour), "shortest": shortest_loop(G)}
    M = np.zeros((7, 7))
    for u, v, w in LINKS:
        M[u - 1, v - 1] = w
    D = shortest_path(M)
    out["transfer_from_yard1"] = {str(j + 1): (None if math.isinf(D[0, j]) else float(D[0, j])) for j in range(7)}
    print(json.dumps(out, indent=2))
    with open("fleet_%s.json" % label, "w") as f:
        json.dump(out, f, indent=2)


if __name__ == "__main__":
    main()
