# SPEC — the map and its lenses: what each is for and what it needs

**Read when:** choosing the front-end stack, designing a lens, or briefing an
outside researcher on what the map has to do.

**Status: 2026-10-13.** Nothing here is built. The stack is chosen (§8); §7 is kept as the request that was sent. It gathers the owner's
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

Any stack has to fit these. The "Status" column says which are locked rows in
`docs/DECISIONS.md` and which are not.

| Constraint | What it means for the stack | Status |
|---|---|---|
| Static site on GitHub Pages, no backend of ours | Everything is files. No server-side rendering at request time, no database, no API we operate. | Locked |
| An address never leaves the browser | Address search and point-in-polygon run client-side against data we ship. | Locked |
| Self-contained on GitHub Pages, for now | The page makes no request to an outside service: no hosted basemap or tile provider, no font or script CDN, no geocoder. Any basemap, tiles, fonts and libraries are files in the site, inside the Pages limits (about 1 GB per site, a soft 100 GB a month, a 10-minute deploy). The 100 MB per-file limit is git's, so it applies only to files committed to the repo. | Locked 2026-10-13, "for now" |
| Data refreshed weekly by GitHub Actions | The build must run unattended in CI and produce the published files. A change in any of them is held for the owner's review, not published automatically. Map tiles are rebuilt only when their source changes. Tile files are committed like the other published files, each with a text manifest beside it. | Locked |
| Every record shows its source and last-verified date | Data files carry provenance; the UI shows a staleness warning by comparing dates in the browser. | Locked |
| The answer comes before the map | Most visitors look up their own address or neighbourhood. The cards must appear without waiting for the map, buildings or terrain, and a slow device still gets its answer. | Owner, 2026-10-10 and 2026-10-13 |
| Works on phone and desktop | Neither comes first. The owner expects the phone work to be mostly interface (layout, touch, the cards and the map sharing a small screen) more than raw performance. Phone performance is still measured for the 3D layers in the detail phase. | Locked 2026-10-13 |
| A different stack from `edmonton-tax-viz`, where a sound alternative exists | That project is a single hand-written HTML page, no framework, no build step and no tiles. It uses MapLibre GL JS 4.7 as the map canvas and camera, with no basemap, and deck.gl 9.0 for its layers, fed by whole GeoJSON files. Trying something else is a goal of this project, but not at the cost of a weak or unsuitable library: if the alternatives to MapLibre or deck.gl are not robust or do not fit, reusing either is acceptable and the difference can come from the rest of the stack. | Locked 2026-10-13 |
| Free to run | No usage-billed services or paid API keys. Open-source libraries and free static hosting. | Follows from the self-contained row |

## 3. The base view

**Use.** The default view: rough geography of the city with "ghost buildings",
meaning buildings drawn faint and translucent as context, with boundary lines
on top. The reader searches an address or clicks; the map marks the spot and
the cards appear. They can also type a neighbourhood name, or pick a ward from
a list, without touching the map.

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

- **Neighbourhood search.** 407 neighbourhood names, a few kB, so it works
  before the address index has loaded. A neighbourhood that a boundary line
  divides (§4.2: 13 for provincial ridings, 8 federal, 2 council, 2 Catholic
  school) shows each district it touches and asks for an address.

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
  class; about 8,900 are arterials, including primary highways. Highways and
  arterials come from this City feed, not OpenStreetMap (decided 2026-10-15).
  No ready layer
  has been found for the river valley edge or rail lines.
- **Needs.** Line layers filtered by class; strong visual separation between
  "barrier" lines and "boundary" lines, which will often coincide; possibly
  terrain, since the river valley reads best as relief.

### 4.4 Population density

- **Question it answers.** Where do people live, and how do the ward lines sit
  over that?
