# SPEC — Edmonton Civic Map: the founding brief

**Read when:** scoping any feature, or before re-opening something that feels
settled. This is the owner's brief of 2026-10-09, kept verbatim below. The rows
in `docs/DECISIONS.md` point here.

**Amendments since the brief was written**

- 2026-10-10 — the name is **Edmonton Civic Map** (owner). This replaces
  "Edmonton Civic Atlas" in §2 item 6 and closes §9 question 1.
- 2026-10-10 — §10 tasks 1–4 are done; findings are in `data/DATA.md`,
  `docs/DATA_ISSUES.md`, `docs/SPEC_data_schema.md` and `prototype/README.md`.
- 2026-10-10 — **Tier 2 approach** (owner; closes §9 question 3). Start with
  what can be said plainly from a primary source by automation, then move up
  to written content only where that runs out. The ladder:
  1. **Stated by a source, refreshed by script.** A publisher's own statement
     of who handles something, carried with its `source_url` and
     `last_verified` like any Tier 1 record, and held by the same diff check.
  2. **Assembled from sources.** A plain sentence built from two or more such
     facts, with every part linked. Drafted by Claude, approved by the owner.
  3. **Written explanation.** Only where an issue genuinely spans bodies and no
     source says it plainly. Drafted by Claude from primary sources, approved
     by the owner, with an owner and a review date per entry (§6).

  Each entry records which rung it is on. Nothing on rungs 2–3 publishes
  without the owner's approval.
- 2026-10-10 — **Launch scope** (owner; closes §9 question 4). The first
  public version is Tier 1, the lookup. Tier 2 entries have no deadline and are
  added one at a time as each is judged ready. The site is public from launch,
  so it must be complete and honest with no Tier 2 entries at all.
- 2026-10-10 — **Static site on GitHub Pages** (owner; closes §9 question 2).
  No backend of ours: the site is files, and the lookup runs in the browser.
- 2026-10-10 — **A geographic map is in scope, with 2D and 3D views** (owner;
  not in the brief). Comparable in kind to `edmonton-tax-viz`, but **built on a
  different stack**: trying one is part of the point of this project. Not yet
  decided: which stack.
- 2026-10-10 — **The main view is rough geography, possibly with buildings**
  (owner). 3D shows the city's shape, not a quantity: nothing is extruded to
  encode a number. **How much detail is a phase of its own**: experiment with
  terrain and building detail until storage or performance limits are hit, and
  record where they are. The lookup must work without the detail layers.

---

# Brief: Edmonton Civic Atlas (working title)

Status: draft for CC. Separate repo from the Edmonton tax viz. Nothing here is built yet.

## 1. Purpose

A **reference tool** answering: *"Who represents me, and who is responsible for what?"* for any Edmonton address. It is a lookup and explainer, not a politics or scorecard dashboard.

Audience: residents, journalists, community groups, students. Mobile-friendly; most use will be a quick lookup.

## 2. Locked decisions (from planning conversation, 2026-10-09)

1. **Separate repo and deployment** from the tax viz. At most a neutral link between them at city or neighbourhood level, never per councillor.
2. **Descriptive only.** No rankings, alignment/"voting similarity" scores, league tables, or per-councillor evaluation. Record only what is on the public record and neutrally framed.
3. **Roles and departments over individual staff.** Name staff only where the City publishes them as public contacts. Elected officials are fine.
4. **No address storage.** Geocoding and point-in-polygon should run client-side or statelessly; do not log or persist addresses.
5. **Currency by design** (section 6). An out-of-date reference tool is worse than none.
6. **Name:** working title "Edmonton Civic Atlas". Not "politics dashboard", since council is formally non-partisan.

## 3. Scope tiers

**Tier 1: Lookup (MVP)**
- Address (or map click) returns: municipal ward and councillor, mayor, Edmonton Public and Catholic school ward and trustees, provincial MLA and riding, federal MP and riding.
- Each result: name, role, official contact link, source link, "last verified" date.
- Map layers: ward boundaries, school wards, provincial and federal ridings. Population per ward shown beside any ward-level figure (wards are only balanced within an allowed variance, so raw ward totals are not comparable).

**Tier 2: Who is responsible for what**
- Static, curated content mapping common issues (potholes, snow clearing, zoning/infill, transit, policing, schools, water/stormwater, property tax and assessment) to the responsible body: council, City administration, EPCOR, police commission, school boards, Government of Alberta, federal.
- Each entry: who decides, who delivers, how a resident can engage (contact, written submission, public hearing, 311), with source links.
- This is the "next steps" layer and probably the most valuable part. It is written content, not data.

