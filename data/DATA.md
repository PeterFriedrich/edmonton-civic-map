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

**Weekly refresh, 2026-10-16:** `.github/workflows/refresh.yml` runs the
download, the three builders and the diff check every Monday (`docs/SPEC_data_schema.md` §8).
The download also GETs each source's `landing_url`; all 10 distinct ones
answered 200 on 2026-10-16. **robots.txt, checked once by hand 2026-10-16**
with Python's `robotparser` and the project User-Agent: every fetch, landing
and Socrata metadata URL is allowed. `data.edmonton.ca`, `elections.ca`,
`open.canada.ca`, `ecsd.net`, `assembly.ab.ca` and `ourcommons.ca` serve one;
`elections.ab.ca` and `epsb.ca` answer 404 (no restrictions). Recheck when a
source is added.

**Builds are reproducible only on one CPU architecture.** The same source
bytes rebuilt on x86_64 (GitHub's `ubuntu-latest`) and on aarch64 (this
server) give boundary files that differ by float noise after reprojection and
simplification: on 2026-10-16 the shared edge of `provincial_riding:33` and `:35`
moved 13 m², and the diff check held the first refresh run (issue #52).
Addresses were unaffected. The refresh runs on `ubuntu-24.04-arm` for this
reason; build anything you commit on aarch64 too, or the next refresh holds.
Even on aarch64, an exact tie decided by float noise could differ between
machines: the refresh of 2026-10-16 (`376288f`) published six address points
13–73 m from this server's build, from the same parcel file (sha256
`59cb2826…`). **The City had not moved them**, though PR #54 said so. Each
address had two parcel rows in the same districts, which are always exactly as
far from their midpoint, and the runner broke the tie the other way. Since
2026-10-16 the distance is rounded to 0.01 m² and a tie goes to the first row
(`test_two_parcel_tie_goes_to_the_first_row_whatever_the_float_noise`).

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

