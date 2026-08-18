# tools/

Maintenance scripts for the dataset.

## enrich_mandates.py — populate elected members' mandates from Democracy Club

Fills the stubbed `mandate` block (dc_id, election_id, source, term) on `people[]`
elected members from the Democracy Club **candidates** API (which serves who *won*).

```bash
pip install requests

# 1. dry run — reports what it would do, writes nothing
python3 tools/enrich_mandates.py

# 2. apply
python3 tools/enrich_mandates.py --write
```

### Getting the Democracy Club person IDs

Enrichment needs each person's DC person ID. Supply them in **`dc_person_ids.csv`**
(a template listing the 26 elected members is committed here) — fill the `dc_id`
column by finding each person at
`https://candidates.democracyclub.org.uk/search/?q=<name>` and copying the number
from their `/person/<id>/` URL. The script then fetches each person, takes their most
recent *elected* candidacy, and writes `dc_id` + `election_id` (a
[uk-election-id](https://democracyclub.github.io/uk-election-ids/)) + `term` + `source`.

`--search` will *attempt* to resolve IDs by name, but it only accepts unambiguous single
matches and prints the rest for you to set by hand — so the CSV is the dependable route.

### First-run caveat

This was written without live access to the DC API (their robots.txt blocks automated
fetches from the authoring environment), so the API base URL and a few response-field
names in the CONFIG / `_extract_mandate` section are best-effort. **Run the dry run first**
and, if the output looks wrong, adjust those (they're isolated and commented). The
ID→mandate extraction logic itself is unit-tested against the expected record shape.

Idempotent (skips already-populated people) and rate-limited (1s between calls).
