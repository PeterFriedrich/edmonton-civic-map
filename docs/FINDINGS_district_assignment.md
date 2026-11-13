# Findings: does an address get the right districts? (run of 2026-11-13)

Output of one run of the decision audit briefed in `docs/AUDIT_district_assignment.md`.
Verdicts are as of 2026-11-13. No code was changed; fixes are listed as follow-ups.

**Result: no level is UNSOUND. L3 and L5 are SOUND. L0, L1, L2 and L4 are CONDITIONAL.**
The build places each address correctly in the layers it is given. What is not
proven is that the school-ward layers are the lines the boards' bylaws describe:
both bylaws were found and read, and at a few addresses the site's answer differs
from the bylaw's words as read here.

## Inputs and limits

- Layers: the copies in `data/raw/` (council, school wards, provincial, federal).
- Addresses: the local parcel copy of 2026-10-21 (298,561 rows). The published
  index was built from the 2026-11-09 copy, so counts here are close to, not
  equal to, the published ones. The 20 m counts below reproduce the published
  manifest on three layers and are one off on the fourth.
- Fetched 2026-11-13 for comparison only: the boards' own ward layers
  (`azimuth.epsb.ca`, `EPSB_Wards_2025` and `FC_ECSD_Wards_2025`) and the City's
  Road Network centre lines (`9j8t-zm52`). All distances in EPSG:3776.
- Parcel rows are points. No parcel polygons are in the repo.

## Verdicts

### L0. A district per address, at the confidence shown — CONDITIONAL
The card names one district with no qualifier. The only qualifier is the
near-boundary note, set at 20 m. That note measures the site's own error
(5 m simplification, map-click precision). It does not measure disagreement
between sources, which reaches about 360 m.

- Of the three addresses where the City's and a board's layer disagree, two
  carry the note by coincidence of distance (15928 Manning Drive NW, 18.3 m;
  610 Calgary Trail NW, 15.1 m) and one does not (17611 34 Street NW, 63.8 m).
- Widening the note is the wrong fix. Rows within 20 / 50 / 100 / 200 / 400 m of
  their own district's edge: council 529 / 4,618 / 10,714 / 25,202 / 55,990;
  public 340 / 3,522 / 8,549 / 21,118 / 48,241; Catholic 123 / 3,148 / 7,409 /
  17,476 / 40,232; provincial 233 / 5,495 / 14,058 / 35,302 / 81,511. A note
  wide enough to cover the largest disagreement would mark tens of thousands
  of addresses to cover a handful.

**Condition:** addresses where sources are known to disagree are flagged
individually, whatever their distance from a line, and the About page says the
school wards are the City's drawing of the boards' bylaws.
**Sharpest counter-argument:** the note tells a reader "you are near a line",
and a reader takes its absence to mean the answer is certain. At 17611
34 Street NW it is not.
**Would change it:** to SOUND, the flag above. To UNSOUND, a sweep of the
school-ward lines against the bylaw text finding hundreds of addresses on the
other side.

### L1. Each layer is the operative boundary — CONDITIONAL
- **Council wards.** The instrument is the City's ward bylaw (15142, as
  amended). Its text was not retrieved in this run (404 and 502 from the City's
  site), so this is unread. The outer-edge question of `docs/DATA_ISSUES.md`
  2026-10-21 stays open. No address is outside the wards: 0 rows fall outside
  the union, 5 / 33 / 791 / 3,452 are within 5 / 20 / 80 / 200 m of the outer edge.
