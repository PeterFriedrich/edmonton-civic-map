# Data Sources

Reference for raw input files. Update this file when you discover column name
quirks, encoding issues, or anything unexpected. Do not rely on memory — write it
down here. A defect in the *publisher's* data goes in `docs/DATA_ISSUES.md`,
with a status saying whether they have been told.

**Download completeness:** an API that pages or caps (`$limit` on Socrata, for
instance) truncates *silently* — it returns exactly that many rows with no
error. Every downloader verifies its row count against the live server count
and fails hard on a mismatch.

**Vintage:** record, per source, the dataset id, the retrieval timestamp and
the publisher's own last-updated stamp. A guard must measure the DATA (row
counts, max date in the file), never a metadata string that can go stale
while the guard stays green.

## Sources

This is the **source ledger**. Nothing is downloaded into the repo yet: every
entry below was inspected on 2026-10-10 from the live source, and the figures
are from that inspection. A source moves from "candidate" to "in use" when a
downloader exists for it.

**In use (downloader exists), 2026-10-15:** `python -m src.download` fetches
the map and address sources into `data/raw/<id>/` (git-ignored), each with a `fetch.json`
(`docs/SPEC_data_schema.md` §2): `coe_parcels` (`ut27-nrpn`, `PARCEL` rows),
`coe_wards`, `coe_public_school_wards`, `coe_catholic_school_wards`,
`ab_ridings`, `fed_ridings`. All six passed on the first live run
(298,453 / 12 / 9 / 7 / 87 / 343 rows; about 30 s, 43 MB).

**Office holders in use, 2026-10-16:** seven more sources, each with a fixed
row count: `coe_council_contacts` (13), `coe_election_results_2025` (140),
`epsb_trustees` (9), `ecsd_trustees` (7), `ab_mlas` (87), `ab_mla_list` (87
current members) and `ca_mps` (37). The pages and CSVs are counted by the
build's own parsers, so a changed layout fails the download. A vacancy changes
a count too, and stops the download until a person looks. Then
`python -m src.build_officeholders` writes `site/public/data/officeholders.json`:
71 seats (mayor, 12 councillors, 9 + 7 trustees, 29 MLAs, 13 MPs), one per
district in the boundary files. All 71 `contact_url` pages were fetched on
2026-10-16 and each showed the holder's surname.

**Name variants** (`data/name_variants.csv`): name pairs a person has approved
as the same holder, per seat. The build stops on any other cross-check
mismatch. Approved by the owner, 2026-10-16:
- `council_ward:pihesiwin`: "Mike Elliott" (ward layer) and "Michael Elliott" (contacts).
- `catholic_school_ward:76`: "Lisa Turchansky" (board page) and "CASTELL TURCHANSKY, Lisa" (2025 results).
  The earlier note that the rosters "match the 2025 official results in all 16
  seats" compared surnames by eye; the build compares full names.

**Boundary build, 2026-10-15:** `python -m src.build_boundaries` turns the five
layers into `site/public/data/boundaries/<layer>.geojson` and `site/public/data/layers.json`.
No City boundary file is sourced, so the city outline is the union of the 12
council wards (783.0 km², one piece; 28 pinholes totalling 67 m²). Clipped to
it: 29 provincial divisions (20 Edmonton, 9 neighbours with 0.001–0.34 km²
each) and 13 federal districts (9 Edmonton, 4 neighbours with 0.26–0.81 km²).
Four of the five layers are not clean coverages: `docs/DATA_ISSUES.md`.

**Diff check, 2026-10-16:** a refresh runs the three builders with `--out <scratch>`,
then `python -m src.diff_check --new <scratch>` compares the result with
`site/public/data` (severities in `data/diff_rules.json`). Comparing the committed
files with themselves takes about 7 s. `site/public/data/staleness.json` is
hand-kept, not built: the 45 and 180 day thresholds and four recheck dates,
each from the statute or publisher that sets it.

**Primary sources only** (`docs/SPEC_civic_map.md` §4). News and Wikipedia are
context, never data.

**Fetching from this server:** the system CA bundle on Oracle Linux 8 does not
carry the Sectigo R46 root, so `curl` and the system Python fail TLS
verification on `www.elections.ca`, `www.ourcommons.ca` and `www.edmonton.ca`.
Use Python with `certifi`'s bundle. Do not disable verification.

### Summary

