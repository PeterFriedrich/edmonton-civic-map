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
