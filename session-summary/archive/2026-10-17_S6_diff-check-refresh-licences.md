# Session handoff — 2026-10-16/17, S6: diff check, weekly refresh, about page, licences

## 0. Session Metadata
- **Model:** Opus 5.5 (`claude-opus-5-5`), from the session's own context. No `/model` switch.
- **Effort:** `$CLAUDE_EFFORT` reads `medium` (checked at handoff).
- **Date / session #:** 2026-10-16 to 2026-10-17 (Edmonton), S6. One session, no `/clear`. PRs #47–#57, all merged.

## 1. Goal
- **Project:** Edmonton Civic Map, a public reference tool answering "who represents me, and who is responsible for what?" for any Edmonton address. Descriptive only.
- **This session:**
  1. build the diff check and staleness guard (spec §5–§6);
  2. build the weekly refresh (spec §8);
  3. write the About page and the README;
  4. license the repo, and fix the unlicensed provincial layer.

  It also took two template updates that `server` and `template` asked for.

## 2. Current State

### ✅ Completed (all merged)

**#47 Diff check.**
- **`src/diff_check.py`:** run as `--new <scratch> [--old site/public/data] [--report dir]`.
  - Exit codes: 0 pass, 1 review, 2 stop.
  - It writes `report.md` and `report.json`.
  - It works offline, and skips checks the builders already enforce.
- **Severities and thresholds:** set in **`data/diff_rules.json`**, including `geometry_threshold_m2: 10` and `parcel_rows_max_change: 0.01`.
- **Owner decisions:**
  - a change to a seat's `contact_url` or affiliation is held for **review**;
  - any other seat field change, and any change to a layer's dates, is also review.
- **`site/public/data/staleness.json`:** 45 and 180 days, plus 4 recheck dates, each from a statute or publisher:

  | Date | Event | Basis |
  |---|---|---|
  | 2026-11-02 | Alberta boundaries committee report | |
  | 2027-10-18 | Provincial general election | Election Act s.38.1 |
  | 2029-10-15 | Municipal general election | LAEA s.10(1)(b) and 11(1)(a) |
  | 2029-10-15 | Federal general election | Canada Elections Act s.56.1(2) |

  `app.js` reads this file; the boundary warning appears on each layer's cards.

**#48, #49 Template updates** (`0907382 → bbc82eb → e79c7b1`).
- `bootstrap.sh` builds the venv with uv; `scripts/check_requirements.py` joins the merge gate.
- `prototype/terrain.py`'s imports are marked `# noqa: requirements`: it was a one-off build in its own venv.
- `.venv` was rebuilt with uv. `df` showed no saving, because the uv cache was new.

**#50 Weekly refresh: `.github/workflows/refresh.yml`.** Mondays 10:00 UTC, plus `workflow_dispatch`.
- **Steps:** download, rebuild into `$RUNNER_TEMP/rebuild`, diff check, copy into place, `scripts/check_refresh_diff.py`, pytest, build, `check:dist`, smoke.
- **On a pass:** commit to master as `github-actions[bot]`, then `gh workflow run pages.yml`. A push made with `GITHUB_TOKEN` triggers no other workflow, so the deploy is started explicitly.
- **On a hold or failure:** the run goes red and files one issue labelled `refresh`, or comments on the open one.
- **`src/download.py`:** GETs every `landing_url`.
- **robots.txt:** checked once by hand for all sources; the result is in `data/DATA.md`.

**#51 `scripts/check_refresh_diff.py`.** A passing refresh may change only:
- `last_verified`;
- in `layers.json`, also `source_sha256` and `addresses_checked`;
- the address files.

**#53 ARM runner.** The first refresh run (38848809606, issue #52) held on 13 m² of float noise: the x86 runner versus this aarch64 server. The refresh now runs on `ubuntu-24.04-arm`. The second run (38925804720) passed and committed `376288f`.

**#54 New pass rule `address_point_moved`.**

**#55 `site/about.html`**, a third Vite entry, with `site/src/about.js`.
- The text is owner-approved. Corrections go to GitHub issues.
- Its numbers are read from the published files.
- The council note cites MGA s.154 and s.182, read in the King's Printer PDF, and EPCOR's own Edmonton page.

**#56 README** for this project.

**#57 Provincial layer, licences, two fixes.**
- **Provincial source:** `ab_ridings` now comes from the Government of Alberta's "Provincial Electoral Division - Current 2019", under OGL – Alberta.
  - ArcGIS layer: `geospatial.alberta.ca/titan/.../goa_administrative_area_10tm_nad83_aep/MapServer/3`.
  - New download `kind: "arcgis"`.
  - Against the old Elections Alberta copy: the same 87 divisions and names, at most 1.264 m apart (Hausdorff), and every address in the same division.
  - Why: Elections Alberta's shapefile states no licence, and the layer had shipped on 2026-10-15 despite the TODO saying it could not.
- **Licences:**
  - `LICENSE` is MIT with carve-outs; `LICENSE-docs` is CC BY 4.0. Both are copied from `edmonton-tax-viz`, which helped.
  - `tests/test_license.py` guards the carve-outs.
  - The About page carries the 3 OGL sentences verbatim, pinned by `test_about_page_carries_each_prescribed_attribution_verbatim`, plus a non-endorsement line.
