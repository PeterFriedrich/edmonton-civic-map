# Session handoff — 2026-10-14, S3: building and terrain tiles, live test page, phone tests

## 0. Session Metadata
- **Model:** Opus 5.5 (`claude-opus-5-5`), from the session's own context. No `/model` switch that I know of.
- **Effort:** `$CLAUDE_EFFORT` reads `high` (checked at handoff).
- **Date / session #:** 2026-10-13 evening to 2026-10-14 (Edmonton), S3. Commits are dated 2026-10-14 UTC. One session after a `/clear`.

## 1. Goal
- **Project:** Edmonton Civic Map, a public reference tool answering "who represents me, and who is responsible for what?" for any Edmonton address. Descriptive only.
- **This session:** prove the map-detail layers on the locked stack. Build the 2019 rooflines and the terrain as PMTiles, measure them, publish a test page on GitHub Pages, and get frame rates from the owner's phone and laptop. No app code; still feasibility work.

## 2. Current State

### ✅ Completed
All merged to `master` through PRs #23–#25 and #27–#30 (`master` at `d52ebb4`). PR #26 was closed unmerged on purpose (below).

- **Trial building tiles** (#23): all 384,228 rooflines of `jpxi-a9a5`, height `h` the only attribute. `prototype/rooflines.py` downloads (pages on `:id`, count matches `count(*)`), checks (every row has a height ≥ 1.02 m and an outline; 325 outlines self-intersect and are tiled as published) and writes `heights.ndjson`.
- **Zoom levels** (#29): buildings now start at z10. `MIN_AREA = ((10, 400), (11, 150), (12, 50))` in `prototype/rooflines.py` sets each building's tippecanoe `minzoom` by footprint; all show from z13. File **28.0 MB** (was 26.8 at z12–z15). Busiest tiles: z11 454 kB, z12 402 kB. Variant z10 ≥ 200 / z11 ≥ 50 m² rejected (busiest z11 tile 989 kB).
- **GitHub Pages is on, deploying by Actions** (owner turned it on, source "GitHub Actions"). Site: https://peterfriedrich.github.io/edmonton-civic-map/
  - `.github/workflows/pages.yml` (#24, CI change approved in session): on push to master touching `site/**` or by hand, `sha256sum --check --strict` on `site/vendor/SHA256SUMS`, then upload `site/` as-is with `actions/upload-pages-artifact` v5.0.0 and `actions/deploy-pages` v5.0.1, pinned to commit SHAs. No build step, no cache busting.
  - `site/index.html`: the **test page**, not the app. Flat/Tilted, Solid/Translucent, No terrain/Shading/3D ground, a fixed 10-second frame-rate fly-over, first-draw time, tile bytes (Resource Timing), live range-request check. No outside requests.
  - `site/vendor/`: MapLibre GL JS 6.14.0 (`maplibre-gl.mjs`, `maplibre-gl-worker.mjs`, `maplibre-gl.css`) and pmtiles 4.5.0 (`pmtiles.js`), npm integrity hashes checked, licences beside them.
  - `site/data/buildings.pmtiles` (28.0 MB) and `site/data/terrain.pmtiles` (2.69 MB), each with a `.manifest.txt` per the 2026-10-13 tile-files decision. `tiles_sha256` in each manifest is stable across rebuilds; the file bytes are not.
- **Range requests on Pages** (#25): work for browsers. See learnings for the gzip trap.
- **Terrain** (#27): `prototype/terrain.py` range-reads the Edmonton window of MRDEM-30 in ~15 s and writes Terrain-RGB PNG tiles z9–z12 (2.69 MB). `data/DATA.md` "Terrain and elevation" records: EPSG:3979, 30 m; heights in the city 602.1–752.2 m; river valley about 48–59 m deep on four cross-sections; vertical datum not stated, and MRDEM reads 0.48 m lower than the City's `elevation_ground` at the median (19,110 buildings).
- **Phone and laptop tests** (all in `prototype/README.md`). iPhone 14 Plus, Safari:
  - 60 fps tilted, solid and translucent;
  - 60 fps tilted with 3D ground;
  - 59 fps at z10.4 tilted with 3D ground;
  - 1.25 s first draw in a private window.

  Laptop (144 Hz): 127–144 fps.
- **Decision locked** (`docs/DECISIONS.md`, 2026-10-14): terrain is MRDEM-30 at 30 m. Owner: "it's plenty". 1 m lidar not needed.
- **TODO items closed:**
  - Buildings step 1 and step 2;
  - Pages range check;
  - Terrain;
  - Terrain step 2.

  New: "Measure data used per view and per session".
- **Stale TODO note fixed:** "Blocks the stack research run" removed from the Project-picker item.

### ⚠️ In Progress (where exactly did we stop?)
- **Nothing half-edited.** All work is merged; the working tree is clean on branch `zoomed-out-readings` (merged).
- **Not measured:** tilted + translucent + 3D ground on the phone.
- **Template update not evaluated:** session start reported `scripts/handoff_gap.py` and `tests/test_handoff_gap.py` changed upstream (`474d0b1...2696438`). Told the owner; not applied, not reviewed.
- **Still waiting on the owner (from S2):** confirm or strike `docs/SPEC_lenses.md` §5; highways from the City feed (recommended) or OpenStreetMap.

### ❌ Blocking Issues
None. 28 tests pass; no open GitHub issues.
- **Disk is tight:** `/` was at 97% (1.3 GB free) during handoff, 2.1 GB after deleting spare tile builds from the scratchpad. The repo now carries ~31 MB of tiles, and every tile rebuild adds its full size to git history.

## 3. Technical Learnings
- **tippecanoe needs no compiling here:** the PyPI wheel `tippecanoe==2.72.0` ships an aarch64 binary (upstream is 2.79.0). The pmtiles CLI is go-pmtiles 1.31.2 (`gh release download v1.31.2 -R protomaps/go-pmtiles -p '*Linux_arm64*'`). Per-zoom sizes come from the `pmtiles` Python reader (`pmtiles.reader.all_tiles`).
- **tippecanoe output is not byte-reproducible** (metadata differs run to run, with or without `-P`), but tile contents are identical. Hence `tiles_sha256` in the manifests.
- **The busiest z12 building tile stays under tippecanoe's 500 kB default cap.** The capped and uncapped builds were the same.
- **GitHub Pages gzip trap:** Pages compresses `application/octet-stream` on the fly. A range request with `Accept-Encoding: gzip` gets `206` with ranges of the **gzipped** stream (`content-range: .../26793940` against 26,800,417 bytes), which PMTiles can't read. Browsers send `identity` with any `Range` header (Fetch standard), so the site works. **Check with curl and no `Accept-Encoding`, never `--compressed`.** Pages also sends `cache-control: max-age=600` and a weak etag, which the PMTiles reader ignores.
- **Resource Timing reports cached responses as 0 bytes.** The phone's first "0.00 MB in 30 requests" was a repeat visit, not missing support. PR #26 (count bytes in the page) was closed for that reason. Ask for a private window for first-load numbers.
- **MapLibre 6 is ESM-only:** `import * as maplibregl from "./vendor/maplibre-gl.mjs"`. It finds `maplibre-gl-worker.mjs` beside itself via `import.meta.url`, so no worker setup is needed. pmtiles 4.x is a classic script (global `pmtiles`); register with `maplibregl.addProtocol("pmtiles", new pmtiles.Protocol().tile)`.
- **Terrain in MapLibre:** separate `raster-dem` sources for hillshade and terrain (MapLibre's guidance), `encoding: "mapbox"`, `tileSize: 256`. Buildings sit on the 3D terrain without extra work.
- **Reading MRDEM-30:** no-data −32767; LZW COG with overviews. Read with rasterio 1.5.2 (bundled GDAL 3.12.2) via `/vsicurl/` and `GDAL_DISABLE_READDIR_ON_OPEN=EMPTY_DIR`. Pad the read window a few cells, or bilinear leaves empty edge pixels.
- **Local testing:** Playwright browsers are cached at `~/.cache/ms-playwright/` (`chromium_headless_shell-1228`). `pip install playwright` in a scratch venv and launch with `executable_path=` that `headless_shell`, `--use-angle=swiftshader --enable-unsafe-swiftshader`.
  - Python's `http.server` has no Range support. A ~20-line subclass that answers `206` was used (scratchpad only).
  - **Port 8765 is taken by another service on this machine**; bind port 0 and use what it gives.
  - Headless frame rates are software rendering and mean nothing.
- **Owner style this session:** decides quickly; asked plain-language questions ("what are pmtiles", "higher layers have less buildings?"). Explain mechanisms before options. They turned on Pages themselves when told it needed a setting.
- **Cross-session mix-up (resolved):** the owner pasted a Claude web stack report for `edmonton-open-data-landscape` here. It was filed at `/home/opc/research/edmonton-open-data-landscape/stack_reply_2026-10-13.md`, and an evaluation went to that session, which triaged it (its PRs #29/#30). Nothing of it belongs to this repo.

## 4. Next Steps (prioritized)
1. **Press Sync in the claude.ai Project** (owner). Changed synced paths since the S2 handoff:
   ```
   docs/BRIEF.md
   data/DATA.md
   ```
2. **Write the two proposals** (CLAUDE.md "Propose the plan first"; `TODO.md` "Build"):
   - **(a) Districts worked out per address at build time:** the per-street index format, the 9,923 parcel rows sharing a house number and street, how the diff check covers the index, and a test comparing every stored district with point-in-polygon.
   - **(b) The Vite build and its CI changes:** it replaces the test page's no-build deploy in `.github/workflows/pages.yml`, adds cache busting (`docs/WEB_CACHE_BUSTING.md`), and should gate the deploy on tests.
3. **Glyph files for Noto Sans and Noto Sans Canadian Aboriginal**, tested with pihêsiwin and ᐱᐦᐁᓯᐏᐣ on Android, iOS and desktop (`TODO.md` "Map detail phase").
4. **Measure data per view and per session**, zoomed out and tilted (new `TODO.md` item). The test page has no way to jump to a fixed view without the fly-over; a URL parameter for the view would make this repeatable.
5. **Evaluate the template update** (`scripts/handoff_gap.py`, `tests/test_handoff_gap.py`; `docs/COPIER.md` §"When the session-start notice appears"). Tell the owner; don't apply unasked.
6. **Carried from S2:**
   - verify the "21 provincial divisions" claim against `assembly.ab.ca`;
   - ask the owner about `docs/SPEC_lenses.md` §5 and the highways source.

## 5. Restoration Procedure
```bash
cd /home/opc/edmonton-civic-map
git fetch && git checkout master && git pull --ff-only
git config core.hooksPath              # should print .githooks
gh issue list --state open             # nothing pushes these to a session
.venv/bin/python -m pytest tests -q    # 28 passed at handoff
gh run list --workflow pages.yml -L 3  # last deploy should be green
```
For tile or terrain work, make a throwaway venv in the session scratchpad:
```bash
python3.12 -m venv venv && venv/bin/pip install tippecanoe==2.72.0 'shapely>=2.1' numpy pmtiles rasterio pillow
venv/bin/python prototype/rooflines.py work/        # ~220 MB download + heights.ndjson
venv/bin/tippecanoe -P -f -o work/buildings.pmtiles -l buildings -n buildings \
  -N "City of Edmonton Rooflines (as of 2019), jpxi-a9a5, height only" \
  -Z10 -z15 --no-feature-limit --no-tile-size-limit work/heights.ndjson
curl -o wards.geojson 'https://data.edmonton.ca/resource/b4er-5rp2.geojson'
venv/bin/python prototype/terrain.py wards.geojson work/
```
Check free disk first (`df -h /`); keep downloads out of the repo.