**Tier 3: Structure and connections**
- Committees and membership, council/administration/province relationships as a simple diagram.
- Optional and last. Descriptive only (no vote-based metrics).

## 4. Data sources (verify each before relying on it)

| Need | Candidate source | Notes |
|---|---|---|
| Ward boundaries | City of Edmonton Open Data portal | **First task: confirm the layer reflects the current post-October-2025 state** and check whether any boundary review has changed it since the 2021 redraw. |
| Councillors and mayor | City of Edmonton council pages, Edmonton Elections official results | Cross-check the two. |
| Ward populations | City census / Urban Planning and Economy data | Needed for the population-balance note. Record the year. |
| School wards and trustees | Edmonton Public Schools and Edmonton Catholic Schools sites; Edmonton Elections results | Public board: 9 trustees. Catholic board: 7. |
| Provincial ridings and MLAs | Elections Alberta boundary files; Legislative Assembly of Alberta member list | Confirm the current electoral division map. |
| Federal ridings and MPs | Elections Canada / Statistics Canada boundary files; House of Commons member list | Confirm the current representation order. |
| Geocoding | City of Edmonton address data (open data) preferred; otherwise a privacy-respecting option | Must not leak addresses to third parties without a clear decision. |

Rule: **primary sources only.** No news or wiki scraping as a source of record. News links are acceptable as context, not as data.

## 5. Address lookup design

- Preferred: client-side. Ship simplified boundary GeoJSON, geocode against a local address layer or a vetted service, and run point-in-polygon in the browser. No server-side address handling.
- If a third-party geocoder is unavoidable, that is a decision for Peter before implementation. Document the privacy implication.
- Also support map click and "choose your ward from a list" so the tool works without typing an address.
- Boundaries must be simplified for load time, and the simplification tolerance recorded so boundary-edge errors are understood. Near a boundary, show a "check official lookup" note.

## 6. Currency and verification

- Every record carries `last_verified` and a `source_url`. Show both in the UI.
- Refresh is scripted (same philosophy as the tax viz refresh): fetch from primary sources, regenerate data files, and run a **diff check** that flags unexpected changes (a councillor changed, a boundary moved, a count changed) for human review instead of publishing silently.
- Expected change events to plan for: municipal elections (next 2029), by-elections and resignations, provincial and federal elections, ward boundary reviews, school board changes. Add a calendar-driven "recheck everything" task.
- Staleness guard: if any record is older than a set threshold, the UI shows a visible warning.
- Tier 2 content has owners and a review date per entry.

## 7. Content and framing rules

- Neutral, factual wording. No evaluative language about officials or bodies.
- Council is described as a collective decision-maker. Say clearly that the mayor has one vote and that much of what residents experience is delivered by administration, the province or EPCOR, not by councillors.
- Public hearings: when pointing people to them, also surface lower-barrier routes (written submissions, 311, contacting the ward office) so the tool does not funnel engagement only toward people who attend hearings.
- Include a short "about and methodology" page: sources, verification dates, known limitations.

## 8. Repo and process conventions

Decide at kickoff whether to reuse the tax viz conventions (DECISIONS.md, audit ledger, brief/audit relay between Claude instances) or keep a lighter version. Recommendation: **DECISIONS.md and a source ledger from day one**, since provenance is the whole value of a reference tool. Skip heavier audit machinery until Tier 2.

## 9. Open questions for Peter

1. Name: "Edmonton Civic Atlas", or something else?
2. Static site with prebuilt JSON, or a small backend? Recommendation: static, to keep address handling client-side and hosting simple.
3. Tier 2 authorship: Peter writes and reviews the "who is responsible for what" content, with CC drafting from primary sources?
4. Launch scope: Tier 1 only, or Tier 1 plus a handful of Tier 2 entries?

## 10. Suggested first tasks for CC

1. Locate and verify the current ward boundary layer and population data; report vintage and any discrepancies with the 2025 election results.
2. Find authoritative boundary files for school wards, provincial ridings and federal ridings; report format, license and vintage.
3. Prototype client-side point-in-polygon with ward boundaries only, with no address storage.
4. Draft the source ledger and `last_verified` data schema.
5. Report back before building UI.

Do not name individual staff, add vote-based metrics, or add any third-party geocoding without checking with Peter.
