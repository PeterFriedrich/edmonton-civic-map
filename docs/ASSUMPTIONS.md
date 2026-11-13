# Assumptions index

One row per premise a published number rests on that no guard proves. Use it to
come back to an assumption, and read it before scoping an audit. **This is an
index, not an argument:** each row points at the place that holds the evidence,
and the reasoning stays there. A row copies no figures, so it can't drift from
its source. Only a rough size is kept here, for ranking.

How this differs from the other docs:
- `docs/DECISIONS.md` records *choices*. An `[unverifiable]` decision row is
  not a premise; add one here only if a published number rests on it.
- `docs/DATA_ISSUES.md` records *defects* in other people's data. One belongs
  here only once a number rests on working around it.
- `docs/AUDIT_LEDGER.md` records *what has been checked*.
- This index records *what we take as true without having proven it*.

Rules:
- **Add a row when a number starts depending on something unproven.** That
  includes a "looks like" or "probably" inference written in `data/DATA.md`.
- **Point at the machine-readable source when there is one** (a data file's
  field, a notebook row), not at prose that describes it. Prose about a field
  goes stale while the field moves.
- **Update a row in place when its status changes; never reuse an ID.** A row a
  test now proves becomes `VERIFIED`, naming the test. A premise found wrong
  gets a test before it gets a new status.
- **Keep the pointer live.** When the evidence moves, move the pointer.
- **Add a completeness test once the project keeps a register of its own** (a
  verified notebook's sized rows, a `confidence` field in a data file): it fails
  when a register entry has no row here. The template can't write it, because
  every project's registers differ.

Status values:
- `VERIFIED`: a guard proves it; the row names the test.
- `SUPPORTED`: the evidence agrees, but doesn't cover every year or member the
  row applies to.
- `UNVERIFIED`: taken on trust.
- `ACCEPTED`: known to be off by a measured amount, and used anyway by decision.

`scripts/check_assumptions.py` fails on an unknown status, a VERIFIED row with
no existing test, a row other than VERIFIED with no size, a row with no evidence,
or a repeated ID. `scripts/check_doc_citations.py` checks the `.md` pointers.
Extra columns (`Build`, `Lens`) and several tables are fine: columns are found
by header name, and any table with a `Status` column is part of the index.

| ID | Assumption | Status | If wrong (rough size) | Evidence and test |
|----|------------|--------|-----------------------|-------------------|
| DA-1 | The City's school-ward layers (`d7pj-rist`, `pwzf-sjj2`) draw the lines each board's ward bylaw describes. | UNVERIFIED | A handful of addresses show the other ward's trustee; six are known, and most of each line has not been read against the text | `docs/FINDINGS_district_assignment.md` L1; `docs/DATA_ISSUES.md` 2026-11-13 |
| DA-2 | The returning officer used the City's school-ward layers for the 2025 vote. | UNVERIFIED | The same handful of addresses as DA-1 | `data/DATA.md`, "School wards" (an inference there) |
| DA-3 | The outer edge of the council wards (`b4er-5rp2`) is the city limit. It decides "inside Edmonton" and clips the provincial and federal outlines. | UNVERIFIED | No address today; hundreds sit within the distance the edge last moved | `docs/DATA_ISSUES.md` 2026-10-21; `docs/FINDINGS_district_assignment.md` L1, L3 |
| DA-4 | The Government of Alberta's "Current 2019" divisions are the map sitting MLAs represent until the next general election. | SUPPORTED | Every provincial card | `data/DATA.md`, "Provincial ridings"; `docs/FINDINGS_district_assignment.md` L1 |
| DA-5 | The 2023 Representation Order layer is the map sitting MPs were elected on. | SUPPORTED | Every federal card | `docs/FINDINGS_district_assignment.md` L1 (Elections Canada's statement) |
| DA-6 | The parcel point stands for the whole address: no parcel lies across a district line with its point on one side. | UNVERIFIED | Unknown; likely a small number of large parcels | `docs/FINDINGS_district_assignment.md` L2 |
| DA-7 | A person acts on each `recheck_dates` entry in `site/public/data/staleness.json` when it passes. Nothing compares a date with today. | UNVERIFIED | Missed once, leaving a stale paragraph on the About page; a missed new map would touch every card at that level | `docs/FINDINGS_district_assignment.md` L4 |
| DA-8 | The `effective_from` dates typed in `src/build_boundaries.py` for the provincial and federal layers are right and stay right. | SUPPORTED | A published date only; no district answer | `docs/FINDINGS_district_assignment.md` L4 |
