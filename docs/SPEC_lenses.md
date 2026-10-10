# SPEC — the map and its lenses: what each is for and what it needs

**Read when:** choosing the front-end stack, designing a lens, or briefing an
outside researcher on what the map has to do.

**Status: 2026-10-10.** Nothing here is built. It gathers the owner's
decisions from `docs/SPEC_civic_map.md` (amendments) and the measurements in
`data/DATA.md` into one place, written to stand alone. §7 is the research
request this document was written to support.

## 1. The product in one paragraph

Edmonton Civic Map is a public reference tool. A resident types an address or
clicks a map of Edmonton and sees who represents that spot at five levels:
City Council ward, public school ward, Catholic school ward, provincial riding
and federal riding. Each office holder appears as a card with name, role,
official contact link, source and the date it was last verified. On top of
that base, optional "lenses" add context about the boundary lines themselves.
It describes; it never scores, ranks or evaluates officials.

Audience: residents, journalists, community groups, students. Most use is a
quick lookup on a phone.

## 2. Fixed constraints

Any stack has to fit these. All are decided (`docs/DECISIONS.md`) except the
last row, which is the owner's stated preference and not yet a locked decision.

| Constraint | What it means for the stack |
|---|---|
| Static site on GitHub Pages, no backend of ours | Everything is files. No server-side rendering at request time, no database, no API we operate. |
| An address never leaves the browser | Address search and point-in-polygon run client-side against data we ship. No third-party geocoder, and no map service that receives the typed address. |
| Data refreshed weekly by GitHub Actions | The build must run unattended in CI and produce the published files, including any map tiles. |
| Every record shows its source and last-verified date | Data files carry provenance; the UI shows a staleness warning by comparing dates in the browser. |
| Mobile-first | The lookup must work on a mid-range phone on a mobile connection. |
| The lookup works without the heavy layers | Buildings and terrain are an addition. A slow device still gets its answer. |
| A different stack from `edmonton-tax-viz` | That project is a single hand-written HTML page, no framework and no build step, using MapLibre GL JS 4.7 for the base map and deck.gl 9.0 for 3D layers. Trying something else is a goal of this project. |
| Free to run | No usage-billed services or paid API keys. Open-source libraries and free static hosting. |

## 3. The base view

**Use.** The default view: rough geography of the city with "ghost buildings",
meaning buildings drawn faint and translucent as context, with boundary lines
on top. The reader searches an address or clicks; the map marks the spot and
the cards appear. They can also pick a ward from a list without touching the
map.

**What it needs.**

- **Boundary layers**, five of them, as polygons with a visible outline and a
  highlight for the selected district:

  | Layer | Features | Notes |
  |---|---|---|
  | Council wards | 12 | 14,892 vertices at full resolution; 28 kB gzipped when simplified to 5 m, with no address changing ward |
  | Public school wards | 9 | 9,358 vertices |
  | Catholic school wards | 7 | 10,691 vertices |
  | Provincial ridings | 20 in the city, plus neighbours at the edge | change pending after a legislature committee reports in November 2026 |
  | Federal ridings | 9 in the city, plus neighbours at the edge | |

  Ward names include Cree, Blackfoot and other Indigenous-language names with
  diacritics (pihêsiwin, Ipiihkoohkanipiaohtsi), and two are also published in
  syllabics (ᐱᐦᐁᓯᐏᐣ). Labels must render them correctly.

