# Session handoff — 2026-11-23 to 2026-11-25, S13: Pages deploy outage fixed

## 0. Session Metadata
- **Model:** Opus 5.5 (`claude-opus-5-5`) for the whole session, no switch.
- **Effort:** `$CLAUDE_EFFORT` reads `medium` (checked at handoff).
- **Date / session #:** 2026-11-23 to 2026-11-25, S13. PR #95 (owner merged), plus this handoff's PR.

## 1. Goal
- **Project:** Edmonton Civic Map, a public lookup answering "who represents me, and who is responsible for what?" for any Edmonton address. Descriptive only.
- **This session:** read the S12 handoff. That surfaced a failed Pages deploy after the 2026-11-23 refresh, and the session became finding and fixing it.

## 2. Current State
### ✅ Completed
- **Pages outage, 2026-11-23 to 2026-11-25, fixed by PR #95** (merged as 9124b6d; 3646fa7 confirmed on `origin/master` with `merge-base --is-ancestor`).
  - **Symptom:** in every `pages.yml` run from 2026-11-23, `actions/deploy-pages` reported "Found 0 artifact(s)" about one second after `upload-pages-artifact` had finalized the bundle.
    - Run 45274319932 failed this way.
    - Run 45539541171, the owner's manual dispatch, failed the same way.
    - The re-run of 45274319932 (attempt 2) failed differently, on "Multiple artifacts named github-pages". It saw attempt 1's bundle next to its own. **Re-running a failed Pages run can't work.** Start a fresh run instead.
  - **Impact:** the live site kept serving the 2026-11-20 data. The 2026-11-23 refresh changed only `last_verified` and `addresses_checked`, so no representative was wrong.
  - **Cause, partly proven:**
    - Nothing changed on our side. `pages.yml` was last touched 2026-10-15, and the 2026-11-20 deploy used identical action SHAs.
    - GitHub status showed no incident.
    - civic-map was the only repo on the account that uploaded and deployed in a single job. tax-viz, physics_sim, math-stats and the portfolio all use `build` → `deploy` (`needs: build`), and tax-viz deployed fine on 11-23 and 11-24.
    - What changed on GitHub's side is unknown.
  - **Fix:** `pages.yml` now has three jobs:
    - `build`: tests, build, `check:dist`, smoke, upload
    - `deploy`: `needs: build`
    - `report-failure`: `if: failure()`, `issues: write`. It opens an issue titled "Pages deploy failed <date>", or comments on one that's already open.
  - **Records:**
    - a DECISIONS row dated 2026-11-25, tagged `[unverifiable]`
    - the CHANGE_PIPELINE "Watch and roll back" row
    - a regenerated `docs/BRIEF.md`
  - **Verified:**
    - In branch dispatch run 45549983277, `build` passed. `deploy` was refused by the `github-pages` environment's master-only branch policy, which was expected. `report-failure` filed #94, which I then closed as a test.
    - After the merge, push run 45550763045 had `build` and `deploy` pass and `report-failure` skipped.
    - The live `https://peterfriedrich.github.io/edmonton-civic-map/data/officeholders.json` sha256 equals master's (`7b0248d0…`).
    - 242 tests pass.
- **civic-docs-index:** the owner asked whether we had requested anything from it. Neither repo references the other, and nothing is pending in either direction. Its README is still the template's text. A natural first request, once it can fetch eSCRIBE: the post-election ward boundary report (TODO "Post-2025-election ward boundary report", recheck after 2026-12-31).
- **Template notice evaluated, not applied:** `.gitignore` changes `.venv/` and `venv/` to `.venv` and `venv`, which also ignores symlinked venvs, as in worktrees. I recommended taking it, and the owner hasn't decided.

### ⚠️ In Progress
- Nothing is mid-edit.
- **Local branches:**
  - `template-update` and `template-update-f0fd83b` are fully merged and safe for `git branch -d`.
  - `template-a104a5f` has one unmerged commit, 0907fb2, an old version of #91, and needs `-D`.
  - `pages-split-jobs` is merged.

  Owner command: `! git branch -d template-update template-update-f0fd83b pages-split-jobs && git branch -D template-a104a5f`

### ❌ Blocking Issues
- None. There are no open issues.

## 3. Technical Learnings
- **A failed Pages job can't be rescued with `gh run rerun --failed`.** The earlier attempt's `github-pages` artifact still counts, so deploy-pages finds 2 and fails. Use `gh workflow run pages.yml --ref master` instead.
- **The `github-pages` environment allows only `master`** (custom branch policy). A branch dispatch therefore tests `build` and `report-failure` but never the deploy, which is proven only after merge.
- **The auto-mode classifier blocked `gh workflow run pages.yml --ref master`** as destructive before the owner had approved the fix. After approval, a branch dispatch went through.
- **An issue check at session start can't see a failed Pages run.** Before #95, that failure filed nothing. `gh run list --status failure --limit 5` is the check that caught it.
- To confirm what's live, fetch the deployed `officeholders.json` with a `?cb=$RANDOM` query string and certifi's CA bundle, then compare its sha256 with `git show origin/master:site/public/data/officeholders.json | sha256sum`.
- A DECISIONS row changes `docs/BRIEF.md` through `scripts/make_brief.py`, so `test_committed_brief_is_current` fails until you run `make_brief.py --write`. That makes the PR a synced-file PR.

## 4. Next Steps (prioritized)
1. **Press Sync in the claude.ai Project** (from #95):
   docs/BRIEF.md
   If not yet done, this carries over from S11:
   data/DATA.md
2. **Template `.gitignore` update**: take it or decline it (owner's call). Steps are in `docs/COPIER.md`.
3. **School-ward question** to both school boards and Edmonton Elections, covering the six S10 addresses. Claude drafts it when asked, and the owner sends it.
4. **Owner decisions, carried over:**
   - a CI trigger for a past `recheck_dates` entry
   - whether to plan a per-address "sources disagree" flag
   - the blocked-`ca_mps` notice in `refresh.yml`
   - Ward F option B, a published "covered by" field (needs a plan first)
5. **About page fixes** (TODO "About page after the audit"). Run `/code-review`, and `/security-review` if `site/src/` address or rendering code is touched.
6. **Next audit:** district → office holder (`docs/AUDIT_LEDGER.md` "Never audited" item 2). It needs a brief first.

## 5. Restoration Procedure
- `cd ~/edmonton-civic-map && git checkout master && git pull`, then `gh issue list --state open` and `gh run list --status failure --limit 5`.
- Tests and guards:
  - `.venv/bin/python -m pytest tests -q` (242 tests)
  - `scripts/check_doc_citations.py`, `check_assumptions.py`, `check_requirements.py`, `check_fit_table.py` and `check_decisions_log.py --root .`
- Site: `npm ci && npm run build && npm run check:dist`.
