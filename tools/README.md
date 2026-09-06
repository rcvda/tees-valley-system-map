# tools/

Maintenance scripts for the dataset.

## resolve_mandates.py — auto-find AND enrich elected members (recommended)

One command, no lookups, no CSV. It pulls the *winners* of the relevant elections from the
Democracy Club candidates API (`candidates_elected/`, by date), builds a name index scoped to each
person's borough, matches your `people[]` elected members to it, and writes the full mandate —
`dc_id`, `election_id` (a uk-election-id), `source`, `term`, `office` (with ward for councillors),
and `party` — in a single pass.

```bash
python3 -m pip install --user --break-system-packages requests   # once
python3 tools/resolve_mandates.py            # dry run — reports matches, writes nothing
python3 tools/resolve_mandates.py --write     # apply to data/system-data.json, then commit + push
```

Public API, no key. Idempotent (skips anyone already resolved). Matching is tolerant of middle
names and initials and is scoped to each councillor's own authority, so collisions are rare; anyone
it can't match confidently (usually a by-election winner or a differently-spelled name) is listed
for you to set by hand — but it resolves the bulk automatically.

If it misses people, widen the `DATES` list near the top (it sweeps the main May polling days plus
the 2024 general election), or check the borough slug in `LA_SLUG`.

## enrich_mandates.py — enrich from a known dc_id (fallback)

Only needed for the odd person the resolver can't match. Put their Democracy Club person ID in
`dc_person_ids.csv` (the `dc_id` column) and run `python3 tools/enrich_mandates.py --write`; it
fetches that person and fills their mandate. `dc_person_ids.csv` is the worklist of elected members.
