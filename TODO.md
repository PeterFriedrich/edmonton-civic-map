# TODO

The source of truth for what's left. Read first every session; update in place.

**Format contract** (`tools/todo_archive.py` depends on it): top-level items are
`- [ ]` / `- [x]` lines directly under `## Open work`; `###` sub-headings may
group them; closed items are moved to `docs/TODO_archive.md` by the tool, which
leaves a one-line stub under `## Done`. An open item can be stale — reproduce the
symptom and re-measure the stated cause before acting on it.

## Open work

### Next session

### Waiting on the owner

- [ ] **Reopen "3D never encodes a quantity" for the density lens, or not.** Waits on the owner seeing 2D and 3D density examples from the stack report.
- [ ] **Confirm the Project picker has the synced set ticked.** The 2026-10-12 reconciliation chat reported only `docs/BRIEF.md`, `docs/DECISIONS.md` and `docs/SPEC_civic_map.md`; the set in `docs/CLAUDE_WEB.md` also has `docs/SPEC_lenses.md`, `docs/SPEC_data_schema.md` and `data/DATA.md`. (The stack research has since run and did read the lens spec.)
- [ ] **A trigger for a past `recheck_dates` entry: yes or no** (audit 2026-11-13, L4; `docs/ASSUMPTIONS.md` DA-7). Nothing compares those dates with today, and 2026-11-02 passed unnoticed. Options: a test that fails, or a refresh step that opens an issue. A CI change, so it waits for the owner.
- [ ] **Report data defects to the City.** The owner will send one report later, collecting what `docs/DATA_ISSUES.md` holds by then (2026-10-10). Done when each row there has a status other than NOT SENT.

- [ ] **Ask the City to publish its community league boundaries as open data** (owner decided 2026-10-17 to ask). The layer exists: `GDB.V_COMMUNITY_LEAGUES` on `gis.edmonton.ca/arcgisintegration/.../DPIM/DPIM_FS/FeatureServer/12`, 163 leagues with bylaw boundary text, no licence stated; the City's printed league map (2024-04-02) is no-reproduction (`data/DATA.md`, "Community leagues — City GIS service"). Ask via the open data portal's dataset request or Mapdesk@Edmonton.ca: publish under OGL – City of Edmonton, without the staff-logon and mailing-address columns. Can go with the defect report below. Claude drafts the request on asking; the owner sends it. Done when the City has answered and the answer is recorded; until then the communities lens uses neighbourhoods only.

### Sources still to verify

