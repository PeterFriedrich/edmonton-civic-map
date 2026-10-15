# Session handoff — 2026-10-10, S1: founding brief, source verification, scoping

## 0. Session Metadata
- **Model:** Opus 5.5 (`claude-opus-5-5`), from the session's own context. No `/model` switch that I know of.
- **Effort:** `$CLAUDE_EFFORT` reads `medium` (checked at handoff). The owner said early in the session that they had turned it to high; the variable does not show that, so treat the level as uncertain rather than trusting either.
- **Date / session #:** 2026-10-10, S1 (first session in this repo)

## 1. Goal
- **Project:** Edmonton Civic Map — a public reference tool answering "who represents me, and who is responsible for what?" for any Edmonton address (council, both school boards, MLA, MP). Descriptive only; no scoring of officials.
- **This session:** take the owner's founding brief (2026-10-09), do its first four tasks (verify sources, prototype point-in-polygon, draft schema and source ledger), and settle the scoping questions that followed. No UI and no pipeline code was to be written, and none was.

## 2. Current State

### ✅ Completed
All merged to `master` through PRs #1–#13. `master` is at `7863a64`.

- **Brief recorded verbatim** in `docs/SPEC_civic_map.md`, with an "Amendments since the brief was written" list at the top holding every later owner decision.
- **Source ledger** in `data/DATA.md`: every Tier 1 source inspected live on 2026-10-10 with id, format, CRS, licence, vintage and quirks.
- **Findings from verification:**
  - Council ward layer `b4er-5rp2`: all 12 councillors match the 2025 official results (`fv5x-8efu`); boundaries are the 2021 redraw; history layer `nydb-6rce` has no `Future` rows.
  - School-ward layers `d7pj-rist` / `pwzf-sjj2`: `trustee` column is stale (5 of 9 public, 2 of 7 Catholic wrong). Logged in `docs/DATA_ISSUES.md`, status NOT SENT. Trustees come from `epsb.ca` and `ecsd.net`, which match the 2025 results.
  - Provincial: Elections Alberta 2017-enacted shapefile (87 divisions, EPSG:3401), no licence stated. A legislature committee must report on a new map by 2026-11-02.
  - Federal: Elections Canada 2023 Representation Order shapefile (343 districts, EPSG:3347), OGL – Canada.
  - 7 City parcel addresses fall in ridings not named "Edmonton" (1 provincial, 6 federal).
  - Address layer `ut27-nrpn`: 288,315 distinct addresses, about 2.2 MB gzipped as a compact index.
- **Prototype** in `prototype/` (`pip.js`, `check_pip.py`, `README.md`): browser point-in-polygon agrees with shapely on all 298,238 parcel addresses; 5 m simplification changes no address's ward (28 kB gzipped).
- **Schema** in `docs/SPEC_data_schema.md`: `sources.json`, `layers.json` + boundary files, `officeholders.json`, the diff check (§5), staleness (§6), owner's answers (§7), refresh design (§8).
- **Lens spec** in `docs/SPEC_lenses.md`: base view and four lenses, with a research request in §7 for a Claude web chat.
- **`docs/BRIEF.md` generated and committed** for the first time (`scripts/make_brief.py --write`). `tests/test_brief.py` now fails when it is stale.
- **Decisions locked** (rows in `docs/DECISIONS.md`): the brief's six, the name "Edmonton Civic Map", published files under `site/data/`, staleness thresholds (45 days office holders, 180 boundaries and population), affiliation as an opt-in lens on MLA and MP cards only, weekly refresh on GitHub Actions with hold-on-change, Tier 2 ladder (automate plain statements first), launch is Tier 1 with Tier 2 added as ready, static site on GitHub Pages, 2D/3D geographic map on a stack other than the tax viz's, main view is rough geography with possible buildings.
- **Lenses recorded as wanted, not scheduled:** communities of interest, physical and natural boundaries, population density (a density map with ward boundaries as an overlay; no number per ward).
- **Peer sessions consulted:** `server` (cron conventions, fetch etiquette; later told no cron is needed) and `edmonton-tax-viz` (how its refresh runs). Both replies are folded into `docs/SPEC_data_schema.md` §8.

### ⚠️ In Progress (where exactly did we stop?)
- **Stack choice.** The owner is taking `docs/SPEC_lenses.md` §7 to a Claude web chat. No reply yet. Nothing gets built until a stack is chosen.
- **Two parts of `docs/SPEC_lenses.md` are mine, not the owner's**, and are marked so in the file: "free to run" as a constraint (§2 last row) and the shared lens behaviours (§5).
- **"3D never encodes a quantity"** is a locked row I wrote from the owner's "rough geography" answer. The owner later parked 2D-vs-3D for the density lens, so this row may be amended.

