# Audit brief: does an address get the right districts?

A read-cold instrument for a **decision audit** (`.claude/skills/project-audit/SKILL.md`,
family a) of the chain from a typed or clicked Edmonton address to the five
districts the site names for it. It holds the grounding order and the
questions, never the findings: a run writes `docs/FINDINGS_district_assignment.md`
and a row in `docs/AUDIT_LEDGER.md`.

**Why this target first.** The site answers one question, "who represents me?",
and every card hangs off the district set. A wrong office holder shows up on
one card and the publisher's own page corrects it. A wrong district gives a
confident wrong answer with a primary-source link beside it, and nothing on
the page contradicts it. Every guard in the build checks that the code agrees
with itself and with the source layers. None checks that the source layer is
the boundary the office holder was elected on.

## Grounding order (read before writing any finding)

1. `docs/SPEC_civic_map.md` (the founding brief), then `docs/SPEC_data_schema.md`
   §1, §3 and §9 in full.
2. Every `docs/DECISIONS.md` row about boundaries, the address index, share links or
   map clicks, **read whole, never cut**: 2026-10-15 "Districts are worked out per
   address at build time", 2026-10-15 "Boundaries ship as GeoJSON", 2026-10-16
   "Provincial boundaries come from the Government of Alberta's ... Current
   2019", 2026-10-16 "Office holders are built into `officeholders.json`",
   2026-10-17 neighbourhood search and share link, and any later row that
   amends one.
3. `docs/DATA_ISSUES.md`, every row. Three of them are this target: the
   2026-10-21 city edge, the 2026-10-17 City-versus-board school wards and the
   2026-10-15 overlaps and gaps.
4. `data/DATA.md` sections on each of the five layers and on parcels;
   `prototype/README.md` "Districts per address".
5. The code: `src/build_boundaries.py`, `src/build_address_index.py`,
   `site/src/pip.js` and the lookup and map-click paths in `site/src/app.js`.
6. `docs/ASSUMPTIONS.md`. It is empty as of 2026-11-13, so every premise below
   that no test proves is a candidate first row.

Data rules: never `Read` a `.geojson`, `.csv` or address file; summarise it
with a short python script (`docs/TOKEN_EFFICIENCY.md`). The downloaded
sources are in `data/raw/` on the server (gitignored). Run `df -h /` before
writing anything large.

## The decision stack (evaluate top-down; an UNSOUND level moots those below)

**L0. Should the site state a district per address at all, at the confidence it shows?**
Publishers disagree by more than the site's own uncertainty band. School wards
differ between the City and the boards by up to 361 m, and the city edge moved
by up to 80 m on 2026-10-19. The near-edge note is set at 20 m. Does the card's
wording claim more certainty than the sources support? Is the note
(`near_boundary_m`) the right signal, at the right distance?

**L1. Is each layer the operative boundary for the people now in office?**
For each of the five layers, name the instrument that legally fixes it (bylaw,
order, Act), and check that the sourced layer is that boundary, for the term
the current holders were elected to:
- Council wards: `b4er-5rp2`, republished 2026-10-19 with a new outer edge. Which edge is right?
- Public and Catholic school wards: City layers `d7pj-rist` and `pwzf-sjj2`, which disagree with the boards' own layers. Which one does the board's bylaw describe?
- Provincial: the GoA "Current 2019" layer. Confirm it is still the operative map for the sitting Assembly. Find out whether any redistribution has been enacted, and when it takes effect.
- Federal: the 2023 Representation Order (343 districts).
The sharpest risk: a layer that is right by its own metadata but is not the
boundary the official was elected on.

**L2. Is "an address" the right unit, placed at the right point?**
Addresses are City `ut27-nrpn` PARCEL rows. A multi-row address takes the row
nearest the group's centre, and a split address shows every district set.
Where does the parcel point sit away from where people live (large parcels,
condo complexes, rural edges, new subdivisions)? What happens to an address
that is not in the City list but is typed anyway?

**L3. Does processing preserve the source answer?**
Provincial and federal ridings are clipped to the union of the council wards,
so the moved city edge moves them too. Each layer is simplified as a coverage
(5 m). Publisher overlaps and gaps are kept. Is clipping to the council-ward
edge sound, given DATA_ISSUES 2026-10-21? Can an address fall out of the city
through the clip alone?

**L4. Do the guards measure the right thing?**
The two `pip.js` checks (§9.5) prove that shapely and ray casting agree, and
that simplification moved no address. Both read the same inputs, so neither
can catch a wrong source (L1) or a wrong unit (L2). Since §9.6, new addresses
pass the refresh without review. Name what an unattended weekly refresh can
change about a district answer without a person seeing it.

**L5. Does the browser give the same answer as the build?**
A typed address uses the stored districts. A map click runs `pip.js` over the
simplified files, and an overlap returns two districts. Look at share links
(`#d=`, `#a=`, `#n=`) and the "outside Edmonton" message.

## Out of scope here (each is its own target in the ledger)
District → office holder (names, cross-checks, vacancies, the kept-MP path),
refresh-guard coverage as a whole, the privacy promise, and source currency.

## Output shape
One verdict line per level (SOUND / CONDITIONAL / UNSOUND), with the sharpest
counter-argument and the evidence that would change it. Then fixes, ranked.
Then **What this run got wrong** (required, never empty). Finish with step 5 of
the skill: a ledger row, `docs/ASSUMPTIONS.md` rows for each unproven premise
found, TODO follow-ups and any DECISIONS row. Anything that should go to a
publisher goes in `docs/DATA_ISSUES.md` as NOT SENT.
