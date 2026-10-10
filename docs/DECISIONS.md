# Decisions Index

Append-only. **One ROW per locked decision** — when, what, why (including what
was rejected), and a pointer to where the argument lives in full. When a decision
locks, add a row; when one is superseded, strike it (`~~...~~`) or mark it
`SUPERSEDED <date>` in place and add the successor — don't delete history.

**What a row owes you:**

1. ⚠️ **EVERY ROW CARRIES A POINTER TO A DOC** — not only to code. Code moves;
   the argument has to live somewhere prose can hold it.
   `scripts/check_doc_citations.py` checks that every pointer resolves.
2. **The row is a self-contained summary** and may paraphrase the argument.
3. **The pointer is the authority.** When a row and its target disagree, the
   target wins and the row gets fixed.
4. **A row names the test that protects it**, or carries `[unverifiable]`.
   `scripts/check_decisions_log.py` enforces this on the merge gate (and that a
   superseded row is marked where it stands).

| When | Decision | Full reasoning |
|------|----------|----------------|
| 2026-10-09 | **Separate repo and deployment from `edmonton-tax-viz`.** At most a neutral link between the two at city or neighbourhood level, never per councillor. `[unverifiable]` | `docs/SPEC_civic_map.md` §2 |
| 2026-10-09 | **Descriptive only.** No rankings, alignment or voting-similarity scores, league tables or per-councillor evaluation; only what is on the public record, neutrally framed. `[unverifiable]` | `docs/SPEC_civic_map.md` §2, §7 |
| 2026-10-09 | **Roles and departments over individual staff.** Staff are named only where the City publishes them as public contacts; elected officials are fine. `[unverifiable]` | `docs/SPEC_civic_map.md` §2 |
| 2026-10-09 | **No address storage.** Geocoding and point-in-polygon run client-side or statelessly; addresses are never logged or persisted. A third-party geocoder needs the owner's decision first. `[unverifiable]` until there is an app to test | `docs/SPEC_civic_map.md` §2, §5 |
| 2026-10-09 | **Currency by design.** Every record carries `last_verified` and `source_url`, shown in the UI; refresh is scripted with a diff check that holds unexpected changes for review; stale records show a warning. `[unverifiable]` until the refresh exists | `docs/SPEC_civic_map.md` §6 |
| 2026-10-09 | **Primary sources only.** No news or wiki scraping as a source of record; news is context, not data. `[unverifiable]` | `docs/SPEC_civic_map.md` §4 |
| 2026-10-10 | **The name is "Edmonton Civic Map"**, chosen by the owner as the more common phrasing over the brief's working title "Edmonton Civic Atlas". Not "politics dashboard": council is formally non-partisan. `[unverifiable]` | `docs/SPEC_civic_map.md` "Amendments since the brief was written" |
