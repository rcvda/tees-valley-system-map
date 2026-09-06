#!/usr/bin/env python3
"""
resolve_mandates.py — find elected members on Democracy Club AND fill their mandate,
automatically. No per-person lookups, no CSV to hand-fill.

How: for each borough with unresolved councillors, query the winners of that council's
election directly (DC candidates API `candidates_elected/?election_id=local.<authority>.<date>`
— confirmed to return just that election's ~50 winners, not the national list), build a
name index scoped to the borough, match your `people[]` elected members to it, and write the
full mandate (dc_id, election_id, source, term, office with ward, party) in one pass.

    python3 tools/resolve_mandates.py            # dry run — reports matches, writes nothing
    python3 tools/resolve_mandates.py --write     # apply to data/system-data.json

Requires: requests. Public API, no key. Idempotent (skips people already resolved).
Queries are targeted (a dozen small calls, not hundreds) with 429 back-off, so it finishes
quickly even under the API's rate limit. Anyone it can't match confidently is listed for you.
"""
import argparse, json, os, re, sys, time
try:
    import requests
except ImportError:
    sys.exit("Needs requests:  python3 -m pip install --user --break-system-packages requests")

API = "https://candidates.democracyclub.org.uk/api/next/candidates_elected/"
PERSON_URL = "https://candidates.democracyclub.org.uk/person/{id}/"
POLITE = 1.0
MAX_RETRIES = 8

# GSS code -> uk-election-id authority slug
LA_SLUG = {"E06000001": "hartlepool", "E06000002": "middlesbrough",
           "E06000003": "redcar-and-cleveland", "E06000004": "stockton-on-tees",
           "E06000005": "darlington"}
# local polling days to try per borough (whole-council + by-thirds years). Non-existent
# ones 404 and are skipped cheaply.
LOCAL_DATES = ["2023-05-04", "2024-05-02", "2022-05-05", "2021-05-06", "2025-05-01"]
# election groups for national-office holders (used only if such a person is unresolved)
PARL_GROUPS = ["parl.2024-07-04"]
MAYOR_GROUPS = ["mayor.tees-valley.2024-05-02", "mayor.middlesbrough.2023-05-04"]
PCC_GROUPS = ["pcc.cleveland.2024-05-02"]
TERM_YEARS = {"parl": 5, "mayor": 4, "local": 4, "pcc": 4}

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data", "system-data.json")


def norm(name):
    s = re.sub(r"^(cllr|councillor|mayor|dr|sir|dame|mr|mrs|ms|the hon)\.?\s+", "", (name or "").strip(), flags=re.I)
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def name_key(name):
    t = norm(name).split()
    return (t[0], t[-1]) if len(t) >= 2 else ((t[0], "") if t else ("", ""))


def scope_of(bpid):
    parts = (bpid or "").split(".")
    return (parts[0], parts[1]) if len(parts) >= 2 else ("", "")


def ward_from(bpid):
    parts = (bpid or "").split(".")
    return parts[2].replace("-", " ").title() if len(parts) >= 4 and parts[0] == "local" else ""


def term_from(etype, bpid):
    m = re.search(r"(\d{4})-\d{2}-\d{2}$", bpid or "")
    return f"{int(m.group(1))}–{int(m.group(1)) + TERM_YEARS.get(etype, 4)}" if m else None


def api_get(url, params):
    """GET with 429 back-off; returns None on 404 (election doesn't exist)."""
    for attempt in range(MAX_RETRIES):
        r = requests.get(url, params=params, timeout=60,
                         headers={"User-Agent": "rcvda-tees-valley-system-map resolver"})
        if r.status_code == 404:
            return None
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After") or min(120, 5 * (2 ** attempt)))
            print(f"    rate-limited — waiting {wait}s")
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r
    r.raise_for_status()