- **Address search in the browser.** 288,315 distinct addresses across 2,800
  street names, about 2.2 MB gzipped as a compact index. Needs type-ahead that
  tolerates how people write Edmonton addresses ("10220 104 Ave", "104 Avenue
  NW") without sending keystrokes anywhere.

- **Point-in-polygon in the browser** across all five layers, with a
  "near a boundary, check the official lookup" note within about 20 m of a
  line. Proven for wards: a plain JavaScript implementation agrees with a
  reference library on all 298,238 City parcel addresses (`prototype/README.md`).

- **Buildings.** The City's roofline layer has 384,228 building polygons with
  a height each (mean 5.7 m, tallest 146.8 m, 597 over 20 m). It dates from
  2019. Far too large to ship as one file, so this is tiles or heavy
  simplification.

- **Terrain.** Edmonton's defining feature is the North Saskatchewan river
  valley. No ready terrain source has been found yet. "Rough geography" may
  mean real elevation or may mean the river, valley edge and major roads drawn
  flat; that is open.

- **2D and 3D.** A flat view and a tilted view of the same map, switchable.

**The detail phase.** How much building and terrain detail the site can carry
is to be found by experiment: add detail in steps and measure published size
against the host's limits, first-load time, and frame rate on a mid-range
phone. A stack that makes those steps easy to take and measure is worth more
than one that looks best at full detail.

## 4. The lenses

A lens is an optional view the reader turns on. All are **off by default**.
All follow one rule: a lens shows geometry and published facts and leaves the
judgement to the reader. It never says a line is good or bad.

### 4.1 Affiliation

- **Use.** Shows party or caucus on MLA and MP cards only, from each body's own
  member list. Council and trustee cards never show one.
- **Needs.** No map work. A display toggle on the cards. It does not colour
  the map.

### 4.2 Communities of interest

- **Question it answers.** Does a boundary line run through a neighbourhood or
  community league area?
- **Use.** The reader turns it on and sees neighbourhood outlines under the
  boundary lines, with the neighbourhoods a line divides picked out. Selecting
  one states the fact: "addresses in this neighbourhood fall in two ridings".
- **Data.** 407 neighbourhood polygons from the City. Community league
  boundaries are not on the City's portal; a source is still to be found.
- **Measured.** Counting a neighbourhood as divided when at least 10 addresses
  sit on each side of a line: council wards divide 2 of 407, public school
  wards 0, Catholic school wards 2, provincial ridings 13, federal ridings 8.
  The 10-address floor is a first guess.
- **Needs.** A second polygon layer under the boundaries; styling driven by a
  precomputed "divided by layer X" flag per neighbourhood; a way to show which
  boundary layer is being compared.

### 4.3 Physical and natural boundaries

- **Question it answers.** Does a boundary line follow barriers residents
  recognise?
- **Use.** The reader turns it on and the river valley, arterial roads,
  highways and rail lines are drawn prominently, so it is visible where a
  boundary runs along one and where it does not.
- **Data.** The City's road network has 53,873 segments with a functional
  class; about 8,900 are arterials, including primary highways. No ready layer
  has been found for the river valley edge or rail lines.
- **Needs.** Line layers filtered by class; strong visual separation between
  "barrier" lines and "boundary" lines, which will often coincide; possibly
  terrain, since the river valley reads best as relief.

### 4.4 Population density

- **Question it answers.** Where do people live, and how do the ward lines sit
  over that?
- **Use.** A population density map of the city. Ward boundaries are an
  overlay the reader can add to compare roughly by eye. **No number is attached
  to a ward** and wards are not ranked.
- **Data.** 2021 Census population for 278 neighbourhoods, and neighbourhood
  areas. Finer census geography has not been looked at yet.
- **Open.** Whether density is shown flat (shaded areas) or in 3D (height).
  The owner wants to see examples of both before deciding. A later part of
  this lens is growth: where population is forecast to go, starting from how
  the City itself forecasts. No forecast dataset has been found yet.
- **Needs.** A choropleth at least; possibly extruded areas or a density
  surface; a legend that stays honest about the census year.

## 5. What every lens shares

Proposed, not yet confirmed by the owner:

- Layers switch on and off without reloading, and a lens can combine a base
  layer, an extra data layer and a boundary overlay.
- The selected address or district stays selected when a lens changes.
- Each lens has its own legend and its own source and date line.
- The state of the view (place, lens, 2D or 3D) should be shareable as a link,
  **without** the address in it unless the reader chooses that.
- Keyboard and screen-reader users must be able to do the lookup and read the
  cards without the map.

## 6. What is open

1. **The stack**: rendering library, how tiles are made and hosted on a static
   site, whether there is a framework and build step, and how address search
   is done.
2. **Terrain**: real elevation or a flat drawing of the river valley.
3. **Buildings**: tiles or simplification, and how current the source needs to
   be given the City's layer is from 2019.
4. **Density in 2D or 3D.**
5. **Sources still missing**: community league boundaries, river valley edge,
   rail lines, terrain, population forecasts.

## 7. Research request

For an outside researcher. Please produce a report the owner can use to pick a
stack and to go and look at working examples.

**A. Candidate stacks.** Three to five realistic options for this map, each a
complete combination: rendering library, tile format and how tiles are built
and served from static hosting, front-end framework and build tooling if any,
and in-browser address search. Exclude the combination in §2 that
`edmonton-tax-viz` already uses, though a stack may share one component with
it if you say why. For each:

- how it handles each item in §3 and each lens in §4, noting anything it
  cannot do or does awkwardly;
- 3D buildings and terrain on a mid-range phone: what is known about
  performance, with sources;
- fit with §2: static hosting only, no address leaving the browser, builds
  unattended in GitHub Actions, free to run;
- published size limits that matter (GitHub Pages site and file size, and
  alternatives such as Cloudflare Pages if tiles outgrow it);
- maturity, licence, how actively it is maintained, and how much of it one
  person can reasonably learn and own.

**B. Example projects to look at.** For each stack, two or three live public
sites the owner can open, preferably civic or electoral maps, with what to
notice in each: how it does address lookup, layer switching, ghost or
translucent buildings, terrain, and density in 2D and in 3D. Include good
examples of population density maps of both kinds even if they use a stack you
do not recommend, since the owner wants to compare 2D and 3D before deciding.

**C. Specific questions.**

1. What is the smallest practical way to serve 384,228 building footprints
   with heights from static hosting, and what did comparable projects end up
   shipping?
2. What open terrain data covers Edmonton at a useful resolution, under what
   licence, and how is it packaged for the web?
3. How do comparable sites do address type-ahead entirely in the browser at
   this scale?
4. Is there prior work on showing where electoral boundaries divide
   neighbourhoods or follow physical barriers, and how was it presented without
   editorialising?

**D. What not to recommend.** Anything that needs a server we run, a paid or
usage-billed map or geocoding service, sending addresses to a third party, or
scoring of officials or boundaries. `docs/SCOPE.md` lists what has already been
turned down.

Say plainly where a claim is from documentation, from a benchmark, or from your
own judgement, and give links. End with the reply format in `docs/BRIEF.md`.
