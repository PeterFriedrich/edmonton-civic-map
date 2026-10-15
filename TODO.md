# TODO

The source of truth for what's left. Read first every session; update in place.

**Format contract** (`tools/todo_archive.py` depends on it): top-level items are
`- [ ]` / `- [x]` lines directly under `## Open work`; `###` sub-headings may
group them; closed items are moved to `docs/TODO_archive.md` by the tool, which
leaves a one-line stub under `## Done`. An open item can be stale — reproduce the
symptom and re-measure the stated cause before acting on it.

## Open work

### Waiting on the owner

- [ ] **Reopen "3D never encodes a quantity" for the density lens, or not.** Waits on the owner seeing 2D and 3D density examples from the stack report.
- [ ] **Confirm the Project picker has the synced set ticked.** The 2026-10-12 reconciliation chat reported only `docs/BRIEF.md`, `docs/DECISIONS.md` and `docs/SPEC_civic_map.md`; the set in `docs/CLAUDE_WEB.md` also has `docs/SPEC_lenses.md`, `docs/SPEC_data_schema.md` and `data/DATA.md`. (The stack research has since run and did read the lens spec.)
- [ ] **Report data defects to the City.** The owner will send one report later, collecting what `docs/DATA_ISSUES.md` holds by then (2026-10-10). Done when each row there has a status other than NOT SENT.

### Sources still to verify

- [ ] **Licence for the Elections Alberta boundary shapefile.** None is stated on the download page (`data/DATA.md`, "Provincial ridings"). Done when a written licence or permission is recorded there; until then the provincial layer cannot ship.
- [ ] **Exact attribution text for the Open Government Licence – Edmonton**, and Statistics Canada's for the ward populations. Done when `data/DATA.md` quotes both.
- [ ] **Post-2025-election ward boundary report (Policy C469A).** Not found; the City's ward-boundary-review page returned 404 on 2026-10-10. Done when the report's status and any proposed adjustments are recorded in `data/DATA.md`.
- [ ] **Join the 278 census neighbourhoods to the 407 neighbourhood polygons** (`eg3i-f4bj` to `65fr-66s6`). Done when `data/DATA.md` says which of the other 129 are industrial or unpopulated and which, if any, are missing a census row.
- [ ] **A ward population newer than the 2021 Census**, from a primary source. Done when found, or when recorded as not existing.
- [ ] **School-ward boundaries used in the 2025 election** — confirm against each board's ward bylaw that they match the City layers.
- [ ] **Check the provincial boundary process now, and again after 2026-11-02**, when the Select Special Committee on Electoral Boundaries must report. The 2026-10-13 stack report says the commission's final report gives Edmonton 21 electoral divisions, where the map in force has 20; not verified against `assembly.ab.ca`. Done when `data/DATA.md` records what was tabled, whether anything is enacted, and which map applies to the next provincial election.

### Map detail phase

- [ ] **Measure data used per view and per session, zoomed out and tilted.** A zoomed-out tilted session on the phone fetched 13.33 MB (`prototype/README.md`, "Buildings at z10 and z11"), most of it from the frame-rate fly-over. Done when the cost of the opening view and of a typical look around (zoom out, tilt, pan across the river) is recorded, and a size budget for one view is set, or the current cost is judged fine.
- [ ] **Build glyph files for Noto Sans and Noto Sans Canadian Aboriginal and test pihêsiwin and ᐱᐦᐁᓯᐏᐣ** on Android, iOS and desktop. Done when a test page shows both from our own files.
- [ ] **Find how much geographic detail the site can carry.** Start with "ghost buildings" (faint, translucent, from the 2019 rooflines layer `jpxi-a9a5`), then add terrain and detail in steps; at each step measure the published size against the host's limits, first-load time and frame rate on a mid-range phone. Done when the limits and the chosen level are recorded with their numbers, and a test holds the size budget.

### Lenses

- [ ] **Communities-of-interest lens** (`docs/SPEC_civic_map.md`, amendments). Before building: find a primary source for community league boundaries (not on the City portal); settle the threshold that separates a divided neighbourhood from a digitising sliver; decide what "shared services" means in data terms, if anything. Neighbourhoods are measured already (`data/DATA.md`, "Neighbourhoods").

