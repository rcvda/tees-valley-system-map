# Geography model & lenses

The map's data is **Tees Valley-wide**. Geography is coded (ONS GSS codes for places), and the map is
viewed through **lenses** — saved filters over the one dataset — rather than being split into separate
per-area datasets. Shared and joint bodies therefore exist once and appear in whichever lenses include
them. Places are coded; *organisations* keep their own identifiers (org-id.guide / GB-UKLA for
councils, ODS for NHS bodies) — the two are not conflated.

## Node geography fields

| Field | Meaning |
|---|---|
| `area` | GSS code (`E06…`/`E12…`/`E47…`/`E92…`) for a place, or a grouping slug (`south-tees`, `north-tees`, `cleveland`). Canonical geography. |
| `area_label` | Human label for `area`. |
| `ceremonial` | Ceremonial county: `north-yorkshire` or `county-durham` (absent where mixed / n-a). |
| `external` | `true` if the body sits outside Tees Valley (shown only when connected to an in-lens node). |
| `constituency` | Westminster constituency, on MP nodes only (separate axis from `area`). |
| `geography` | Original free-text value, retained as provenance; not used for filtering. |

## The spine (containment)

| Level | Name | GSS code |
|---|---|---|
| Country | England | E92000001 |
| Region | North East | E12000001 |
| Combined authority | Tees Valley | E47000006 |
| Local authority | Hartlepool | E06000001 |
| Local authority | Middlesbrough | E06000002 |
| Local authority | Redcar and Cleveland | E06000003 |
| Local authority | Stockton-on-Tees | E06000004 |
| Local authority | Darlington | E06000005 |

(LA codes verified against the mySociety register; region/CA/country codes to be locked against ONS
before wider publication.)

## Lenses

A lens is a set of local-authority GSS codes. Administrative lenses:

| Slug | Member LAs |
|---|---|
| `tees-valley` | all five |
| `cleveland` | Hartlepool, Middlesbrough, R&C, Stockton (ex-county — all but Darlington) |
| `south-tees` | Middlesbrough, Redcar and Cleveland |
| `north-tees` | Hartlepool, Stockton-on-Tees |
| `darlington` … `stockton` | the single borough |

Ceremonial-county lenses: `ceremonial-north-yorkshire` (Middlesbrough + R&C) and
`ceremonial-county-durham` (Darlington + Hartlepool + Stockton — Stockton assigned whole, though the
Tees technically splits it). Identity: `north-tees` ∪ `south-tees` = `cleveland`;
`cleveland` + Darlington = `tees-valley`.

## How a lens decides what shows

Resolve each node to an **area-set**: a local authority → itself; a grouping → its member LAs; Tees
Valley → all five; region/country → treated as covering all LAs; an external partner → empty.

- **Context on** (default): a node shows if its area-set **overlaps** the lens — so shared bodies
  (South Tees), the Combined Authority, and regional/national bodies appear as the context a borough
  plugs into, and external partners appear when connected (one hop) to a shown node.
- **Context off**: a node shows only if its area-set is **wholly within** the lens — i.e. bodies
  native to that area only. No regional/national umbrellas, no externals.

Verified counts against the current 399-node model: `tees-valley` = 399 on / 397 off (off drops the
2 externals); `south-tees` = 338 / 275; `north-tees` = 109 / 48; `cleveland` = 386 / 337;
`ceremonial-county-durham` = 122 / 61.

## Shortcode

`lens=` sets the opening lens, `context="off"` for the tight view; both are switchable live in the
sidebar. E.g. `[rcvda_system_map lens="south-tees"]`, `[rcvda_system_map lens="redcar-cleveland" context="off"]`.

## Tier

`tier` (local / sub-regional / regional / national) is aligned to the coded `area`: local
authority → local; grouping or Combined Authority → sub-regional; North East → regional; England →
national. Deliberate national tags are preserved (the four Parliament/MP nodes, UK Shared Prosperity
Fund, NHS England, etc. stay national even where their `area` is a local patch — `area` places them
on the map, `tier` records their institutional level). Distribution: local 290, sub-regional 89,
regional 9, national 11.

## Constituency lenses

Westminster constituencies are a separate axis (`constituency` field on MP nodes, PCON `E14…` codes).
They don't nest in boroughs, so a constituency lens resolves to the **borough(s) the constituency
covers** — borough-resolution, not ward-level — and then filters exactly like any other lens. Covers
the constituencies currently in the dataset:

| Lens slug | Constituency (PCON) | Borough set |
|---|---|---|
| `constituency-redcar` | Redcar (E14001440) | Redcar and Cleveland |
| `constituency-middlesbrough-south-east-cleveland` | Middlesbrough South and East Cleveland | Middlesbrough + R&C |
| `constituency-middlesbrough-thornaby-east` | Middlesbrough and Thornaby East | Middlesbrough + Stockton |

Add more as MP nodes are added — one line in the plugin's `LENS` map (borough set) plus a dropdown
option. (The two Middlesbrough PCON codes are 2024-boundary constituencies; lock their exact `E14…`
codes against ONS when convenient — the lens works from the borough set regardless.)

## Notes / to-do

- Constituency lenses are borough-resolution; true ward-level scoping would need ward data per node.
