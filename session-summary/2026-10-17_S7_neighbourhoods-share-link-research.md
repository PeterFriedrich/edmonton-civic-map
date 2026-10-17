# Session handoff — 2026-10-17, S7: neighbourhood search, share link, research

## 0. Session Metadata
- **Model:** Opus 5.5 (`claude-opus-5-5`), from the session's own context. No `/model` switch.
- **Effort:** `$CLAUDE_EFFORT` reads `medium` (checked at handoff).
- **Date / session #:** 2026-10-17 (Edmonton), S7. One session, started after a `/clear`. PRs #59–#65, all merged.

## 1. Goal
- **Project:** Edmonton Civic Map, a public lookup answering "who represents me, and who is responsible for what?" for any Edmonton address. Descriptive only.
- **This session:** work S6's next steps:
  1. neighbourhood search;
  2. a shareable view link;
  3. join the census table to the neighbourhood map;
  4. three research TODOs: school-ward bylaws, a newer ward population, the post-2025 ward review;
  5. then a source for community league boundaries.

## 2. Current State

### ✅ Completed (all merged)

**#59 Neighbourhood search.**
- **New module `src/build_neighbourhoods.py`**, run after `build_address_index` against the same `--out`.
  - Writes `site/public/data/neighbourhoods.json`: 407 records `{id, name, point, districts{layer:[ids]}, source_id, source_url, last_verified}`. About 11 kB gzipped.
  - A neighbourhood's districts are those of its published address records, tested in lon/lat (no reprojection).
  - More than one district in a layer means divided, by **any** address (owner chose no floor). Divided counts: 3 council, 2 public, 4 Catholic, 44 provincial, 30 federal.
  - The build stops on: an address in no neighbourhood or in two, a neighbourhood with no address, or a duplicate id or name.
- **New source `coe_neighbourhoods`** (`65fr-66s6`, expected 407) in `src/download.py`.
- **Weekly refresh:** `.github/workflows/refresh.yml` runs the new builder.
- **Diff check:** four new **review** rules in `data/diff_rules.json`: `neighbourhood_added_or_removed`, `neighbourhood_name`, `neighbourhood_districts`, `neighbourhood_other_field`.
- **`scripts/check_refresh_diff.py`:** a passing refresh may change only `last_verified` in this file.
- **Page:**
  - The address box also matches neighbourhood names with `matchNeighbourhoods` (`site/src/address.js`), ignoring case, accents and punctuation.
  - Choosing one shows its cards. A divided layer shows each district with a note.
  - The map moves to `point` with no marker (`map.show(point, ids, marker)`).
- **About page:** a source row and a "Neighbourhoods" known-limits line. That is new wording the owner should check.
- **Docs:** `docs/SPEC_data_schema.md` §10, a DECISIONS row, and a DATA_ISSUES row (`civic_ward_name` of Anthony Henday South East, 6665, is wrong; NOT SENT).

**#60 Share link.**
- **New module `site/src/share.js`:** `encode(sel, view, withAddress)` and `decode(hash)`, using the URL fragment:

  | Key | Holds |
  |---|---|
  | `d=` | district ids |
  | `n=` | neighbourhood number |
  | `a=` | address (only with consent) |
  | `p=` | lat,lon (only with consent) |
  | `lines=` | boundary layer drawn |
  | `3d=1` | tilted view |

  Unknown keys are ignored; `lens=` is reserved.
- **No address by default:** an address or map point is shared as its districts unless the reader ticks "Include the address" (or "map point").
- **Address bar:** `history.replaceState` keeps it on the address-free form.
- **No camera position** in the link.
- **Stale links:** a link to an unknown id or address shows a notice.
- **Map:** `map.js` gained `view` / `onView` / `setView`. When there is no point, it fits the map to the selected districts in the shown layer.
- **Copy link** control on the results, with a clipboard fallback to a read-only field.
- **About page:** one sentence under "Your address".
- **Tests:** `site/src/share.test.js` (4) and a smoke test, "share links reopen the view and keep the address out unless included".