### ❌ Blocking Issues
None. No failing tests, no open PRs, no open GitHub issues at handoff.

## 3. Technical Learnings
- **CA bundle:** the system bundle on this Oracle Linux 8 server lacks the Sectigo R46 root. `curl` and system Python fail TLS on `www.elections.ca`, `www.ourcommons.ca` and `www.edmonton.ca`. Use Python with `certifi`. `server` knows and is raising it with the owner.
- **`pkill -f <script>` from a Bash tool call kills the calling shell** if the script path appears in the same command line. It cost one run this session.
- **Socrata paging:** `record_id` in `ut27-nrpn` is not unique within `PARCEL` rows; page on `:id`. A single 300,000-row CSV request stalled; 50,000-row pages take about 9 s each.
- **`ut27-nrpn` `neighbourhood_name` is empty on every row**; neighbourhood has to come from point-in-polygon against `65fr-66s6` (407 polygons).
- **Building permits `24uj-dj8v`:** 26% of units permitted since the 2021 Census have no coordinates, so a by-ward sum from lat/lon is not usable. Deliberately not recorded.
- **The owner merges within minutes.** Six of this session's pushes found the previous PR already merged. Check `gh pr view <n> --json state` before every push; `.githooks/pre-push` blocks a push to a merged branch and prints the cherry-pick recipe.
- **`gh pr edit` works on a merged PR.** I overwrote PR #4's description by mistake after it had merged, and rewrote it to match what it merged.
- **`docs/BRIEF.md` is now gated:** any change to `CLAUDE.md`, `docs/SCOPE.md`, `docs/DECISIONS.md`, `TODO.md`, `docs/DATA_ISSUES.md` or the requirements files needs `python scripts/make_brief.py --write` in the same PR.
- **Scratch work is gone with the session:** downloads, the measurement venv (shapely, pyproj, pyshp, certifi) and ad-hoc scripts lived in the session scratchpad. Only `prototype/check_pip.py` was kept in the repo; its deps are not in `requirements.txt`.
- **Not verified, listed in `TODO.md`:** Elections Alberta licence; exact attribution text for the City and Statistics Canada licences; the post-2025 ward boundary report under Policy C469A (the City page returned 404) and that policy's allowed variance; school-ward boundaries against the boards' bylaws; sources for community league boundaries, river valley edge, rail lines, terrain and population forecasts.

## 4. Next Steps (prioritized)
1. **Press Sync in the claude.ai Project** (owner). Changed synced paths since the repo began:
   ```
   docs/BRIEF.md
   docs/SPEC_civic_map.md
   docs/SPEC_data_schema.md
   docs/SPEC_lenses.md
   data/DATA.md
   ```
   After merging the PR that carries this handoff, `docs/BRIEF.md` changes again only if that PR touched its sources; it did not.
2. **When the owner pastes the Claude web stack report:** save it first to `/home/opc/research/edmonton-civic-map/stack_reply_<date>.md` (that folder does not exist yet and `research/README.md` belongs to the `server` session, so ask `server` to add the row), then triage its tables into `TODO.md` and `docs/DECISIONS.md`.
3. **Ask the owner to confirm or strike** the two unconfirmed parts of `docs/SPEC_lenses.md` (§2 "free to run", §5).
4. **After 2026-11-02:** recheck the Select Special Committee on Electoral Boundaries (`https://www.assembly.ab.ca/assembly-business/committees/CEB`) and record the outcome in `data/DATA.md`, "Provincial ridings".
5. **Once a stack is chosen, propose before building** (CLAUDE.md "Propose the plan first"): the downloaders, the boundary build, the diff check, then the weekly GitHub Actions workflow. `TODO.md` "Build" has the list.
6. **Source verification items** in `TODO.md` "Sources still to verify" can be done at any time and do not depend on the stack.

## 5. Restoration Procedure
```bash
cd /home/opc/edmonton-civic-map
git checkout master && git pull --ff-only
git config core.hooksPath            # should print .githooks
gh issue list --state open           # nothing pushes these to a session
.venv/bin/python -m pytest tests -q  # 28 passed at handoff
```
To re-run the prototype measurement, follow `prototype/README.md` (needs `shapely>=2.1`, `pyproj`, `numpy` in a throwaway venv, and node).
