"""Record the raw number each vector store returns for the same query and documents."""
import json, math, time, sys

COS = {"D1": 0.95, "D2": 0.88, "D3": 0.84, "D4": 0.81, "D5": 0.77, "D6": 0.72, "D7": 0.66, "D8": 0.55}
NORM_RAW = {"D1": 1.35, "D2": 0.70, "D3": 1.00, "D4": 0.92, "D5": 1.05, "D6": 0.98, "D7": 1.10, "D8": 1.02}
Q = [1.0, 0.0, 0.0, 0.0]


def vectors(dataset):
    out = {}
    for d, c in COS.items():
        n = 1.0 if dataset == "unit" else NORM_RAW[d]
        out[d] = [n * c, n * math.sqrt(1 - c * c), 0.0, 0.0]
    return out


results = {"versions": {}, "pgvector": {}, "chroma": {}, "qdrant": {}, "elasticsearch": {}}


def run_pgvector():
    import psycopg
    conn = psycopg.connect("postgresql://postgres:postgres@localhost:5432/postgres", autocommit=True)
    cur = conn.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    cur.execute("SELECT extversion FROM pg_extension WHERE extname='vector'")
    results["versions"]["pgvector"] = cur.fetchone()[0]
    for ds in ("unit", "raw"):
        cur.execute(f"DROP TABLE IF EXISTS items_{ds}")
        cur.execute(f"CREATE TABLE items_{ds} (id text, embedding vector(4))")
        for d, v in vectors(ds).items():
            cur.execute(f"INSERT INTO items_{ds} VALUES (%s, %s::vector)", (d, str(v)))
        q = str(Q)
        rows = {}
        for op, name in (("<->", "l2"), ("<#>", "neg_inner_product"), ("<=>", "cosine_distance")):
            cur.execute(f"SELECT id, embedding {op} %s::vector AS v FROM items_{ds} ORDER BY embedding {op} %s::vector", (q, q))
            rows[name] = [[r[0], float(r[1])] for r in cur.fetchall()]
        results["pgvector"][ds] = rows


def run_chroma():
    import chromadb
    results["versions"]["chromadb"] = chromadb.__version__
    client = chromadb.EphemeralClient()
    for ds in ("unit", "raw"):
        vs = vectors(ds)
        rows = {}
        for space in ("default", "l2", "cosine", "ip"):
            meta = None if space == "default" else {"hnsw:space": space}
            col = client.create_collection(name=f"c_{ds}_{space}", metadata=meta)
            col.add(ids=list(vs), embeddings=list(vs.values()))
            r = col.query(query_embeddings=[Q], n_results=len(vs))
            rows[space] = [[i, float(x)] for i, x in zip(r["ids"][0], r["distances"][0])]
        results["chroma"][ds] = rows


def run_qdrant():
    import qdrant_client
    from qdrant_client import QdrantClient, models
    from importlib.metadata import version
    results["versions"]["qdrant-client"] = version("qdrant-client")
    c = QdrantClient(url="http://localhost:6333")
    try:
        import requests
        results["versions"]["qdrant-server"] = requests.get("http://localhost:6333").json().get("version", "unknown")
    except Exception:
        results["versions"]["qdrant-server"] = "unknown"
    for ds in ("unit", "raw"):
        vs = vectors(ds)
        rows = {}
        for dist in ("Cosine", "Dot", "Euclid"):
            name = f"q_{ds}_{dist}"
            if c.collection_exists(name):
                c.delete_collection(name)
            c.create_collection(name, vectors_config=models.VectorParams(size=4, distance=getattr(models.Distance, dist.upper())))
            c.upsert(name, points=[models.PointStruct(id=i + 1, vector=v, payload={"doc": d}) for i, (d, v) in enumerate(vs.items())], wait=True)
            hits = c.query_points(name, query=Q, limit=len(vs), with_payload=True).points
            rows[dist] = [[h.payload["doc"], float(h.score)] for h in hits]
        results["qdrant"][ds] = rows


def run_es():
    import requests
    base = "http://localhost:9200"
    results["versions"]["elasticsearch"] = requests.get(base).json()["version"]["number"]
    for ds in ("unit", "raw"):
        vs = vectors(ds)
        rows = {}
        sims = ("cosine", "l2_norm", "max_inner_product") + (("dot_product",) if ds == "unit" else ())
        for sim in sims:
            idx = f"e_{ds}_{sim}"
            requests.delete(f"{base}/{idx}")
            r = requests.put(f"{base}/{idx}", json={"mappings": {"properties": {
                "doc": {"type": "keyword"},
                "v": {"type": "dense_vector", "dims": 4, "index": True, "similarity": sim,
                      "index_options": {"type": "hnsw"}}}}})
            r.raise_for_status()
            for d, v in vs.items():
                requests.put(f"{base}/{idx}/_doc/{d}", json={"doc": d, "v": v}).raise_for_status()
            requests.post(f"{base}/{idx}/_refresh")
            res = requests.post(f"{base}/{idx}/_search", json={"knn": {"field": "v", "query_vector": Q, "k": len(vs), "num_candidates": 100}, "size": len(vs)}).json()
            rows[sim] = [[h["_source"]["doc"], float(h["_score"])] for h in res["hits"]["hits"]]
        results["elasticsearch"][ds] = rows


for fn in (run_pgvector, run_chroma, run_qdrant, run_es):
    try:
        fn()
    except Exception as e:  # keep going so one failure doesn't hide the rest
        results.setdefault("errors", {})[fn.__name__] = repr(e)

json.dump(results, open("vec_results.json", "w"), indent=2)

# Human-readable summary
lines = ["# Vector-store raw scores", "", "Versions: " + ", ".join(f"{k} {v}" for k, v in results["versions"].items()), ""]
for store in ("pgvector", "chroma", "qdrant", "elasticsearch"):
    for ds, metrics in results.get(store, {}).items():
        for m, rows in metrics.items():
            lines.append(f"- {store} | {ds} | {m} | " + " ; ".join(f"{d} {x:.6f}" for d, x in rows))
if "errors" in results:
    lines += ["", "Errors: " + json.dumps(results["errors"])]
open("SUMMARY.md", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
