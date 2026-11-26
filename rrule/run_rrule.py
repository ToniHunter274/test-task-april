"""RFC 5545 recurrence ground truth across 2026 time-zone changes.

Expands simple RRULEs in local time, then maps each local instance to UTC under:
  mode 'original' : RFC 5545 s3.3.10 as printed -- instances at nonexistent local times are dropped and not counted
  mode 'erratum'  : verified Erratum 4271 -- nonexistent local times are kept and interpreted per s3.3.5
                    (UTC offset before the gap); ambiguous times use the first occurrence (s3.3.5)
Invalid dates (e.g. 31 April) are dropped and not counted in both modes.
Also reports per-zone transitions in 2026 (UTC offset, abbreviation, DST flag) for the installed tzdata.
"""
import datetime as dt, json, sys
from zoneinfo import ZoneInfo
import importlib.metadata as md
try:
    import tzdata; IANA = getattr(tzdata, "IANA_VERSION", "?")
except Exception:
    IANA = "system"
OUT = sys.argv[1] if len(sys.argv) > 1 else "results.json"
UTC = dt.timezone.utc

def classify(local_naive, tz):
    """Return ('ok'|'gap'|'ambiguous', utc_first, utc_second)."""
    a = local_naive.replace(tzinfo=tz, fold=0); b = local_naive.replace(tzinfo=tz, fold=1)
    ua, ub = a.astimezone(UTC), b.astimezone(UTC)
    back_a = ua.astimezone(tz).replace(tzinfo=None)
    if ua == ub: return "ok", ua, None
    if back_a != local_naive:          # fold=0 does not round-trip -> nonexistent (gap)
        return "gap", ua, ub
    return "ambiguous", min(ua, ub), max(ua, ub)

def gap_utc(local_naive, tz):
    """s3.3.5: nonexistent local time interpreted using the UTC offset BEFORE the gap."""
    before = (local_naive - dt.timedelta(hours=3)).replace(tzinfo=tz)
    off = before.utcoffset()
    return (local_naive - off).replace(tzinfo=UTC)

def candidates(rule, start):
    """Yield local naive datetimes (or None for invalid dates) in order."""
    f = rule["freq"]; t = start.time()
    if f == "DAILY":
        d = start.date()
        while True:
            yield dt.datetime.combine(d, t); d += dt.timedelta(days=1)
    if f == "MONTHLY":   # BYMONTHDAY single value
        y, m = start.year, start.month
        while True:
            try: yield dt.datetime(y, m, rule["bymonthday"], t.hour, t.minute)
            except ValueError: yield None
            m += 1
            if m == 13: y, m = y + 1, 1
    if f == "YEARLY":    # BYMONTH + BYMONTHDAY
        y = start.year
        while True:
            try: yield dt.datetime(y, rule["bymonth"], rule["bymonthday"], t.hour, t.minute)
            except ValueError: yield None
            y += 1

def expand(rule, start_local, tzname, mode):
    tz = ZoneInfo(tzname); out = []; n = 0
    until = rule.get("until")
    for loc in candidates(rule, start_local):
        if loc is None:
            out.append({"local": "invalid-date", "status": "dropped (invalid date)"}); 
            if len(out) > 400: break
            continue
        if loc < start_local: continue
        kind, u1, u2 = classify(loc, tz)
        if kind == "gap":
            if mode == "original":
                rec = {"local": loc.isoformat(), "status": "dropped (nonexistent local time)"}
                out.append(rec); continue
            u = gap_utc(loc, tz); status = "kept, shifted (nonexistent local time)"
        elif kind == "ambiguous":
            u = u1; status = f"ambiguous; first occurrence used (other {u2.strftime('%H:%MZ')})"
        else:
            u = u1; status = "ok"
        if until and u > until: break
        lt = u.astimezone(tz)
        out.append({"local": loc.isoformat(), "status": status, "utc": u.strftime("%Y-%m-%dT%H:%MZ"),
                    "wall_clock": lt.strftime("%Y-%m-%d %H:%M %Z"), "utc_offset": lt.strftime("%z"), "dst": bool(lt.dst())})
        n += 1
        if rule.get("count") and n >= rule["count"]: break
    return out

