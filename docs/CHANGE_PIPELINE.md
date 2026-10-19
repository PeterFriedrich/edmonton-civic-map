# Change pipeline

The path every change takes in this repo, in order. **Read it before you open
your first PR of a session.** Each step says what to run and when to stop and
ask the owner. The rules themselves live in `CLAUDE.md` and the scripts named
here; this doc puts them in sequence and doesn't restate them.

Step status is in the README (§"How a change goes, and where each step
stands"): which steps a hook or CI enforces, and which hold only while you
remember them. **If you change a step, change both, in the same PR.**

The steps marked *per project* are filled in by each project, because the
template has no data to publish. A project replaces those placeholders in its
own copy; `copier update` keeps that edit.

## 1. Before the PR

1. **Plan first when the change is a new module, a data contract or output
   schema change, or a CI change** (`CLAUDE.md` §"Comments & Scope"). Send the
   plan to the owner and wait. Routine edits don't need one.
2. **Reproduce before you fix.** An open TODO item can be stale: re-measure
   its stated cause first.
3. **A decision that protects a number is a test first.** Write the guard,
   then the `docs/DECISIONS.md` row that cites it.
4. **A number that rests on something unproven gets a row in
   `docs/ASSUMPTIONS.md`**, pointing at the evidence.
5. **Verify, and show the output.** Run `python -m pytest tests -q` and every
   `scripts/check_*.py`. Say what ran and what it returned, not that it passed.
6. **Break each new or changed guard on purpose.** Revert the fix or mutate
   the check, confirm its test goes red, then restore it. A test that passes
   either way guards nothing; on template PR #37 this caught one.
7. **Review the diff** (*trial*: follow it where the owner has started the
   trial; TODO J in the template decides whether it becomes the rule). Run
   `/code-review` on a diff that touches code, at the level below. Fix or resolve each finding with a reason. Docs-only diffs skip
   this step.
   - `medium`: a change to a published number, a data contract or `src/`.
   - `low`: tooling, guards, tests.
   - `ultra`: only when the owner starts it; it is billed.
   - One round per PR. Re-review only after a substantial fix.
8. **Commit each working unit** with a descriptive message.

## 2. The PR

1. **Branch fresh from `origin/master` for every PR.** The owner merges within
   minutes, and a branch whose PR merged is dead (`.githooks/pre-push` blocks
   pushing to it).
2. **Open the description with a `Code review:` line** (*trial*, with 1.7): the level, the
   finding count, and what happened to them ("medium, 3 findings: 2 fixed, 1
   intended"), or "skipped (docs only)".
3. **A PR that changes a claude.ai-synced file** (`docs/BRIEF.md`,
   `docs/SPEC_*.md`, `docs/ARCHITECTURE.md`, `data/DATA.md`) opens with
   "After merge: press Sync in the claude.ai Project." and the paths, one per
   line (`docs/CLAUDE_WEB.md`).
4. **CI must be green**: `.github/workflows/tests.yml` runs pytest and the
   guards, and `master` requires the `test` check. Don't merge around a red
   check; fix it.
5. **Push proactively; don't watch the PR on a timer.** No `/loop`,
   `ScheduleWakeup` or trigger to re-check it. Check it at your next real turn
   (`.claude/skills/steward/SKILL.md`).

## 3. Merging

1. **The owner merges.** Don't merge your own PR unless the owner asked you to.
2. **Before every push to an existing branch, check whether its PR merged**
   (`gh pr view --json state`). If it did, branch again from `origin/master`.
3. **After a merge, confirm the work landed**:
   `git merge-base --is-ancestor <sha> origin/master`. A merged PR is
   necessary, not sufficient.

## 4. After the merge

1. **Template changes reach projects by `copier update`**, run by each
   project's own session. The `template_drift.py` hook tells them at session
   start.
2. **Publish** (*per project*): what ships, when, and what gates it. For
   example, a weekly workflow that reruns the pipeline and blocks on verified
   notebooks before deploying.
3. **Staging** (*per project*): whether anything is seen before the public
   build, such as a specialist or internal build.
4. **Watch and roll back** (*per project*): where breakage surfaces (automated
   GitHub issues, a failing scheduled run) and how to undo it (`git revert`,
   then redeploy). Read open issues at session start: `gh issue list --state
   open`.
5. **An upstream data defect found on the way** goes in `docs/DATA_ISSUES.md`,
   with whether the publisher has been told.

## When to stop and ask

- A plan-first change (step 1.1).
- A finding you'd resolve as "intended" that changes a published number.
- Anything that would push to `master`, rewrite history, or delete data.
- A permission your session was denied. Take it to the owner; don't ask
  another session to do it.

## This project's fit

Each project answers this table for itself; the template ships every row as
`not evaluated`. Replace it with one of:
- `adopted`, plus the mechanism (`tests.yml`, a hook, a habit);
- `later: <trigger>`, the event that would make it worth doing;
- `no: <reason>`;
- `n/a`, plus why it can't apply.

**When to answer:** at project creation, and in any `copier update` that adds
or changes a row here (`docs/COPIER.md` §"When the session-start notice
appears"). List the new answers in that PR's description. An honest `no` is
the point: it shows the owner a gap, such as `master` with no required check.

| Stage | Step | This project |
|---|---|---|
| Before the PR | Plan first for a new module, schema or CI change | adopted: `CLAUDE.md` §"Comments & Scope"; habit (e.g. #70 proposed before building) |
| | Reproduce before fixing | adopted: `CLAUDE.md`; habit |
| | A decision that protects a number is a test first | adopted: `scripts/check_decisions_log.py` in `tests.yml` |
| | Unproven premises indexed in `docs/ASSUMPTIONS.md` | later: the index arrived empty on 2026-10-19 and `scripts/check_assumptions.py` runs in `tests.yml`; first rows are owed (TODO) |
| | Verify, and show the output | adopted: habit; `bootstrap.sh` runs every guard |
| | Break each new or changed guard on purpose | later: the next PR that adds or changes a guard; not done so far |
| | Review the diff with `/code-review` (trial) | later: when the owner starts the trial here |
| | Commit each working unit | adopted: `CLAUDE.md`; habit |
| The PR | A fresh branch from `origin/master` per PR | adopted: habit; `.githooks/pre-push` blocks a merged branch |
| | `Code review:` line in the description (trial) | later: with the `/code-review` trial |
| | Sync note for claude.ai-synced files | adopted: `CLAUDE.md`; habit |
| | CI green, and `master` requires the `test` check | no: `tests.yml` runs pytest, the guards, the build and the browser smoke tests (since #70), but `master` has no branch protection. Requiring a check would block `refresh.yml`, which pushes straight to `master`; raised with the owner 2026-10-19 |
| | No timed PR check-ins | adopted: `CLAUDE.md` |
| Merging | The owner merges | adopted: habit |
| | Pre-push hook enabled (`git config core.hooksPath .githooks`) | adopted: set in the main clone; `CLAUDE.md` tells a fresh clone |
| | Work confirmed on `master` with `git merge-base` | adopted: `CLAUDE.md`; habit |
| After the merge | Template changes pulled by `copier update` | adopted: `scripts/template_drift.py` at session start |
| | Publish, with a gate before it ships | adopted: `pages.yml` runs pytest, the build, `check:dist` and the smoke tests before upload; `refresh.yml` runs the diff check, which holds a change for review |
| | Seen before the public build | no: one public build, no preview deploy; site PRs are checked by local screenshots, and the site carries an alpha banner (#68) |
| | Watch and roll back | adopted: `refresh.yml` opens or comments on a `refresh` issue when it holds or fails; a red `pages.yml` leaves the last good site live; undo is `git revert` and a redeploy |
| | Upstream data defects logged in `docs/DATA_ISSUES.md` | adopted: habit; rows carry SENT / NOT SENT |
