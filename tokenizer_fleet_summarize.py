"""Combine versioned fleet CSVs. Preserves all failures, counts and delta flags."""
import csv
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else "fleet-artifacts")
csvs = sorted(root.rglob("fleet-*.csv"))
if not csvs:
    raise SystemExit("no version CSVs found")
rows = []
for path in csvs:
    with path.open(encoding="utf-8", newline="") as f:
        rows.extend(csv.DictReader(f))
output = Path("tokenizer-fleet-matrix.csv")
fields = list(rows[0])
with output.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
all_dir = Path("all-eight-csv")
all_dir.mkdir(exist_ok=True)
for p in csvs:
    shutil.copyfile(p, all_dir / p.name)

versions = sorted({r["matrix_version"] for r in rows})
models = sorted({r["model"] for r in rows})
statuses = Counter(r["status"] for r in rows)
print(f"Version CSV files: {len(csvs)}")
print(f"Versions: {', '.join(versions)}")
print(f"Distinct models: {len(models)}")
print(f"Total rows: {len(rows)}")
print(f"Statuses: {dict(statuses)}")

# Only compare models at a single identical Hub commit across different environments.
by_cell = defaultdict(list)
for r in rows:
    if r["status"] == "ok":
        by_cell[(r["model"], r["raw"])].append(r)
different = []
for key, cell_rows in by_cell.items():
    revs = {r["revision"] for r in cell_rows}
    if len(revs) != 1:
        print(f"REVISION_MISMATCH: {key[0]} (different Hub revisions; exclude from causal comparisons)")
        continue
    vals = {r["decoded_default"] for r in cell_rows}
    if len(vals) > 1:
        different.append((key, cell_rows))
print(f"Model/input pairs with differing default outputs across tested versions: {len(different)}")
for (model, raw), cells in different:
    print(f"CHANGES model={model!r} input={raw!r}")
    for r in sorted(cells, key=lambda x: tuple(map(int,x["matrix_version"].split(".")))):
        print(f"  {r['matrix_version']}: effective={r['effective_cleanup']} config={r['config_value']} class={r['tokenizer_class']} decoded={r['decoded_default']!r}")
print("Rows with errors:")
for ver in versions:
    bad = sorted({r["model"] for r in rows if r["matrix_version"] == ver and r["status"] != "ok"})
    print(f"  {ver}: {len(bad)} failed models" + (" (" + ", ".join(bad) + ")" if bad else ""))
