# Session handoff — 2026-10-15/16, S5: template update, Vite build, office holders, the lookup page

## 0. Session Metadata
- **Model:** Opus 5.5 (`claude-opus-5-5`), from the session's own context. No `/model` switch.
- **Effort:** `$CLAUDE_EFFORT` reads `medium` (checked at handoff).
- **Date / session #:** 2026-10-15 evening to 2026-10-16 (Edmonton), S5. One session, no `/clear`.

## 1. Goal
- **Project:** Edmonton Civic Map, a public reference tool answering "who represents me, and who is responsible for what?" for any Edmonton address. Descriptive only.
- **This session:**
  1. take the pending template update;
  2. propose and build the Vite build and its CI;
  3. add the office-holder sources and `officeholders.json`;
  4. build the first real lookup page.

## 2. Current State

### ✅ Completed (merged unless marked)
- **#42 Template update** `e051159 → 0907382`, merged. Adds one bullet to `docs/TOKEN_EFFICIENCY.md` §Disk: the server deletes scratch untouched for 7 days, and a `KEEP` file opts out. Nothing declined.
- **#43 Vite build**, merged and deployed. The first Vite deploy was green on every step; the live site serves hashed assets.
  - **Layout:**
    - `site/` is the Vite root.
    - Published data moved from `site/data/` to **`site/public/data/`**, so its URLs are unchanged.
    - The Python builders' default `--out` moved with it.
  - **Libraries:**
    - `site/vendor/` was replaced by npm, pinned exactly: `maplibre-gl` 6.14.0, `pmtiles` 4.5.0, `vite` 8.3.4, `@playwright/test` 1.63.0.
    - Licence texts live in `site/public/licenses/`: the minifier strips the notices, and the pmtiles package ships no LICENSE file.
  - **Worker:** MapLibre's worker is passed via `setWorkerUrl` from `import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?url"`.
  - **Guards:**
    - `scripts/check_dist.mjs`, with its own tests in `tests/test_site_build.py`;
    - `smoke/built-site.spec.js`, a Playwright browser check;
    - `pages.yml` runs pytest, then `npm ci`, the Chromium install, the build, `check:dist` and the smoke test, then uploads `dist/`;
    - `tests.yml` adds the build and `check:dist`.
  - DECISIONS row added; the 2026-10-10 and 2026-10-13 data-folder rows are marked AMENDED.
- **#44 Office holders**, merged.
  - **Sources:** 7 new ids in `src/download.py`, each with a fixed row count:
    - `coe_council_contacts` (13)
    - `coe_election_results_2025` (140)
    - `epsb_trustees` (9)
    - `ecsd_trustees` (7)
    - `ab_mlas` (87)
    - `ab_mla_list` (87; the Assembly members page, a new source)
    - `ca_mps` (37)
  - The new `kind: "page"` counts rows with the build's own parsers, so a layout change fails the download.
  - **Build:** new `src/build_officeholders.py` writes **`site/public/data/officeholders.json`: 71 seats**:
    - mayor and 12 councillors, 9 + 7 trustees;
    - 29 MLAs and 13 MPs, including neighbouring ridings at the city edge.

    It has no vacant seats, every cross-check agrees, and a rebuild is byte-identical.
  - **Owner decisions:**
    1. accept name variants listed in **`data/name_variants.csv`**, each entry approved by the owner;
    2. store affiliation exactly as the source gives it (`NDP`, `UC`, `PTP`, `Conservative`);
    3. compare cross-check names after normalising;
    4. include the neighbouring ridings.
  - **Approved name variants:** Mike/Michael Elliott (pihêsiwin); Lisa Turchansky / CASTELL TURCHANSKY (Catholic 76).
  - **Contact pages:** all 71 `contact_url`s were fetched, and each page showed the holder's surname.
- **#45 The lookup page**: **OPEN, CI green, awaiting merge**, branch `lookup-page`, one commit.
  - **Pages:** `site/index.html` is the app; the tile test page is now `site/buildings-test.html`, a second Vite entry.
  - **New files:**
    - `site/src/address.js`: parse and match against `streets.json`, with tests in `site/src/address.test.js`, run as `npm run test:js` and added to `tests.yml`;
    - `site/src/app.js`: cards, combobox, district picker, map-click lookup;
    - `site/src/map.js`: a lazy chunk with ghost buildings, one layer's lines, the selected fill and the point;
    - `site/src/app.css`.
  - **pip.js:** `prototype/pip.js` moved to **`site/src/pip.js`** as ESM. `prototype/pip.js` is now a CommonJS CLI wrapper that `import()`s it, so the build's cross-check runs the browser's code.
  - **Node guard:** `src/build_address_index.py` now raises if node answers fewer points than asked. Before, node exiting 0 with no output read as "pip.js disagrees on 298,453 rows".
  - **Rebuild check:** I rebuilt the address index through the moved file; all checks pass and `site/public` shows no diff.
  - **Smoke test:** a lookup of `10024 124 st` (a split address; expects 7 cards and the provincial split note), then a map click, then the test page.
- **TODO.md:**
  - closed: the Vite build, the office-holder downloaders, the first lookup page;
  - added under Build: neighbourhood search (propose first: new published file), the About/methodology page (owner-approved content, including the council note from brief §7), boundary staleness in the page, and a shareable view link.