- **Use.** A population density map of the city. Ward boundaries are an
  overlay the reader can add to compare roughly by eye. **No number is attached
  to a ward in this lens** and wards are not ranked. (The lookup still shows a
  ward's population beside any ward-level figure, as the brief requires.)
- **Data.** 2021 Census population for 278 neighbourhoods, and neighbourhood
  areas. The City's neighbourhood layer has 407 polygons, residential and
  industrial; the two have not been joined yet, so which of the other 129 have
  no residents and which are missing a census row is not known. Finer census
  geography has not been looked at yet.
- **Open.** Whether density is shown flat (shaded areas) or in 3D (height).
  Showing density as height is currently ruled out by the locked decision that
  3D never encodes a quantity (`docs/DECISIONS.md`). That decision stands until
  the owner has seen examples of both, and would have to be reopened first. A
  later part of
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

1. ~~The stack~~ Chosen 2026-10-13: §8.
2. **Terrain**: real elevation or a flat drawing of the river valley.
3. **Buildings**: tiles or simplification, and how current the source needs to
   be given the City's layer is from 2019. Tile files are committed with a
   text manifest beside each, which carries the readable diff (decided
   2026-10-13).
4. **Density in 2D or 3D.**
5. **The basemap**: none (boundaries, river, major roads and ghost buildings
   drawn from our own files, as `edmonton-tax-viz` does) or a street basemap
   served as a tile file from the site. A hosted provider is out for now (§2).
6. **Sources still missing**: community league boundaries, river valley edge,
   rail lines, terrain, population forecasts.

## 7. Research request

For an outside researcher. Please produce a report the owner can use to pick a
stack and to go and look at working examples.

**A. Candidate stacks.** Three to five realistic options for this map, each a
complete combination: rendering library, tile format and how tiles are built
and served from static hosting, front-end framework and build tooling if any,
and in-browser address search. Exclude the combination in §2 that
`edmonton-tax-viz` already uses. Say plainly whether robust, maintained
alternatives to MapLibre GL JS and to deck.gl exist for this job; if they do
not, say so and recommend a stack that reuses one of them and differs
elsewhere. For each:

- how it handles each item in §3 and each lens in §4, noting anything it
  cannot do or does awkwardly;
- 3D buildings and terrain on a mid-range phone: what is known about
  performance, with sources;
- fit with §2: static hosting only, no request to any outside service, builds
  unattended in GitHub Actions, free to run;
- time to the answer on a mid-range phone: what must download before an
  address or neighbourhood lookup returns its cards, and what can wait;
- published size against the GitHub Pages limits in §2, and what would have
  to move elsewhere if tiles outgrow them;
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
   this scale, and can a 2.2 MB index be split so a search fetches only a
   small part of it?
4. Is there prior work on showing where electoral boundaries divide
   neighbourhoods or follow physical barriers, and how was it presented without
   editorialising?

5. No basemap, or a street basemap served as one tile file from GitHub Pages:
   which gets a phone to a usable map sooner, and what does each cost in
   published size?

**D. What not to recommend.** Anything that needs a server we run, a hosted map,
tile, font or geocoding service, sending addresses to a third party, or
scoring of officials or boundaries. `docs/BRIEF.md`, "Out of scope", lists what
has already been turned down.

Say plainly where a claim is from documentation, from a benchmark, or from your
own judgement, and give links. End with the reply format in `docs/BRIEF.md`.

## 8. The stack (chosen 2026-10-13)

From the report at `/home/opc/research/edmonton-civic-map/stack_reply_2026-10-13.md`
(Claude web, 2026-10-13). Library versions were checked against the npm
registry the same day: `maplibre-gl` 6.14.0, `pmtiles` 4.5.0, `vite` 8.3.4.

| Part | Choice | Why |
|---|---|---|
| Rendering | MapLibre GL JS 6, its own layers only: `fill`, `line`, `fill-extrusion`, `hillshade`, terrain | One engine does flat and tilted views, buildings and relief. deck.gl is not needed. |
| Tiles | PMTiles files built with tippecanoe (vector) and GDAL (elevation), read in the browser through the `pmtiles` protocol | One file per layer, read in pieces from static hosting. |
| Build | Vite, plain JavaScript modules, no framework | Bundles the libraries into the site, fingerprints files, and lets the cards load before the map. |
| Address search | A static index: the street list loads with the page, then one small file per street | Fastest lookup; the owner's choice over mixed buckets. |
| Basemap | None. Our own river, roads and ghost buildings, with shading from the elevation file | Decided in §2 and §6. |
| Labels | Glyph files built by us from Noto Sans and Noto Sans Canadian Aboriginal | Ward names in syllabics must render with no outside font service. |

**Recommended by the report, not yet decided:**

- Work out all five districts and the near-boundary flag for every address at
  build time and store them in the index, so an address lookup needs no
  geometry and no map. Point-in-polygon stays for map clicks. This changes the
  published data, so it is proposed before it is built.
- Keep the view's state in our own URL parameters. MapLibre's built-in `hash`
  option writes the camera position, which after an address search is the
  address's location.
- ~~Tile files built at deploy.~~ Decided 2026-10-13 the other way: tile
  files are committed, and the report's manifest idea is kept beside them.

**Corrections to the report:** the river is a provincial layer, not City data,
and no river valley edge is sourced (`data/DATA.md`). Its size figures
(buildings 10–30 MB, terrain 3–10 MB) are estimates the detail phase replaces
with measurements.
