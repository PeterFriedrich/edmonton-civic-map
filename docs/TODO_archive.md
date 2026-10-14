# TODO — archive of CLOSED items

Closed work moved out of `TODO.md` so the file that is read at the start of **every** session carries only live work. **Nothing here is a to-do.**

`TODO.md`'s `## Done` section keeps a one-line entry for each of these, so the *never redo a closed item without asking* rule still works by grepping there; this file holds the reasoning behind each one.

Items are verbatim as they were closed, newest-moved first in the order they appeared in `TODO.md`. Line numbers and "next up" markers inside them are historical — do not act on them.

---

- [x] **Terrain: read the Edmonton window of MRDEM-30, check it, and pack it as elevation PMTiles.** Sources are in `data/DATA.md`, "Terrain and elevation"; nothing has been read yet. Done when the ledger records CRS, vertical datum, the elevation range across the city and the depth of the river valley as the data shows it, and `prototype/README.md` has the PMTiles size (the report estimates 3–10 MB; encode at 0.1 m steps, since 1 m steps look blocky). Then decide whether the 1 m federal lidar (`AB-Edmonton-1m`, 2.38 GB) resampled to about 5–10 m is worth it.

- [x] **Buildings, step 2: draw the tile files in MapLibre on a real phone** (the owner's; this server has no GPU). With one stack chosen this is a feasibility check, not a comparison. Record first-load time and frame rate, flat and tilted, faint-solid against translucent buildings. Done when the numbers are in `prototype/README.md`.

- [x] **Check that GitHub Pages serves a `.pmtiles` file by range request, uncompressed, from a test deploy.** `edmonton-tax-viz` recorded Pages answering range requests on 2026-08-07, but not for this file type. Done when a test deploy reads one tile.

- [x] **Buildings, step 1: one trial tippecanoe build of the rooflines to PMTiles, and record the size.** Turn the 384,228 polygons of `jpxi-a9a5` into PMTiles at z12–z15, height as the only attribute, and record bytes per zoom (`pmtiles show`). Replaces the report's 10–30 MB estimate. Lives in `prototype/`. Done when `prototype/README.md` has the sizes.

- [x] **Tile files: committed under `site/data/` or built at deploy.** Decided 2026-10-13: committed, each with a text manifest beside it, while each file is under 100 MB (`docs/DECISIONS.md`).

- [x] **Map: pick the stack.** Chosen 2026-10-13: MapLibre GL JS 6 native layers, PMTiles, Vite with plain JavaScript, per-street address index (`docs/DECISIONS.md`; `docs/SPEC_lenses.md` §8). The report is filed at `/home/opc/research/edmonton-civic-map/stack_reply_2026-10-13.md`.