- [ ] **Physical-and-natural-boundaries lens** (`docs/SPEC_civic_map.md`, amendments). Before building: download and check the road network's arterial classes; find primary sources for the river valley edge and rail lines (neither is a ready layer on the City portal). Candidates: `data/DATA.md`, "Buildings and physical barriers".

- [ ] **Population density lens** (`docs/SPEC_civic_map.md`, amendments): a density map with ward boundaries as an overlay, no number per ward. Parked until the owner has looked at 2D and 3D density maps. Growth is a later part: begin by finding how the City forecasts population and what it has stated (`data/DATA.md`, "Population and growth").

### Tier 2

- [ ] **Survey what Tier 2 can say by automation.** For each issue in brief §3 (potholes, snow clearing, zoning and infill, transit, policing, schools, water and stormwater, property tax and assessment), find whether a primary source states the responsible body and the way to engage in a form a script can fetch and diff: the City's 311 service catalogue and `q7ua-agfg`, City and EPCOR service pages, the governing bylaw or Act. Done when each issue is placed on a rung of the ladder in `docs/SPEC_civic_map.md` with its source, and reported to the owner before any entry is written.

### Build

- [ ] **Build `src/build_address_index.py`** per `docs/SPEC_data_schema.md` §9: the street files and `manifest.txt` under `site/data/addresses/`, the §9.4 diff-check rows and the §9.5 tests. Needs the address downloader and the boundary build first (items below). Done when the index is committed and all four §9.5 tests pass.
- [ ] **Propose: the Vite build and what it changes in CI.** Adds a Node toolchain to a Python project and replaces the template's cache-busting step (`docs/WEB_CACHE_BUSTING.md`). Propose before writing.
- [ ] **Downloaders for the office-holder sources** (`e9qt-cc3j`, `fv5x-8efu`, `eg3i-f4bj`, Assembly `contacts.csv`, House of Commons CSV, the two trustee pages), added to `src/download.py`, each checking its row count and writing `fetch.json`. The trustee scrapers must fail on a layout change, never return an empty roster. The six map and address sources are done (2026-10-15, `data/DATA.md` "In use").
- [ ] **Diff check and staleness guard** per `docs/SPEC_data_schema.md` §5–§6.
- [ ] **Weekly refresh workflow on GitHub Actions** per `docs/SPEC_data_schema.md` §8: auto-publish when nothing changed, hold and file an issue otherwise. Changes CI, so propose the workflow before writing it.
- [ ] **Replace the template `README.md`** with one for this project.

## Done

Closed items moved out of `## Open work` live in **`docs/TODO_archive.md`** — one line each below, reasoning there.

- [x] **Boundary build** — DONE 2026-10-15 · `docs/TODO_archive.md`

- [x] **Districts worked out per address at build time: proposal written, waiting on the owner.** — DECIDED 2026-10-15 · `docs/TODO_archive.md`

- [x] **Terrain, step 2: draw the terrain under the buildings and decide whether 30 m is enough.** · `docs/TODO_archive.md`

- [x] **Terrain: read the Edmonton window of MRDEM-30, check it, and pack it as elevation PMTiles.** · `docs/TODO_archive.md`

- [x] **Buildings, step 2: draw the tile files in MapLibre on a real phone** · `docs/TODO_archive.md`

- [x] **Check that GitHub Pages serves a `.pmtiles` file by range request, uncompressed, from a test deploy.** — 2026-08-07 · `docs/TODO_archive.md`

- [x] **Buildings, step 1: one trial tippecanoe build of the rooflines to PMTiles, and record the size.** · `docs/TODO_archive.md`

- [x] **Tile files: committed under `site/data/` or built at deploy.** — DECIDED 2026-10-13 · `docs/TODO_archive.md`

- [x] **Map: pick the stack.** — 2026-10-13 · `docs/TODO_archive.md`

- [x] 2026-10-10 — Brief §10 tasks 1–4: sources located and verified (`data/DATA.md`), point-in-polygon prototype measured (`prototype/README.md`), schema drafted (`docs/SPEC_data_schema.md`).
