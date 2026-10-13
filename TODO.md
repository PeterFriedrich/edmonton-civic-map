# TODO

The source of truth for what's left. Read first every session; update in place.

**Format contract** (`tools/todo_archive.py` depends on it): top-level items are
`- [ ]` / `- [x]` lines directly under `## Open work`; `###` sub-headings may
group them; closed items are moved to `docs/TODO_archive.md` by the tool, which
leaves a one-line stub under `## Done`. An open item can be stale — reproduce the
symptom and re-measure the stated cause before acting on it.

## Open work

### Waiting on the owner

- [ ] **Map: pick the stack.** The owner is taking `docs/SPEC_lenses.md` §7 to a Claude web chat for a report on candidate stacks and example projects. When the reply comes back, file it under `/home/opc/research/edmonton-civic-map/` first, then triage it here. Done when a `docs/DECISIONS.md` row names the stack.
- [ ] **Tile files: committed under `site/data/` or built at deploy.** Binary tiles give no readable diff, which is what the commit rule is for, and they grow the repo. Informed by the buildings size measurement below. Done when a `docs/DECISIONS.md` row says which (`docs/SPEC_lenses.md` §6 item 3).
- [ ] **Reopen "3D never encodes a quantity" for the density lens, or not.** Waits on the owner seeing 2D and 3D density examples from the stack report.
- [ ] **Confirm the Project picker has the synced set ticked.** The 2026-10-12 reconciliation chat reported only `docs/BRIEF.md`, `docs/DECISIONS.md` and `docs/SPEC_civic_map.md`; the set in `docs/CLAUDE_WEB.md` also has `docs/SPEC_lenses.md`, `docs/SPEC_data_schema.md` and `data/DATA.md`. Blocks the stack research run.
- [ ] **Report data defects to the City.** The owner will send one report later, collecting what `docs/DATA_ISSUES.md` holds by then (2026-10-10). Done when each row there has a status other than NOT SENT.

### Sources still to verify

- [ ] **Licence for the Elections Alberta boundary shapefile.** None is stated on the download page (`data/DATA.md`, "Provincial ridings"). Done when a written licence or permission is recorded there; until then the provincial layer cannot ship.
- [ ] **Exact attribution text for the Open Government Licence – Edmonton**, and Statistics Canada's for the ward populations. Done when `data/DATA.md` quotes both.
- [ ] **Post-2025-election ward boundary report (Policy C469A).** Not found; the City's ward-boundary-review page returned 404 on 2026-10-10. Done when the report's status and any proposed adjustments are recorded in `data/DATA.md`.
- [ ] **Join the 278 census neighbourhoods to the 407 neighbourhood polygons** (`eg3i-f4bj` to `65fr-66s6`). Done when `data/DATA.md` says which of the other 129 are industrial or unpopulated and which, if any, are missing a census row.
- [ ] **A ward population newer than the 2021 Census**, from a primary source. Done when found, or when recorded as not existing.
- [ ] **School-ward boundaries used in the 2025 election** — confirm against each board's ward bylaw that they match the City layers.
- [ ] **Recheck the provincial boundary process after 2026-11-02**, when the Select Special Committee on Electoral Boundaries must report. Done when `data/DATA.md` records what was tabled and whether anything is enacted.

### Map detail phase

- [ ] **Buildings feasibility, step 1: package the rooflines and measure the size.** Proposed 2026-10-13, awaiting the owner's go. Turn the 384,228 polygons of `jpxi-a9a5` into a tile file at a few detail levels and record each size against the Pages limits (100 MB per file, about 1 GB per site). Needs no stack, so it can run before the research report. Lives in `prototype/`. Done when `prototype/README.md` has the sizes.
- [ ] **Terrain: read the Edmonton window of MRDEM-30 and check it.** Sources are in `data/DATA.md`, "Terrain and elevation"; nothing has been read yet. Done when the ledger records CRS, vertical datum, the elevation range across the city, the depth of the river valley as the data shows it, and the gzipped size of the window at 30 m. Then decide whether the 1 m federal lidar (`AB-Edmonton-1m`, 2.38 GB) resampled to about 10 m is worth it.
- [ ] **Buildings feasibility, step 2: draw the same tile file on each candidate stack on a real phone** (the owner's; this server has no GPU). Record first-load time and frame rate, flat and tilted. Done when the numbers are recorded and feed the stack decision.
- [ ] **Find how much geographic detail the site can carry.** Start with "ghost buildings" (faint, translucent, from the 2019 rooflines layer `jpxi-a9a5`), then add terrain and detail in steps; at each step measure the published size against the host's limits, first-load time and frame rate on a mid-range phone. Done when the limits and the chosen level are recorded with their numbers, and a test holds the size budget.

### Lenses

- [ ] **Communities-of-interest lens** (`docs/SPEC_civic_map.md`, amendments). Before building: find a primary source for community league boundaries (not on the City portal); settle the threshold that separates a divided neighbourhood from a digitising sliver; decide what "shared services" means in data terms, if anything. Neighbourhoods are measured already (`data/DATA.md`, "Neighbourhoods").

- [ ] **Physical-and-natural-boundaries lens** (`docs/SPEC_civic_map.md`, amendments). Before building: download and check the road network's arterial classes; find primary sources for the river valley edge and rail lines (neither is a ready layer on the City portal). Candidates: `data/DATA.md`, "Buildings and physical barriers".

- [ ] **Population density lens** (`docs/SPEC_civic_map.md`, amendments): a density map with ward boundaries as an overlay, no number per ward. Parked until the owner has looked at 2D and 3D density maps. Growth is a later part: begin by finding how the City forecasts population and what it has stated (`data/DATA.md`, "Population and growth").

### Tier 2

- [ ] **Survey what Tier 2 can say by automation.** For each issue in brief §3 (potholes, snow clearing, zoning and infill, transit, policing, schools, water and stormwater, property tax and assessment), find whether a primary source states the responsible body and the way to engage in a form a script can fetch and diff: the City's 311 service catalogue and `q7ua-agfg`, City and EPCOR service pages, the governing bylaw or Act. Done when each issue is placed on a rung of the ladder in `docs/SPEC_civic_map.md` with its source, and reported to the owner before any entry is written.

### Build

- [ ] **Downloaders, one per source in `data/DATA.md`**, each checking its row count and writing a `sources.json` entry.
- [ ] **Boundary build**: reproject, clip provincial and federal layers to the city, simplify at the recorded tolerance, with a test that no parcel address changes district against full resolution.
- [ ] **Diff check and staleness guard** per `docs/SPEC_data_schema.md` §5–§6.
- [ ] **Weekly refresh workflow on GitHub Actions** per `docs/SPEC_data_schema.md` §8: auto-publish when nothing changed, hold and file an issue otherwise. Changes CI, so propose the workflow before writing it.
- [ ] **Replace the template `README.md`** with one for this project.

## Done

- [x] 2026-10-10 — Brief §10 tasks 1–4: sources located and verified (`data/DATA.md`), point-in-polygon prototype measured (`prototype/README.md`), schema drafted (`docs/SPEC_data_schema.md`).
