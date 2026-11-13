# AUDIT LEDGER — what has been audited, when, and what came back

One row per **executed audit run**. This is the coverage map the audit docs
don't give individually: briefs are reusable *instruments*, findings docs record
*one run's output*, and the `project-audit` skill deliberately picks ONE target
per session — so nothing else says what has and hasn't been looked at. This does.

Rules: add a row when an audit **executes** (not when a brief is written); every
row carries a **pointer to the findings doc**; verdicts are **point-in-time** — a
row says the target was audited *as of that date*, not that it's still clean
after later changes. Not part of any session's mandatory reading — open it to
scope an audit or to check what has already been covered. Audits are framed
top-down, fundamental decisions first.

## Executed audits

| Date | Target / scope | Instrument | Output | Verdict (one line) | Outstanding |
|------|----------------|------------|--------|--------------------|-------------|

## Queued — briefed, not yet run

- **Address → district assignment** (decision audit), `docs/AUDIT_district_assignment.md`, briefed 2026-11-13. Run it first; it is item 1 below.

## Never audited (candidates, roughly ranked)

Ranked by harm to the site's one answer, "who represents me?" (2026-11-13).

1. **Address → district assignment.** Is each layer the boundary the current holders were elected on? Is the parcel point the right unit? Is the 20 m near-edge note honest, given publisher disagreements of up to 361 m? Briefed, above.
2. **District → office holder.** `src/build_officeholders.py` and `officeholders.json`: joins on constituency name (MPs) and number (MLAs), cross-check sources and approved `data/name_variants.csv` entries, vacancies (2026-11-03), the kept-MP path on a 403 (2026-11-03), and whether `last_verified` (the retrieval date) means what the card says.
3. **What an unattended refresh can publish.** `data/diff_rules.json` severities, `scripts/check_refresh_diff.py`, "new addresses pass without review" (SPEC §9.6), and the two November carve-outs (vacancies, kept MP rows). List every path from a source change to the live site with no person in it.
4. **"An address never leaves the browser."** Per-street fetches show the host which street was looked up (hashing was rejected 2026-10-13). Also: share links, console and error output, and the "no outside requests" rule (`check:dist`, smoke).
5. **Source of record and currency.** Each `source_url` opens a page that shows the fact, the staleness thresholds (45 and 180 days) against how often each source really changes, licences and attribution (TODO "Exact attribution text").
6. Neighbourhood search and the lenses (lower: the answer comes from the address index).