### ⚠️ In Progress
- PR #45 waits on the owner's merge. Nothing is half-done. The local checkout is on `lookup-page`, clean, before this handoff.

### ❌ Blocking Issues
None. No open GitHub issues. Disk: 12 GB free.

## 3. Technical Learnings
- **A root `package.json` with `"type": "module"` turns every `.js` under the repo into ESM.** That silently broke the CommonJS `prototype/pip.js`: node exited 0 with no output. The fix is `prototype/package.json` `{"type": "commonjs"}`; it's kept because `prototype/pip.js` is still CJS.
- **MapLibre 6 ESM:** there's no default export, so use `import * as maplibregl`. The worker URL is built at run time (`new URL(\`./${t}\`, import.meta.url)`), so Vite can't see it; hence the `?url` import and `setWorkerUrl`.
- **Vite 8 (rolldown):** `comments.legal` and `legalComments` did not keep the licence notices after minifying. Multi-page input goes under `build.rolldownOptions.input`.
- **Playwright on this ARM Oracle Linux 8 box works** with `PLAYWRIGHT_BROWSERS_PATH=<scratch>/pw npx playwright install chromium` (about 115 MB). Delete it after use.
- **MapLibre cancels tile reads when the camera moves.** These show up as `requestfailed net::ERR_ABORTED`; the smoke watcher ignores exactly that.
- **`node --test site/src/`** (a directory) fails under node 22; use the glob `site/src/*.test.js`.
- **Assembly `contacts.csv`:**
  - it opens with a 3-line banner (label, quoted date, blank), then a quoted header;
  - the address columns repeat their names;
  - one caucus is `PTP`.
- **The Assembly members page** gives `member-information?mid=<4 digits>&legl=31` per current member; former members show "Former Member" instead of a division.
- **House of Commons** member pages are `https://www.ourcommons.ca/Members/en/<Person ID>`.
- **Official lookup tools**, all returning 200 on 2026-10-16, are kept as `OFFICIAL_LOOKUP` in `site/src/app.js`:
  - City ward maps: `edmonton.ca/city_government/municipal_elections/ward-maps`
  - EPSB Find My Trustee
  - ECSD trustees page
  - Elections Alberta `/where-to-vote-tool/`
  - Elections Canada `Scripts/vis/FindED?L=e`
- **Privacy:** an address lookup fetches `data/addresses/<street>.json` from Pages, so the host sees the street but never the house number. The page says so in its hint text. This follows the owner's per-street index decision (2026-10-13).
- **Harness:** `sleep N && …` is blocked; wait with `until …; do sleep 5; done`. Kill `vite preview` by PID from `ps`, not `pkill -f`, because a `pkill -f` pattern also matches the calling shell.
- **`git checkout master` failed with local doc edits**, so `git checkout -b` cut `lookup-page` from the merged `officeholders` branch. It was harmless (its parent is on master, and the PR shows 1 commit), but stash or commit before switching.

## 4. Next Steps (prioritized)
1. **Press Sync in the claude.ai Project** (owner):
   ```
   docs/BRIEF.md
   docs/SPEC_data_schema.md
   data/DATA.md
   ```
   After merging #45, `docs/BRIEF.md` and `docs/SPEC_data_schema.md` change again.
2. **Merge #45** (owner).
   - After the merge, confirm the Pages deploy is green: `gh run list --workflow pages.yml --limit 1`.
   - Then confirm the live page answers a lookup: `curl -s <site>/ | grep main-`.
3. **Diff check and staleness guard** (`docs/SPEC_data_schema.md` §5–§6, plus the §9.4 address rows).
   - It now covers `officeholders.json` too.
   - After it, propose the weekly refresh workflow (§8; a CI change).
4. **About and methodology page:** draft the text for the owner's approval. It includes the council note (brief §7).
5. **Neighbourhood search:** propose the published names file first (`65fr-66s6`).
6. **Smaller items:** boundary staleness warning in the page; a shareable view link; glyph files for map labels (ward names in syllabics); measuring data per view.
7. **Owner items still open** (TODO "Waiting on the owner"):
   - the City defect report (`docs/DATA_ISSUES.md`, two rows NOT SENT);
   - the Elections Alberta licence;
   - confirming the Project picker has the full synced set ticked.
8. **Carried:** check the provincial boundary process after the Select Special Committee reports (due 2026-11-02).

## 5. Restoration Procedure
```bash
cd /home/opc/edmonton-civic-map
git fetch && git checkout master && git pull --ff-only
git config core.hooksPath                 # .githooks
gh issue list --state open
.venv/bin/pip install -r requirements.txt
npm ci                                    # node 22 (.nvmrc); ~94 MB node_modules
.venv/bin/python -m pytest tests -q       # 74 passed
npm run test:js                           # 4 passed
# data pipeline (data/raw/ is git-ignored, present on this server):
.venv/bin/python -m src.download          # 13 sources
.venv/bin/python -m src.build_boundaries
.venv/bin/python -m src.build_address_index   # ~5.5 min
.venv/bin/python -m src.build_officeholders
# site:
npm run build && npm run check:dist
PLAYWRIGHT_BROWSERS_PATH=<scratch>/pw npx playwright install chromium && PLAYWRIGHT_BROWSERS_PATH=<scratch>/pw npm run smoke
npm run dev                               # local site
git status                                # a rebuild from unchanged sources shows no diff
```
Check `df -h /` before any build that writes more than ~500 MB.
