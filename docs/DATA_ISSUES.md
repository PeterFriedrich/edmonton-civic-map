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
| 2026-10-17 | City of Edmonton open data: `65fr-66s6` (neighbourhoods) | `civic_ward_name` for Anthony Henday South East (`neighbourhood_number` 6665) reads Sspomitapi, but the neighbourhood's addresses are all in Karhiio on the City's own ward layer `b4er-5rp2`. | All 288,534 published address records placed in the neighbourhood polygons, 2026-10-17: for 406 of 407 neighbourhoods the field names the ward holding most of its addresses; this is the one that does not. | Nothing: the field is not used, and districts come from the addresses. | NOT SENT |
| 2026-10-15 | City of Edmonton open data: `b4er-5rp2` (council wards), `d7pj-rist` (public school wards), `pwzf-sjj2` (Catholic school wards); Elections Alberta 2017 divisions | Neighbouring districts do not share exact edges: the layers overlap slightly and leave small gaps. Elections Canada's federal layer is clean. | Measured on the full-resolution layers, 2026-10-15 (shapely `coverage_is_valid` false on all four): overlap between neighbours 4.2 m² (council), 67.4 m² (public school; also about 0.0007 km² of holes inside the layer), 0.2 m² (Catholic), 0.6 m² (provincial); edges that fail to match run 3.7, 21.1, 14.0 and 33.8 km. The public and Catholic ward layers also differ from the council wards' outer edge by about 0.11 and 0.07 km². | Nothing measured: every parcel address still falls in exactly one district on every layer. A map click inside an overlap returns two districts and the card shows both. The lines are published as the publisher drew them; GEOS's coverage clean-up was tried and rejected because it reshaped small edge ridings by up to 9.7 km. Areas after simplifying are in `site/public/data/layers.json` (`overlap_m2`, `gap_m2`). | NOT SENT |
| 2026-10-10 | City of Edmonton open data: `d7pj-rist` (public school wards), `pwzf-sjj2` (Catholic school wards) | The `trustee` column still names the 2021–2025 trustees, although the datasets describe themselves as "the associated board trustee in office" and were refreshed 2026-10-05. | Against the 2025 official results (`fv5x-8efu`) and both boards' own trustee pages, read 2026-10-10: public wards B, C, D, E and H differ (5 of 9); Catholic wards 71 and 73 differ (2 of 7). The council ward layer `b4er-5rp2` from the same publisher was updated correctly. | Trustee names cannot come from the City layer; they are read from the boards' sites and only the geometry is used. | NOT SENT |
