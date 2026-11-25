import itertools
import json
import math
import os
import sys

import networkx as nx
from networkx.algorithms import approximation as approx

CITIES = {
    "A": (17, 23),
    "B": (0, 11),
    "C": (14, 0),
    "D": (40, 29),
    "E": (28, 20),
    "F": (30, 12),
    "G": (29, 15),
}


def build():
    G = nx.Graph()
    for u, v in itertools.combinations(CITIES, 2):
        G.add_edge(u, v, weight=round(math.hypot(CITIES[u][0] - CITIES[v][0], CITIES[u][1] - CITIES[v][1])))
    return G


def cost(G, tour):
    return sum(G[a][b]["weight"] for a, b in zip(tour, tour[1:]))


def best_tour(G):
    nodes = sorted(G)
    first, rest = nodes[0], nodes[1:]
    best = None
    for perm in itertools.permutations(rest):
        t = [first, *perm, first]
        c = cost(G, t)
        if best is None or c < best[0]:
            best = (c, t)
    return best


def main():
    G = build()
    out = {"label": os.environ.get("LABEL", "local"), "networkx": nx.__version__, "python": sys.version.split()[0]}
    tree = nx.minimum_spanning_tree(G, weight="weight")
    out["mst_edges"] = sorted("".join(sorted(e)) for e in tree.edges)
    out["mst_weight"] = sum(d for _, _, d in tree.edges(data="weight"))
    odd = sorted(v for v, d in tree.degree if d % 2)
    out["odd_vertices"] = odd
    L = G.subgraph(odd).copy()
    try:
        m = nx.min_weight_matching(L, maxcardinality=True, weight="weight")
    except TypeError:
        m = nx.min_weight_matching(L, weight="weight")
    out["min_weight_matching_on_odd"] = sorted("".join(sorted(e)) for e in m)
    out["matching_weight"] = sum(G[a][b]["weight"] for a, b in m)
    out["nx_approximation_attribute_works"] = hasattr(nx, "approximation")
    t = approx.christofides(G, weight="weight")
    out["christofides_tour"] = t
    out["christofides_cost"] = cost(G, t)
    t2 = approx.traveling_salesman_problem(G, weight="weight")
    out["tsp_default_tour"] = t2
    out["tsp_default_cost"] = cost(G, t2)
    c, bt = best_tour(G)
    out["optimal_cost"] = c
    out["optimal_tour"] = bt
    out["weights"] = {
        "".join(sorted((u, v))): d for u, v, d in sorted(G.edges(data="weight"))
    }
    print(json.dumps(out, indent=2))
    with open("tsp_%s.json" % out["label"], "w") as f:
        json.dump(out, f, indent=2)


if __name__ == "__main__":
    main()
