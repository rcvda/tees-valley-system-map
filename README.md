# Tees Valley System Map — data

The dataset for the RCVDA system map: the public system of the Tees Valley — organisations, boards,
roles, places and the relationships between them — as a single coded model. This repo holds the
**data and its documentation only**; the tool that renders and publishes it (the WordPress plugin +
build) lives in [`rcvda/rcvda-system-map`](https://github.com/rcvda/rcvda-system-map).

## What's here

| Path | What it is |
|---|---|
| `data/system-data.json` | **The model** — the canonical source of truth (`{nodes, edges, sources}`). Edit here. |
| `docs/schema.md` | The node/edge schema. |
| `docs/geography.md` | Coded geography (ONS GSS codes), the lenses, and how a lens filters the map. |
| `docs/sources/` | Source archive + `_manifest.md` — provenance for every sourced node. |

## Model (brief)

~399 nodes / ~578 edges. Each node: `id, label, type, group` (system domain), `tier`, `org`
(container), `subtype`, `person`, `status`, `source`, plus coded geography — `area` (ONS GSS code or
grouping slug), `area_label`, `ceremonial`, `external`, `constituency`. Each edge: `source, target,
label, kind` (governance / officer / political / commissioning / funding / membership / delivery),
`weight`. Full detail in `docs/schema.md` and `docs/geography.md`.

## How it's used

The `rcvda-system-map` plugin loads this file **live** via the jsDelivr CDN
(`https://cdn.jsdelivr.net/gh/rcvda/tees-valley-system-map@main/data/system-data.json`) and falls
back to a copy bundled inside the plugin. So editing here and pushing updates the site — no plugin
reinstall for data-only changes.

## Update loop

```bash
# edit data/system-data.json
git add -A && git commit -m "Update model: <what changed>" && git push
```

The site picks up the change once the CDN cache expires (~12h on `main`), or immediately if the tool
is pinned to a release tag you bump. If you keep both repos checked out side by side, the tool's
`build/build.sh` reads this repo directly to refresh its bundled fallback.

## Provenance & licence

Compiled by RCVDA from public sources — see `docs/sources/` and each node's `source`. The underlying
facts are public information (council democratic-services sites, published board pages, ONS, etc.).
**Licence: to confirm** — intended for open reuse; RCVDA to set the exact terms (e.g. CC-BY-4.0 or
Open Government Licence v3.0) and add a `LICENSE` file before external distribution.