- [ ] **Statistics Canada attribution wording**, before ward populations are published: quote the Statistics Canada Open Licence's required statement in `data/DATA.md` and on the About page.
- [ ] **Post-2025-election ward boundary report (Policy C469B; due Q4 2026).** Recheck after 2026-12-31; Council documents on eScribe answer 403 to scripts, so read by hand. Done when its status, any proposed adjustments, and its ward populations are recorded in `data/DATA.md` "Ward boundary review", including whether Yellowhead Corridor West moves.
- [ ] **School-ward boundaries used in the 2025 election.** Both ward bylaws are online and were read on 2026-11-13 (`data/DATA.md` "School wards"). As read, the site names the other ward at 15928 Manning Drive NW and 610 Calgary Trail NW; 17611 34 Street NW, 903 Gateway Boulevard NW, 106 and 104 101 Street NW are open too (`docs/DATA_ISSUES.md` 2026-11-13; `docs/FINDINGS_district_assignment.md` L1). Claude drafts the question, quoting the bylaw text; the owner sends it to both boards and Edmonton Elections. Done when their answer on which lines the 2025 vote used at these six addresses is recorded.
- [ ] **Read the council ward bylaw by hand** (Bylaw 15142 as amended; the City's site answered 404 and 502 to scripts on 2026-11-13). Done when `data/DATA.md` "Council wards" records how it fixes the outer edge, against `docs/DATA_ISSUES.md` 2026-10-21.
- [ ] **Provincial boundaries: which map applies to the next election.** The committee reported on 2026-11-02 and no establishing bill was listed to 2026-11-05 (`data/DATA.md` "Provincial ridings", read 2026-11-13). Not verified: what the Assembly did with the report (a search result names a Government Motion 45), and the stack report's claim of 21 Edmonton divisions. Done when `data/DATA.md` records what was enacted and which map applies to the next provincial election.

### Map detail phase

- [ ] **Measure data used per view and per session, zoomed out and tilted.** A zoomed-out tilted session on the phone fetched 13.33 MB (`prototype/README.md`, "Buildings at z10 and z11"), most of it from the frame-rate fly-over. Done when the cost of the opening view and of a typical look around (zoom out, tilt, pan across the river) is recorded, and a size budget for one view is set, or the current cost is judged fine.
- [ ] **Build glyph files for Noto Sans and Noto Sans Canadian Aboriginal and test pihêsiwin and ᐱᐦᐁᓯᐏᐣ** on Android, iOS and desktop. Done when a test page shows both from our own files.
- [ ] **Find how much geographic detail the site can carry.** Start with "ghost buildings" (faint, translucent, from the 2019 rooflines layer `jpxi-a9a5`), then add terrain and detail in steps; at each step measure the published size against the host's limits, first-load time and frame rate on a mid-range phone. Done when the limits and the chosen level are recorded with their numbers, and a test holds the size budget.

### Lenses

- [ ] **Communities-of-interest lens** (`docs/SPEC_civic_map.md`, amendments). Before building: decide on community league boundaries: the City's GIS layer has 163 with no stated licence and covers 94% of addresses (`data/DATA.md`, "Community leagues — City GIS service"), so either ask the City to publish it under OGL or build the lens on neighbourhoods only; settle the threshold that separates a divided neighbourhood from a digitising sliver; decide what "shared services" means in data terms, if anything. Neighbourhoods are measured already (`data/DATA.md`, "Neighbourhoods").

- [ ] **Physical-and-natural-boundaries lens** (`docs/SPEC_civic_map.md`, amendments). Before building: download and check the road network's arterial classes; find primary sources for the river valley edge and rail lines (neither is a ready layer on the City portal). Candidates: `data/DATA.md`, "Buildings and physical barriers".

- [ ] **Population density lens** (`docs/SPEC_civic_map.md`, amendments): a density map with ward boundaries as an overlay, no number per ward. Parked until the owner has looked at 2D and 3D density maps. Growth is a later part: begin by finding how the City forecasts population and what it has stated (`data/DATA.md`, "Population and growth").

### Tier 2

### Build

- [ ] **`docs/ASSUMPTIONS.md` row for the census-day neighbourhood join** (`data/DATA.md` "Ward population"). The district rows DA-1 to DA-8 went in on 2026-11-13. Done when each premise a published number rests on has a row.
- [ ] **Flag addresses where sources disagree, whatever their distance from a line** (audit 2026-11-13, L0). A short hand-kept list with a `source_url` per entry; the card says the two maps differ there and links both lookups. A data-contract change: propose the plan first.
- [ ] **About page after the audit:** update the "Provincial boundaries may change" paragraph and the passed 2026-11-02 entry in `recheck_dates`; add a known limit saying the school wards are the City's drawing of the boards' bylaws.
- [ ] **Repeatable City-versus-board school-ward comparison** through every address, and a sweep of the rest of both ward lines against the bylaw text (audit 2026-11-13, L4; run by hand twice so far). The boards' layers state no licence: compare, do not publish. A new module: propose the plan first.
- [ ] **Parcels that lie across a district line** (audit 2026-11-13, L2). Find a City parcel-polygon source and count the parcels each layer's lines cross. Done when the count and the addresses are in `data/DATA.md`, and `docs/ASSUMPTIONS.md` DA-6 has a new status.
- [ ] **Measure weekly address churn, around 2026-11-27** (after 4–6 refresh runs): read the "N added, M removed" counts in the `Weekly refresh` commit messages and check the 1% stop line (`data/diff_rules.json` `parcel_rows_max_change`) against real weeks. Unmeasured so far: the address dataset keeps no history.
## Done

Closed items moved out of `## Open work` live in **`docs/TODO_archive.md`** — one line each below, reasoning there.

- [x] **Run the first audit: address → district assignment** — CLOSED 2026-11-13 · `docs/TODO_archive.md`

- [x] **The refresh can't fetch the MP list: ourcommons.ca answers 403 to the GitHub runner (issue #76).** — BUILT 2026-11-03 · `docs/TODO_archive.md`

- [x] **Survey what Tier 2 can say by automation.** — DONE 2026-10-17 · `docs/TODO_archive.md`

- [x] **A ward population newer than the 2021 Census** — CLOSED 2026-10-17 · `docs/TODO_archive.md`

- [x] **Join the 278 census neighbourhoods to the 407 neighbourhood polygons** — CLOSED 2026-10-17 · `docs/TODO_archive.md`

- [x] **Shareable view link** — CLOSED 2026-10-17 · `docs/TODO_archive.md`

- [x] **Neighbourhood search** — CLOSED 2026-10-17 · `docs/TODO_archive.md`

- [x] **Licence for the Elections Alberta boundary shapefile.** — DONE 2026-10-16 · `docs/TODO_archive.md`
- [x] **Exact attribution text for the Open Government Licence – Edmonton** — DONE 2026-10-16 · `docs/TODO_archive.md`

- [x] **Replace the template `README.md`** — DONE 2026-10-16 · `docs/TODO_archive.md`

- [x] **About and methodology page** — DONE 2026-10-16 · `docs/TODO_archive.md`

- [x] **Check every `landing_url` resolves** — DONE 2026-10-16 · `docs/TODO_archive.md`
- [x] **Weekly refresh workflow on GitHub Actions** — DONE 2026-10-16 · `docs/TODO_archive.md`

- [x] **Diff check and staleness guard** — DONE 2026-10-16 · `docs/TODO_archive.md`
- [x] **Boundary staleness in the page** — DONE 2026-10-16 · `docs/TODO_archive.md`

- [x] **The first lookup page.** — DONE 2026-10-16 · `docs/TODO_archive.md`

- [x] **Downloaders for the office-holder sources** — DONE 2026-10-16 · `docs/TODO_archive.md`

- [x] **Vite build and what it changes in CI** — DONE 2026-10-15 · `docs/TODO_archive.md`

- [x] **Build `src/build_address_index.py`** — DONE 2026-10-15 · `docs/TODO_archive.md`

- [x] **Boundary build** — DONE 2026-10-15 · `docs/TODO_archive.md`

- [x] **Districts worked out per address at build time: proposal written, waiting on the owner.** — DECIDED 2026-10-15 · `docs/TODO_archive.md`

- [x] **Terrain, step 2: draw the terrain under the buildings and decide whether 30 m is enough.** · `docs/TODO_archive.md`

- [x] **Terrain: read the Edmonton window of MRDEM-30, check it, and pack it as elevation PMTiles.** · `docs/TODO_archive.md`

- [x] **Buildings, step 2: draw the tile files in MapLibre on a real phone** · `docs/TODO_archive.md`

- [x] **Check that GitHub Pages serves a `.pmtiles` file by range request, uncompressed, from a test deploy.** — 2026-08-07 · `docs/TODO_archive.md`

- [x] **Buildings, step 1: one trial tippecanoe build of the rooflines to PMTiles, and record the size.** · `docs/TODO_archive.md`

- [x] **Tile files: committed under `site/public/data/` or built at deploy.** — DECIDED 2026-10-13 · `docs/TODO_archive.md`

- [x] **Map: pick the stack.** — 2026-10-13 · `docs/TODO_archive.md`

- [x] 2026-10-10 — Brief §10 tasks 1–4: sources located and verified (`data/DATA.md`), point-in-polygon prototype measured (`prototype/README.md`), schema drafted (`docs/SPEC_data_schema.md`).