def fetch_group(election_id, idx, log):
    """Add all winners of one election group to idx, keyed (etype, slug, first, last)."""
    url, params, got = API, {"election_id": election_id, "page_size": 200}, 0
    while url:
        r = api_get(url, params)
        if r is None:
            return  # 404 — no such election
        d = r.json()
        for rec in d.get("results", []):
            bpid = (rec.get("ballot") or {}).get("ballot_paper_id", "")
            etype, slug = scope_of(bpid)
            per = rec.get("person") or {}
            fk, lk = name_key(per.get("name", ""))
            key = (etype, slug, fk, lk)
            cur = idx.get(key)
            if not cur or bpid > cur["bpid"]:
                idx[key] = {"id": per.get("id"), "name": per.get("name"), "bpid": bpid,
                            "etype": etype, "party": (rec.get("party") or {}).get("name", ""),
                            "ward": ward_from(bpid)}
            got += 1
        url, params = d.get("next"), None
        time.sleep(POLITE)
    log(f"  {election_id}: {got} winners")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    with open(DATA) as f:
        d = json.load(f)

    auth = {}  # person_ref -> authority slug (from role nodes' coded area)
    for n in d["nodes"]:
        nd = n["data"]
        if nd.get("person_ref") and nd.get("area") in LA_SLUG:
            auth.setdefault(nd["person_ref"], LA_SLUG[nd["area"]])

    elected = [p for p in d.get("people", []) if p.get("kind") == "elected"]
    todo = [p for p in elected if not (p.get("dc_id") and (p.get("mandate") or {}).get("election_id"))]
    if not todo:
        print("All elected people already resolved.")
        return

    def kind_of(p):
        o = (p.get("mandate") or {}).get("office", "") or ""
        if re.search(r"\bMP\b|Member of Parliament", o, re.I): return "parl"
        if re.search(r"mayor", o, re.I): return "mayor"
        if re.search(r"police and crime|PCC", o, re.I): return "pcc"
        return "local"

    # build the minimal set of election groups to query
    groups = []
    local_slugs = {auth.get(p["id"]) for p in todo if kind_of(p) == "local"} - {None}
    for slug in sorted(local_slugs):
        groups += [f"local.{slug}.{dte}" for dte in LOCAL_DATES]
    if any(kind_of(p) == "parl" for p in todo):  groups += PARL_GROUPS
    if any(kind_of(p) == "mayor" for p in todo): groups += MAYOR_GROUPS
    if any(kind_of(p) == "pcc" for p in todo):   groups += PCC_GROUPS

    print(f"Resolving {len(todo)} of {len(elected)} elected people via {len(groups)} targeted queries...")
    idx = {}
    for g in groups:
        fetch_group(g, idx, print)

    matched = ambiguous = unmatched = 0
    for p in todo:
        fk, lk = name_key(p["name"])
        types = [kind_of(p)]
        slug = auth.get(p["id"])
        hits = {}
        for (etype, s, f2, l2), rec in idx.items():
            if etype in types and f2 == fk and l2 == lk and (etype != "local" or slug is None or s == slug):
                hits[rec["id"]] = rec
        hits = list(hits.values())
        if len(hits) == 1:
            rec = hits[0]
            p["dc_id"] = str(rec["id"])
            m = p.setdefault("mandate", {})
            m["election_id"] = rec["bpid"]
            m["source"] = PERSON_URL.format(id=rec["id"])
            m["term"] = term_from(rec["etype"], rec["bpid"])
            m["party"] = rec["party"]
            if rec["ward"] and (not m.get("office") or m["office"] == "Councillor"):
                m["office"] = f"Councillor, {rec['ward']}"
            matched += 1
            print(f"  ✓ {p['name']:<26} {rec['bpid']}  {rec['party']}")
        elif len(hits) > 1:
            ambiguous += 1
            print(f"  ? {p['name']:<26} {len(hits)} matches {[h['id'] for h in hits]} — set by hand")
        else:
            unmatched += 1
            print(f"  — {p['name']:<26} no match (by-election, or name differs on DC)")

    print(f"\n{matched} resolved, {ambiguous} ambiguous, {unmatched} unmatched (of {len(todo)}).")
    if args.write and matched:
        with open(DATA, "w") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        print(f"Written to {os.path.relpath(DATA)} — review the diff, then commit + push.")
    elif matched:
        print("Dry run — rerun with --write to save.")


if __name__ == "__main__":
    main()