**#61 Census join** (`data/DATA.md` "Ward population").
- `eg3i-f4bj` is published on the **census-day** neighbourhood map `5bk4-5txu` (403 polygons; numbers stored as `"2010.0"`), not today's map.
- **274 rows join by number; 4 were renumbered** and join by geometry:
  - Oliver 1150 → Wîhkwêntôwin 1151;
  - Horse Hill 1A 2691 → Quarry Ridge 2692;
  - Chappelle 5462 → 5471;
  - Heritage Valley Town Centre 5464 → 5472.
- **129 current neighbourhoods have no row:** 53 industrial, 40 river valley / Henday / "Area", and 36 built after 2021 or institutional.
- 34 edges moved since census day.
- Glenridding Ravine (860 people) now spans two council wards.
- City total 1,010,595 is **not** checked against Statistics Canada: statcan.gc.ca serves scripts a security check.

**#62 Research** (`data/DATA.md` "School wards", "Council wards → Ward boundary review", "Population and growth").
- **School wards:** the boards' own layers on `azimuth.epsb.ca` (`EPSB_Wards_2025/FeatureServer/264`, `FC_ECSD_Wards_2025/FeatureServer/227`) disagree with the City layers at 3 addresses:

  | Address | City layer | Board layer |
  |---|---|---|
  | 610 Calgary Trail NW | public I | public H |
  | 15928 Manning Drive NW | Catholic 72 | Catholic 73 |
  | 17611 34 Street NW | Catholic 72 | Catholic 73 |

  The bylaws are not online (EPSB Bylaw 2020-2; no Catholic number found). DATA_ISSUES row added, NOT SENT. The TODO stays open.
- **Ward review:** the policy is **C469B** (2022-10-17). The City's `C469A.pdf` link serves C469B.
  - The Returning Officer reports **in Q4 2026**; not found yet.
  - The 2023 change (Bylaw 20304: Calgary Trail South to papastew) is in our layer.
  - **Unresolved:** a search summary mentions moving Yellowhead Corridor West from Anirniq to O-day'min. Our layer still has it in Anirniq. eScribe answers 403, so this has to be read by hand.
  - The ±25% variance is now verified.
- **Ward population:** nothing newer than the 2021 Census exists on the portal. TODO closed.

**#63, #64 Community league boundaries** (`data/DATA.md` "Community leagues — City GIS service").
- **The only source:** `gis.edmonton.ca/arcgisintegration/rest/services/DPIM/DPIM_FS/FeatureServer/12` (`GDB.V_COMMUNITY_LEAGUES`). It has 163 polygons with bylaw boundary text.
  - **No licence stated; not open data. Do not publish.**
  - ⚠️ **Column `CRCLOGON` holds apparent staff logon IDs: never request it.** No values are recorded anywhere, and the scratch sample was deleted.
- **Coverage:** 58% of the city's area. 6.1% of address records fall in no league (The Uplands, Stillwater, Alces, Paisley and others).
- **The owner's EFCL Google Drive JPEG** turned out to be the City's own map (printed 2024-04-02, "No reproduction … without the express written consent"). It shows the same gaps, so those areas have no league boundary on record. It is recorded as evidence only, not to be traced.

**#65 TODO:** "Ask the City to publish its community league boundaries as open data". The owner decided to ask. Claude drafts the request on asking; the owner sends it. Until then the communities lens uses neighbourhoods only.

### ⚠️ In Progress
Nothing half-done. The local branch is `handoff-s7`; master is at the #65 merge.

### ❌ Blocking Issues
- **No open GitHub issues.** Disk: 12 GB free.
- **Not reachable by script:**
  - statcan.gc.ca (security check);
  - `pub-edmonton.escribemeetings.com` (403, also to WebFetch);
  - the City's `legislation-bylaws`, `epsb-election-maps` and `ward-boundary-review` pages (404 now).