| Need | Source | Id / file | Format, CRS | Licence | Vintage |
|---|---|---|---|---|---|
| Council wards + councillor | City of Edmonton open data | `b4er-5rp2` | GeoJSON via Socrata, CRS84 | Open Government Licence – Edmonton | boundaries effective 2021-10-18; rows refreshed 2026-10-05 |
| Mayor and councillor contacts | City of Edmonton open data | `e9qt-cc3j` | Socrata table | OGL – Edmonton | rows updated 2025-10-29 |
| 2025 election results | City of Edmonton open data | `fv5x-8efu` | Socrata table | OGL – Edmonton | official results, reported 2025-11-06 |
| Ward population | City of Edmonton open data (Statistics Canada 2021 Census) | `eg3i-f4bj` | Socrata table | Statistics Canada Open Licence | census day 2021-05-11; published 2023-09-27 |
| Public school wards | City of Edmonton open data | `d7pj-rist` | GeoJSON via Socrata, CRS84 | OGL – Edmonton | boundaries effective 2021-10-18 |
| Catholic school wards | City of Edmonton open data | `pwzf-sjj2` | GeoJSON via Socrata, CRS84 | OGL – Edmonton | boundaries effective 2020-11-25 |
| Public trustees | Edmonton Public Schools | `epsb.ca/ourdistrict/board/trustees/` | web page | n/a (facts) | read 2026-10-10 |
| Catholic trustees | Edmonton Catholic Schools | `ecsd.net/ecsd-trustees` | web page | n/a (facts) | read 2026-10-10 |
| Provincial ridings | Elections Alberta | `2019Boundaries_ED-Shapefiles.zip` | shapefile, EPSG:3401 | **none stated — open item** | enacted 2017-12-15, in force 2019-03-19 |
| MLAs | Legislative Assembly of Alberta | `assembly.ab.ca/txt/mla_home/contacts.csv` | CSV | n/a (facts) | read 2026-10-10 |
| MLA pages (cross-check, contact links) | Legislative Assembly of Alberta | `assembly.ab.ca/members/members-of-the-legislative-assembly` | web page | n/a (facts) | read 2026-10-16 |
| Federal ridings | Elections Canada | `FederalElectoralDistricts_SHP.zip` | shapefile, EPSG:3347 | Open Government Licence – Canada | 2023 Representation Order; file modified 2026-09-15 |
| MPs | House of Commons | `ourcommons.ca/Members/en/search/csv?province=AB` | CSV | n/a (facts) | read 2026-10-10 |
| Addresses | City of Edmonton open data | `ut27-nrpn` | Socrata table, lat/lon | OGL – Edmonton | rows refreshed 2026-10-05 |

### Council wards — `b4er-5rp2`
- **Publisher / URL:** City of Edmonton, https://data.edmonton.ca/d/b4er-5rp2
- **Retrieved:** 2026-10-10 — **publisher last-updated:** 2026-10-05
- **Rows / columns:** 12; `name_1` (ward name), `name_2` (name + " Ward"), `effective_start_date`, `effective_end_date`, `councillor`, `councillor2`, `geometry_multipolygon`
- **CRS:** CRS84 (lon/lat). 14,892 vertices, 600 kB as GeoJSON. One polygon per ward.
- **Currency, verified:** all 12 `councillor` values match the winners in the 2025 official results (`fv5x-8efu`) and the contacts table (`e9qt-cc3j`). The boundaries are the 2021 redraw: `effective_start_date` is 2021-10-18 on every row.
- **No boundary change since 2021, verified from the data:** the companion history layer `nydb-6rce` (42 rows) holds 2007, 2013, 2017 and 2021 boundary sets and **no row with `effdt_type = 'Future'`**. That layer is where an adopted change would first appear, so the refresh should watch it.
- **Not verified:** whether the Returning Officer's post-election ward report required by Policy C469A has gone to Council, and what it proposes. The City's ward-boundary-review page returned 404 on 2026-10-10.
- **Quirks:**
  - `effective_start_date` is typed **text** here, with a `-07:00` offset, and `calendar_date` in `nydb-6rce`.
  - `councillor2` is empty on every row; purpose unknown.
  - Ward names differ between datasets: `O-day'min` (straight apostrophe) here and in results, `O-day’min` (curly) in contacts; contacts append syllabics to two names (`Ward pihêsiwin ᐱᐦᐁᓯᐏᐣ`, `Ward tastawiyiniwak ᑕᐢᑕᐃᐧᔨᓂᐊᐧᐠ`) and prefix "Ward ". Join on a normalised key, never on the raw string.
  - The contacts table gives the pihêsiwin councillor as "Michael Elliott"; the ward layer says "Mike Elliott".
  - The 12 polygons are a valid coverage but leave 28 sliver gaps between wards totalling 67 m² (largest 62 m²). No parcel address falls in one.