- **Tie fix:** in `src/build_address_index.py`, a two-parcel tie now goes to the first row (the distance is rounded to 0.01 m²).
  - **Correction:** the six "City moved points" in `376288f` (and in #54's text) were really this tie, broken differently on the runner. The parcel sha was identical.
  - As a one-time effect, 678 records changed their stored point.
- **Gateway retry:** 502, 503 and 504 now retry like network errors.
- **Data rebuilt** (diff: review, as expected for a source switch).

**TODO:** 9 items closed and archived. Added:
- measure weekly address churn around 2026-11-27;
- Statistics Canada attribution wording, before ward populations are published.

### ⚠️ In Progress
- When this handoff was written, the Tests and Pages runs for the #57 merge had not finished. Check them first (Next Steps 2).
- No code work is half-done. The local branch is `handoff-s6`.

### ❌ Blocking Issues
None. No open GitHub issues; #52 is closed. Disk: 13 GB free.

## 3. Technical Learnings
- **The build is reproducible on one CPU architecture only.**
  - x86 and aarch64 give different floats after PROJ reprojection and GEOS simplification. A vertex near the 5 m tolerance can be kept on one and dropped on the other.
  - Exact ties decided by float noise also differ between two aarch64 machines.
  - So: build anything you commit on aarch64, and break every tie explicitly.
- **The diff check compares geometry even when the source sha256 is unchanged.** That's what caught the cross-architecture noise. Keep it.
- **OGL – City of Edmonton text, from the primary source** (method from `edmonton-tax-viz`):
  - GET `https://data.edmonton.ca/stories/s/msh8-if28.json`;
  - take the signed S3 `url` (valid 1 h) and GET it;
  - strip the tags.

  The prescribed sentence is "Contains information licensed under the Open Government Licence – City of Edmonton." OGL – Alberta (v2, `open.alberta.ca/licence`) and OGL – Canada use the same pattern.
- **open.alberta.ca CKAN search:** `https://open.alberta.ca/api/3/action/package_search?q=title:electoral`. Layers 4 and 5 of the same ArcGIS service are the historical 2010 and 2003 divisions.
- **open.canada.ca returned 504/502 for minutes on 2026-10-16.** It's `fed_ridings`' landing page, so a refresh can hold on it. The zip itself comes from elections.ca.
- **Rebuilding locally:** download fresh first (`python -m src.download`). A stale `data/raw` rebuild reverts the published data, and that shows only as pass-level `address_point_moved` rows.
- **actionlint:** pinned 1.7.7, downloaded into scratch (`actionlint_1.7.7_linux_arm64.tar.gz`); there is no system install.
- **PDF text on this box:** there's no `pdftotext`. Use `python3.12 -m pip install --target <scratch> pypdf`, then `pypdf.PdfReader`.
- **`workflow_dispatch` on a branch would push that branch's HEAD to master** (`git push origin HEAD:master`). Only dispatch the refresh on master.
- **Peers:**
  - `edmonton-tax-viz` owns the licence pattern (its `LICENSE`, `LICENSE-docs`, `tests/test_license.py`, and its DECISIONS rows of 2026-07-26 and 2026-09-20).
  - Its advice for an unlicensed source: look for an explicitly licensed copy first.

## 4. Next Steps (prioritized)
1. **Press Sync in the claude.ai Project** (owner):
   ```
   docs/BRIEF.md
   docs/SPEC_data_schema.md
   data/DATA.md
   ```
2. **Confirm #57 deployed:** `gh run list --branch master --limit 3` shows Tests and Pages succeeding for "Merge pull request #57". Then confirm the live site carries the licence lines: `curl -s https://peterfriedrich.github.io/edmonton-civic-map/about.html | grep -c 'Open Government Licence – Alberta'`.
3. **After Monday 2026-10-19's refresh:** it should pass with **no** `address_point_moved` rows. If point moves appear with an unchanged parcel sha, the tie fix didn't hold: compare runner and server output for those addresses.
4. **Neighbourhood search:** propose the new published file of the 407 names from `65fr-66s6` first (`docs/SPEC_lenses.md` §3).
5. **Shareable view link** (`docs/SPEC_lenses.md` §5).
6. **Research TODOs:**
   - school-ward boundaries against each board's bylaw;
   - a ward population newer than 2021;
   - the post-2025 ward boundary report (Policy C469A).
7. **Carried:**
   - after 2026-11-02, check the Alberta committee report, and whether open.alberta.ca publishes a successor layer;
   - measure address churn around 2026-11-27;
   - the City defect report (`docs/DATA_ISSUES.md`, two rows not sent; owner).

## 5. Restoration Procedure
```bash
cd /home/opc/edmonton-civic-map
git fetch && git checkout master && git pull --ff-only
git config core.hooksPath                 # .githooks
gh issue list --state open
./bootstrap.sh                            # uv venv, pytest, guards (venv has no pip: use `uv pip install --python .venv/bin/python`)
npm ci
.venv/bin/python -m pytest tests -q       # 127 passed
npm run test:js
# data (data/raw is git-ignored; download fresh before any rebuild you commit):
.venv/bin/python -m src.download
S=<scratch>/rebuild
.venv/bin/python -m src.build_boundaries --out $S
.venv/bin/python -m src.build_address_index --out $S   # ~6 min
.venv/bin/python -m src.build_officeholders --out $S
.venv/bin/python -m src.diff_check --new $S            # 0 pass / 1 review / 2 stop
# site:
npm run build && npm run check:dist
PLAYWRIGHT_BROWSERS_PATH=<scratch>/pw npx playwright install chromium && PLAYWRIGHT_BROWSERS_PATH=<scratch>/pw npm run smoke
```
Check `df -h /` before any build that writes more than ~500 MB.