def transitions(tzname, year=2026):
    tz = ZoneInfo(tzname); res = []; t = dt.datetime(year, 1, 1, tzinfo=UTC); end = dt.datetime(year + 1, 1, 1, tzinfo=UTC)
    prev = t.astimezone(tz); prev_k = (prev.utcoffset(), prev.tzname(), prev.dst())
    while t < end:
        t2 = t + dt.timedelta(minutes=30); cur = t2.astimezone(tz); k = (cur.utcoffset(), cur.tzname(), cur.dst())
        if k != prev_k:
            lo, hi = t, t2
            while hi - lo > dt.timedelta(minutes=1):
                mid = lo + (hi - lo) / 2; mk = mid.astimezone(tz)
                if (mk.utcoffset(), mk.tzname(), mk.dst()) == prev_k: lo = mid
                else: hi = mid
            res.append({"utc": hi.strftime("%Y-%m-%dT%H:%MZ"),
                        "from": {"offset": str(prev_k[0]), "abbr": prev_k[1], "dst": str(prev_k[2])},
                        "to": {"offset": str(k[0]), "abbr": k[1], "dst": str(k[2])},
                        "offset_changes": prev_k[0] != k[0]})
            prev_k = k
        t = t2
    return res

CASES = {
  "A_gap_vancouver_daily_0230": ("America/Vancouver", dt.datetime(2026, 3, 1, 2, 30), {"freq": "DAILY", "count": 14}),
  "B_invalid_date_monthly_31": ("America/Vancouver", dt.datetime(2026, 1, 31, 9, 0), {"freq": "MONTHLY", "bymonthday": 31, "count": 6}),
  "B2_invalid_date_yearly_feb29": ("America/Vancouver", dt.datetime(2024, 2, 29, 9, 0), {"freq": "YEARLY", "bymonth": 2, "bymonthday": 29, "count": 3}),
  "C_ambiguous_losangeles_0130_nov": ("America/Los_Angeles", dt.datetime(2026, 10, 30, 1, 30), {"freq": "DAILY", "count": 5}),
  "C2_vancouver_0130_nov": ("America/Vancouver", dt.datetime(2026, 10, 30, 1, 30), {"freq": "DAILY", "count": 5}),
  "D_casablanca_daily_0130_sep": ("Africa/Casablanca", dt.datetime(2026, 9, 17, 1, 30), {"freq": "DAILY", "count": 7}),
  "E_casablanca_daily_0230_mar": ("Africa/Casablanca", dt.datetime(2026, 3, 18, 2, 30), {"freq": "DAILY", "count": 7}),
  "F_edmonton_daily_0130_nov": ("America/Edmonton", dt.datetime(2026, 10, 30, 1, 30), {"freq": "DAILY", "count": 5}),
  "G_winnipeg_daily_0130_nov": ("America/Winnipeg", dt.datetime(2026, 10, 30, 1, 30), {"freq": "DAILY", "count": 5}),
}
res = {"python": sys.version.split()[0], "tzdata_pkg": md.version("tzdata") if IANA != "system" else "system", "iana_version": IANA,
       "transitions_2026": {z: transitions(z) for z in ["America/Vancouver", "America/Los_Angeles", "America/Edmonton", "America/Winnipeg", "Africa/Casablanca"]},
       "cases": {}}
for name, (tz, start, rule) in CASES.items():
    res["cases"][name] = {"tz": tz, "dtstart_local": start.isoformat(), "rule": rule,
                          "original": expand(rule, start, tz, "original"), "erratum": expand(rule, start, tz, "erratum")}
json.dump(res, open(OUT, "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "cases"}, indent=1)[:4000])
for name, c in res["cases"].items():
    print("==", name, c["tz"])
    for mode in ("original", "erratum"):
        print("  ", mode, [ (r.get("utc") or r["local"], r["status"][:12]) for r in c[mode]])
