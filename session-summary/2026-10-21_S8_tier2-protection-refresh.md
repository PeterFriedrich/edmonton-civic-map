# Session handoff — 2026-10-21, S8: Tier 2 survey, alpha banner, branch protection, held refresh

## 0. Session Metadata
- **Model:** Opus 5.5 (`claude-opus-5-5`), from the session's own context. No `/model` switch.
- **Effort:** `$CLAUDE_EFFORT` reads `medium` (checked at handoff).
- **Date / session #:** 2026-10-17 → 2026-10-21, S8. One session, compacted once. PRs #67–#75, all merged.

## 1. Goal
- **Project:** Edmonton Civic Map, a public lookup answering "who represents me, and who is responsible for what?" for any Edmonton address. Descriptive only.
- **This session:** the Tier 2 survey; an alpha banner; smoke tests on PRs; the template update to 5b48600; branch protection on `master`; publishing the refresh held in #69; starting the `/code-review` trial.

## 2. Current State
### ✅ Completed
- **#67** Tier 2 survey: `data/DATA.md` §"Tier 2 sources — who is responsible, and how to engage" places each of 8 issues on the rung ladder with its source. TODO item closed.
- **#68** "Alpha build: work in progress" banner on `site/index.html` and `site/about.html` (`.alpha-banner` in `site/src/app.css`; index body is `body.app` so the desktop layout still fills the height).
- **#70, #72** `tests.yml` runs `npm ci`, playwright chromium, `test:js`, build, `check:dist`, smoke on every PR (#72 removed a duplicate `check:dist`).
- **#71** template 5b48600 pulled: `docs/CHANGE_PIPELINE.md` (fit table answered), `docs/ASSUMPTIONS.md` (empty), `scripts/check_assumptions.py` in `tests.yml`.
- **#73** `refresh.yml` checks out with `secrets.HEARTBEAT_TOKEN` (fails if empty), drops `actions: write` and the `gh workflow run pages.yml` step: the PAT push itself starts `pages.yml`.
- **Branch protection on `master`, 2026-10-21** (owner said go): required check `test`, strict false, `enforce_admins` false, no force push or deletion. Verified with `gh api .../branches/master/protection`.
- **#74** published the held 2026-10-19 refresh (closed #69): the City republished `b4er-5rp2` and only the outer city edge moved (four wards, ≤80 m; outline 783.02 → 782.78 km²). The new edge departs from `qqvh-dp5m` and both school layers; logged in `docs/DATA_ISSUES.md` (NOT SENT). `pages.yml` deployed it (run 39551627729).
- **#75** `/code-review` trial started: before a PR whose diff touches code, run `/code-review` at the levels in `docs/CHANGE_PIPELINE.md` step 1.7; every PR description opens with a `Code review:` line.

### ⚠️ In Progress
- **The token push past protection is unproven.** Two refresh dispatches after #74 (runs 39643689274, 39644394951) failed before the push: ourcommons.ca returned HTTP 403 for `ca_mps` to the runner (200 from this server the same hour). Issue #76 open. TODO "Build" has the item. The `template` session was told and is waiting for the run ID.
- **Template update 5b48600 → a104a5f** (12 files incl. `scripts/check_fit_table.py`) not yet evaluated; next in this session.

### ❌ Blocking Issues
- `ca_mps` 403 from GitHub runners, above. Log line: `ERROR download ca_mps: FAILED: HTTP 403 from https://www.ourcommons.ca/Members/en/search/csv?province=AB`.

## 3. Technical Learnings
- A same-UTC-day refresh can commit nothing: `last_verified` is `retrieved_at[:10]`, so it proves nothing about the push path. Test the push on a later day than the last publish.
- A successful refresh does not close its `refresh` issue; close it by hand (or by the PR that publishes a held change).
- `docs/BRIEF.md` must be regenerated (`python scripts/make_brief.py --write`) after any TODO or DECISIONS edit, or `test_brief` fails.
- One smoke flake seen on #74 (share-link test failed once, passed three reruns); error not captured. If it recurs, capture it.
- System curl fails TLS here; use `.venv/bin/python` with certifi and the project User-Agent.

## 4. Next Steps (prioritized)
1. **Press Sync in the claude.ai Project:**
   docs/BRIEF.md
   docs/SPEC_data_schema.md
   data/DATA.md
2. Evaluate template a104a5f per `docs/COPIER.md` §"When the session-start notice appears"; report fit to the owner before applying.
3. After the Monday 2026-10-26 refresh: confirm the push, one `pages.yml` run, close #76; send `template` the run ID. If 403 persists, propose a fix (TODO item).
4. Backlog: first `docs/ASSUMPTIONS.md` rows; Tier 2 first entry (property tax, needs a format proposal); Anthony Henday provincial source; send the NOT SENT `docs/DATA_ISSUES.md` rows; league-boundary request.

