# Session handoff — 2026-11-13 → 2026-11-14, S10: the first audit (address → district assignment)

## 0. Session Metadata
- **Model, by phase:**
  - Fable 5.2 (`claude-fable-5-2`), from the session's own context: the whole audit, which covered the evidence, the measurements, `docs/FINDINGS_district_assignment.md` and the close-out edits in PR #86.
  - Opus 5.5 (`claude-opus-5-5`): only this handoff. The model changed between the two; no review pass was run after the switch.
- **Effort:** `$CLAUDE_EFFORT` reads `medium` (checked at handoff).
- **Date / session #:** 2026-11-13 → 2026-11-14, S10. PR #86 (merged), this handoff's PR.
- The session ran out of usage once mid-write. The findings doc was pushed alone (5f39f6e), and the rest followed in the same PR (987fc35).

## 1. Goal
- **Project:** Edmonton Civic Map, a public lookup answering "who represents me, and who is responsible for what?" for any Edmonton address. Descriptive only.
- **This session:** run the `project-audit` skill on the district-assignment target, from the brief `docs/AUDIT_district_assignment.md`. Work top-down L0–L5, change no code, ship as one docs PR.

## 2. Current State
### ✅ Completed
- **PR #86, merged 2026-11-13** (0ae1598; 987fc35 confirmed on `origin/master` with `git merge-base --is-ancestor`).
  - `docs/FINDINGS_district_assignment.md`: verdicts, ranked fixes, "What this run got wrong".
  - `docs/AUDIT_LEDGER.md`: executed row; queued entry removed; never-audited item 1 struck with its re-audit triggers.
  - `docs/ASSUMPTIONS.md`: first rows, DA-1 to DA-8.
  - `TODO.md`: audit item closed and archived; follow-ups added.
  - `docs/DATA_ISSUES.md`: a NOT SENT row dated 2026-11-13.
  - `data/DATA.md`: "School wards" and "Provincial ridings" corrected.
  - `docs/CHANGE_PIPELINE.md`: the fit-table row for the assumptions index now reads "adopted".