### Mayor and councillor contacts — `e9qt-cc3j`
- **Publisher / URL:** City of Edmonton, https://data.edmonton.ca/d/e9qt-cc3j
- **Retrieved:** 2026-10-10 — **publisher last-updated:** 2025-10-29
- **Rows / columns:** 13 (mayor + 12); `electoral_area`, `primary_role`, `first_name`, `last_name`, `email`, `photo_url`, `url`, address fields, `phone`, `fax`
- **Quirks:** `url` is each member's official edmonton.ca page and is the contact link to show. Not refreshed since nine days after the election, so a mid-term change may not appear here promptly.

### 2025 election results — `fv5x-8efu`
- **Publisher / URL:** City of Edmonton (Edmonton Elections), https://data.edmonton.ca/d/fv5x-8efu
- **Retrieved:** 2026-10-10 — **publisher last-updated:** rows 2025-11-06
- **Rows / columns:** 140 candidate rows; `contest`, `wardname`, `candidatename` (`SURNAME, Given`), `votes`, `acclaimed`, `partyname`, `slatename`, plus turnout fields repeated on every row
- **Use:** cross-check only. It records who won on 2025-10-20, not who holds office today.
- **Quirks:** 29 contests: mayor, 12 councillors, 9 public trustees, 7 Catholic trustees. Catholic Ward 75 was acclaimed (`votes` = 0, `acclaimed` = Yes), so "most votes" alone does not find that winner.

