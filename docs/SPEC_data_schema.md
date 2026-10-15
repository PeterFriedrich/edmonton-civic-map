# SPEC — data schema and source ledger (DRAFT, not approved)

**Read when:** writing any downloader, the refresh, or anything that reads the
published data files.

**Status: proposal, 2026-10-10.** Brief §10 task 4 (`docs/SPEC_civic_map.md`).
Nothing here is built. It becomes a contract when the owner approves it; a row
goes in `docs/DECISIONS.md` then.

## 1. What the schema has to guarantee

From brief §6: every record shown carries where it came from and when it was
last checked; a refresh never publishes a change nobody looked at; a stale
record is visibly stale.

Three kinds of thing are published, and they change on different clocks:

| Kind | Changes when | File |
|---|---|---|
| Sources | a publisher moves or re-issues a file | `sources.json` |
| Districts (boundaries) | a redistribution or boundary review | `layers.json` + one GeoJSON per layer |
| Office holders | an election, by-election, resignation, death | `officeholders.json` |

Keeping them apart is the point: a by-election changes one office-holder row
and must not touch a boundary file, and the diff check can then say exactly
which kind of thing moved.

## 2. `sources.json` — the machine-readable source ledger

`data/DATA.md` is the prose ledger (quirks, what was verified). This file is
what the build and the UI read. One entry per fetched resource.

```json
{
  "id": "coe_wards",
  "publisher": "City of Edmonton",
  "title": "City of Edmonton Ward Boundary and Council Composition_Current",
  "landing_url": "https://data.edmonton.ca/d/b4er-5rp2",
  "fetch_url": "https://data.edmonton.ca/resource/b4er-5rp2.geojson",
  "licence": "Open Government Licence – Edmonton",
  "attribution": "<exact statement the licence requires>",
  "retrieved_at": "2026-10-10T05:41:00Z",
  "publisher_updated_at": "2026-10-05",
  "sha256": "<of the bytes fetched>",
  "row_count": 12,
  "expected_row_count": 12
}
```

- `sha256` is what lets the refresh say "unchanged" without comparing geometry.
- `row_count` is measured from the file, and checked against the server's own
  count for Socrata sources (`data/DATA.md`, "Download completeness").
- `expected_row_count` is the guard: 12 wards, 9 and 7 school wards, 87
  provincial divisions, 343 federal districts, 13 council contacts. A mismatch
  stops the refresh.

## 3. `layers.json` and the boundary files

```json
{
  "id": "council_ward",
  "label": "City Council ward",
  "body": "edmonton_council",
  "source_id": "coe_wards",
  "effective_from": "2021-10-18",
  "effective_to": null,
  "simplification_tolerance_m": 5,
  "near_boundary_m": 20,
  "feature_count": 12,
  "last_verified": "2026-10-10",
  "file": "boundaries/council_ward.geojson"
}
```

Layers: `council_ward`, `public_school_ward`, `catholic_school_ward`,
`provincial_riding`, `federal_riding`.

Each feature carries only `district_id` and `name`. Everything else joins by
`district_id`, so a boundary file holds no names of people.

