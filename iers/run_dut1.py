"""DUT1 practice check: fetch IERS Bulletin D issues, parse effective date and DUT1,
and compare with observed UT1-UTC (finals2000A, archived by run_iers.py) on the effective date."""
import datetime as dt, json, os, re, sys, urllib.request
OUT = sys.argv[1] if len(sys.argv) > 1 else "results"
RAW = os.path.join(OUT, "raw_bulletinD"); os.makedirs(RAW, exist_ok=True)
MON = {m: i for i, m in enumerate(["january","february","march","april","may","june","july","august","september","october","november","december"], 1)}
fin = {}
for line in open(os.path.join(OUT, "raw", "finals2000A.data"), errors="replace"):
    try: fin[int(float(line[7:15]))] = (line[57], float(line[58:68]))
    except Exception: pass
def mjd(d): return (d - dt.date(1858, 11, 17)).days
rows = []
for n in range(100, 150):
    txt = None
    for url in (f"https://datacenter.iers.org/products/eop/bulletind/bulletind-{n:03d}.txt",
                f"https://hpiers.obspm.fr/iers/bul/buld/bulletind.{n}"):
        try:
            txt = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read().decode("latin-1"); src = url; break
        except Exception as e: last = repr(e)
    if not txt: rows.append({"n": n, "error": last}); continue
    open(os.path.join(RAW, f"bulletinD_{n:03d}.txt"), "w").write(txt)
    flat = " ".join(txt.split())
    issued = re.search(r"Paris,?\s+(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", flat)
    eff = re.search(r"From the\s+(\d{1,2})\s+([A-Za-z]+)\s+(\d{4}),?\s*0\s*h", flat, re.I)
    val = re.search(r"DUT1\s*=\s*([+-]?\s*\d?\.\d)\s*s", flat)
    r = {"n": n, "src": src}
    try:
        if issued: r["issued"] = str(dt.date(int(issued.group(3)), MON[issued.group(2).lower()], int(issued.group(1))))
        if eff:
            e = dt.date(int(eff.group(3)), MON[eff.group(2).lower()], int(eff.group(1))); r["effective"] = str(e)
            f = fin.get(mjd(e)); r["ut1_utc_at_effective"] = f[1] if f else None; r["flag"] = f[0] if f else None
        if val: r["dut1"] = float(val.group(1).replace(" ", ""))
    except Exception as ex: r["parse_error"] = repr(ex)
    if "dut1" in r and r.get("ut1_utc_at_effective") is not None:
        r["diff_at_effective"] = round(r["ut1_utc_at_effective"] - r["dut1"], 4)
    rows.append(r)
# previous DUT1 value and the residual just before the change
prev = None
for r in rows:
    if "dut1" in r and "effective" in r:
        if prev is not None:
            e = dt.date.fromisoformat(r["effective"]); f = fin.get(mjd(e) - 1)
            r["prev_dut1"] = prev
            r["ut1_utc_day_before"] = f[1] if f else None
            r["diff_vs_prev_day_before"] = round(f[1] - prev, 4) if f else None
        prev = r["dut1"]
json.dump(rows, open(os.path.join(OUT, "dut1_history.json"), "w"), indent=1)
L = ["# DUT1 change history (IERS Bulletin D) vs observed UT1-UTC", "",
     "| D no. | issued | effective | new DUT1 | prev DUT1 | UT1-UTC day before | (UT1-UTC) - prev DUT1 | UT1-UTC at effective | (UT1-UTC) - new DUT1 |", "|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    if "error" in r: L.append(f"| {r['n']} | fetch failed: {r['error'][:60]} |||||||| "); continue
    L.append(f"| {r['n']} | {r.get('issued','')} | {r.get('effective','')} | {r.get('dut1','')} | {r.get('prev_dut1','')} | {r.get('ut1_utc_day_before','')} | {r.get('diff_vs_prev_day_before','')} | {r.get('ut1_utc_at_effective','')} | {r.get('diff_at_effective','')} |")
open(os.path.join(OUT, "DUT1_HISTORY.md"), "w").write("\n".join(L) + "\n")
print("\n".join(L))

# ---- NIST broadcast DUT1 history (WWV/WWVH/WWVB/ACTS) ----
import html as _html
nist_url = "https://www.nist.gov/pml/time-and-frequency-division/time-realization/leap-seconds"
try:
    page = urllib.request.urlopen(urllib.request.Request(nist_url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read().decode("utf-8", "replace")
    open(os.path.join(OUT, "raw", "nist_leap_seconds_page.html"), "w").write(page)
    cells = [_html.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", page, re.S)]
    nist = []
    for i in range(len(cells) - 2):
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", cells[i]) and "UTC" in cells[i + 1] and re.search(r"[+-]?\s*\d\.\d\s*s", cells[i + 2]):
            nist.append({"start": cells[i], "dut1": float(re.sub(r"[^\d.+-]", "", cells[i + 2]))})
    iers_eff = {r["effective"]: r["dut1"] for r in rows if "effective" in r and "dut1" in r}
    L2 = ["", "# NIST broadcast DUT1 changes vs IERS Bulletin D", "", "| NIST start | NIST DUT1 | IERS Bulletin D effective date for same value (nearest) | days NIST - IERS |", "|---|---|---|---|"]
    for r in nist[:30]:
        d0 = dt.date.fromisoformat(r["start"])
        cands = [(abs((dt.date.fromisoformat(e) - d0).days), e) for e, v in iers_eff.items() if abs(v - r["dut1"]) < 1e-9]
        if cands:
            _, e = min(cands); L2.append(f"| {r['start']} | {r['dut1']:+.1f} | {e} | {(d0 - dt.date.fromisoformat(e)).days} |")
        else:
            L2.append(f"| {r['start']} | {r['dut1']:+.1f} | (no IERS issue in fetched range) | |")
    json.dump(nist, open(os.path.join(OUT, "nist_dut1_history.json"), "w"), indent=1)
except Exception as ex:
    L2 = ["", f"NIST page fetch/parse failed: {ex!r}"]
open(os.path.join(OUT, "DUT1_HISTORY.md"), "a").write("\n".join(L2) + "\n")
print("\n".join(L2))