- **Catholic school wards.** The instrument is ECSD Bylaw #2020-01,
  "Establishment of Wards" (three readings 2020-11-25, the layer's own
  effective date): https://www.ecsd.net/documents/ECSD-Bylaw-2020-01-Establishment-of-Wards.pdf.
  Schedule B describes wards 72 and 73 as running "south along 34 Street NW to
  the intersection with Manning Drive NW", then "southwesterly along Manning
  Drive NW", using road centre lines.
  - **15928 Manning Drive NW.** The parcel point is 184–217 m east of the
    Manning Drive centre lines and 171 m west of 34 Street NW, about 1 km south
    of where the two roads meet. By the text as read here that is the Ward 73
    side. The site says 72. The board's layer says 73 and runs 14–17 m from the
    Manning Drive centre lines; the City's line leaves the road there to take in
    this parcel. Why is not known.
  - **17611 34 Street NW.** The point sits at the junction, 19 m west of the
    nearer Manning Drive centre line. By the text it is on the Ward 72 side, as
    the site says, by a small margin that depends on how the junction is read.
    Not settled.
- **Public school wards.** The instrument is EPSB Bylaw No. 2020-2 (three
  readings 2020-09-08, per the approved minutes):
  https://www.epsb.ca/media/epsb/ourdistrict/boardoftrustees/boardmeetings/2020-21/september82020/05-BylawtoAmendtheTrusteeWardBoundaries.pdf.
  It puts the H/I line on Gateway Boulevard south of 23 Avenue NW.
  - **610 Calgary Trail NW.** The point is 167 m west of the Gateway Boulevard
    NW centre line. By the text that is the Ward H side. The site says I; the
    board's layer says H. Both layers' H/I lines run 125–182 m west of Gateway
    Boulevard along this stretch.
  - Three more addresses are in Ward I on **both** layers and west of both the
    Gateway Boulevard and Calgary Trail centre lines: 903 Gateway Boulevard NW,
    106 101 Street NW and 104 101 Street NW.
  - This reading depends on which physical road the bylaw's "Gateway Boulevard"
    means south of Ellerslie Road. It is a question for the board and the City,
    not a settled defect.
  - Whether either board amended its wards for the 2025 term was not found.