## 5. Restoration Procedure
- `cd ~/edmonton-civic-map && git checkout master && git pull`; `gh issue list --state open`.
- Python: `.venv/bin/python -m pytest tests -q`. Site: `npm ci && npm run build && npm run check:dist && npm run smoke` (set `PLAYWRIGHT_BROWSERS_PATH` to a scratch folder).

---

# Addendum — 2026-10-21 → 2026-10-30, S8 continued (same session)

## 0. Session Metadata
- **Model:** Opus 5.5 (`claude-opus-5-5`), no `/model` switch. **Effort:** `$CLAUDE_EFFORT` reads `medium` (checked at this addendum).

## 2. Current State
### ✅ Completed since the handoff above
- #77 (the handoff above, S5 archived, TODO item for #76) merged.
- Answered `server`'s prompt-injection survey: untrusted inputs, command shapes, secrets (only `HEARTBEAT_TOKEN`, an Actions secret; no `.env`, no API keys), the domain allow-list, workflow exposure. No changes made; `server` owns any settings change.

### ⚠️ In Progress
- **Template update, branch `template-a104a5f` (commit 0907fb2), pushed, NO PR yet — waiting on the owner's go.** `copier update` brought `_commit` to d710841. Takes everything, declines nothing:
  - `scripts/check_fit_table.py` (+ test) in `tests.yml` and `bootstrap.sh`. The `tests.yml` conflict was resolved by keeping both: the fit-table step goes before the site steps, and the stale "master has no required checks" comment was corrected. Broke it on purpose: a wiped answer with `--base origin/master` fails, exit 9.
  - `docs/CHANGE_PIPELINE.md`: new steps (`Risk:`/`Tested:`/`Undo:`/`Cause:` lines, pre-existing findings → TODO, fix a repeated finding at the source, `/security-review` on risky paths, announce a push after the owner looked, scheduled-job checklist in 4.4). Fit table merged: earlier answers kept, 9 new rows answered (Risk paths: high = `.github/workflows/`, `src/`, `data/diff_rules.json`, `site/public/data/`, `docs/SPEC_data_schema.md`; security-review extra paths `src/download.py`, `site/src/` address/fetched-text code; "fixes after a merge counted" = later, before the code-review trial is judged). "Break each guard" row now adopted.
  - `scripts/handoff_gap.py` hooks-off reminder, `template_drift.py`, project-audit skill, `docs/COPIER.md`.
  - pytest 182 passed; every `scripts/check_*.py` ok except `check_refresh_diff.py` (refresh-only, expected).
  - The branch predates #77, so rebase onto `origin/master` before opening the PR (expect a `docs/BRIEF.md` regen).
- **Refresh still failing, #76 open.** Monday 2026-10-26 scheduled run 40358145775 failed in "Download every source": this time the CSV passed and the liveness fetch of `landing_url` (`https://www.ourcommons.ca/Members/en/search?province=AB`, `src/download.py` ~line 331) got 403. Both URLs return 200 from this server. So ourcommons.ca intermittently 403s GitHub runner IPs; 3 of 5 runs since 10-16 hit it. Token push past protection is still unproven; `template` is waiting for a run ID.
- **Fix proposed to the owner, no answer yet** (plan-first: changes fail-closed `src/download.py`): on a 403 from `ca_mps`, retry once or twice with a pause; if it still fails, keep last week's MP data for that one source with its old `last_verified` (the page's staleness warning covers it). Every other failure still stops the run. Alternatives offered: retry only; run the refresh on this server (moves the token onto the box).

### ❌ Blocking Issues
- `ERROR download ca_mps: FAILED: HTTP 403 from https://www.ourcommons.ca/Members/en/search?province=AB` (run 40358145775); 2026-10-21 runs failed on `.../search/csv?province=AB`.

## 3. Technical Learnings
- `_get` in `src/download.py` retries only `TRANSIENT_HTTP` codes; 403 fails at once. Page-kind sources also fetch `landing_url` as a liveness check, so `ca_mps` makes two requests to ourcommons.ca per run.

## 4. Next Steps (prioritized)
1. Get the owner's answers: (a) open the template PR from `template-a104a5f` (rebase first); (b) which `ca_mps` fix. Then build it, with a `Risk: high (src/download.py)` description and `/code-review medium` + `/security-review`.
2. After a refresh passes: confirm the HEARTBEAT_TOKEN push landed on master and `pages.yml` ran once; close #76 by hand; SendMessage the run ID to `template`.
3. Backlog unchanged from §4 above.