### Ward population — `eg3i-f4bj`
- **Publisher / URL:** City of Edmonton, from Statistics Canada 2021 Census, https://data.edmonton.ca/d/eg3i-f4bj
- **Retrieved:** 2026-10-10 — **publisher last-updated:** 2023-09-27
- **Rows / columns:** 278 neighbourhoods; `neighbourhood_number`, `neighbourhood`, `total_population`, `ward`
- **Figures (2021 Census, summed by ward):** Anirniq 90,035 · Dene 89,520 · Ipiihkoohkanipiaohtsi 84,370 · Karhiio 94,525 · Métis 85,340 · Nakota Isga 81,175 · O-day'min 68,110 · papastew 71,675 · pihêsiwin 81,800 · sipiwiyiniwak 95,020 · Sspomitapi 83,610 · tastawiyiniwak 85,415. Total 1,010,595; mean 84,216. Range −19.1% (O-day'min) to +12.8% (sipiwiyiniwak) from the mean.
- **Quirks:** these are neighbourhood counts added up, and Statistics Canada rounds each to a multiple of 5, so ward totals are approximate and the city total differs slightly from the published census figure. Requires the acknowledgement "Adapted from Statistics Canada, 2021 Census of Population" and a statement that this does not constitute an endorsement by Statistics Canada.
- **Open:** this is the most recent ward-level population on the portal. Five years old; growth since 2021 has been uneven across wards. No newer primary source found yet (the City's last municipal census was 2019, on pre-2021 wards).

### School wards — `d7pj-rist` (public), `pwzf-sjj2` (Catholic)
- **Publisher / URL:** City of Edmonton, https://data.edmonton.ca/d/d7pj-rist and https://data.edmonton.ca/d/pwzf-sjj2
- **Retrieved:** 2026-10-10 — **publisher last-updated:** 2026-10-05
- **Rows / columns:** 9 and 7; `name` (A–I, 71–77), `descriptive_name`, `effective_start_date`, `effective_end_date`, `trustee`, `geometry_multipolygon`
- **CRS:** CRS84. 9,358 and 10,691 vertices; 377 kB and 430 kB.
- **⚠️ The `trustee` column is stale. Use the geometry only.** See `docs/DATA_ISSUES.md`.
- **Quirks:** the catalogue search surfaces the map views (`acvv-cap3`, `gx56-4iuu`); the tables behind them are the ids above. History layers: `y5qu-dj6t` (public; 2013, 2017, 2021 sets, no Future rows). The Catholic boundaries predate the public ones (2020-11-25 against 2021-10-18).
- **Not verified:** that the school-ward boundaries used in the 2025 election are these. The boards set their own ward bylaws; the City layer shows no change since 2021.

### Trustees — board websites
- **Edmonton Public Schools:** https://www.epsb.ca/ourdistrict/board/trustees/ — nine trustees, one page each at `/ourdistrict/board/trustees/ward-<a..i>/`.
- **Edmonton Catholic Schools:** https://www.ecsd.net/ecsd-trustees — seven trustees, one page each at `ecsd.net/ward-<71..77>`.
- **Read:** 2026-10-10. Both rosters match the 2025 official results in all 16 seats.
- **Quirks:** HTML pages, no export. A scraper here is fragile; a page-layout change must fail loudly rather than return an empty roster.

### Provincial ridings — Elections Alberta
- **Publisher / URL:** Elections Alberta, https://www.elections.ab.ca/resources/maps/ → `https://www.elections.ab.ca/uploads/2019Boundaries_ED-Shapefiles.zip`
- **Retrieved:** 2026-10-10 — **publisher last-updated:** HTTP Last-Modified 2024-09-11; files inside dated 2018-03-01
- **Rows / columns:** 87; `EDNumber20`, `EDName2017`, `Km2`, `Hectares`, `Acres`, `Authority`
- **CRS:** EPSG:3401, NAD83 / Alberta 10-TM (Resource)
- **Vintage:** `EDS_ENACTED_BILL33_15DEC2017` — the divisions enacted in 2017, in force since 2019-03-19. These are the divisions the current 31st Legislature sits for.
- **⚠️ Change pending.** The Electoral Boundaries Commission's final report (tabled 2026-03-26) was set aside. Government Motion 37 (passed 2026-04-21) created the Select Special Committee on Electoral Boundaries, which must report to the Assembly by **2026-11-02**. Nothing was enacted as of 2026-10-09. A new map would apply from the next general election, so MLAs keep representing the 2017 divisions until then; the tool will need to show current ridings and, once enacted, label the future ones as future. Source: https://www.assembly.ab.ca/assembly-business/committees/CEB
- **Coverage of Edmonton, measured:** 20 "Edmonton-" divisions. All 298,238 City parcel addresses fall in exactly one division; **1 address falls in Morinville-St. Albert**. Eight other neighbouring divisions overlap the City's area by slivers under 0.4 km² each, with no addresses in them.
- **Quirks:** the server answers 403 to Python's default User-Agent; send one naming the project (2026-10-15). No licence or terms of use are stated on the download page. The open.alberta.ca "electoral division" dataset describes the 2010 boundaries; do not use it.

### MLAs — Legislative Assembly of Alberta
- **Publisher / URL:** https://www.assembly.ab.ca/members/members-of-the-legislative-assembly → `https://www.assembly.ab.ca/txt/mla_home/contacts.csv`
- **Retrieved:** 2026-10-10
- **Rows / columns:** 91 lines. **It opens with a banner: "Date file created", the quoted date, a blank line; the header is line 4** (corrected 2026-10-16). Address columns repeat their names for the two offices. Columns then run: division number, division name, title, first, middle, last, caucus, office fields.
- **Quirks:** division number matches `EDNumber20` in the boundary file (27–46 are the Edmonton divisions), which is the join key. All 20 Edmonton seats are filled.

### Federal ridings — Elections Canada
- **Publisher / URL:** Elections Canada, https://open.canada.ca/data/en/dataset/18bf3ea7-1940-46ec-af52-9ba3f77ed708 → `https://www.elections.ca/res/cir/mapsCorner/edb/FederalElectoralDistricts_SHP.zip`
- **Retrieved:** 2026-10-10 — **publisher last-updated:** HTTP Last-Modified 2026-09-15; catalogue record modified 2026-09-17
- **Rows / columns:** 343; `ED_CF_NUM` (5-digit code, 48xxx in Alberta), `ED_NAMEE`, `CF_NOMF`
- **CRS:** EPSG:3347, NAD83 / Statistics Canada Lambert
- **Vintage:** 2023 Representation Order, first used at the general election of 2025-04-28. The current map.
- **Coverage of Edmonton, measured:** 9 "Edmonton" districts. All 298,238 parcel addresses fall in exactly one district; **5 fall in Sherwood Park—Fort Saskatchewan and 1 in Leduc—Wetaskiwin**. St. Albert—Sturgeon River and Parkland overlap the City's area by under 0.3 km² each with no addresses.
- **Quirks:** 10 MB zip for the whole country; clip to the Edmonton area before simplifying.

### MLA list — Legislative Assembly of Alberta (`ab_mla_list`)
- **URL:** https://www.assembly.ab.ca/members/members-of-the-legislative-assembly (HTML)
- **Read:** 2026-10-16. One table row per member: a link `member-information?mid=<id>`, "Last, Honorific First", caucus, division. Former members are listed with "Former Member" in place of a division.
- **Use:** each MLA's `contact_url` (the member page, `&legl=31`), and the MLA cross-check: the surname in `contacts.csv` must appear in the listed name for the same division. Same publisher as `contacts.csv`, so it catches a stale or mis-joined file, not a publisher error.

### MPs — House of Commons
- **Publisher / URL:** https://www.ourcommons.ca/Members/en/search?province=AB → CSV at `/Members/en/search/csv?province=AB`, XML at `/Members/en/search/xml?province=AB`
- **Retrieved:** 2026-10-10
- **Rows / columns:** 37 Alberta members; `Person ID`, `Honorific Title`, `First Name`, `Last Name`, `Constituency`, `Province / Territory`, `Political Affiliation`, `Start Date`, `End Date`
- **Quirks:** joins to the boundary file on constituency **name**, not code. `Start Date` contains a narrow no-break space (U+202F) before "a.m.". All 9 Edmonton seats are filled. `contact_url` is `https://www.ourcommons.ca/Members/en/<Person ID>` (200 on 2026-10-16). No second source: `cross_check` is null.

### Addresses — `ut27-nrpn`
- **Publisher / URL:** City of Edmonton, https://data.edmonton.ca/d/ut27-nrpn
- **Retrieved:** 2026-10-10 — **publisher last-updated:** 2026-10-05
- **Rows / columns:** 776,614 (298,238 `PARCEL`, 478,376 `SUITE`, all `status = OFFICIAL`); `sub_address`, `house_number`, `street_name`, `latitude`, `longitude`, `object_type`, `record_id`, `neighbourhood_number`, `neighbourhood_name`
- **Use:** the address layer for client-side geocoding. Suites share their parcel's ward, so the parcel rows are enough.
- **Size, measured:** 288,315 distinct house number + street pairs across 2,800 street names. As a compact JSON index (street → house number, lat, lon to 5 decimals) it is 8.4 MB, **2.2 MB gzipped**.
- **Quirks:**
  - **`record_id` is not unique within `PARCEL` rows** (298,238 rows, 298,154 distinct ids), so `$order=record_id` is not a stable paging order. Page on Socrata's `:id` and check the total against `count(*)`.
  - 2,474 house number + street pairs appear on more than one parcel row (2,477 on 2026-10-15, 9,927 rows beyond the first). **8 of them have rows in different districts** on at least one layer, so they cannot be collapsed to one answer; the other 2,469 agree on all five layers. Measured 2026-10-15, `prototype/README.md` "Districts per address".
  - 298,453 `PARCEL` rows on 2026-10-15 (298,238 on 2026-10-10).
  - `street_name` is upper case with the quadrant suffix (`ALEXANDER CIRCLE NW`). No postal code.
  - A single 300,000-row CSV request stalled twice; 50,000-row pages return in about 9 s each.

### Neighbourhoods — `65fr-66s6`
- **Publisher / URL:** City of Edmonton, https://data.edmonton.ca/d/65fr-66s6
- **Retrieved:** 2026-10-10 — **publisher last-updated:** 2026-10-05
- **Rows / columns:** 407 (residential and industrial); `neighbourhood_number`, `name`, `descriptive_name`, `description`, `civic_ward_name`, `district`, `effective_start_date`, `effective_end_date`, geometry
- **CRS:** CRS84
- **Use:** the communities-of-interest lens (`docs/SPEC_civic_map.md`, amendments).
- **Measured 2026-10-10, by address:** every parcel address falls in exactly one neighbourhood. Neighbourhoods with at least 10 addresses on each side of a boundary line:

  | Layer | Divided neighbourhoods (of 407) | Any address on a second side |
  |---|---|---|
  | Council wards | 2 | 3 |
  | Public school wards | 0 | 2 |
  | Catholic school wards | 2 | 4 |
  | Provincial ridings | 13 | 44 |
  | Federal ridings | 8 | 30 |

  Largest: The Orchards at Ellerslie (2,468 addresses in Edmonton-Ellerslie, 1,320 in Edmonton-South) and Walker (1,855 in Edmonton Gateway, 1,574 in Edmonton Southeast). The 10-address floor is a first guess to keep digitising slivers out; the right threshold is not settled.
- **Quirks:** `neighbourhood_name` and `neighbourhood_number` in the address layer `ut27-nrpn` are **empty on every row**, so neighbourhood has to come from a point-in-polygon against this layer. The catalogue search surfaces the centroid table `3b6m-fezs` first; this is the polygon one. `Neighbourhood Boundaries : 2019` (`xu6q-xcmj`) is an old snapshot.
- **Not found:** community league **boundaries**. The portal has league halls as points (`kaps-rk7z`) only. The Edmonton Federation of Community Leagues is the likely primary source; not yet checked.

### Buildings and physical barriers (candidates, catalogue metadata only)
Found on the City portal 2026-10-10. Row counts and columns are from the
portal's API; **no geometry has been downloaded or checked yet.**

| Need | Dataset | Rows | Vintage | Notes |
|---|---|---|---|---|
| Buildings with height | `jpxi-a9a5` City of Edmonton - Rooflines (as of 2019) | 384,228 | 2019; rows updated 2021-01-20 | `building_height`, `elevation_ground`, `elevation_rooftop`, `area`. Mean height 5.7 m, tallest 146.8 m, 597 over 20 m (re-measured from the full download 2026-10-14: every row has a height of at least 1.02 m and `elevation_rooftop` − `elevation_ground` equals it; 325 outlines are self-intersecting; 3,472,472 vertices; `layer` is `Building` on 343,169 rows and `Building_2019` on 41,059; licence field reads "See Terms of Use"). Trial tiles: 26.8 MB at z12–z15 (`prototype/README.md`). **Seven years old**: newer neighbourhoods will be missing buildings. |
| Buildings, older | `6n9r-ddf8` Building Footprint | 365,822 | May 2017 | no height column; superseded by the 2019 layer |
| Roads by class | `9j8t-zm52` Road Network | 53,873 segments | rows updated 2026-10-10 | `functional_class_code` separates arterials (classes A–D, about 8,900 segments; class A is primary highway) from collectors and locals. 14,229 segments have no class. |
| River valley | none found as a boundary layer | | | `6w3s-58pv` Zoning Overlays may carry the river valley overlay; not checked. `edmonton-tax-viz` has no edge either, only two proxies: zoning codes `A` and `NA` (River Valley), and neighbourhoods in `65fr-66s6` named "RIVER VALLEY ...". An edge could also be derived from terrain, if terrain is sourced. |
| Rail lines | `9j8t-zm52` Road Network, rows with `centerline_type = 'Railway'` | 2,117 rows, 704 km (as counted by `edmonton-tax-viz`) | | Reported by the `edmonton-tax-viz` session 2026-10-13; not checked here. A City feed, so expect it to stop at the municipal boundary. Federal alternative, not checked: Natural Resources Canada's National Railway Network. |
| Terrain | found 2026-10-13; see "Terrain and elevation" below | | | The 2026-10-10 search missed these: it did not try "elevation", "lidar" or "contour". |

**Sources `edmonton-tax-viz` already uses** (reported by that session
2026-10-13 from its `data/DATA.md` and build scripts; none re-checked here, and
each needs its licence confirmed before this project ships it):

| Need | Source | Licence, as reported | Notes |
|---|---|---|---|
| River | Alberta `base_water_feature` MapServer layer 72 "Lake/River (20K)", `NAME='North Saskatchewan River'`, https://geospatial.alberta.ca/titan/rest/services/environment/base_water_feature/MapServer/72/query | Open Government Licence – Alberta | Polygons. Simplified there at 25 m in EPSG:3400. |
| City limit and neighbouring municipalities | Alberta `urban_and_rural_municipality` MapServer, layer 78 for Edmonton, https://geospatial.alberta.ca/titan/rest/services/base/urban_and_rural_municipality/MapServer/78/query | Open Government Licence – Alberta | Edmonton outline 782.38 km² after 100 m simplification. |
| Highways | OpenStreetMap through Overpass, classes motorway and trunk | ODbL, attribution required | **Not a primary source.** Usable here only as drawn context, and only if the owner agrees; `docs/SCOPE.md` rules out community wikis as data. The City feed `9j8t-zm52` has the same highways as Province rows (1,164) but they stop at the municipal boundary, which may be enough for a city-only map. |
| Arterial, collector and local roads | `9j8t-zm52`, `centerline_type == 'Road'`, City-owned rows | Open Government Licence – City of Edmonton | Its build script is `src/load_roads.py` in that repo: dissolved, welded and simplified to 272 kB gzipped. Its filter drops 12,088 alley rows and the Railway and Province rows. |

⚠️ **Alberta MapServer layers can return features with NULL geometry and HTTP
200.** `edmonton-tax-viz` found `transportation/highways_public` returning all
510 features with no geometry. Check geometry, not counts.

`edmonton-tax-viz` never touched the Rooflines layer, so there is no size or
quality record to borrow.

### Terrain and elevation (candidates, catalogue metadata only)
Found 2026-10-13 through the federal STAC catalogue
(`https://datacube.services.geo.ca/stac/api`, searched with an Edmonton
bounding box) and the City portal's catalogue API. Sizes are from HTTP headers
and portal metadata. Elevation values have been read for MRDEM-30 only (below); the other rows are
catalogue metadata, with vertical datum and CRS as stated by the publisher.

| Dataset | Publisher | Resolution | Vintage | Size and format | Licence, as stated |
|---|---|---|---|---|---|
| MRDEM-30, STAC collection `mrdem-30`, `https://canelevation-dem.s3.ca-central-1.amazonaws.com/mrdem-30/mrdem-30-dtm.tif` | Natural Resources Canada | 30 m, bare ground (DTM) and surface (DSM) | file dated 2026-06-24 | one national cloud-optimised GeoTIFF, 83.9 GB; the server accepts range requests, so the Edmonton window can be read without the rest | OGL-Canada-2.0 |
| HRDEM by lidar project, STAC collection `hrdem-lidar`, item `AB-Edmonton-1m` | Natural Resources Canada | 1 m, DTM and DSM | flown 2018-05-12 | DTM 2.38 GB, cloud-optimised GeoTIFF | OGL-Canada-2.0 |
| same collection, item `NRCAN-Edmonton_2018-1m` | Natural Resources Canada | 1 m, DTM and DSM | flown 2018-05-12 | DTM 18.78 GB; a wider area than the item above, extent not compared yet. `AB-St_Albert_UTM12_2018-1m` also intersects the box. | OGL-Canada-2.0 |
| HRDEM mosaics, `hrdem-mosaic-1m` and `hrdem-mosaic-2m`, tile `3_4` | Natural Resources Canada | 1 m and 2 m | mosaic dated 2024-10-19 | 368 GB and 96 GB per regional tile; range-readable | OGL-Canada-2.0 |
| `i85g-8mg6` 2025 Lidar - Bare Earth | City of Edmonton | not stated in the part of the description read | flown 2025-06-29 and 30; 859.6 km², city limit plus 100 m | one 26.7 GB zip | "See Terms of Use" |
| `8tsc-dykz` 2019 Lidar - Bare Earth | City of Edmonton | includes a 50 cm hydro-flattened DEM | flown 2019-09-04 to 13; 816 km², city limit plus 200 m; datum CGVD28, 3TM 114 | one 25.5 GB zip | "See Terms of Use" |
| `n6cj-24tp` Contour Lines LL - WGS84 | City of Edmonton | 0.5 m contour interval | 2016 | 383,934 lines, `elevation` + geometry, queryable through the API | none stated on the dataset |
| `nppw-6ykk`, `4zih-x3jw` DEM Points and Break Lines 3TM | City of Edmonton | points and break lines | 2009 | 37 MB and 154 MB zips | "See Terms of Use" |
| `tarx-cg5m` Spot Elevation | City of Edmonton | hill tops and pit bottoms | 2009 | 686,638 points | "See Terms of Use"; described as "will likely be replaced or removed" |

- **Full-feature lidar** (surface with buildings and trees) is also published: `sz3i-y5ze` (2025, 42.7 GB) and `bf5f-8bzd` (2019, 15.3 GB).
- **`78sz-qcfr` 3D Buildings**: a City 3D model built from the 2019 rooflines `jpxi-a9a5` and the 2019 lidar. One 225 MB file geodatabase zip (453 MB unpacked), 3TM 114, made public 2023-06-15, static. No licence stated on the dataset.
  - **Opened and counted 2026-10-13** (every feature read through GDAL; triangles counted, coordinates not checked): one layer `Building_MP_Merge`, 383,329 buildings, all with geometry, stored as triangle meshes (OGR type TIN Z). Fields `PRESEG_FID`, `District`, `BLDGHEIGHT`, `ROOFFORM`, `BASEELEV`.
  - **13.8 million triangles** in all. Per building: median 28, mean 36, 95th percentile 88, largest 2,848. A four-cornered footprint pushed up to a flat roof is 10.
  - **`ROOFFORM`:** Gable 362,319 · Flat 20,084 · Hip 383 · Vault 304 · Mansard 67 · Shed 65 · Dome 19 · empty 84. Gable on 94.5% of buildings, sheds and garages included, reads like the modelling tool's default more than a survey of roofs; not checked against imagery.
  - **`BLDGHEIGHT`:** median 5.5 m, tallest 198.9 m, 439 over 20 m, 46 at zero or below. The rooflines layer's catalogue figures differ (tallest 146.8 m, 597 over 20 m, 384,228 rows); the two have not been reconciled.
  - `BASEELEV` gives each building's ground height, which a terrain view needs to seat buildings on the slope.
  - Reading it: `pyogrio` refuses the geometry type; it was read by calling the GDAL library bundled with `pyogrio` directly.
- **MRDEM-30 DTM, Edmonton window read 2026-10-14** (`prototype/terrain.py`; range-read, about 1,900 by 1,900 cells):
  - **CRS:** EPSG:3979, NAD83(CSRS) / Canada Atlas Lambert; 30 m cells, float32, no-data −32767, LZW, overviews to 1:513. File date 2026-06-22. No no-data cells in the Edmonton window.
  - **Vertical datum: not stated** in the file or in the STAC collection and item. Against the City's own ground heights (`elevation_ground` of a 5% sample of the rooflines, 19,110 buildings), MRDEM reads **0.48 m lower** at the median (5th to 95th percentile −1.11 to +0.17 m; 0.2% differ by more than 3 m). That fits a CGVD2013 against CGVD28 offset, the City's 2019 lidar being CGVD28, but neither datum is confirmed for these two layers. Half a metre does not show on a map; it matters only if heights are ever quoted.
  - **Range inside the city** (the 12 wards of `b4er-5rp2` unioned, 759.7 km²): **602.1 to 752.2 m**, median 679.3 m, 1st to 99th percentile 611.0 to 736.0 m.
  - **River valley depth:** on four north–south cross-sections, the valley floor is 611.5–620.1 m and the higher ground on each side 659–674 m, so the valley is **about 48–59 m deep** (Capilano 48–53, Terwillegar 49–54, Groat Road 52–55, downtown 53–59). "Higher ground" is the highest cell within about 2.5 km on each side of the floor, which can include rises beyond the rim.
  - Packed as elevation tiles: 2.69 MB (`prototype/README.md`).
- **Scale check, arithmetic only:** the city is roughly 30 km across, so a 30 m grid is about 1,000 by 1,000 heights and a 10 m grid about 3,000 by 3,000.
- **River valley edge:** not a layer anywhere found, but derivable from any of the bare-ground models above as the line where slope steepens, or readable from the City's contours.
- **Not usable as found:** the Alberta Provincial DEM (25 m and 100 m rasters) is built from 1955–1996 photogrammetry; listed only so it is not rediscovered.

384,228 roofline polygons is the storage question for the detail phase: far too
large to ship as GeoJSON, so buildings mean vector tiles or heavy
simplification, whichever stack is chosen.

### Population and growth (for the population lens)
- **Balance today:** ward population from the 2021 Census, "Ward population" above. Every ward was within −19.1% to +12.8% of the mean in 2021. **The tolerance Policy C469A actually allows is not verified**; ±25% is a common Canadian figure, not a quoted Edmonton one.
- **Density:** the same census table is by neighbourhood (278 rows), and `65fr-66s6` gives neighbourhood areas, so people per hectare by neighbourhood is derivable. Not yet computed.
- **Forecasts: none found on the City portal** (searched "population forecast", "population projection", 2026-10-10). Leads not yet checked: `k8bn-rfq9` Growth Monitoring Reports (updated 2025-02-13), `avbh-ga6n` City Plan_Planning Districts, `jdmr-bidz` Plans in Effect, and the City Plan's population targets by district, which may exist only in documents.
- **Growth already permitted — `24uj-dj8v` General Building Permits:** 247,482 rows; `issue_date`, `units_added`, `neighbourhood`, `latitude`, `longitude`. Between 2021-05-12 and 2026-10-08, 27,353 permits changed the unit count, for a net **70,165 dwelling units** (273 rows are negative: demolitions and conversions).
  - **⚠️ 7,466 of those rows, carrying 18,167 units (26%), have no coordinates.** Placing permits by latitude and longitude alone drops a quarter of the units, and probably not evenly: large multi-unit buildings are the likely ones missing. A first by-ward sum of the 51,998 located units is therefore **not usable** and is not recorded here. Use the `neighbourhood` column for the unlocated rows, and report what still cannot be placed.
  - Note the misspelt column `neighbourhood_numberr`.
  - Units permitted are not units built or occupied, and not people. Converting them to population needs a persons-per-unit assumption that must be stated and sourced.

### Not a source: Represent (Open North)
`represent.opennorth.ca` answers "who represents this point" for all three levels, but it is a third-party aggregator and sending it a location is the third-party geocoding the brief rules out without the owner's say-so. Listed so it is not rediscovered as a shortcut.
