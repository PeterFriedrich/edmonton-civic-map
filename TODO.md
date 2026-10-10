# TODO

The source of truth for what's left. Read first every session; update in place.

**Format contract** (`tools/todo_archive.py` depends on it): top-level items are
`- [ ]` / `- [x]` lines directly under `## Open work`; `###` sub-headings may
group them; closed items are moved to `docs/TODO_archive.md` by the tool, which
leaves a one-line stub under `## Done`. An open item can be stale — reproduce the
symptom and re-measure the stated cause before acting on it.

## Open work

### Waiting on the owner

- [ ] **Map: pick the stack.** The owner wants a 2D/3D geographic map on a stack other than the tax viz's MapLibre + deck.gl (`docs/SPEC_civic_map.md`, amendments). If the owner wants options, survey candidates against boundary layers, in-browser address search, terrain and buildings in 3D, and mobile, and report before choosing.
- [ ] **Report data defects to the City.** The owner will send one report later, collecting what `docs/DATA_ISSUES.md` holds by then (2026-10-10). Done when each row there has a status other than NOT SENT.

### Sources still to verify

- [ ] **Licence for the Elections Alberta boundary shapefile.** None is stated on the download page (`data/DATA.md`, "Provincial ridings"). Done when a written licence or permission is recorded there; until then the provincial layer cannot ship.
- [ ] **Exact attribution text for the Open Government Licence – Edmonton**, and Statistics Canada's for the ward populations. Done when `data/DATA.md` quotes both.
- [ ] **Post-2025-election ward boundary report (Policy C469A).** Not found; the City's ward-boundary-review page returned 404 on 2026-10-10. Done when the report's status and any proposed adjustments are recorded in `data/DATA.md`.
- [ ] **A ward population newer than the 2021 Census**, from a primary source. Done when found, or when recorded as not existing.
- [ ] **School-ward boundaries used in the 2025 election** — confirm against each board's ward bylaw that they match the City layers.
- [ ] **Recheck the provincial boundary process after 2026-11-02**, when the Select Special Committee on Electoral Boundaries must report. Done when `data/DATA.md` records what was tabled and whether anything is enacted.

### Map detail phase (after the lookup works on the chosen stack)

- [ ] **Find how much geographic detail the site can carry.** Add terrain, then buildings, in steps; at each step measure the published size against the host's limits, first-load time and frame rate on a mid-range phone. Done when the limits and the chosen level are recorded with their numbers, and a test holds the size budget.

### Lenses

- [ ] **Communities-of-interest lens** (`docs/SPEC_civic_map.md`, amendments). Before building: find a primary source for community league boundaries (not on the City portal); settle the threshold that separates a divided neighbourhood from a digitising sliver; decide what "shared services" means in data terms, if anything. Neighbourhoods are measured already (`data/DATA.md`, "Neighbourhoods").

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
