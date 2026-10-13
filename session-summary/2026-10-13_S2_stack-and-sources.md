# Session handoff — 2026-10-13, S2: spec reconciliation, geography and terrain sources, stack locked

## 0. Session Metadata
- **Model:** Opus 5.5 (`claude-opus-5-5`), from the session's own context. No `/model` switch that I know of.
- **Effort:** `$CLAUDE_EFFORT` reads `high` (checked at handoff).
- **Date / session #:** 2026-10-12 to 2026-10-13, S2. One continuous session after a `/clear`; commits are dated 2026-10-13 UTC.

## 1. Goal
- **Project:** Edmonton Civic Map — a public reference tool answering "who represents me, and who is responsible for what?" for any Edmonton address. Descriptive only.
- **This session:** go over the Claude web reconciliation of the brief against the lens spec, settle the decisions it raised, find geography and terrain sources, and evaluate the Claude web stack report. Still no UI or pipeline code, and none was written.

## 2. Current State

### ✅ Completed
Merged to `master` through PRs #15–#21 (`master` at `77acef5`). **PR #22 is open** and carries the tile-files decision plus this handoff.

- **Reconciliation (web chat, 2026-10-12) verified row by row and applied** (PR #15). All eight rows held. `docs/SPEC_lenses.md` §2 now has a Status column so nothing unlocked reads as locked.
- **Decisions locked this session** (rows in `docs/DECISIONS.md`, all dated 2026-10-13):
  - Self-contained on GitHub Pages, for now: no request to any outside service. The owner's test for revisiting is speed, not privacy.
  - A different stack from `edmonton-tax-viz` only where a robust alternative exists (the 2026-10-10 row is marked AMENDED).
  - The answer comes before the map; a neighbourhood name is a way into the lookup.
  - Phone and desktop both work, neither is "first". "Mobile-first" was my wording in S1, not the owner's.
  - Buildings are the 2019 rooflines `jpxi-a9a5` pushed up to a flat roof. The City's 3D Buildings model is not used.
  - **The stack:** MapLibre GL JS 6 with its own layers and no deck.gl; PMTiles built with tippecanoe and GDAL; Vite with plain JavaScript modules; a static address index. Detail in `docs/SPEC_lenses.md` §8.
  - The address index is split per street (the owner: "fastest"), not hash buckets.
  - Tile files are committed under `site/data/` with a text manifest beside each, while each is under git's 100 MB limit (PR #22, open).
- **Geography sources from `edmonton-tax-viz`** recorded in `data/DATA.md`, "Buildings and physical barriers", as reported-not-rechecked: river and city limit from Alberta MapServer layers, roads from `9j8t-zm52`, and rail as 2,117 Railway rows in that same feed.
- **Terrain sources found** and recorded in `data/DATA.md`, "Terrain and elevation": federal MRDEM-30 (one 83.9 GB range-readable file) and 1 m HRDEM lidar of Edmonton (2.38 GB), both OGL-Canada; City bare-earth lidar 2019 and 2025 (about 26 GB each) and 0.5 m contours. Catalogue metadata and HTTP headers only.
- **City "3D Buildings" (`78sz-qcfr`) opened and counted:** 383,329 buildings as triangle meshes, 13.8 million triangles, median 28 per building; `ROOFFORM` is Gable on 94.5%; no licence stated. Numbers in `data/DATA.md`.
- **Stack report filed** at `/home/opc/research/edmonton-civic-map/stack_reply_2026-10-13.md` (outside the repo) and triaged into `TODO.md` and `docs/DECISIONS.md` (PR #21). Its library versions were checked against the npm registry: `maplibre-gl` 6.14.0, `pmtiles` 4.5.0, `vite` 8.3.4.

### ⚠️ In Progress (where exactly did we stop?)
- **Nothing half-edited.** The next piece of work, the trial building-tile build, was announced but not started.
- **PR #22 is open** at handoff. If it has merged by the time this is read, `docs/DECISIONS.md` has the tile-files row; if not, merge it first.
- **Asked `server`** to add an `edmonton-civic-map/` row to `/home/opc/research/README.md`. No reply seen.
- **Recommended by the stack report, not decided:** districts worked out per address at build time; our own URL state in place of MapLibre's `hash` option. Both are in `docs/SPEC_lenses.md` §8 and `TODO.md` "Build".
- **Left as is:** the name-decision date stays 2026-10-10 (UTC), with an amendment explaining that S1 ran across midnight Edmonton time. The owner did not rule on it.
- **Not confirmed by the owner:** that the Project picker has `docs/SPEC_lenses.md`, `docs/SPEC_data_schema.md` and `data/DATA.md` ticked (`TODO.md`, "Waiting on the owner"). The stack report did read the lens spec, so at least that one reached the web side somehow.
- **Still mine, not the owner's, in `docs/SPEC_lenses.md`:** §5 shared lens behaviours ("Proposed, not yet confirmed").

### ❌ Blocking Issues
None. 28 tests pass; no open GitHub issues.

## 3. Technical Learnings
- **The owner merges within minutes, every time.** All seven PRs this session merged before the next push. One push to a merged branch was blocked by `.githooks/pre-push`; the fix is `git checkout -B <new> origin/master && git cherry-pick <sha>`. Start each unit with `git fetch && git checkout -B <branch> origin/master`.
- **The owner's working style this session:** decides in one line when given a recommendation; wants the simplest option; cares about speed over request-level privacy ("i don't really care about that if other people already do it"). Asked more than once what a term meant, so explain mechanisms plainly.
- **`edmonton-tax-viz` has no basemap and no tiles**: an inline MapLibre style with one background layer, whole GeoJSON files, vendored libraries, no outside request. Its one profiled first load was GPU-bound, not network-bound (on this GPU-less server, so only relative). GitHub Pages answered range requests there on 2026-08-07, serves gzip only, and sets `cache-control: max-age=600`.
- **S1's "no terrain on the City portal" was wrong**: it never searched "elevation", "lidar" or "contour". Search the Socrata catalogue API (`https://api.us.socrata.com/api/catalog/v1?domains=data.edmonton.ca&q=...`) with several terms before recording "none found".
- **Federal elevation catalogue:** STAC at `https://datacube.services.geo.ca/stac/api`; `/search?collections=<id>&bbox=-113.72,53.39,-113.27,53.72`. Files live under `https://canelevation-dem.s3.ca-central-1.amazonaws.com/`. The older `datacube-prod-data-public` URL returns 403.
- **System Python 3.12's `urllib` reached `data.edmonton.ca`, `geo.ca`, the S3 bucket and `registry.npmjs.org` without `certifi`** this session. S1's TLS failures were on other hosts (`elections.ca`, `ourcommons.ca`, `edmonton.ca`).
- **Reading the 3D Buildings file geodatabase:** `pyogrio` refuses geometry type 1016 (TIN Z) in `list_layers`, `read_info` and `read_arrow`. `fiona` has no aarch64 wheel and will not build without `gdal-config`. What worked: `ctypes.CDLL` on the `libgdal-*.so` inside `site-packages/pyogrio.libs/`, after `import pyogrio` to set the data paths, calling the OGR C API directly.
- **Download endpoint for a Socrata blob:** `https://data.edmonton.ca/download/<id>/application%2Fx-zip-compressed` (225 MB in 16 s).
- **The rooflines layer already has `elevation_ground` and `elevation_rooftop`** per building, so nothing from the 3D model is needed to seat buildings on terrain.
- **Height figures disagree between the two building sources** (tallest 146.8 m in the rooflines catalogue figures against 198.9 m in the 3D model; 597 against 439 over 20 m). Not reconciled; recorded in `data/DATA.md`.
- **Alberta MapServer layers can return every feature with NULL geometry and HTTP 200** (reported by `edmonton-tax-viz`). Check geometry, not counts.
- **The 100 MB per-file limit is git's, not GitHub Pages'.** Pages limits: about 1 GB per site, a soft 100 GB a month, 10 minutes per deploy.
- **Unverified claim worth checking early:** the stack report says the Alberta commission's final report gives Edmonton 21 electoral divisions; the map in force has 20.
- **`tools/todo_archive.py`** moves any `- [x]` item to `docs/TODO_archive.md` and leaves a Done line; run it after ticking an item.
- **Scratch work is gone with the session:** the throwaway venv (pyogrio, numpy, shapely, pyarrow), the 3D Buildings download and the inspection scripts lived in the session scratchpad. Nothing from them is in the repo except the numbers.

## 4. Next Steps (prioritized)
1. **Press Sync in the claude.ai Project** (owner), after merging #22. Changed synced paths since the last handoff:
   ```
   docs/BRIEF.md
   docs/SPEC_civic_map.md
   docs/SPEC_data_schema.md
   docs/SPEC_lenses.md
   data/DATA.md
   ```
2. **Trial building-tile build** (`TODO.md`, "Map detail phase", step 1). Download the 384,228 rooflines of `jpxi-a9a5` (page on `:id`, 50,000 rows a page), check that every row has a height and a valid outline, build PMTiles at z12–z15 with height as the only attribute, and record bytes per zoom in `prototype/README.md`. tippecanoe is not installed on this server; building it from source or finding an aarch64 package is the first hurdle. Confirm each file is under 100 MB, which the tile-files decision depends on.
3. **Terrain window** (`TODO.md`, same section). Range-read the Edmonton bounding box of `mrdem-30-dtm.tif` with GDAL or rasterio, record CRS, vertical datum, elevation range and valley depth in `data/DATA.md`, then encode at 0.1 m steps and pack as PMTiles.
4. **Write two proposals before building anything** (CLAUDE.md "Propose the plan first"): districts worked out per address at build time, and the Vite build with its CI changes. Both are in `TODO.md` "Build" with what each must cover.
5. **Verify the "21 provincial divisions" claim** against `assembly.ab.ca` and record the result in `data/DATA.md`, "Provincial ridings".
6. **Ask the owner** to confirm or strike `docs/SPEC_lenses.md` §5, and whether the highways come from the City feed (my recommendation) and not OpenStreetMap, which `edmonton-tax-viz` uses and which is not a primary source.
7. **Check whether `server` added the research README row**; if `/home/opc/research/README.md` has no `edmonton-civic-map/` row, ask again.

## 5. Restoration Procedure
```bash
cd /home/opc/edmonton-civic-map
gh pr view 22 --json state -q .state   # merge it first if still OPEN
git checkout master && git pull --ff-only
git config core.hooksPath              # should print .githooks
gh issue list --state open             # nothing pushes these to a session
.venv/bin/python -m pytest tests -q    # 28 passed at handoff
```
For any measurement, make a throwaway venv with `python3.12 -m venv` in the session scratchpad; the repo's `.venv` has no geospatial libraries. Keep downloads in their own directory and run scripts that read them with `python -I`.