- **Ward boundary review (read 2026-10-17).** Council Policy C469B: the Returning Officer reviews the wards after every general election and, **"During Quarter 4 of the year following each municipal general election"**, reports to Council whether minor or major adjustments are needed, on population, projected population and estimated electors. For the 2025 election that is **October–December 2026**; no report was found on 2026-10-17. Changes must be in a bylaw by December 31 of the year before the election (MGA s.151(1)), so any change takes effect for 2029. A Ward Boundary Commission reviews every third election cycle after the last one (whose report was May 2020).
  - **The last post-election review:** Bylaw 20304, Amendment No. 4 (first reading 2023-01-31; petition period closed 2023-05-17 with no petition), moved **Calgary Trail South from Karhiio to papastew** to match both school boards' wards, with no other change. The City layer has Calgary Trail South in papastew: in effect.
  - **Unresolved:** a search summary of a Returning Officer report also names moving **Yellowhead Corridor West from Anirniq to O-day'min** to match Edmonton Public's wards. The City layer still has it in Anirniq (public ward C). Whether that was a proposal not adopted, or belongs to a report not yet acted on, is unknown: Council documents on `pub-edmonton.escribemeetings.com` answer 403 to this server and to WebFetch, and the City's ward-boundary-review pages and `engaged.edmonton.ca/wardreview` return 404. Read by hand before relying on either.

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
- **Boundaries it was published on:** the neighbourhoods **as of census day**, `5bk4-5txu` "2021 Federal Census: Neighbourhoods as of Official Census Day" (403 polygons; its `neighbourh` column holds the number as a float string, `"2010.0"`), not the current `65fr-66s6` (407). All 278 census rows join to a census-day polygon by number, and every row's `ward` is among the council wards of that neighbourhood's addresses today.
- **Joined to the current 407 (measured 2026-10-17):** 274 census rows join by number. **Four populated neighbourhoods were renumbered since census day** and join by geometry only, each overlapping one current polygon almost entirely:

  | Census row | 2021 population | Current neighbourhood | Share of the census-day polygon |
  |---|---|---|---|
  | 1150 Oliver | 18,695 | 1151 Wîhkwêntôwin | 99.9% |
  | 2691 Horse Hill Neighbourhood 1A | 630 | 2692 Quarry Ridge | 100.0% (current is 11 ha larger) |
  | 5462 Chappelle | 10,910 | 5471 Chappelle | 99.0% (0.7% now in Desrochers Area) |
  | 5464 Heritage Valley Town Centre | 1,220 | 5472 Heritage Valley Town Centre | 99.6% |

  So 407 − 274 = 133 current neighbourhoods do not join by number; 4 are these renumbered ones, and **129 have no 2021 row at all**. None is a populated 2021 neighbourhood left out, as far as names and addresses show:
  - **53 industrial or business** by name ("… Industrial", "Eastgate Business Park", "Lewis Farms Business Employment" and the like);
  - **40 river valley, "… Area", or Anthony Henday road corridors** ("River Valley …", "Anthony Henday …", "Blatchford Area", "Clover Bar Area", "CPR Irvine");
  - **36 others**: neighbourhoods still being built in 2021 (Alces, Aster, Marquis, River's Edge, Crystallina Nera East, Mattson, Meltwater, Gorman, Pintail Landing), new since census day (Crossroads, Lewis Farms, Kendal), and institutional, commercial, park or ravine land (University of Alberta, South Edmonton Common, Edmonton Northlands, Mill Woods Park, the Whitemud and Mill Creek ravines). Several now hold hundreds of addresses (Alces 1,491, Aster 1,163, Marquis 1,128), so **2021 population says nothing about them today**.
  The publisher does not say why a census-day neighbourhood has no row (lowest published count: Kinglet Gardens, 305); not asked.
- **Boundaries moved since census day:** 34 neighbourhoods present on both maps differ by more than 0.1 ha. Among those with a census row, the largest are Riverview Area (75 ha), Keswick (55 ha), Desrochers Area (16 ha), The Orchards At Ellerslie (10 ha), Windermere and Evergreen (9 ha each). A 2021 count belongs to the census-day polygon; shown against today's polygon it is approximate where the edge moved.
- **Ward split:** of the census neighbourhoods, only Glenridding Ravine (860 people, row's ward pihêsiwin) has addresses in two council wards today. A ward total from this table puts all 860 in pihêsiwin.
- **City total not checked against Statistics Canada:** the rows sum to 1,010,595. statcan.gc.ca answered a script with a "Security Check" page on 2026-10-17, so the published census profile was not read; compare by hand before quoting a city total.
- **Open:** this is the most recent ward-level population on the portal. Five years old; growth since 2021 has been uneven across wards. No newer primary source found yet (the City's last municipal census was 2019, on pre-2021 wards).

### School wards — `d7pj-rist` (public), `pwzf-sjj2` (Catholic)
- **Publisher / URL:** City of Edmonton, https://data.edmonton.ca/d/d7pj-rist and https://data.edmonton.ca/d/pwzf-sjj2
- **Retrieved:** 2026-10-10 — **publisher last-updated:** 2026-10-05
- **Rows / columns:** 9 and 7; `name` (A–I, 71–77), `descriptive_name`, `effective_start_date`, `effective_end_date`, `trustee`, `geometry_multipolygon`
- **CRS:** CRS84. 9,358 and 10,691 vertices; 377 kB and 430 kB.
- **⚠️ The `trustee` column is stale. Use the geometry only.** See `docs/DATA_ISSUES.md`.
- **Against each board's own layer (measured 2026-10-17).** Edmonton Public Schools' GIS server publishes both boards' wards: `azimuth.epsb.ca/server/rest/services/Hosted/EPSB_Wards_2025/FeatureServer/264` ("as defined and used for the four-year trustee term beginning in October 2025", Data Analysis Team, Infrastructure Planning, EPSB) and `.../FC_ECSD_Wards_2025/FeatureServer/227` (created by Educational Planning, Edmonton Catholic Schools; its description still says the term "beginning in October 2021", and its `date_effec` is 2020-11-25, the same as the City layer). No licence is stated on either. Same ward names; the edges differ:
  - **Public:** ward areas differ by up to 1.69 km² (H) and edges by up to 361 m (B), mostly slivers along the city limit. Through the 288,534 published address records: 2 fall in no board ward, and **1 is in a different ward: 610 Calgary Trail NW, I on the City layer, H on the board's**.
  - **Catholic:** 71 and 74–77 agree to 1.3 m. The 72/73 edge differs by up to 368 m near Manning Drive and 34 Street NE, putting **2 addresses in a different ward: 15928 Manning Drive NW and 17611 34 Street NW, 72 on the City layer, 73 on the board's**. 17611 34 Street NW carries no near-boundary note on our site, because it is 368 m from the City's line.
  - **Which is right is not settled.** The ward bylaws were not found online: the City's page (2026-10-17, via search) says EPSB passed **Bylaw 2020-2 on 2020-09-08** for the 2021 election; no Catholic bylaw number was found. The City's per-ward PDF maps on the ward-maps page ("Map Revised: April 29, 2025" for Catholic 72/73, "June 05, 2025" for public H, "WARD BOUNDARIES IN EFFECT FOR 2025 EDMONTON ELECTION") are drawings, not boundary text. Edmonton Elections administers the school-board votes, so the City layer is what the returning officer used, by inference only. `docs/DATA_ISSUES.md` 2026-10-17.
- **Quirks:** the catalogue search surfaces the map views (`acvv-cap3`, `gx56-4iuu`); the tables behind them are the ids above. History layers: `y5qu-dj6t` (public; 2013, 2017, 2021 sets, no Future rows). The Catholic boundaries predate the public ones (2020-11-25 against 2021-10-18).
- **Not verified:** that the school-ward boundaries used in the 2025 election are these. The boards set their own ward bylaws; the City layer shows no change since 2021.

### Trustees — board websites
- **Edmonton Public Schools:** https://www.epsb.ca/ourdistrict/board/trustees/ — nine trustees, one page each at `/ourdistrict/board/trustees/ward-<a..i>/`.
- **Edmonton Catholic Schools:** https://www.ecsd.net/ecsd-trustees — seven trustees, one page each at `ecsd.net/ward-<71..77>`.
- **Read:** 2026-10-10. Both rosters match the 2025 official results in all 16 seats.
- **Quirks:** HTML pages, no export. A scraper here is fragile; a page-layout change must fail loudly rather than return an empty roster.

### Provincial ridings — Government of Alberta (`ab_ridings`, since 2026-10-16)
- **Publisher / URL:** Government of Alberta (Environment and Parks), "Provincial Electoral Division - Current 2019", https://open.alberta.ca/opendata/gda-e201c640-1f76-429c-8c24-89ff496f956e → ArcGIS layer `https://geospatial.alberta.ca/titan/rest/services/boundary/goa_administrative_area_10tm_nad83_aep/MapServer/3`, queried as GeoJSON in EPSG:4326.
- **Licence:** Open Government Licence – Alberta (version 2, https://open.alberta.ca/licence). Prescribed statement, read from the licence 2026-10-16: "Contains information licensed under the Open Government Licence – Alberta."
- **Rows / columns:** 87; `EDNUMBER`, `EDNAME` used (also `EDPROV` and `MLA_TITLE`/`MLA_FNAME`/`MLA_LNAME`, not used: the Assembly's own lists are the source for members). The layer publishes no edit date. Layers 4 and 5 of the same service are the historical 2010 and 2003 divisions; do not use them.
- **Vintage:** the description says the divisions "were enacted in December 2017 and came into effect for the 2019 provincial general election": the same map as Elections Alberta's `EDS_ENACTED_BILL33_15DEC2017`.
- **Why this copy (2026-10-16):** Elections Alberta's shapefile (`https://www.elections.ab.ca/uploads/2019Boundaries_ED-Shapefiles.zip`, from https://www.elections.ab.ca/resources/maps/) states no licence or terms, and the project published it from 2026-10-15 without one (DECISIONS row 2026-10-16). Measured against it: the same 87 division numbers and names; over the 29 published divisions, the boundaries never differ by more than 1.264 m (Hausdorff distance); the area between the two outlines sums to 2.58 km² over those 29, as thin slivers along long edges (riding 62 the largest, 0.48 km²); **all 288,534 published address records fall in the same division under either copy.** Elections Alberta stays linked as the body that administers the divisions.
- **⚠️ Change pending.** The Electoral Boundaries Commission's final report (tabled 2026-03-26) was set aside. Government Motion 37 (passed 2026-04-21) created the Select Special Committee on Electoral Boundaries, which must report to the Assembly by **2026-11-02**. Nothing was enacted as of 2026-10-09. A new map would apply from the next general election, so MLAs keep representing the 2017 divisions until then; the tool will need to show current ridings and, once enacted, label the future ones as future. Check that this layer's successor appears on open.alberta.ca when one is enacted. Source: https://www.assembly.ab.ca/assembly-business/committees/CEB
- **Coverage of Edmonton, measured (on the Elections Alberta copy, 2026-10-10):** 20 "Edmonton-" divisions. All 298,238 City parcel addresses fall in exactly one division; **1 address falls in Morinville-St. Albert**. Eight other neighbouring divisions overlap the City's area by slivers under 0.4 km² each, with no addresses in them.

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
- **Use:** neighbourhood search (`site/public/data/neighbourhoods.json`, `docs/SPEC_data_schema.md` §10), downloaded as `coe_neighbourhoods`; the communities-of-interest lens (`docs/SPEC_civic_map.md`, amendments). Names are the `descriptive_name` column, as published ("The Orchards At Ellerslie").
- **Measured 2026-10-10, by address:** every parcel address falls in exactly one neighbourhood. Neighbourhoods with at least 10 addresses on each side of a boundary line:

  | Layer | Divided neighbourhoods (of 407) | Any address on a second side |
  |---|---|---|
  | Council wards | 2 | 3 |
  | Public school wards | 0 | 2 |
  | Catholic school wards | 2 | 4 |
  | Provincial ridings | 13 | 44 |
  | Federal ridings | 8 | 30 |

  Largest: The Orchards at Ellerslie (2,468 addresses in Edmonton-Ellerslie, 1,320 in Edmonton-South) and Walker (1,855 in Edmonton Gateway, 1,574 in Edmonton Southeast). The 10-address floor is a first guess to keep digitising slivers out; the right threshold is not settled.
- **Quirks:** `neighbourhood_name` and `neighbourhood_number` in the address layer `ut27-nrpn` are **empty on every row**, so neighbourhood has to come from a point-in-polygon against this layer. The catalogue search surfaces the centroid table `3b6m-fezs` first; this is the polygon one. `Neighbourhood Boundaries : 2019` (`xu6q-xcmj`) is an old snapshot. `civic_ward_name` is not used: for Anthony Henday South East it reads Sspomitapi, but the neighbourhood's addresses are all in Karhiio (measured 2026-10-17, the only disagreement of 407). Not yet reported to the City.
- **Community league boundaries:** not on the open data portal (league halls only, as points, `kaps-rk7z`). Found 2026-10-17 on the City's own GIS server instead: "Community leagues — City GIS service" below.

### Community leagues — City GIS service (candidate; **not an open-data publication**)
- **Publisher / URL:** City of Edmonton, `https://gis.edmonton.ca/arcgisintegration/rest/services/DPIM/DPIM_FS/FeatureServer/12`, layer `GDB.V_COMMUNITY_LEAGUES` in the service behind the City's District Planning maps. A development copy (`gis.edmonton.ca/dev_arcgisintegration/.../DPIM/DisctrictPlaning/MapServer`) also lists "Community League Area" and "Community League Licensed Area"; the dev server is not a source.
- **Licence: none stated** (empty description and copyright; not on the open data portal, so OGL – City of Edmonton is not shown to apply). **Do not publish without the owner's decision**; asking the City to publish it under OGL is the clean route. EFCL publishes no boundary file (its "League Search" is a contact tool; checked 2026-10-17).
- **Retrieved:** 2026-10-17, measured in scratch only, nothing committed. 163 polygons, `maxRecordCount` 2000, CRS EPSG:3776 (requested as 4326).
- **Columns used:** `NAME`, `BYLAW_DATE` (free text, mixed formats: `Feb-15-2011`, `02-Jul-1980`, `Sept 12, 2018`), `LEAGUE_BOUNDARY` (the boundary text of the league's bylaw), `TYPE` (162 "Community League", 1 "Associated Area": Lago Lindo), `EFFECTIVE_START_DATE` / `EFFECTIVE_END_DATE` (no end dates set). **⚠️ `CRCLOGON` holds what look like City staff logon IDs: never request, store or publish it** (CLAUDE.md, no staff names). Mailing-address columns are not needed either; request named fields only.
- **Quality (measured):** 1 invalid polygon; 13 have no boundary text ("No description"); league polygons overlap by 8.0 ha in 42 pairs, almost all of it Rossdale / Downtown (7.0 ha). Bylaw dates run 1950s–2023, newest Allard (2023-09-16).
- **Coverage: 58.1% of the city's area; 17,489 of 288,534 address records (6.1%) fall in no league**, mostly newer suburbs (The Uplands 2,011, Stillwater 1,744, Alces 1,491, Desrochers Area 1,222, River's Edge 995, Paisley 982) and industrial land. **The City's own printed map agrees: those areas have no league boundary on record.** "Edmonton Community Leagues — EFCL Districts" (a JPEG shared from Google Drive, linked by EFCL per the owner; 5100×6600 px, Illustrator file dated 2026-05-04) is a City product: "Map compiled by: Enterprise Geospatial Information, Service Innovation and Performance", Mapdesk@Edmonton.ca, "Printed: April 02, 2024", "Note: Some Community League boundaries may currently be under review", and "No reproduction of this map, in whole or in part, is permitted without the express written consent of the City of Edmonton". Checked by eye 2026-10-17: The Uplands, Stillwater and River's Edge (west of the Henday), Paisley, Graydon Hill and Desrochers Area (between the Chappelle and Heritage Point leagues), and Alces (east of the Ellerslie league) carry no league outline there either. Only the EFCL district shading covers them. Allard (bylaw 2023) is drawn on both. The claim that every resident lives in a league area came from a league's website, not EFCL, and is contradicted by this. The map is evidence only: not a source, and not to be traced.
- **Leagues and neighbourhoods:** 100 leagues sit mainly in one neighbourhood; 63 span two to eight (each counted when it holds over 5% of the league).
- **Divided by a boundary line,** by address (any address / at least 10 on each side): council 5 / 3, public school 4 / 3, Catholic school 6 / 6, provincial 14 / 9, federal 11 / 8. Largest: Greater Windermere (federal 9,001 / 3,650), Horizon (provincial 9,400 / 2,327), The Baturyn (council and Catholic 2,877 / 2,131). 8 address records fall in two leagues (the overlaps).

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
- **Balance today:** ward population from the 2021 Census, "Ward population" above. Every ward was within −19.1% to +12.8% of the mean in 2021. **The allowed variance is ±25% of the optimal ward population** (city population ÷ number of wards), for population and for projected population: Council Policy **C469B** "Ward Boundary Design", approved 2022-10-17, next scheduled review 2030, read 2026-10-17. The City's ward-maps page links it as `C469A.pdf`, but that file is C469B (title and number), which superseded C469A.
- **No ward population newer than 2021 Census exists on the City portal** (catalogue searched 2026-10-17 for "population ward", "population estimate", "population forecast", "electors ward", "neighbourhood population"). The newest by-ward tables are the City's 2019 municipal census, on the pre-2021 wards. `frjf-2vsa` "Edmonton Population History" is citywide only. **The likely first newer source is the Returning Officer's post-election ward report** ("Council wards", "Ward boundary review" above), which C469B requires to assess each ward's population, projected population and estimated electors. Statistics Canada's 2026 Census population counts are another; their release date was not read (statcan.gc.ca serves scripts a security check).
- **Density:** the same census table is by neighbourhood (278 rows), and `65fr-66s6` gives neighbourhood areas, so people per hectare by neighbourhood is derivable. Not yet computed.
- **Forecasts:** C469B defines projected ward population "as determined by the Neighbourhood Population Projection maintained by Administration", so a by-neighbourhood projection exists inside the City. Not found published. **None found on the City portal** (searched "population forecast", "population projection", 2026-10-10). Leads not yet checked: `k8bn-rfq9` Growth Monitoring Reports (updated 2025-02-13), `avbh-ga6n` City Plan_Planning Districts, `jdmr-bidz` Plans in Effect, and the City Plan's population targets by district, which may exist only in documents.
- **Growth already permitted — `24uj-dj8v` General Building Permits:** 247,482 rows; `issue_date`, `units_added`, `neighbourhood`, `latitude`, `longitude`. Between 2021-05-12 and 2026-10-08, 27,353 permits changed the unit count, for a net **70,165 dwelling units** (273 rows are negative: demolitions and conversions).
  - **⚠️ 7,466 of those rows, carrying 18,167 units (26%), have no coordinates.** Placing permits by latitude and longitude alone drops a quarter of the units, and probably not evenly: large multi-unit buildings are the likely ones missing. A first by-ward sum of the 51,998 located units is therefore **not usable** and is not recorded here. Use the `neighbourhood` column for the unlocated rows, and report what still cannot be placed.
  - Note the misspelt column `neighbourhood_numberr`.
  - Units permitted are not units built or occupied, and not people. Converting them to population needs a persons-per-unit assumption that must be stated and sourced.

### Tier 2 sources — who is responsible, and how to engage (survey 2026-10-17)
Each brief §3 issue placed on the ladder in `docs/SPEC_civic_map.md` (amendment 2026-10-10). All pages read 2026-10-17 with the project User-Agent; nothing written as an entry yet.

| Issue | Rung | Source of record | States |
|---|---|---|---|
| Potholes | 1 | `edmonton.ca/transportation/report_requests/report-a-pothole` | City Roadway Maintenance; report by 311, app or online; target inspect/repair times; damage claims page |
| Snow clearing | 1 | `edmonton.ca/transportation/on_your_streets/snow-ice` | City Snow and Ice Control; Council policy and service levels linked; report by 311; residential sidewalks under Bylaw 14600 |
| Zoning and infill | 1 | `edmonton.ca/city_government/urban_planning_and_design/public-engagement-in-development-process` | Council decides rezonings at the MGA-required public hearing, where anyone may speak; a City planner decides permits (MGA s.642(1)); appeals to SDAB; postcard notice and earlier input routes |
| Transit | 1 | `edmonton.ca/ets/fares-passes`, `edmonton.ca/ets/general-feedback` | ETS is a City service; "The price of Arc products are set by City Council in conjunction with ETS"; responses via 311. Regional routes are other municipalities' |
| Property tax and assessment | 1 | `edmonton.ca/residential_neighbourhoods/property_tax_assessment/tax-breakdown`, `.../property-assessment` | Municipal share (~70%) set by the City; education share (~30%) set by the Government of Alberta, collected by the City; assessment questions to 311, formal complaints to the Assessment Review Board. Corroborated by `alberta.ca/education-property-tax`, which adds that separate (Catholic) boards opted out of the ASFF |
| Policing | 2 | `edmonton.ca/city_government/city_organization/edmonton-police-commission`; `edmontonpolicecommission.com/contact/make-a-complaint/`; `albertaprc.ca` | The Commission oversees EPS (Bylaw 14040). **Since 2025-12-01 the Commission no longer accepts complaints; they go to the Police Review Commission** (Police Act change). Non-emergency line on the City 311 page |
| Schools | 2 | `ecsd.net/board-of-trustees`; `epsb.ca/ourdistrict/board/`; `alberta.ca/education-property-tax` | Boards govern under the Education Act, which delegates the province's authority; each has a contact-the-board page; funding through the provincial education tax |
| Water and stormwater | 2 | `edmonton.ca/city_government/utilities`; EPCOR `.../how-water-and-wastewater-rates-are-set.html`, `.../contact-edmonton.html` | EPCOR runs sewer and stormwater (City page); City Council is EPCOR's rate regulator (EPCOR page); the province regulates the systems (City page) |

- **Open:** the Anthony Henday. 311 routes it to a "Gov. AB. Anthony Henday General Info" category, but no provincial page stating who maintains it was found; until one is, the potholes and snow entries say nothing about it.
- **Fetch and diff:** edmonton.ca (Drupal) pages carry `<meta name="last-modified">` and the marker "Main page content begins here"; the text after it, up to the site-wide banner, is the part to diff. `edmonton.ca/sitemap.xml` (2 pages, ~2,060 URLs) is an index. `edmontonpolicecommission.com` is WordPress: `wp-json/wp/v2/pages?slug=<slug>&_fields=modified,link` gives a page's change time. EPCOR's sitemap is `epcor.com/ca.sitemap.xml` (not read). The Acts download as PDFs: `kings-printer.alberta.ca/documents/Acts/P17.pdf` (Police), `E00P3.pdf` (Education), `m26.pdf` (MGA).
- **⚠️ EPCOR's number differs by publisher.** The City's 311 page lists EPCOR as 780-412-4000; EPCOR's own contact page gives 780-412-4500 (emergencies: power, water, drainage) and 310-4300 (customer service). Take each body's contact from its own page.
- **⚠️ The Commission's complaint page links albertaprc.ca through an Outlook safelink that embeds a staff email address.** Link to `albertaprc.ca` directly; never copy that href.
- **Not a source of record: `q7ua-agfg` 311 Requests.** It is routing data (service area, category, "Full Service"/"Referral"), not a statement of responsibility, and its licence reads "See Terms of Use". Useful only to see which issues residents bring: e.g. "Non Municipal Services" holds EPCOR Water, Land Titles and Henday categories.

### Not a source: Represent (Open North)
`represent.opennorth.ca` answers "who represents this point" for all three levels, but it is a third-party aggregator and sending it a location is the third-party geocoding the brief rules out without the owner's say-so. Listed so it is not rediscovered as a shortcut.