- **Provincial.** The 2017 map (in force 2019) is still the map sitting MLAs
  represent. The Select Special Committee reported on 2026-11-02 and its mandate
  ended (https://www.assembly.ab.ca/assembly-business/committees/CEB). The bill
  status report to 2026-11-05 (https://assembly.ab.ca/LAO/Bills/bsr31-2.pdf)
  lists no bill establishing new divisions; Bill 32 (SA 2026 c7) changes the
  commission's Act. A new map is coming and is not enacted.
- **Federal.** Sound. Elections Canada: the 2023 Representation Order districts
  "came into effect, for each province, with the issue of the writs of the 45th
  general election".

**Condition:** the boards or Edmonton Elections confirm which lines the 2025
vote used at the six addresses above, and the council bylaw is read.
**Sharpest counter-argument:** the legal boundary is the bylaw's words. The
site publishes a drawing of them by a third party, and at one address the
drawing and the words disagree as read here.
**Would change it:** the returning officer's answer; a board saying the City's
layer is its record; the council bylaw text.

### L2. The address as the unit, placed at the parcel point — CONDITIONAL
The parcel point is sound for an ordinary lot. A typed address that is not in
the City list gets "No address … on …" and no guess. Eight split addresses show
every district set. Unmeasured: parcels that lie across a district line with
their point on one side. 15928 Manning Drive NW may be one.

**Condition:** a parcel-polygon check shows the straddling parcels are few and listed.
**Sharpest counter-argument:** on a large parcel the point is a labelling
choice by the City, and the district answer inherits it without saying so.
**Would change it:** parcel polygons intersected with each layer's lines.

### L3. Processing preserves the source answer — SOUND
Addresses are assigned against the unclipped, full-resolution layers. The clip
to the council-ward union changes only the published riding outlines and the
map click. Check 2 compares every record with the published simplified files.
Publisher overlaps and gaps are kept and shown. An address in no district, or
in two, stops the build, so the clip cannot drop an address silently.

**Sharpest counter-argument:** a map click near the city's north edge uses the
clipped ridings, so it follows the 2026-10-19 edge that no other City layer follows.
**Would change it:** an address whose stored districts differ from the full-resolution answer.

### L4. The guards measure the right thing — CONDITIONAL
The guards prove the build agrees with itself and with its inputs. Not covered:

1. No guard compares a layer with its legal instrument or with the second
   publisher. The City-versus-board comparison was run by hand on 2026-10-17
   and again here.
2. `recheck_dates` in `staleness.json` is read by the About page, one test of
   its shape and one smoke test. Nothing compares a date with today. The
   2026-11-02 date passed; the About page still says the committee "is due to report".
3. New addresses pass a refresh without review (`docs/SPEC_data_schema.md`
   §9.6), including one beside a disputed line.
4. `effective_from` for the provincial and federal layers is typed in
   `src/build_boundaries.py`, not read from a source.

**Condition:** a repeatable source-against-source comparison, and a trigger on past recheck dates.
**Sharpest counter-argument:** every check is green on a layer that differs
from the bylaw, and stays green.
**Would change it:** a guard that fails when the set of addresses on which two
publishers differ changes.

### L5. The browser gives the build's answer — SOUND
A typed address uses the stored districts. Record points agree with the
published files by test. A share link to a missing address or an unknown
district says so. A click with no council ward says "outside the City of Edmonton".

**Sharpest counter-argument:** a click and a typed address can differ within
5 m of a line; the note covers that case.
**Would change it:** a stored district that the published file contradicts.

## Fixes, ranked (follow-ups; none applied)

1. **Ask Edmonton Elections and both boards** which lines the 2025 vote used at
   15928 Manning Drive NW, 17611 34 Street NW, 610 Calgary Trail NW, 903 Gateway
   Boulevard NW, 106 and 104 101 Street NW, quoting the bylaw text. The owner sends it.
2. **Flag disputed addresses individually**, independent of distance, with both
   lookups linked. A data-contract change: plan first.
3. **About page:** update the provincial paragraph and the passed recheck date;
   add a known limit on where the school-ward lines come from.
4. **A trigger for a past `recheck_dates` entry.** A CI change: the owner decides.
5. **A repeatable City-versus-board comparison** through every address, and a
   sweep of the rest of the school-ward lines against the bylaw text. A new
   module: plan first.
6. **Parcel-polygon straddle check**, one measurement.
7. **Read the council ward bylaw by hand** and record which outer edge it describes.
8. **Provincial:** confirm what the Assembly did with the committee's report,
   watch for the establishing bill, record which map applies to the next election.

Corrected in the same PR, in `data/DATA.md`: the bylaws are online (it said they
were not); 17611 34 Street NW is 63.8 m from the City's line, not 368 m; the
committee has reported.

## What this run got wrong

- **A wrong offset tool.** The first measurement used `project()` on a
  multi-part line and reported the address as 21,916 m from a road it sits
  beside. Replaced with nearest-point distances.
- **A false count of 792.** A ray-parity test against Gateway Boulevard flagged
  792 addresses as west of the road that are 220–1,100 m east of it, because
  ramps and paired carriageways break parity. Discarded. The three addresses
  reported above come from the replacement test and were not checked a third way.
- **A search summary nearly used as fact.** It dated a stage of Bill 32 to
  2026-11-03; the bill status report shows the bill passed in April and May.
  A reported Government Motion 45 on the committee's report is still unverified.
- **The council bylaw was never read.** The council-ward verdict rests on
  `data/DATA.md` and search results, not the instrument.
- **The brief inherited a wrong negative.** `data/DATA.md` said the school-ward
  bylaws were not online, and the brief and TODO repeated it. Both were found
  on the boards' own sites in one search each.
- **The bylaw reading is this run's own.** Road names were matched to the City's
  Road Network names, only the stretches near known disagreements were read, and
  no surveyor or board has confirmed the reading.
- **Older parcels than the published index**, and points instead of polygons.
- **Shipped in two parts.** This file was pushed alone when the session ran out
  of usage; the ledger, assumptions, TODO and data-doc changes followed in a
  later turn of the same PR.
