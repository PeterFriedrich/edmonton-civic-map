# DATA_ISSUES — defects in data we do not control, and what we've told the publisher

**What belongs here:** a defect in a source we consume — plus the evidence, what
it breaks on our side, and **whether anyone has been told**. One row per defect,
newest first.

**What does NOT belong here:**

| this file | where it goes instead |
|---|---|
| how a source is shaped, its columns, its quirks | `data/DATA.md` |
| our own build work and backlog | `TODO.md` |
| a locked decision + its reasoning | `docs/DECISIONS.md` |
| an audit we ran over our own pipeline | `docs/AUDIT_LEDGER.md` |

⚠️ **The point of the file is the last column.** Findings that never leave the
repo are the standing failure mode: a measured upstream defect can be archived
unsent as a sub-item of a closed parent and go invisible. Status must be one of
**NOT SENT · SENT (date) · ACKNOWLEDGED (date) · FIXED (date) · WONTFIX**, and
"the artifact exists" is **not** sent.

---

| Date found | Source / dataset | Defect | Evidence | What it breaks here | Status |
|------------|------------------|--------|----------|---------------------|--------|
| 2026-10-10 | City of Edmonton open data: `d7pj-rist` (public school wards), `pwzf-sjj2` (Catholic school wards) | The `trustee` column still names the 2021–2025 trustees, although the datasets describe themselves as "the associated board trustee in office" and were refreshed 2026-10-05. | Against the 2025 official results (`fv5x-8efu`) and both boards' own trustee pages, read 2026-10-10: public wards B, C, D, E and H differ (5 of 9); Catholic wards 71 and 73 differ (2 of 7). The council ward layer `b4er-5rp2` from the same publisher was updated correctly. | Trustee names cannot come from the City layer; they are read from the boards' sites and only the geometry is used. | NOT SENT |
