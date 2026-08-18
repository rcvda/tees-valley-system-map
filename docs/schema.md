# South Tees Public System Map

An interactive, self-hosted network map of the South Tees public system (Middlesbrough + Redcar & Cleveland). Fully owned, open stack, no SaaS. Graph Commons was trialled and dropped (AI-first relaunch, upsell-heavy, degraded); this build replaces it and ports directly into `rcvda-core` later (see `Self-Hosted Spec.md`).

## What to open

**`South Tees Public System Map.html`** — double-click to open in any browser. Self-contained (Cytoscape.js from CDN, data embedded). Current state: 91 nodes, 119 relationships.

## The data

**`system-data.json` is the single source of truth.** The HTML is generated from it. (The old `nodes.csv` / `edges.csv` / `.xlsx` were for the abandoned Graph Commons route and are no longer maintained.)

## The model — two cross-cutting structures

The core insight, per the English elected-mayor/cabinet model: political portfolios and officer directorates are **separate structures that deliberately cross-cut**. The map captures both as distinct relationship types:

- **Between organisations** (grey) — commissioning, funding, statutory partnerships, membership.
- **Officer line management** (blue) — the management chain: Head → Corporate Director → Chief Executive.
- **Political / portfolio oversight** (pink, dashed) — the Mayor chairs the Executive; each cabinet member holds a portfolio; the portfolio holder politically oversees a function, cutting across the officer directorates.

The worked example: Cllr Jan Ryles (Public Health portfolio) *politically oversees* Mark Adams (Joint Director of Public Health), who is *line-managed by* Louise Grabham (Corporate Director, Adult Social Care & Health). Two edges of different kinds landing on the same person.

### Node types

Top-level bodies are coloured by type (statutory, NHS, emergency, partnership/board, VCSE, education, funder, programme, representative body, role/post). Inside an organisation, nodes are coloured by role: **officer** (slate, rectangle), **cabinet member** (magenta, diamond), **committee** (purple, hexagon). Dashed orange outline = flagged to verify.

Every node also carries a **geography tier** (local / sub-regional / regional / national) so you can filter the map to a footprint.

## Using the viewer

- **Click an organisation** (e.g. Middlesbrough Council) to expand its internal structure; click again or use the sidebar to collapse. Middlesbrough is the fully-built template; other bodies are top-level only so far.
- **Click any node** for a detail panel that groups its connections into political oversight, officer line management, and links to other bodies.
- Filter by **node type** (click the legend) or **geography tier**; switch **layout**; **search** to jump to any node.

## What's in, and what still needs you

Middlesbrough Council is built out from primary sources (the council org chart you provided + the moderngov democratic-services record):

- **Officer structure:** CEO Erik Scollay; five Corporate Directors (Field, Humble, Grabham, Benjamin, Horniman) and their heads of service. Children's directorate deferred (placeholder node).
- **Political structure:** the nine-member Executive with portfolios — Cooke (Mayor/Chair), Storey (Deputy Mayor, Education & Culture), Rostron (Adult Social Care), Henman (Children's Services), Furness (Development), Gavigan (Environment & Sustainability), Walker (Finance), Blades (Neighbourhoods), Ryles (Public Health).
- **Mayoral appointments** into the wider system (TVCA Cabinet, Live Well South Tees, Cleveland Police & Crime Panel, Middlesbrough Development Corporation, and regional/national bodies), tiered.

**To confirm on your return:**

1. Only **Ryles → Adams** (Public Health) is drawn as a portfolio→officer oversight link — the one you confirmed. The other seven portfolios need their officer/function links added; suggested mappings are noted below for you to approve rather than me guessing.
2. Items flagged `verify` (dashed outline) — mostly named post-holders elsewhere and a few body names.

### Suggested portfolio → officer links (NOT yet drawn — for your approval)

- Finance (Walker) → Corporate Director, Finance (Humble)
- Environment & Sustainability (Gavigan) → Corporate Director, Environment, Communities & Culture (Field)
- Neighbourhoods (Blades) → Head of Neighbourhoods (Walker), under Field
- Adult Social Care (Rostron) → Corporate Director, Adult Social Care & Health (Grabham)
- Children's Services (Henman) → Children's Corporate Director (to be added)
- Development (Furness) → Corporate Director, Regeneration & Housing (Horniman)
- Education & Culture (Storey) → split across Children's (education) and Field's Head of Culture

## Sources

Each node records its source (shown as a link in the detail panel):

- **Middlesbrough Council officer / senior leadership structure** — [Council organisation chart (June 2026 PDF)](https://www.middlesbrough.gov.uk/media/emzm1o33/organisation-chart-june26.pdf). This is the authoritative source for the full officer tree (CEO, Corporate Directors, Service Directors, Heads across all six directorates including Children's).
- **Middlesbrough Executive / cabinet and portfolios** — [moderngov democratic-services record](https://middlesbrough.moderngov.co.uk/mgCommitteeDetails.aspx?ID=1146) and individual member pages.
- **Primary Care Networks and GP practices** — RCVDA's "Tees Valley Primary Care Networks" dataset, sourced from [NHS NE&NC — Tees Valley PCNs](https://northeastnorthcumbria.nhs.uk/media/rl5ppbrf/tees-valley-pcns.pdf). 14 PCNs (each commissioned by the ICB, with Clinical Director noted) containing 80 GP practices; expand a PCN to see its practices.
- **Redcar & Cleveland Borough Council officer structure** — [R&C Senior Management Structure (PDF)](https://www.redcar-cleveland.gov.uk/sites/default/files/2026-02/Senior%20Management%20Structure.pdf). Full officer tree, CEO Brian Archer down to service-manager level. Notes: the Director of Public Health is the **joint South Tees post held by Mark Adams** (legal name Christopher Mark Adams) — modelled as one shared node linked to both councils; **Victoria Wilson** (AD Commissioning & Social Care Resources) is dual-hatted across Children's and Adults, modelled once; several **Public Health posts are 50% shared services with Middlesbrough**.
- **Redcar & Cleveland Cabinet** — [R&C Cabinet page](https://www.redcar-cleveland.gov.uk/councillors-and-committees/the-cabinet-and-cabinet-papers); nine members (Leader Cllr Alec Brown + eight portfolio holders), each also linked to their individual moderngov record.

**Source coverage:** 229 of 279 nodes carry a source link (shown in the detail panel). The ~50 without one are the original sector-knowledge seed — top-level bodies (councils, trusts, boards, VCSE, funders) and the five LA-area containers — i.e. the `verify`-flagged items still to be sourced/confirmed.

*Middlesbrough + Redcar & Cleveland councils (officer + cabinet) and Tees Valley PCNs/practices complete as of 2026-07-25. Remaining: source the seed bodies; the 7 Middlesbrough + R&C portfolio→officer oversight links; other bodies' internals.*
