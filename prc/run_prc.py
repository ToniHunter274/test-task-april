"""Bounded PRC-005 comparison: NERC PRC-005-6, BC PRC-005-6 (WECC-posted BC version), Alberta PRC-005-AB2-6.
Records delivery metadata (status, content-type, disposition, size, sha256), extracts text (pdftotext -layout),
and writes per-document section files for: maintenance tables (per-table interval inventory), monitoring attributes,
footnotes/exceptions, definitions (calendar month/year), applicability. Substantive comparison is done by reading."""
import hashlib, json, os, re, subprocess, sys, urllib.request
OUT = sys.argv[1] if len(sys.argv) > 1 else "results"; os.makedirs(OUT, exist_ok=True)
DOCS = {
 "NERC_PRC-005-6": "https://www.nerc.com/pa/Stand/Reliability%20Standards/PRC-005-6.pdf",
 "BC_PRC-005-6": "https://www.wecc.org/sites/default/files/documents/standards/2024/PRC-005-6%20BC.pdf",
 "AB_PRC-005-AB2-6": "https://aeso.ca/rules-standards-and-tariff/alberta-reliability-standards/prc-005-protection-system-automatic-reclosing-and-sudden-pressure-relaying-maintenance//download/PRC-005-AB2-6-Protection-system-Maintenance.pdf",
}
meta = {}
INT = re.compile(r"(\d+)\s*(calendar\s+(?:months?|years?|days?))", re.I)
for name, url in DOCS.items():
    m = {"url": url}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        r = urllib.request.urlopen(req, timeout=90); data = r.read()
        m.update(status=r.status, final_url=r.geturl(), content_type=r.headers.get("Content-Type"),
                 content_disposition=r.headers.get("Content-Disposition"), bytes=len(data),
                 sha256=hashlib.sha256(data).hexdigest(), starts_with_pdf=data[:5] == b"%PDF-")
        pdf = os.path.join(OUT, name + ".pdf"); open(pdf, "wb").write(data)
        txt = os.path.join(OUT, name + ".txt")
        subprocess.run(["pdftotext", "-layout", pdf, txt], check=True)
        os.remove(pdf)                      # keep only extracted text in the repo
        t = open(txt, errors="replace").read(); m["text_chars"] = len(t)
        # per-table interval inventory
        heads = [(mm.start(), mm.group(0)) for mm in re.finditer(r"Table\s+\d-\d+(?:\([a-f]\))?|Table\s+\d\b", t)]
        inv = {}
        for i, (pos, h) in enumerate(heads):
            seg = t[pos: heads[i + 1][0] if i + 1 < len(heads) else len(t)]
            key = re.sub(r"\s+", " ", h)
            vals = [f"{a} {re.sub(r'\s+', ' ', b).lower()}" for a, b in INT.findall(seg)]
            if vals: inv.setdefault(key, []).extend(vals)
        m["interval_inventory"] = {k: sorted(set(v)) for k, v in inv.items()}
        # section extracts for reading
        def grab(pattern, width=3000):
            return [t[max(0, mm.start() - 200): mm.start() + width] for mm in re.finditer(pattern, t, re.I)][:6]
        sec = {
          "definitions_calendar": grab(r"calendar\s+(?:month|year)s?\b[^\n]{0,80}(?:defin|means|end of)", 1500),
          "applicability": grab(r"\bApplicab(?:ility|le)\b", 5000)[:2],
          "monitoring_attributes": grab(r"monitor(?:ing|ed)\s+attribute|Component Attributes", 2500),
          "footnotes_exceptions": grab(r"\bexcept|\bfootnote|^\s*\d\s+[A-Z][^\n]{20,}", 800),
        }
        json.dump(sec, open(os.path.join(OUT, name + "_sections.json"), "w"), indent=1)
    except Exception as e:
        m["error"] = repr(e)
    meta[name] = m
json.dump(meta, open(os.path.join(OUT, "meta.json"), "w"), indent=1)
# inventory comparison (screening aid only)
L = ["# PRC-005 interval inventory by table (screening aid; read the section files for substance)", ""]
for name, m in meta.items():
    L.append(f"- **{name}**: status {m.get('status')}, type {m.get('content_type')}, disposition {m.get('content_disposition')}, "
             f"bytes {m.get('bytes')}, PDF magic {m.get('starts_with_pdf')}, text chars {m.get('text_chars')}, error {m.get('error')}")
keys = sorted({k for m in meta.values() for k in m.get("interval_inventory", {})}, key=lambda s: [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", s)])
L += ["", "| Table | " + " | ".join(meta) + " |", "|---|" + "---|" * len(meta)]
for k in keys:
    L.append(f"| {k} | " + " | ".join("; ".join(meta[n].get("interval_inventory", {}).get(k, ["—"])) for n in meta) + " |")
open(os.path.join(OUT, "INVENTORY.md"), "w").write("\n".join(L) + "\n")
print("\n".join(L))
