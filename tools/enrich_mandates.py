#!/usr/bin/env python3
"""
enrich_mandates.py — populate elected people's `mandate` block from Democracy Club.

The map's `people[]` registry holds elected members with a stubbed `mandate`
(office, election_id, source, term). This script fills those from the Democracy Club
CANDIDATES API (https://candidates.democracyclub.org.uk), which — unlike the developer
API — serves who *won* past elections.

Two phases:
  1. ID discovery  — get each elected person's Democracy Club person ID.
  2. Enrichment    — given the ID, fetch the person, take their most recent *elected*
                     candidacy, and write dc_id + election_id (uk-election-id) + term +
                     source onto their mandate.

Phase 2 (ID -> mandate) is well defined and reliable. Phase 1 (finding the ID) is the
fuzzy bit: supply IDs via tools/dc_person_ids.csv (a `dc_id` column keyed by person_ref
or name — a template is generated alongside this script), or let --search attempt a
name lookup (best effort; review its matches before writing).

    python3 tools/enrich_mandates.py                 # dry run: report only
    python3 tools/enrich_mandates.py --write         # apply to data/system-data.json
    python3 tools/enrich_mandates.py --search        # also try name search for missing IDs

Requires: requests  (pip install requests)

VERIFY-ON-FIRST-RUN: this was written without live access to the DC API (its robots.txt
blocks automated fetches from the authoring sandbox). The API base + the response-field
names are isolated in the CONFIG / _extract_mandate section below — run --dry-run first
and adjust those if the printed output looks off, rather than trusting them blind.
"""
import argparse, csv, json, os, sys, time

try:
    import requests
except ImportError:
    sys.exit("This script needs `requests`:  pip install requests")

# ---- CONFIG (verify these against the live API on first run) ------------------
API_BASE   = "https://candidates.democracyclub.org.uk/api/next"
PERSON_API = API_BASE + "/people/{id}/"                 # person detail (JSON)
SEARCH_API = API_BASE + "/people/"                      # ?name= (best-effort; may need tuning)
PERSON_URL = "https://candidates.democracyclub.org.uk/person/{id}/"   # human page -> mandate.source
POLITE_SECONDS = 1.0
TERM_YEARS = {"parl": 5, "mayor": 4, "local": 4, "pcc": 4}  # naive default term lengths

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data", "system-data.json")
IDS_CSV = os.path.join(HERE, "dc_person_ids.csv")


def load_id_map():
    """person_ref (or lowercased name) -> dc_id, from the CSV if present."""
    m = {}
    if not os.path.exists(IDS_CSV):
        return m
    with open(IDS_CSV, newline="") as f:
        for row in csv.DictReader(f):
            dcid = (row.get("dc_id") or "").strip()
            if not dcid:
                continue
            if row.get("person_ref"):
                m[row["person_ref"].strip()] = dcid
            if row.get("name"):
                m[row["name"].strip().lower()] = dcid
    return m


def http_json(url, **params):
    r = requests.get(url, params=params or None, timeout=30,
                     headers={"User-Agent": "rcvda-tees-valley-system-map enricher"})
    r.raise_for_status()
    return r.json()


def search_person_id(name):
    """Best-effort name search -> a single dc_id, or None if 0/ambiguous.
    The candidates API's search shape may differ; this is deliberately conservative
    (only returns on an unambiguous single hit) and prints ambiguity for review."""
    try:
        data = http_json(SEARCH_API, name=name)
    except Exception as e:
        print(f"    ! search failed for {name!r}: {e}")
        return None
    results = data.get("results", data if isinstance(data, list) else [])
    hits = [r for r in results if str(r.get("name", "")).lower() == name.lower()]
    if len(hits) == 1:
        return str(hits[0].get("id"))
    if len(hits) > 1:
        print(f"    ? {len(hits)} exact-name matches for {name!r} — set the id manually in dc_person_ids.csv")
    return None


def _term_from(kind, date_iso):
    try:
        y = int(str(date_iso)[:4])
    except (TypeError, ValueError):
        return None
    return f"{y}–{y + TERM_YEARS.get(kind, 4)}"


def _extract_mandate(person_json):
    """From a DC person record, return the most recent WON candidacy as a mandate dict.
    Field names are defensive — DC has used both `candidacies` and `memberships`, and
    ballot ids under `ballot_paper_id`. Adjust here if the live shape differs."""
    cands = person_json.get("candidacies") or person_json.get("memberships") or []
    won = []
    for c in cands:
        elected = c.get("elected")
        if elected is False:
            continue  # explicitly not elected
        ballot = c.get("ballot") or {}
        bpid = ballot.get("ballot_paper_id") or c.get("ballot_paper_id") or ""
        date = (ballot.get("election") or {}).get("election_date") or ballot.get("election_date") or bpid[-10:]
        post = (ballot.get("post") or {}).get("label") or ballot.get("post_name") or ""
        party = (c.get("party") or {}).get("name") or c.get("party_name") or ""
        won.append({"election_id": bpid, "date": str(date), "post": post,
                    "party": party, "elected": elected})
    if not won:
        return None
    won.sort(key=lambda w: w["date"], reverse=True)  # most recent first
    return won[0]


def kind_of(election_id):
    p = (election_id or "").split(".", 1)[0]
    return {"parl": "parl", "mayor": "mayor", "local": "local", "pcc": "pcc"}.get(p, "local")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="apply changes to system-data.json")
    ap.add_argument("--search", action="store_true", help="attempt name search for missing dc_ids")
    args = ap.parse_args()

    with open(DATA) as f:
        d = json.load(f)
    id_map = load_id_map()

    elected = [p for p in d.get("people", []) if p.get("kind") == "elected"]
    done = ambiguous = failed = skipped = 0

    for p in elected:
        m = p.setdefault("mandate", {"office": None, "election_id": None, "source": None, "term": None})
        if p.get("dc_id") and m.get("election_id"):
            skipped += 1
            continue
        dcid = p.get("dc_id") or id_map.get(p["id"]) or id_map.get(p["name"].lower())
        if not dcid and args.search:
            dcid = search_person_id(p["name"])
            time.sleep(POLITE_SECONDS)
        if not dcid:
            ambiguous += 1
            print(f"  ? {p['name']:<26} no dc_id (add it to tools/dc_person_ids.csv)")
            continue
        try:
            pj = http_json(PERSON_API.format(id=dcid))
        except Exception as e:
            failed += 1
            print(f"  ! {p['name']:<26} dc_id {dcid}: fetch failed: {e}")
            continue
        time.sleep(POLITE_SECONDS)
        man = _extract_mandate(pj)
        if not man:
            failed += 1
            print(f"  ! {p['name']:<26} dc_id {dcid}: no elected candidacy found")
            continue
        p["dc_id"] = str(dcid)
        m["election_id"] = man["election_id"] or m.get("election_id")
        m["source"] = PERSON_URL.format(id=dcid)
        m["term"] = _term_from(kind_of(man["election_id"]), man["date"]) or m.get("term")
        if man["post"] and (not m.get("office") or m["office"] == "Councillor"):
            m["office"] = man["post"]
        done += 1
        print(f"  ✓ {p['name']:<26} {man['election_id']}  {man.get('party','')}")

    print(f"\n{done} enriched, {skipped} already done, {ambiguous} need a dc_id, {failed} failed "
          f"(of {len(elected)} elected).")
    if args.write and done:
        with open(DATA, "w") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        print(f"Written to {os.path.relpath(DATA)}. Review the diff, then commit + push.")
    elif done:
        print("Dry run — rerun with --write to save.")


if __name__ == "__main__":
    main()
