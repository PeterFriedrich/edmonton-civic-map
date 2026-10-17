# TODO — archive of CLOSED items

Closed work moved out of `TODO.md` so the file that is read at the start of **every** session carries only live work. **Nothing here is a to-do.**

`TODO.md`'s `## Done` section keeps a one-line entry for each of these, so the *never redo a closed item without asking* rule still works by grepping there; this file holds the reasoning behind each one.

Items are verbatim as they were closed, newest-moved first in the order they appeared in `TODO.md`. Line numbers and "next up" markers inside them are historical — do not act on them.

---

- [x] **Neighbourhood search** (`docs/SPEC_lenses.md` §3): type a neighbourhood, see its districts; a divided one shows each and asks for an address. Needs the 407 names from `65fr-66s6` published, which is a new published file: propose first. **Closed 2026-10-17:** `site/public/data/neighbourhoods.json` from `src/build_neighbourhoods.py`, in the refresh and the diff check; matched in the address box (`docs/SPEC_data_schema.md` §10).

- [x] DONE 2026-10-16: resolved by switching to the Government of Alberta's copy of the same divisions, under OGL – Alberta (`data/DATA.md`, "Provincial ridings"); no permission request needed. **Licence for the Elections Alberta boundary shapefile.** None is stated on the download page (`data/DATA.md`, "Provincial ridings"). Done when a written licence or permission is recorded there; until then the provincial layer cannot ship.

- [x] DONE 2026-10-16 (City part): "Contains information licensed under the Open Government Licence – City of Edmonton.", read from the licence via `data.edmonton.ca/stories/s/msh8-if28.json` (method from edmonton-tax-viz); on the About page and pinned by a test. Statistics Canada's wording waits until ward populations are published. **Exact attribution text for the Open Government Licence – Edmonton**, and Statistics Canada's for the ward populations. Done when `data/DATA.md` quotes both.

- [x] DONE 2026-10-16: what it is, how the data flows, running and rebuilding, where things are, licences. **Replace the template `README.md`** with one for this project.

- [x] DONE 2026-10-16: `site/about.html`, text approved by the owner in session; its numbers come from the published files; the council note cites MGA s.154 and s.182 and EPCOR's own Edmonton page. **About and methodology page** (brief §7): sources, verification dates, known limits, and the council note (council decides as a body; the mayor has one vote; much of what residents meet is delivered by administration, the province or EPCOR). Written content: draft for the owner's approval.

- [x] DONE 2026-10-16: `src/download.py` GETs each `landing_url` after the fetch; a non-200 fails that source. **Check every `landing_url` resolves** in `src/download.py` (§5 "stop" row; the diff check is offline and skips it). Belongs with the refresh workflow.

- [x] DONE 2026-10-16: `.github/workflows/refresh.yml`, Mondays 10:00 UTC; robots.txt checked once for all 13 sources (`data/DATA.md`). **Weekly refresh workflow on GitHub Actions** per `docs/SPEC_data_schema.md` §8: auto-publish when nothing changed, hold and file an issue otherwise. Changes CI, so propose the workflow before writing it.

- [x] DONE 2026-10-16: `src/diff_check.py` with severities in `data/diff_rules.json`; thresholds and recheck dates in `site/public/data/staleness.json` (DECISIONS row). **Diff check and staleness guard** per `docs/SPEC_data_schema.md` §5–§6, including the address-index rows in §9.4 (not built with the index; it compares against `site/public/data/addresses/manifest.txt`).

- [x] DONE 2026-10-16: the page reads `staleness.json` and warns per layer. **Boundary staleness in the page**: the cards warn after 45 days for office holders; boundaries (180 days, `layers.json` `last_verified`) have no warning yet.

- [x] DONE 2026-10-16: `site/index.html` is the lookup (address type-ahead, district list, map click, cards with source and date, near-edge and split notes, affiliation off by default); the tile test page moved to `buildings-test.html`; `pip.js` moved to `site/src/` so the build cross-checks the code the browser runs. **The first lookup page.**

- [x] DONE 2026-10-16: 7 sources in `src/download.py`, `src/build_officeholders.py` writes 71 seats, owner approved two name variants (`data/DATA.md`). **Downloaders for the office-holder sources** (`e9qt-cc3j`, `fv5x-8efu`, `eg3i-f4bj`, Assembly `contacts.csv`, House of Commons CSV, the two trustee pages), added to `src/download.py`, each checking its row count and writing `fetch.json`. The trustee scrapers must fail on a layout change, never return an empty roster. The six map and address sources are done (2026-10-15, `data/DATA.md` "In use").