- `district_id` is ours and stable: `council_ward:papastew`,
  `public_school_ward:C`, `catholic_school_ward:73`, `provincial_riding:44`
  (Elections Alberta's division number), `federal_riding:48022` (Elections
  Canada's code). Ward names are normalised to make the id; the display name
  keeps its diacritics.
- `effective_from` / `effective_to` exist because the provincial map is about
  to change (`data/DATA.md`, "Provincial ridings"). An enacted future map is a
  second layer entry with a future `effective_from`; the lookup uses the layer
  in force today.
- `simplification_tolerance_m` and `near_boundary_m` are published, not just
  used, so the methodology page and the near-boundary note quote the real
  values (brief §5). Measured basis: `prototype/README.md`.
- **Provincial and federal layers are clipped to the Edmonton area, not
  filtered by name.** Seven City addresses sit in ridings not named
  "Edmonton" (measured, `data/DATA.md`). Proposed rule: keep every riding that
  intersects the City boundary, so a map click anywhere in the city resolves.
- **Ward population** hangs off the district, not the layer:

```json
{ "district_id": "council_ward:papastew", "population": 71675,
  "population_year": 2021, "population_source_id": "coe_census_2021" }
```

  The year is shown wherever the number is.

## 4. `officeholders.json`

One row per **seat**, including a vacant one.

```json
{
  "seat_id": "council_ward:papastew",
  "body": "edmonton_council",
  "role": "Councillor",
  "district_id": "council_ward:papastew",
  "name": "Michael Janz",
  "vacant": false,
  "contact_url": "https://www.edmonton.ca/city_government/city_organization/ward-papastew",
  "source_id": "coe_wards",
  "source_url": "https://data.edmonton.ca/d/b4er-5rp2",
  "cross_check": { "source_id": "coe_council_contacts", "agrees": true },
  "last_verified": "2026-10-10"
}
```

- The mayor's row has `district_id: null` and `seat_id: "edmonton_council:mayor"`.
- `vacant: true` with `name: null` is a valid, publishable state. A seat that
  disappears from a source is a diff-check failure, never a silent drop.
- `contact_url` is always the official page for the office, not a personal
  site or social account. No email, phone or staff names are stored: the
  official page carries them and stays current without us (brief §2 item 3).
- `cross_check` records the second primary source and whether it agreed on the
  refresh that set `last_verified`. Where two sources disagree the refresh
  stops and a person decides.
- `last_verified` is the date a refresh last confirmed this row against its
  source. It is **not** the date the source was last modified, and it does not
  move if the fetch failed.
- **Affiliation:** see §7 point 1.

Source and cross-check per body:

| Body | Seats | Source of record | Cross-check |
|---|---|---|---|
| Edmonton City Council | 13 | ward layer `b4er-5rp2` (councillors); contacts `e9qt-cc3j` (mayor) | contacts `e9qt-cc3j` |
| Edmonton Public Schools | 9 | board trustee page | 2025 official results, until the first mid-term change |
| Edmonton Catholic Schools | 7 | board trustee page | 2025 official results, until the first mid-term change |
| Legislative Assembly of Alberta | those in the clipped layer | Assembly `contacts.csv` | none found yet |
| House of Commons | those in the clipped layer | House of Commons CSV export | none found yet |

Election results are a cross-check only while nobody has left office. After a
resignation or by-election they are expected to disagree, and that seat's
cross-check falls back to none.

## 5. The diff check

The refresh fetches, rebuilds into a scratch directory, and compares against
what is committed. It exits non-zero and writes a report when any of these
moved:

| Change | Severity |
|---|---|
| a seat's `name` or `vacant` changed | review |
| a seat appeared or disappeared | stop |
| source and cross-check disagree | stop |
| a layer's `feature_count` differs from `expected_row_count` | stop |
| a district's geometry moved (symmetric difference above a small area threshold) | review |
| a `district_id` or `name` changed | review |
| a source's `landing_url` or `fetch_url` stopped resolving | stop |
| the `Future` rows of the City history layers are no longer empty | review |
| a population figure changed | review |

"Review" means the new files are produced but not published until a person
approves the report. "Stop" means nothing is produced. If nothing moved, only
`last_verified` and `retrieved_at` advance.

## 6. Staleness

- Each kind has a threshold in `layers.json` / a config block, not in code.
  Proposed: **office holders 45 days, boundaries and population 180 days.**
- The UI compares `last_verified` with today in the browser and shows the
  warning itself, so a site nobody has rebuilt still tells the truth.
- The threshold measures when we last checked the source, not how old the
  data is. The 2021 Census population passes for as long as it is rechecked
  within 180 days; its census year has to be shown beside the figure, and the
  schema has no field for that yet.
- A calendar file lists the dates that force a full recheck regardless of
  thresholds: municipal election 2029-10, the Alberta committee report due
  2026-11-02, the next provincial and federal general elections.

## 7. Points put to the owner

1. **Party or caucus — decided 2026-10-10.** Each office holder is shown as a
   card. Affiliation is a field on MLA and MP cards only, taken from the
   Assembly's and the House of Commons' own member lists and labelled with
   that source. Council and trustee cards have no such field, because the
   City's and the boards' lists of who holds office carry none.
   **It is off by default**: an opt-in "lens" the reader turns on, since people
   will look for it anyway but the tool should not lead with it.
   `officeholders.json` gains `affiliation` (string or null) and
   `affiliation_source_id`; the data is always published, the lens only
   controls display. Not decided: whether the lens does anything beyond the
   card text, such as colouring the map. Until that is asked for, it does not.
2. **Where the published files live — decided 2026-10-10, for now:** committed
   under `site/data/`, so every change to who represents whom is a reviewable
   diff in git history.
3. **Thresholds — decided 2026-10-10:** office holders 45 days, boundaries and
   population 180 days (§6).
4. **Trustee rows — decided 2026-10-10: scraped like every other source**, not
   hand-kept. See §8.

## 8. How the refresh runs and who confirms a change (decided 2026-10-10)

Settled with the owner after asking the `server` session (scheduling, fetch
etiquette) and the `edmonton-tax-viz` session (what its refresh does today).

**It runs on GitHub Actions, weekly**, not on server cron: the run can deploy
in the same job, a failed run emails the owner, and it does not depend on the
Oracle server or its CA bundle.

**The split:**

- **Nothing changed — fully automatic.** The run fetches every source,
  rebuilds, and runs the diff check (§5). If nothing moved it advances
  `last_verified`, commits to master and deploys. No issue, no PR, nobody
  acts. This is nearly every run.
- **Something changed — held.** A "review" or "stop" row in §5, or a scraper
  that no longer finds what it expects, publishes nothing: the site keeps
  serving the last good data and the run files a GitHub issue with the trimmed
  diff report. This project's session picks the issue up at its next start
  (`CLAUDE.md`, "Session Management"), checks the change against the primary
  source and the second source where one exists, and opens a PR saying what it
  checked. **The owner's merge is the publish step** (brief §6).

Changes are held rather than published-then-reported because a wrong name on a
"who represents me" tool is worse than a late one. `edmonton-tax-viz`
publishes automatically, and one green run there shipped a doubled figure
that was live for four days.

**Rules that follow:**

- **No "all fine" issues.** An issue means a change or a break. The heartbeat
  is `last_verified` itself: the site's staleness warning (§6) shows a dead
  schedule, an expired token or a broken workflow without anyone watching.
- **A held change shows as stale, not as wrong.** Until the PR merges, the
  affected records stop advancing `last_verified` and age toward the warning.
- **Nothing scraped is ever typed into a live session.** The issue body is
  data for a session to check, not instructions.
- **One run, no retry loop.** A scraper fails closed on any non-200 response
  or a parse that finds zero rows, so a broken scraper can never look like
  "everyone left office".
- **Fetching:** requests one at a time, 1–2 s apart; a User-Agent naming the
  project and its GitHub URL; robots.txt honoured; conditional GETs where a
  site supports them.
- **A warning inside a green run reaches nobody.** Anything that matters is an
  issue or a red run.
- GitHub disables scheduled workflows after 60 days without repository
  activity; the weekly `last_verified` commit keeps this one alive.

**A dial, not a fixed line.** Which §5 rows hold and which pass is a config
list, so the amount of checking can be traded against effort later. A possible
later step, the owner's call: an unattended agent run that opens the PR itself
when an issue is filed.

## 9. The address index: districts worked out per address at build time (PROPOSED 2026-10-15)

**Status: proposal, waiting on the owner (§9.6).** `TODO.md` "Build";
recommended by the stack report (`docs/SPEC_lenses.md` §8). Measured on
2026-10-15 with `prototype/address_districts.py`; numbers in
`prototype/README.md` "Districts per address".

### 9.1 What changes

Today's plan (brief §5): the browser geocodes an address against a local
address list, then runs point-in-polygon against the five boundary files. The
proposal moves the point-in-polygon to the build. For every City parcel
address the build works out all five districts at **full resolution** and
writes them into the per-street address index. Typing an address then needs
one small file and no geometry and no map: the lookup and cards work before
the map loads, and without it (`docs/SPEC_lenses.md` §5, keyboard and screen
reader rule). Point-in-polygon in the browser stays, for map clicks only.

### 9.2 The files

All under `site/data/addresses/`, committed like the other published files
(§7 point 2):

- `streets.json`: the 2,800 street names, sorted, each with its file name
  (`"124 STREET NW"` → `124-street-nw.json`). 11 kB gzipped; loads with the
  page.
- `<street>.json`, one per street: house number → list of records.

  ```json
  { "10024": [[53.54053, -113.53362, "council_ward:odaymin", "public_school_ward:D",
               "catholic_school_ward:75", "provincial_riding:29", "federal_riding:48015", 0],
              [53.54112, -113.5365, "council_ward:odaymin", "public_school_ward:D",
               "catholic_school_ward:75", "provincial_riding:32", "federal_riding:48015", 3]] }
  ```

  (10024 124 Street NW, one of the eight split addresses in §9.3. The second
  record's `3` means within 20 m of a council ward edge and a public school
  ward edge.)

  A record is a point (latitude, longitude, 5 decimals), the five
  `district_id`s in the order of `layers.json`, and a near-edge bitmask: bit
  *n* set means the parcel point is within `near_boundary_m` (20 m) of an edge
  of layer *n*. Nearly every address has one record. There is more than one
  only when the address's parcel rows fall in different districts (§9.3).
  The point is a real address point: the row nearest the group's centre, not
  a computed one.
- `manifest.txt`, the readable diff, as for the tile files: the source ids
  with their `sha256` and retrieval dates, parcel rows in and records out,
  addresses per district per layer, the near-edge counts, every split address
  (§9.3) written out, and one hash over all street files.

**Measured size:** 288,534 records in 2,800 files, **2.33 MB gzipped in all**.
The median street file is 0.4 kB and the largest is 8.7 kB (80 Avenue NW), so
a lookup costs about the street list plus one file. Splitting per street was
already decided (DECISIONS 2026-10-13).

The provincial column is the map in force today (§3 `effective_from`). When a
new provincial map is enacted, the index gains a column for it with its own
`effective_from`, so the card can show "from the next election" beside the
current riding.

### 9.3 Addresses on more than one parcel row

298,453 `PARCEL` rows give 288,526 distinct house number + street pairs. 2,477
pairs sit on more than one row: 9,927 rows beyond the first. The largest is
1025 Secord Promenade NW with 141 rows. The rows of one pair lie a median 22 m
apart, and 26 pairs spread over 500 m (up to 3.0 km, 6015 129 Avenue NW).

- **2,469 pairs agree on all five layers.** They become one record.
- **8 pairs have rows in different districts.** Each distinct set of
  districts is kept as its own record, and the card says the address covers
  parcels in more than one district and shows each. **Never pick one.** Six
  differ in one layer, two in two:

  | Address | Rows | Layers that differ |
  |---|---|---|
  | 10024 124 Street NW | 2 | provincial (29, 32) |
  | 6015 129 Avenue NW | 2 | provincial (35, 27) |
  | 8132 133 Street NW | 2 | council (sipiwiyiniwak, Nakota Isga) |
  | 3705 141 Street SW | 104 | federal (94 rows in 48016, 10 in 48020) |
  | 1650 Hector Road NW | 2 | public school (F, H) |
  | 12030 River Valley Road NW | 6 | council, public school, provincial |
  | 12702 St Albert Trail NW | 2 | public school (C, A) |
  | 19751 Whitemud Drive NW | 2 | provincial (36, 43) |

No parcel row is dropped: every row lands in exactly one record, and the
build counts rows in against rows accounted for.

`SUITE` rows (478,376) are not indexed. The lookup is by house number and
street, and a suite shares its parcel's.

### 9.4 How the diff check covers it

The index is derived from two inputs, addresses and boundaries, so a change
in it is either one of them moving. New rows for the §5 table:

| Change | Severity |
|---|---|
| parcel rows in ≠ rows accounted for in the index | stop |
| an address in no district, or in more than one, on any layer | stop |
| parcel row count moved more than 1% since the last run | stop |
| an existing address changed district **while no boundary moved** | review |
| the list of split addresses (§9.3) changed | review |
| addresses added or removed, under the 1% line | **pass**, counts in the run log (§9.6 point 2) |

An address that changed district because a boundary moved needs no row of its
own: the boundary change already holds the run, and the report lists how many
addresses moved, per district.

### 9.5 Tests

1. **Every stored district matches full resolution, by a second method.** The
   build uses shapely (GEOS). The check re-derives every parcel row with
   `prototype/pip.js` (ray casting, run under node) against the
   full-resolution source layers, and requires every row to match.
   It needs the downloaded sources, so it runs in the build and the refresh,
   not in the unit tests.
2. **A click on the address agrees with typing it.** Every record's point,
   run through `pip.js` against the **published, simplified** boundary files,
   must give the stored districts. Zero mismatches; a failure means the
   tolerance comes down, not that the test loosens. This is also the test the
   "Boundary build" item in `TODO.md` calls for.
3. **No silent drops.** Rows in = rows accounted for; every split address is
   in the manifest.
4. **Shape.** A unit test over the committed files: every record has five
   `district_id`s that exist in `layers.json`, and every street in
   `streets.json` has its file and no file is unlisted.

### 9.6 Points for the owner

1. **Split addresses: show every district set, with a note** (recommended),
   rather than choosing one row.
2. **New addresses pass without review** (recommended). The City adds
   addresses most weeks; each is placed by the same tested code, and the run
   log counts them. The alternative holds every week's refresh for a person.
3. **Near-edge note per layer** (recommended): the card says "near the ward
   edge" for that layer only. 1,342 addresses are within 20 m of an edge on
   at least one layer. The alternative is one flag for all five.
4. **The new module is `src/build_address_index.py`**, run after the
   boundary build and before the diff check.
