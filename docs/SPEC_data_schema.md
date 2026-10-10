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
- A calendar file lists the dates that force a full recheck regardless of
  thresholds: municipal election 2029-10, the Alberta committee report due
  2026-11-02, the next provincial and federal general elections.

## 7. Points put to the owner

1. **Party or caucus — proposed 2026-10-10, awaiting confirmation.** Each
   office holder is shown as a card, and affiliation is one plain field on it,
   shown **only where the body's own member list publishes one**: the Assembly
   list for MLAs and the House of Commons list for MPs. Council and trustee
   cards have no such field, because the City's and the boards' lists of who
   holds office carry none. The field is labelled with its source like every
   other. `officeholders.json` gains `affiliation` (string or null) and
   `affiliation_source_id`. This supersedes "No party or caucus field" in §4.
2. **Where the published files live — decided 2026-10-10, for now:** committed
   under `site/data/`, so every change to who represents whom is a reviewable
   diff in git history.
3. **Thresholds — decided 2026-10-10:** office holders 45 days, boundaries and
   population 180 days (§6).
4. **Trustee rows — direction from the owner 2026-10-10: scrape, with an
   agent confirming.** See §8.

## 8. Who confirms a change (proposed 2026-10-10)

The owner's direction: scrapers run on a schedule on the Oracle server, and an
always-on agent session there confirms what they find, so no source needs
hand-keeping and no agent time is spent when nothing changed.

- **The script does the routine work and costs no agent time.** A scheduled
  job fetches every source, rebuilds, and runs the diff check (§5). If nothing
  moved it advances `last_verified` and exits. This is the usual case.
- **An agent is woken only when the job exits non-zero**: a "review" or "stop"
  row in §5, or a scraper that no longer finds what it expects. The job hands
  it the diff report, not the raw pages.
- **The agent confirms against the primary source, then opens a PR.** It reads
  the page the scraper read, checks the change against the second source where
  one exists, and writes what it checked into the PR. It does not merge.
- **The owner's merge is the publish step.** Brief §6 asks for human review of
  unexpected changes; the agent prepares that review, it does not replace it.
- **A broken scraper is a finding, not a retry loop.** One attempt to confirm,
  then a GitHub issue. No repeated wake-ups on the same failure.
- **Which session, and how it is scheduled, is the `server` session's call**:
  it owns cron and is always on. This repo owns the scraper, the diff check and
  the report format it hands over.

Open: the cadence. Proposed weekly, which keeps every record well inside the
45-day threshold and survives a few failed runs.
