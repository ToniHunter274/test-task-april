"""Archive IERS bulletins and compute UT1-UTC ground truth for the leap-second / DUT1 task.

Downloads a fixed Bulletin A issue (Vol. XXXIX No. 047, 19 Nov 2026) plus the latest
Bulletin A, C and D files, and the IERS finals2000A series; parses the printed
UT1-UTC prediction formula and table; evaluates the formula (IERS convention:
T = 2000.0 + (MJD - 51544.03)/365.2422 Besselian years); and finds threshold crossings.
"""
import datetime as dt, json, math, os, re, sys, urllib.request

OUT = sys.argv[1] if len(sys.argv) > 1 else "results"
RAW = os.path.join(OUT, "raw"); os.makedirs(RAW, exist_ok=True)
URLS = {
    "bulletinA_047.txt": "https://datacenter.iers.org/data/6/bulletina-xxxix-047.txt",
    "ser7_latest.dat": "https://maia.usno.navy.mil/ser7/ser7.dat",
    "bulletinC_072.txt": "https://hpiers.obspm.fr/iers/bul/bulc/bulletinc.72",
    "bulletinD_latest.dat": "https://hpiers.obspm.fr/iers/bul/buld/bulletind.dat",
    "leap-seconds.list": "https://hpiers.obspm.fr/iers/bul/bulc/ntp/leap-seconds.list",
    "finals2000A.data": "https://maia.usno.navy.mil/ser7/finals2000A.data",
}
log = {}
for name, url in URLS.items():
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=60).read()
        open(os.path.join(RAW, name), "wb").write(data)
        log[name] = {"url": url, "bytes": len(data), "ok": True}
    except Exception as e:
        log[name] = {"url": url, "ok": False, "error": repr(e)}
print(json.dumps(log, indent=1))

def mjd_to_date(m): return dt.date(1858, 11, 17) + dt.timedelta(days=int(m))
def date_to_mjd(d): return (d - dt.date(1858, 11, 17)).days
def T_bes(m): return 2000.0 + (m - 51544.03) / 365.2422
def ut2ut1(m):
    t = 2 * math.pi * T_bes(m)
    return 0.022 * math.sin(t) - 0.012 * math.cos(t) - 0.006 * math.sin(2 * t) + 0.007 * math.cos(2 * t)

res = {"downloads": log}
txtA = open(os.path.join(RAW, "bulletinA_047.txt"), errors="replace").read() if log["bulletinA_047.txt"]["ok"] else ""
m = re.search(r"UT1-UTC\s*=\s*([-+]?\s*[\d.]+)\s*([-+])\s*([\d.]+)\s*\(MJD\s*-\s*(\d+)\)\s*-\s*\(UT2-UT1\)", txtA)
if m:
    a = float(m.group(1).replace(" ", "")); b = float(m.group(3)) * (1 if m.group(2) == "+" else -1); m0 = int(m.group(4))
    res["formula"] = {"a": a, "b_per_day": b, "mjd_ref": m0, "text": m.group(0)}
    f = lambda mm: a + b * (mm - m0) - ut2ut1(mm)
    # printed prediction table: lines like "2026 11 20   61364   0.1601   0.3751  -0.07655"
    rows = re.findall(r"^\s*(20\d\d)\s+(\d{1,2})\s+(\d{1,2})\s+(\d{5})\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*$", txtA, re.M)
    table = [{"date": f"{y}-{int(mo):02d}-{int(d):02d}", "mjd": int(mj), "x": float(x), "y": float(yy), "ut1_utc": float(u)} for y, mo, d, mj, x, yy, u in rows]
    for r in table: r["formula"] = round(f(r["mjd"]), 5); r["diff"] = round(r["ut1_utc"] - r["formula"], 5)
    res["table"] = table
    start = table[0]["mjd"] if table else m0
    def cross(th):
        for k in range(0, 6000):
            if f(start + k) <= th: return {"threshold": th, "mjd": start + k, "date": str(mjd_to_date(start + k)), "value": round(f(start + k), 4)}
    res["crossings_formula"] = [cross(th) for th in (-0.15, -0.2, -0.25, -0.35, -0.8, -0.85, -0.9)]
    res["formula_at"] = {d: round(f(date_to_mjd(dt.date.fromisoformat(d))), 4) for d in
                         ["2026-11-26", "2026-12-31", "2027-03-27", "2027-05-20", "2027-06-30", "2027-12-31", "2030-01-01", "2035-01-01"]}
txtD = open(os.path.join(RAW, "bulletinD_latest.dat"), errors="replace").read() if log["bulletinD_latest.dat"]["ok"] else ""
res["bulletinD_excerpt"] = txtD[:1500]
txtC = open(os.path.join(RAW, "bulletinC_072.txt"), errors="replace").read() if log["bulletinC_072.txt"]["ok"] else ""
res["bulletinC_excerpt"] = txtC[:1500]
# observed UT1-UTC history from finals2000A (Bulletin A values, cols 59-68; flag col 58 I/P)
hist = []
if log["finals2000A.data"]["ok"]:
    for line in open(os.path.join(RAW, "finals2000A.data"), errors="replace"):
        try:
            mj = float(line[7:15]); flag = line[57]; u = float(line[58:68])
            if int(mj) % 30 == 0 and mj >= 59000: hist.append({"mjd": int(mj), "date": str(mjd_to_date(mj)), "flag": flag, "ut1_utc": u})
        except Exception: pass
res["finals_monthly"] = hist
json.dump(res, open(os.path.join(OUT, "iers_results.json"), "w"), indent=1)
L = ["# IERS ground truth", "", "## Downloads", ""] + [f"- {k}: {'OK ' + str(v['bytes']) + ' bytes' if v['ok'] else 'FAILED ' + v['error']} ({v['url']})" for k, v in log.items()]
if "formula" in res:
    L += ["", "## Bulletin A No. 047 formula", "", "`" + res["formula"]["text"] + "`", "", "| date | MJD | printed UT1-UTC | formula | printed - formula |", "|---|---|---|---|---|"]
    L += [f"| {r['date']} | {r['mjd']} | {r['ut1_utc']} | {r['formula']} | {r['diff']} |" for r in res.get("table", [])]
    L += ["", "## Formula crossings", ""] + [f"- {c}" for c in res["crossings_formula"]] + ["", "## Formula values", ""] + [f"- {k}: {v}" for k, v in res["formula_at"].items()]
L += ["", "## Bulletin D (latest) excerpt", "", "```", txtD[:1200], "```", "", "## Observed UT1-UTC (finals2000A, every 30 MJD)", "", "| date | flag | UT1-UTC |", "|---|---|---|"]
L += [f"| {h['date']} | {h['flag']} | {h['ut1_utc']} |" for h in hist]
open(os.path.join(OUT, "SUMMARY.md"), "w").write("\n".join(L) + "\n")