- **Verdicts:**
  - No level is UNSOUND.
  - **SOUND:** L3 (assignment uses the unclipped full-resolution layers) and L5 (the browser gives the build's answer).
  - **CONDITIONAL:** L0, L1, L2 and L4:
    - **L0:** the 20 m note measures the site's own error, not disagreement between sources.
    - **L1:** the school-ward layers are not proven to be the bylaw lines, and the council bylaw is unread.
    - **L2:** no one has checked for parcels that lie across a district line.
    - **L4:** no guard compares a layer with its legal instrument or with the other publisher, and nothing compares `recheck_dates` with today.
- **Primary sources found** (URLs in `data/DATA.md` "School wards"):
  - ECSD Bylaw #2020-01 and EPSB Bylaw No. 2020-2. Both are written descriptions along road centre lines.
  - `data/DATA.md` said these bylaws were not online, which was wrong.
- **Addresses put in question by the bylaw text, as this run read it:**
  - Site and bylaw disagree: 15928 Manning Drive NW (the site says Catholic 72, the text says 73) and 610 Calgary Trail NW (the site says public I, the text says H).
  - Open: 17611 34 Street NW, 903 Gateway Boulevard NW, and 106 and 104 101 Street NW.
  - The reading is the run's own, against the City Road Network `9j8t-zm52`.

### ⚠️ In Progress
- Nothing is half-done in the repo. The open items are the owner's decisions and outside contacts in §4.
- **Template update not applied:** the session-start notice lists 15 files at `5b48600...49c205b`. The S9 branch `origin/template-a104a5f` is also still unopened.

### ❌ Blocking Issues
- None. `gh issue list --state open` returned nothing at handoff.

## 3. Technical Learnings
- **Tools that gave wrong answers in this run:**
  - `shapely` `line.project()` / `interpolate()` on a MultiLineString gives nonsense offsets. Use `shapely.ops.nearest_points`.
  - A horizontal-ray parity test against a road with paired carriageways and ramps flags addresses on the wrong side. It flagged 792 here. Instead, compare against the nearest point on each carriageway's centre line.
  - A WebSearch summary misdated Bill 32. Read the Assembly's bill status report (`assembly.ab.ca/LAO/Bills/bsr31-*.pdf`) instead.
- **The City's bylaw PDFs** (e.g. `C15142.pdf` on `edmonton.ca`) answered 404 and 502 to scripts. The council ward bylaw still needs reading by hand (TODO).
- **Socrata catalogue search:** use `data.edmonton.ca/api/catalog/v1?q=…&search_context=data.edmonton.ca`; `api.us.socrata.com` returned nothing.
- **The boards' own ward layers** are at `azimuth.epsb.ca/server/rest/services/Hosted/EPSB_Wards_2025/FeatureServer/264` and `…/FC_ECSD_Wards_2025/FeatureServer/227`. The public field is `epsb_ward2021_name` and the Catholic field is `name`. No licence is stated: compare against them, never publish them.
- **Instrument check:** counts of rows within 20 m of their own edge reproduce the published manifest. Use it to validate a new measurement script.
- **`recheck_dates`** (`site/public/data/staleness.json`) has three readers: `site/src/about.js`, `tests/test_diff_check.py` and `smoke/built-site.spec.js`. None compares a date with today.
- Pushing more than once to an open PR's branch is fine. Re-check `gh pr view --json state` before each push (#86 merged within minutes of the last push).

## 4. Next Steps (prioritized)
1. **Press Sync in the claude.ai Project** (#86 changed these):
   data/DATA.md
   docs/BRIEF.md
   S9's list also had `docs/SPEC_data_schema.md`. Tick it too if it was never synced.
2. **The school-ward question to both boards and Edmonton Elections.** It covers the six addresses above and asks which lines the 2025 vote used, quoting the bylaw text. Claude drafts it on asking and the owner sends it (TODO "School-ward boundaries used in the 2025 election"; `docs/DATA_ISSUES.md` 2026-11-13).
3. **Owner decisions** (TODO "Waiting on the owner" / "Build"):
   - A trigger for a past `recheck_dates` entry. It is a CI change.
   - Whether to plan the per-address "sources disagree" flag. It changes the data contract.
   - From S9: the blocked-`ca_mps` notice in `refresh.yml`.
4. **About page** (TODO "About page after the audit"):
   - Rewrite the "Provincial boundaries may change" paragraph in `site/about.html`.
   - Drop or update the passed 2026-11-02 entry in `recheck_dates`.
   - Add a known limit saying the school-ward lines are the City's drawing of the boards' bylaws.
   - It touches code, so run `/code-review` before the PR.
5. **Template update:** follow `docs/COPIER.md` §"When the session-start notice appears". Report fit to the owner before opening a PR.
6. **Later in TODO:** read the council ward bylaw by hand; provincial "which map applies"; parcel-straddle check; repeatable City-versus-board comparison (plan first); address churn around 2026-11-27.
7. **Next audit:** `docs/AUDIT_LEDGER.md` "Never audited" item 2, district → office holder. It needs a brief first.

## 5. Restoration Procedure
- `cd ~/edmonton-civic-map && git checkout master && git pull`; `gh issue list --state open`.
- Python: `.venv/bin/python -m pytest tests -q` (177 at this handoff). Doc guards: `scripts/check_doc_citations.py`, `scripts/check_assumptions.py` and `scripts/check_decisions_log.py --root .`.
- Site: `npm ci && npm run build && npm run check:dist`. For smoke, set `PLAYWRIGHT_BROWSERS_PATH` to a scratch folder, run `npx playwright install chromium`, then `npm run smoke`.
- The audit scratch folder is deleted. Re-running the measurements means re-fetching the boards' layers and the Road Network (§3).
