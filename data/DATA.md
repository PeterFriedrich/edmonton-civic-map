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
- **Quirks:** no licence or terms of use are stated on the download page. The open.alberta.ca "electoral division" dataset describes the 2010 boundaries; do not use it.

### MLAs — Legislative Assembly of Alberta
- **Publisher / URL:** https://www.assembly.ab.ca/members/members-of-the-legislative-assembly → `https://www.assembly.ab.ca/txt/mla_home/contacts.csv`
- **Retrieved:** 2026-10-10
- **Rows / columns:** 91 lines. **Line 1 is a "Date file created" banner, not the header.** Columns then run: division number, division name, title, first, middle, last, caucus, office fields.
- **Quirks:** division number matches `EDNumber20` in the boundary file (27–46 are the Edmonton divisions), which is the join key. All 20 Edmonton seats are filled.

### Federal ridings — Elections Canada
- **Publisher / URL:** Elections Canada, https://open.canada.ca/data/en/dataset/18bf3ea7-1940-46ec-af52-9ba3f77ed708 → `https://www.elections.ca/res/cir/mapsCorner/edb/FederalElectoralDistricts_SHP.zip`
- **Retrieved:** 2026-10-10 — **publisher last-updated:** HTTP Last-Modified 2026-09-15; catalogue record modified 2026-09-17
- **Rows / columns:** 343; `ED_CF_NUM` (5-digit code, 48xxx in Alberta), `ED_NAMEE`, `CF_NOMF`
- **CRS:** EPSG:3347, NAD83 / Statistics Canada Lambert
- **Vintage:** 2023 Representation Order, first used at the general election of 2025-04-28. The current map.
- **Coverage of Edmonton, measured:** 9 "Edmonton" districts. All 298,238 parcel addresses fall in exactly one district; **5 fall in Sherwood Park—Fort Saskatchewan and 1 in Leduc—Wetaskiwin**. St. Albert—Sturgeon River and Parkland overlap the City's area by under 0.3 km² each with no addresses.
- **Quirks:** 10 MB zip for the whole country; clip to the Edmonton area before simplifying.

### MPs — House of Commons
- **Publisher / URL:** https://www.ourcommons.ca/Members/en/search?province=AB → CSV at `/Members/en/search/csv?province=AB`, XML at `/Members/en/search/xml?province=AB`
- **Retrieved:** 2026-10-10
- **Rows / columns:** 37 Alberta members; `Person ID`, `Honorific Title`, `First Name`, `Last Name`, `Constituency`, `Province / Territory`, `Political Affiliation`, `Start Date`, `End Date`
- **Quirks:** joins to the boundary file on constituency **name**, not code. `Start Date` contains a narrow no-break space (U+202F) before "a.m.". All 9 Edmonton seats are filled.

### Addresses — `ut27-nrpn`
- **Publisher / URL:** City of Edmonton, https://data.edmonton.ca/d/ut27-nrpn
- **Retrieved:** 2026-10-10 — **publisher last-updated:** 2026-10-05
- **Rows / columns:** 776,614 (298,238 `PARCEL`, 478,376 `SUITE`, all `status = OFFICIAL`); `sub_address`, `house_number`, `street_name`, `latitude`, `longitude`, `object_type`, `record_id`, `neighbourhood_number`, `neighbourhood_name`
- **Use:** the address layer for client-side geocoding. Suites share their parcel's ward, so the parcel rows are enough.
- **Size, measured:** 288,315 distinct house number + street pairs across 2,800 street names. As a compact JSON index (street → house number, lat, lon to 5 decimals) it is 8.4 MB, **2.2 MB gzipped**.
- **Quirks:**
  - **`record_id` is not unique within `PARCEL` rows** (298,238 rows, 298,154 distinct ids), so `$order=record_id` is not a stable paging order. Page on Socrata's `:id` and check the total against `count(*)`.
  - 2,474 house number + street pairs appear on more than one parcel row. Check whether duplicates ever straddle a boundary before collapsing them.
  - `street_name` is upper case with the quadrant suffix (`ALEXANDER CIRCLE NW`). No postal code.
  - A single 300,000-row CSV request stalled twice; 50,000-row pages return in about 9 s each.

### Not a source: Represent (Open North)
`represent.opennorth.ca` answers "who represents this point" for all three levels, but it is a third-party aggregator and sending it a location is the third-party geocoding the brief rules out without the owner's say-so. Listed so it is not rediscovered as a shortcut.
