# Session handoff — 2026-11-26 to 2026-11-28, S14: Owner runs lines, template pull, branch prune

## 0. Session Metadata
- **Model:** Opus 5.5 (`claude-opus-5-5`) for the whole session, no switch.
- **Effort:** `$CLAUDE_EFFORT` reads `high` (checked at handoff; not checked earlier in the session).
- **Date / session #:** 2026-11-26 to 2026-11-28, S14. PRs #97 and #98 (owner merged), plus this handoff's PR.

## 1. Goal
- **Project:** Edmonton Civic Map, a public lookup answering "who represents me, and who is responsible for what?" for any Edmonton address. Descriptive only.
- **This session:** read S13. After that it was mostly answering two peer sessions, pulling a template update and cleaning up branches. No product work.

## 2. Current State
### ✅ Completed
- **Survey answered for `template` (its TODO Z, item records in TODO.md and thinner handoffs).** The answer most likely to matter: `scripts/make_brief.py` `open_items()` joins every two-space-indented line under an open item into the brief. Proposed `Log:` or `Status:` lines would therefore flow into `docs/BRIEF.md`, a synced file, and every log append would need a brief regen and a Sync. No reply has come yet.
- **PR #97, merge commit 5becf89 (confirmed with `merge-base --is-ancestor`).** By-hand actions are now `- [ ] **Owner runs:** \`<action>\` — why · confirm: \`<check>\` · urgency · since YYYY-MM-DD` lines in `TODO.md` "### Waiting on the owner". Peter decided on 2026-11-26, relayed by `server`, that each repo keeps its own lines and `server` collates them. There are 7 lines:
  - Sync
  - the Project picker
  - `git branch -D template-a104a5f`
  - the City defect report
  - the league request
  - the school-ward question
  - three browser reads

  `server` was told when the PR landed.
- **PR #98, merge commit 31d4fa6 (361b331 confirmed on origin/master).** Pulled template 3b226fc → 05a0cdf with `copier update --trust --defaults`:
  - `.gitignore`: `.venv` and `venv` without the trailing slash, so symlinked venvs are ignored too.
  - `scripts/handoff_gap.py` and its tests: SessionStart now lists open `Owner runs:` lines with their `confirm:` checks.
  - `TODO.md`: gained the template's "By-hand actions" paragraph. The conflict was resolved by keeping all of the project's items, and "Waiting on the owner" moved to the last group in Open work.

  Verified: 251 tests pass. Dropping the optional closing `**` from the `OWNER_RUNS` regex turns `test_owner_runs_reminder_matches_what_server_collates` red.
- **Branch prune, with the owner's go-ahead.** After `git fetch --prune`, 88 remote branches were ancestors of `origin/master` (the hook had said 90), and none headed an open PR. All 88 were deleted with `git push origin --delete`; origin now has only `master`. Locally, `git branch -d` removed 21 branches plus `todo-owner-runs` and `template-05a0cdf`.
- **Owner runs `confirm:` checks run on 2026-11-27:** `template-a104a5f` still exists, and `docs/DATA_ISSUES.md` still has 7 NOT SENT rows. Neither line is done. The other five can't be checked from here.

### ⚠️ In Progress
- Nothing mid-edit. This handoff's branch `handoff-s14` also archives S11.

### ❌ Blocking Issues
- None. No open issues and no failed runs since 2026-11-26.

## 3. Technical Learnings
- **The SessionStart hook now prints the open Owner runs lines every session, on purpose.** Run the backticked `confirm:` checks, tick the ones that pass, and ask the owner only about the rest.
- **Our `.githooks/pre-push` never guards a branch delete**, so a bulk `git push origin --delete` goes through.
- **`merged_branch_reminder()` counts the remote-tracking refs as of the last fetch**, so it can read high. Re-count after `git fetch --prune` before acting on it.
- **`git branch -d` refuses a branch whose patch isn't on master, which is the safe way to bulk-delete.** `git cherry master <branch>` shows `+` for a commit that isn't on master.
- **A copier update that touches `TODO.md` conflicts as one block** (`<<<<<<< before updating` / `>>>>>>> after updating`). The template side is just its placeholder, so keep "before updating" and drop the markers.

## 4. Next Steps (prioritized)
1. **Press Sync in the claude.ai Project** (from #97 and #98):
   docs/BRIEF.md
   If not yet done, this carries over from S11:
   data/DATA.md
2. **"Measure weekly address churn, around 2026-11-27"** (TODO Build) is due now. Read the "N added, M removed" counts in the `Weekly refresh` commit messages and check them against `data/diff_rules.json` `parcel_rows_max_change`.
3. **About page fixes** (TODO "About page after the audit"). Run `/code-review`, and `/security-review` if `site/src/` address or rendering code is touched.
4. **Draft the school-ward question** when asked. The owner sends it.
5. **Owner decisions, carried over:**
   - a CI trigger for a past `recheck_dates` entry
   - the "sources disagree" flag
   - the `ca_mps` notice
   - Ward F option B
6. **Next audit:** district → office holder. It needs a brief first.

## 5. Restoration Procedure
- `cd ~/edmonton-civic-map && git checkout master && git pull`, then `gh issue list --state open` and `gh run list --status failure --limit 5`.
- Tests and guards:
  - `.venv/bin/python -m pytest tests -q` (251 tests)
  - `scripts/check_doc_citations.py`, `check_assumptions.py`, `check_requirements.py`, `check_fit_table.py` and `check_decisions_log.py --root .`
- Site: `npm ci && npm run build && npm run check:dist`.