- [x] **Vite build and what it changes in CI** — DONE 2026-10-15. Proposal approved in session; built as proposed: Vite with hashed file names, data in `site/public/data/`, `site/vendor/` replaced by npm, `scripts/check_dist.mjs` on every PR, Playwright check at deploy, Python tests before deploy (`docs/DECISIONS.md`).

- [x] **Build `src/build_address_index.py`** per `docs/SPEC_data_schema.md` §9: the street files and `manifest.txt` under `site/data/addresses/`, the §9.4 diff-check rows and the §9.5 tests. Needs the address downloader and the boundary build first (items below). Done when the index is committed and all four §9.5 tests pass. DONE 2026-10-15: `site/data/addresses/`, 2,800 street files; pip.js agrees with the build on all 298,453 parcel rows at full resolution and on all 288,534 records against the published boundaries.

- [x] **Boundary build**: reproject, clip provincial and federal layers to the city, simplify at the recorded tolerance, with a test that no parcel address changes district against full resolution. DONE 2026-10-15: `src/build_boundaries.py`, `site/data/boundaries/`, `site/data/layers.json`; every one of 298,453 parcel addresses keeps its district at 5 m on all five layers.

- [x] **Districts worked out per address at build time: proposal written, waiting on the owner.** `docs/SPEC_data_schema.md` §9 (2026-10-15) has the format, the 8 split addresses, the diff-check rows and the tests; §9.6 lists four points to settle. Done when the owner settles them and a DECISIONS row records it; building `src/build_address_index.py` is then its own item. DECIDED 2026-10-15: all four §9.6 points as recommended.

- [x] **Terrain, step 2: draw the terrain under the buildings and decide whether 30 m is enough.** Add `terrain.pmtiles` (2.69 MB, `prototype/README.md`) to the test page as hillshade and as 3D terrain, with buildings seated on it, and look at the river valley on the owner's phone. Then decide whether the 1 m federal lidar (`AB-Edmonton-1m`, 2.38 GB) resampled to about 5–10 m is worth its size. Done when the choice is recorded with the sizes and a phone frame rate.

- [x] **Terrain: read the Edmonton window of MRDEM-30, check it, and pack it as elevation PMTiles.** Sources are in `data/DATA.md`, "Terrain and elevation"; nothing has been read yet. Done when the ledger records CRS, vertical datum, the elevation range across the city and the depth of the river valley as the data shows it, and `prototype/README.md` has the PMTiles size (the report estimates 3–10 MB; encode at 0.1 m steps, since 1 m steps look blocky). Then decide whether the 1 m federal lidar (`AB-Edmonton-1m`, 2.38 GB) resampled to about 5–10 m is worth it.

- [x] **Buildings, step 2: draw the tile files in MapLibre on a real phone** (the owner's; this server has no GPU). With one stack chosen this is a feasibility check, not a comparison. Record first-load time and frame rate, flat and tilted, faint-solid against translucent buildings. Done when the numbers are in `prototype/README.md`.

- [x] **Check that GitHub Pages serves a `.pmtiles` file by range request, uncompressed, from a test deploy.** `edmonton-tax-viz` recorded Pages answering range requests on 2026-08-07, but not for this file type. Done when a test deploy reads one tile.

- [x] **Buildings, step 1: one trial tippecanoe build of the rooflines to PMTiles, and record the size.** Turn the 384,228 polygons of `jpxi-a9a5` into PMTiles at z12–z15, height as the only attribute, and record bytes per zoom (`pmtiles show`). Replaces the report's 10–30 MB estimate. Lives in `prototype/`. Done when `prototype/README.md` has the sizes.

- [x] **Tile files: committed under `site/data/` or built at deploy.** Decided 2026-10-13: committed, each with a text manifest beside it, while each file is under 100 MB (`docs/DECISIONS.md`).

- [x] **Map: pick the stack.** Chosen 2026-10-13: MapLibre GL JS 6 native layers, PMTiles, Vite with plain JavaScript, per-street address index (`docs/DECISIONS.md`; `docs/SPEC_lenses.md` §8). The report is filed at `/home/opc/research/edmonton-civic-map/stack_reply_2026-10-13.md`.