## 3. Technical Learnings
- **System `curl` fails TLS here** (exit 60). Fetch with `.venv/bin/python` and `certifi`, as `src/download.py` does. A throwaway helper was in scratch: `urllib` with `certifi` and the project User-Agent.
- **ArcGIS REST** on `gis.edmonton.ca/arcgisintegration/rest/services` is public. Folders include `DPIM`, `WebSharedLayers` and `VertiGISSharedLayers`. `DPIM_FS` also has roads by class, railways, river valley and waterbody layers: candidates for the physical-boundaries lens. **Licence is unknown for all of them.**
- **`azimuth.epsb.ca`** (EPSB's ArcGIS) hosts the City wards 2021, the city boundary, and EPS division layers too.
- **pypdf and pillow:** install with `python3.12 -m pip install --target <scratch>/pylib pypdf pillow`. `Image.MAX_IMAGE_PIXELS=None` is needed for big JPEGs.
- **Smoke tests that read the clipboard** need `context.grantPermissions(["clipboard-read","clipboard-write"])`.
- **`getByRole("combobox")` is ambiguous on the page** (the district `<select>` is one too). Name it: `{ name: "Address" }`.
- **`docs/BRIEF.md` quotes `TODO.md`.** Any TODO edit needs `python scripts/make_brief.py --write`, or `test_committed_brief_is_current` fails. This bit #65.
- **A PR merged mid-session blocks pushes to its branch** through the `.githooks/pre-push` hook. Cherry-pick onto a new branch from `origin/master` (done for #64).
- **The DECISIONS gate resolves Python test names only.** A row citing JS or smoke tests must carry `[unverifiable]` and say why (see the 2026-10-17 share-link row).
- **The neighbourhood `point`** comes from GEOS `representative_point` on lon/lat, rounded to 5 decimals.

## 4. Next Steps (prioritized)
1. **Press Sync in the claude.ai Project:**
   ```
   docs/BRIEF.md
   docs/SPEC_data_schema.md
   data/DATA.md
   ```
   Also tick `docs/SPEC_lenses.md` if it's kept in the Project.
2. **Owner review of new About-page wording:** the "Neighbourhoods" known-limits line, and the share-link sentence under "Your address" (`site/about.html`).
3. **Monday 2026-10-19:**
   - The first refresh with `build_neighbourhoods` should pass, with `neighbourhoods.json` changing only `last_verified` and no `address_point_moved` rows.
   - **If the City's polygons for `65fr-66s6` changed**, the `point` changes too, and that is a review hold by design.
   - `gh run list --workflow refresh.yml --limit 1`.
4. **Owner asks, tracked in TODO.md** (Claude drafts on request):
   - the league-boundary request to the City;
   - the defect report (DATA_ISSUES rows NOT SENT, now 4 including the school-ward disagreement and Anthony Henday South East);
   - ask the boards or Edmonton Elections which ward polygons the 2025 vote used;
   - read the Yellowhead Corridor West report by hand on eScribe.
5. **Next build or research options** offered to the owner, not chosen yet:
   - the Tier 2 survey (recommended);
   - the provincial boundaries check before 2026-11-02;
   - physical-boundaries lens sources (see §3, `DPIM_FS` layers);
   - map label glyphs;
   - data use per view.
6. **Dated:**
   - after 2026-11-02, the Alberta committee report;
   - around 2026-11-27, address churn;
   - after 2026-12-31, the Returning Officer's ward report (Policy C469B).

## 5. Restoration Procedure
```bash
cd /home/opc/edmonton-civic-map
git fetch && git checkout master && git pull --ff-only
git config core.hooksPath                 # .githooks
gh issue list --state open
./bootstrap.sh                            # uv venv, pytest, guards
npm ci
.venv/bin/python -m pytest tests -q       # 138 passed
npm run test:js                           # 9 passed
# data (data/raw is git-ignored; download fresh before any rebuild you commit):
.venv/bin/python -m src.download
S=<scratch>/rebuild
.venv/bin/python -m src.build_boundaries --out $S
.venv/bin/python -m src.build_address_index --out $S   # ~6 min
.venv/bin/python -m src.build_officeholders --out $S
.venv/bin/python -m src.build_neighbourhoods --out $S
.venv/bin/python -m src.diff_check --new $S            # 0 pass / 1 review / 2 stop
# site:
npm run build && npm run check:dist
PLAYWRIGHT_BROWSERS_PATH=<scratch>/pw npx playwright install chromium && PLAYWRIGHT_BROWSERS_PATH=<scratch>/pw npm run smoke   # 6 passed
```
Check `df -h /` before any build that writes more than ~500 MB.
