# TODO

The source of truth for what's left. Read first every session; update in place.

**Format contract** (`tools/todo_archive.py` depends on it): top-level items are
`- [ ]` / `- [x]` lines directly under `## Open work`; `###` sub-headings may
group them; closed items are moved to `docs/TODO_archive.md` by the tool, which
leaves a one-line stub under `## Done`. An open item can be stale — reproduce the
symptom and re-measure the stated cause before acting on it.

## Open work

### Waiting on the owner

- [ ] **Schema points still open** (`docs/SPEC_data_schema.md`): confirm affiliation as a card field for MLAs and MPs only (§7 point 1), and the agent-confirmed refresh in §8 with its weekly cadence. No downloader or UI before these close.
- [ ] **Answer brief §9 questions 2–4** (`docs/SPEC_civic_map.md`): static site or small backend, Tier 2 authorship, launch scope.
- [ ] **Report data defects to the City.** The owner will send one report later, collecting what `docs/DATA_ISSUES.md` holds by then (2026-10-10). Done when each row there has a status other than NOT SENT.

### Sources still to verify

- [ ] **Licence for the Elections Alberta boundary shapefile.** None is stated on the download page (`data/DATA.md`, "Provincial ridings"). Done when a written licence or permission is recorded there; until then the provincial layer cannot ship.
- [ ] **Exact attribution text for the Open Government Licence – Edmonton**, and Statistics Canada's for the ward populations. Done when `data/DATA.md` quotes both.
- [ ] **Post-2025-election ward boundary report (Policy C469A).** Not found; the City's ward-boundary-review page returned 404 on 2026-10-10. Done when the report's status and any proposed adjustments are recorded in `data/DATA.md`.
- [ ] **A ward population newer than the 2021 Census**, from a primary source. Done when found, or when recorded as not existing.
- [ ] **School-ward boundaries used in the 2025 election** — confirm against each board's ward bylaw that they match the City layers.
- [ ] **Recheck the provincial boundary process after 2026-11-02**, when the Select Special Committee on Electoral Boundaries must report. Done when `data/DATA.md` records what was tabled and whether anything is enacted.

### Build (after the schema is approved)

- [ ] **Downloaders, one per source in `data/DATA.md`**, each checking its row count and writing a `sources.json` entry.
- [ ] **Boundary build**: reproject, clip provincial and federal layers to the city, simplify at the recorded tolerance, with a test that no parcel address changes district against full resolution.
- [ ] **Diff check and staleness guard** per `docs/SPEC_data_schema.md` §5–§6.
- [ ] **Ask the `server` session to schedule the refresh** once the diff check exists: the job, its cadence, and which session is woken on a non-zero exit (`docs/SPEC_data_schema.md` §8).
- [ ] **Replace the template `README.md`** with one for this project.

## Done

- [x] 2026-10-10 — Brief §10 tasks 1–4: sources located and verified (`data/DATA.md`), point-in-polygon prototype measured (`prototype/README.md`), schema drafted (`docs/SPEC_data_schema.md`).
