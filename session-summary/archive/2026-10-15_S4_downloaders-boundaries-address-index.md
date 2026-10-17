# Session handoff — 2026-10-15, S4: template update, owner decisions, downloaders, boundary build, address index

## 0. Session Metadata
- **Model:** Opus 5.5 (`claude-opus-5-5`), from the session's own context. No `/model` switch.
- **Effort:** `$CLAUDE_EFFORT` reads `medium` (checked at handoff).
- **Date / session #:** 2026-10-14 to 2026-10-15 (Edmonton), S4. One session, no `/clear`.

## 1. Goal
- **Project:** Edmonton Civic Map, a public reference tool answering "who represents me, and who is responsible for what?" for any Edmonton address. Descriptive only.
- **This session:** clear the owner's open questions, then build the data pipeline up to the address index: downloaders → boundary build → per-address districts. The first real `src/` code in the repo.

## 2. Current State

### ✅ Completed
All merged to `master` (PRs #33–#40, `master` at the #40 merge; `f51847b` confirmed on `origin/master`). Pages deploys for #39 and #40 are green. 59 tests pass.

- **#33 Template update** `474d0b1 → e051159`: all 4 files taken (`scripts/handoff_gap.py` merged-branch reminder at 90, `tests/test_handoff_gap.py`, `docs/TOKEN_EFFICIENCY.md` "Disk", one `CLAUDE.md` line). No conflicts.
- **#34 Highways source:** the owner chose the City road network feed `9j8t-zm52`, not OpenStreetMap. DECISIONS row; `docs/SPEC_lenses.md` §4.3.
- **#35 `docs/SPEC_lenses.md` §5** (five shared lens behaviours) confirmed as written. DECISIONS row.
- **#36 + #37 Address index decided:** `docs/SPEC_data_schema.md` §9 (proposal, measured), then the owner's answers to §9.6:
  1. split addresses show every district set, with a note;
  2. new addresses publish without review, "for now";
  3. the near-edge note names the layer;
  4. new module `src/build_address_index.py`.

  `prototype/address_districts.py` + `prototype/README.md` "Districts per address" hold the measurement.
- **#38 `src/download.py`** (plan approved in session): `python -m src.download [ids…] [--out DIR]`.
  - Six sources: `coe_parcels` (`ut27-nrpn`, PARCEL rows, 5 columns), `coe_wards`, `coe_public_school_wards`, `coe_catholic_school_wards`, `ab_ridings`, `fed_ridings`.
  - Socrata sources are paged 50,000 on `:id` and checked against `count(*)`. The zips are unpacked and counted with pyshp.
  - Fixed counts 12/9/7/87/343; fails on zero rows or any non-200; 2 retries on network errors only.
  - Writes to `<id>.partial` and swaps it in only on success. `fetch.json` carries the §2 fields; `attribution` is null, and the `ab_ridings` licence is null.
  - Live run: all pass, 298,453 / 12 / 9 / 7 / 87 / 343 rows, about 30 s, 43 MB in `data/raw/` (git-ignored, present on this server).
- **#39 `src/build_boundaries.py`** (plan approved in session): `python -m src.build_boundaries [--raw] [--out]`, about 40 s.
  - The city outline is the union of the 12 council wards (no City boundary file is sourced). Ridings are clipped to it, keeping every one that shares area: 29 provincial, 13 federal.
  - `shapely.coverage_simplify` at 5 m in EPSG:3776, then rounded to 6 decimals in lon/lat. Rings that rounding pinches are repaired with `make_valid`; parts dropped and area change go into `layers.json`.
  - Stops on any address that changes district, lands in none or in two, a count mismatch, or empty/invalid output.
  - Output: `site/data/boundaries/<layer>.geojson` (district_id + name, one feature per line) and `site/data/layers.json`. About 160 kB gzipped; the rebuild is byte-identical.
  - DECISIONS row: **boundaries ship as GeoJSON, an exception to "every layer PMTiles"** (owner approved).
  - New `docs/DATA_ISSUES.md` row (NOT SENT): 4 of 5 source layers aren't clean coverages (small overlaps and gaps). Federal is clean.
- **#40 `src/build_address_index.py`:** `python -m src.build_address_index [--raw] [--out]`, about 5½ minutes, nearly all of it the node checks.
  - Output `site/data/addresses/`:
    - `streets.json` (2,800 `[street, file]`);
    - one `<street>.json` per street: house → `[[lat, lon, 5 district_ids, near-edge bitmask]]`;
    - `manifest.txt`.
  - Checks, all passing:
    - §9.5 check 1: `prototype/pip.js` under node agrees with shapely on all 298,453 rows at full resolution (ridings city-clipped first, for speed);
    - check 2: every record's stored point agrees on the **published** boundary files;
    - check 3: rows in = rows accounted for;
    - check 4: a unit test over the committed files.
  - Results: 8 split addresses, 1,342 rows within 20 m of an edge.
  - Size: 3.10 MB gzipped (the proposal said 2.33 MB; it's bigger because of full ids and 6 decimals), 45 MB raw. The rebuild is byte-identical.
- **TODO.md:**
  - closed: address-index proposal, Boundary build, Build `src/build_address_index.py`;
  - "Downloaders" reworded to the office-holder sources only;
  - the §9.4 diff-check rows moved onto the "Diff check and staleness guard" item.

### ⚠️ In Progress
Nothing half-done. The working tree is clean apart from this handoff.

### ❌ Blocking Issues
None. No open GitHub issues at session start or at handoff.

## 3. Technical Learnings
- **Socrata `rowsUpdatedAt`** for the City layers read 2026-10-12 on 2026-10-15 (was 2026-10-05). Parcel rows rose from 298,238 (2026-10-10) to 298,453.
- **Elections Alberta** returns 403 to Python's default User-Agent; any UA naming the project works (recorded in `data/DATA.md`).
- **Elections Canada needs certifi**, as `data/DATA.md` already said: system curl fails on the Sectigo R46 root. `src/download.py` uses `ssl.create_default_context(cafile=certifi.where())`.
- **HTTP header case varies:** `urllib` gave `last-modified` in lower case for Elections Alberta. The zip fetch lower-cases keys before reading.
- **numpy 2 `repr()`** prints `np.float64(…)`. Writing numbers for node with `f"{x!r}"` broke every row; use `float(x)`.
- **Rounding to 6 decimals after coverage_simplify** can make a valid ring self-touch. `make_valid` can then return a GeometryCollection holding a MultiPolygon, so flatten with `shapely.get_parts(shapely.get_parts(g))`. A first fix that dropped invalid parts dropped a whole Edmonton riding; the build's own checks caught both mistakes.
- **GEOS `coverage_clean`** (shapely 2.2 / GEOS 3.14) makes coverages valid but moved small edge ridings by up to 9.7 km (Hausdorff). Rejected.
- **pip.js is a plain O(points × vertices) scan.** Unclipped federal (1.1 M vertices, all of Canada) is far too slow; city-clipped is about 14k vertices and fine. The app should add a bbox prefilter before it runs on unclipped data.
- **Near-edge distances use the unclipped layers.** The city edge is not a district edge.
- **`pkill -f <pattern>` / `pgrep -f` inside a Bash call matches the calling shell's own command line** and kills it (exit 144). Use a pattern that can't appear in your own command, or a PID.
- **`scripts/check_doc_citations.py` false positive:** it resolves `prototype/README.md "Title"` to the root `README.md` and warns. Warnings only. `README.md: 0` in a code comment reads as a line-number citation and **errors**.
- **`scripts/check_decisions_log.py`** wants the test name inside the decision text column, not only in the pointer column.
- `tests/test_build_address_index.py` imports `src.*` by putting the repo root on `sys.path`. `src/build_address_index.py` does `from src import build_boundaries as bb`, so run modules as `python -m src.<name>` from the repo root.
- **Disk:** 8.5 GB free at handoff. Scratch venvs and downloads deleted; `data/raw/` (43 MB) kept.

## 4. Next Steps (prioritized)
1. **Press Sync in the claude.ai Project** (owner):
   ```
   docs/BRIEF.md
   docs/SPEC_lenses.md
   docs/SPEC_data_schema.md
   data/DATA.md
   ```
2. **Propose the Vite build and its CI changes** (`TODO.md` "Build"; needs the owner's OK). It replaces the no-build Pages deploy in `.github/workflows/pages.yml`, adds cache busting (`docs/WEB_CACHE_BUSTING.md`), and should gate the deploy on tests. Now worth doing: there is published data for an app to read.
3. **Downloaders for the office-holder sources**, added to `src/download.py` (`TODO.md`):
   - `e9qt-cc3j`, `fv5x-8efu`, `eg3i-f4bj`;
   - Assembly `contacts.csv`: line 1 is a banner;
   - House of Commons CSV: has U+202F in `Start Date`;
   - the two trustee pages: scrapers must fail on a layout change.

   Then `officeholders.json` (§4).
4. **Diff check and staleness guard** (§5–§6 plus the §9.4 address rows), then the weekly refresh workflow (§8; CI change, so propose first).
5. Glyph files for Noto Sans and Noto Sans Canadian Aboriginal; measure data per view (`TODO.md` "Map detail phase").
6. Owner items still open in `TODO.md` "Waiting on the owner": the City defect report now has two NOT SENT rows in `docs/DATA_ISSUES.md`.
7. Carried: verify the "21 provincial divisions" claim against `assembly.ab.ca`; the Select Special Committee reports by 2026-11-02.

## 5. Restoration Procedure
```bash
cd /home/opc/edmonton-civic-map
git fetch && git checkout master && git pull --ff-only
git config core.hooksPath                 # .githooks
gh issue list --state open
.venv/bin/pip install -r requirements.txt # now has certifi, pyshp, numpy, pyproj, shapely
.venv/bin/python -m pytest tests -q       # 59 passed at handoff
# full pipeline (needs node for the address index):
.venv/bin/python -m src.download          # ~30 s, 43 MB into data/raw/
.venv/bin/python -m src.build_boundaries  # ~40 s
.venv/bin/python -m src.build_address_index  # ~5.5 min
git status                                # a rebuild from unchanged sources shows no diff
```
Check `df -h /` before any build that writes more than ~500 MB.
