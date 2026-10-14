# Prototype — client-side point-in-polygon (wards only)

Brief §10 task 3 (`docs/SPEC_civic_map.md`). Not the app and not the pipeline:
a proof that the lookup can run in the browser with no address leaving it.

- `pip.js` — `locate(lon, lat, featureCollection)` and
  `distanceToBoundary(...)`. Pure functions: no network, no storage, no logging.
- `check_pip.py` — runs `pip.js` under node against every City parcel address
  and compares it with shapely, at full resolution and at each simplification
  tolerance.

## Result (2026-10-10)

Inputs: ward layer `b4er-5rp2` (12 wards, 14,892 vertices, 600 kB) and the
298,238 `PARCEL` rows of `ut27-nrpn`, both retrieved 2026-10-10.

- `pip.js` and shapely agree on **all 298,238 addresses** at full resolution.
  Every address falls in exactly one ward.
- Simplification is topology-preserving (`shapely.coverage_simplify`), so wards
  still share edges afterwards and no gaps or overlaps open between them.

| Tolerance | Vertices | Size | Gzipped | Addresses that change ward |
|---|---|---|---|---|
| 1 m | 7,259 | 174.0 kB | 44.5 kB | 0 |
| 2 m | 6,041 | 145.0 kB | 37.3 kB | 0 |
| 5 m | 4,659 | 112.2 kB | 28.4 kB | 0 |
| 10 m | 3,631 | 87.7 kB | 21.9 kB | 0 |
| 25 m | 2,216 | 54.0 kB | 12.7 kB | 3 |
| 50 m | 1,482 | 36.6 kB | 8.6 kB | 21 (2 land in no ward) |

**Proposed: 5 m.** No address changes ward, with a factor of two in hand before
the first error appears, and the layer is 28 kB over the wire.

"Addresses" means the City's address points. A map click is an arbitrary
point, so a click within the tolerance of a boundary can still resolve to the
wrong side. That is what the near-boundary note is for: 91 addresses lie within
10 m of a ward boundary and 533 within 20 m.

## Re-running

```bash
# inputs (not committed)
curl -o wards.geojson 'https://data.edmonton.ca/resource/b4er-5rp2.geojson'
# parcels: page ut27-nrpn 50,000 rows at a time, object_type='PARCEL',
# columns latitude, longitude (see data/DATA.md for the paging quirk)

pip install 'shapely>=2.1' pyproj numpy
python prototype/check_pip.py --wards wards.geojson --addresses 'parcels*.csv'
```

# Trial building tiles (2026-10-14)

`TODO.md` "Buildings, step 1". A size measurement, not a published layer.

Input: all 384,228 rooflines of `jpxi-a9a5`, retrieved 2026-10-14 (count matches
`count(*)`). Every row has a height and an outline; 325 outlines are
self-intersecting and were tiled as published, not repaired or dropped.
Height (`h`, metres, one decimal) is the only attribute.

| Zoom | Tiles | Size | Largest tile | Mean tile |
|---|---|---|---|---|
| z12 | 36 | 4.64 MB | 463.4 kB | 128.8 kB |
| z13 | 117 | 5.90 MB | 172.6 kB | 50.4 kB |
| z14 | 417 | 7.29 MB | 70.7 kB | 17.5 kB |
| z15 | 1,385 | 8.96 MB | 25.3 kB | 6.5 kB |
| **File** | 1,955 | **26.8 MB** | | |

Sizes are gzipped, as stored and as sent. Build time 21 s on this server.

- The file is **26.8 MB**, inside the stack report's 10–30 MB estimate and
  under git's 100 MB limit, which the tile-files decision depends on.
- tippecanoe's default 500 kB tile cap was never reached: a build with
  `--drop-smallest-as-needed` and a build with no cap are the same size. The
  busiest z12 tile is 463 kB, so there is little room at z12 for a second
  attribute.
- tippecanoe replaces polygons too small to draw with a placeholder: 2,541 at
  z12, 275 at z13, 230 at z14, 153 at z15. Nothing else is dropped.
- Not measured here: drawing speed. That is step 2, on a real phone.

## Re-running

```bash
python3.12 -m venv venv && venv/bin/pip install tippecanoe==2.72.0 'shapely>=2.1' numpy pmtiles
venv/bin/python prototype/rooflines.py work/          # download + check, ~220 MB
venv/bin/tippecanoe -P -f -o work/buildings.pmtiles -l buildings -Z12 -z15 \
    --no-feature-limit --no-tile-size-limit work/heights.ndjson
```

The PyPI `tippecanoe` wheel carries an aarch64 binary (2.72.0, 2024-12-10;
upstream is at 2.79.0), so nothing needs compiling on this server. Per-zoom
sizes come from summing tile lengths with the `pmtiles` Python reader;
`pmtiles show` (go-pmtiles 1.31.2) gives only the totals.

# GitHub Pages and range requests (2026-10-14)

`TODO.md` "Check that GitHub Pages serves a `.pmtiles` file by range request".
Checked against the live test page, https://peterfriedrich.github.io/edmonton-civic-map/,
deployed by `.github/workflows/pages.yml` (run 38508834542).

- **A browser gets what PMTiles needs.** The page's own check, run on the
  owner's phone, got `206` with no `content-encoding`, and the buildings drew.
- **That depends on the browser, not on Pages.** Pages serves the file as
  `application/octet-stream` and compresses it on the fly for any client that
  accepts gzip. Asked for a range with `Accept-Encoding: gzip`, it answers
  `206` with ranges of the *gzipped* stream (`content-range: .../26793940`
  against the file's 26,800,417 bytes), which a PMTiles reader cannot use.
  Asked with no `Accept-Encoding` or with `identity`, it answers ranges of the
  real file. Browsers send `identity` on any request that carries a `Range`
  header (Fetch standard), which is why the page works.
- So: test with a browser, or with curl and no `Accept-Encoding`. A curl run
  with `--compressed` or a gzip header will look broken when it is not.
- Pages sends `cache-control: max-age=600` and a weak `etag` on the file. The
  PMTiles reader ignores weak etags, so a rebuilt file within those 10 minutes
  is not caught by etag.

# Buildings on a real phone (2026-10-14)

`TODO.md` "Buildings, step 2". The owner's iPhone 14 Plus in Safari, on
the live test page, all 384,228 buildings, opening view z14 over
downtown.

| Reading | Result |
|---|---|
| First full draw, private window (nothing cached) | 1.25 s after the page started |
| Tile bytes for that view | 0.21 MB in 8 requests |
| Code over the wire (HTML, MapLibre, worker, CSS, PMTiles reader, gzipped) | 457 kB |
| Frame rate, tilted 60°, solid | 60 fps average, slowest 5% of frames under 17 ms |
| Frame rate, tilted 60°, translucent (opacity 0.35) | 60 fps average, slowest 5% of frames under 17 ms |

- 60 fps with no slow frames is the screen's refresh rate: in the heaviest
  modes the buildings cost nothing visible on this phone. Flat modes draw less
  and were not measured.
- A first visit to this view moves about 0.67 MB in all.
- One phone, one view. A low-end phone and the densest z12 tiles (463 kB) are
  untested.
- The repeat-visit readings (0.22 s, "0.00 MB in 30 requests") came from the
  browser cache: Resource Timing reports cached responses as 0 bytes.

# Trial terrain tiles (2026-10-14)

`TODO.md` "Terrain". The Edmonton window of the federal MRDEM-30 bare-ground
model, packed as elevation tiles. A size measurement, not a published layer.
What the heights say (CRS, datum, range, valley depth) is in `data/DATA.md`,
"Terrain and elevation".

256 px PNG tiles in Mapbox Terrain-RGB encoding at 0.1 m steps, covering the
city's bounding box, resampled bilinear from the 30 m grid. z12 is 22.7 m a
pixel at Edmonton's latitude, the nearest zoom to the source.

| Zoom | Tiles | Size |
|---|---|---|
| z9 | 1 | 66 kB |
| z10 | 4 | 230 kB |
| z11 | 12 | 583 kB |
| z12 | 48 | 1.81 MB |
| **File** | 65 | **2.69 MB** |

- Below the stack report's 3–10 MB estimate. PNG is already compressed, so
  this is also roughly what goes over the wire.
- Encoding and decoding every tile gives back the resampled heights to within
  0.05 m, half a step.
- MapLibre draws terrain past z12 by stretching z12 tiles, so the 30 m source
  sets the detail at every zoom. Whether that looks good enough beside the
  buildings, or the 1 m federal lidar resampled to 5–10 m is worth its size,
  is a visual call not made here.
- Not drawn yet: nothing here has been rendered.

```bash
venv/bin/pip install rasterio pillow 'shapely>=2.1' pmtiles
curl -o wards.geojson 'https://data.edmonton.ca/resource/b4er-5rp2.geojson'
venv/bin/python prototype/terrain.py wards.geojson work/   # 15 s, reads ~15 MB
```

# Buildings at z10 and z11 (2026-10-14)

The first build started at z12, so buildings vanished when the map was zoomed
out, and in tilted views the far distance (drawn from lower-zoom tiles) had
none. The build now starts at z10, and each zoom below 13 draws only
footprints above a size (`MIN_AREA` in `prototype/rooflines.py`):

| Zoom | Footprints drawn | Buildings in tiles* | Size | Largest tile |
|---|---|---|---|---|
| z10 | ≥ 400 m² (4%) | 16,777 | 0.22 MB | 83 kB |
| z11 | ≥ 150 m² (37%) | 149,588 | 1.65 MB | 454 kB |
| z12 | ≥ 50 m² (82%) | 335,999 | 3.99 MB | 402 kB |
| z13–z15 | all | | 22.16 MB | 173 kB |
| **File** | | | **28.0 MB** | |

\* Counted per tile, so a building crossing a tile edge counts twice.

- The cut-offs keep the busiest z10–z12 tiles at or under the z12 tile
  (463 kB) the iPhone test drew at 60 fps.
- Tried and not taken: z10 ≥ 200 m² and z11 ≥ 50 m² (3.7 MB more, busiest
  z11 tile 989 kB).
- Holding back buildings under 50 m² from z12 saved 0.65 MB, less than z10
  and z11 add, so the file is 1.2 MB larger than the z12–z15 build. Half of
  all footprints are under 123 m²; most under 50 m² are also under 4 m tall,
  which fits sheds and garages. That reading comes from size and height; the
  data has no building type.

# Terrain on a real phone (2026-10-14)

`TODO.md` "Terrain, step 2". The live test page with `terrain.pmtiles` as
hillshade and as 3D ground, buildings seated on it.

| Device | View | Frame rate |
|---|---|---|
| iPhone 14 Plus, Safari | flat, solid, 3D ground | 60 fps, slowest 5% under 17 ms |
| iPhone 14 Plus, Safari | tilted, solid, 3D ground | 60 fps, slowest 5% under 17 ms |
| Owner's laptop, 144 Hz screen | flat, solid, 3D ground | 144 fps, slowest 5% under 7 ms |
| Owner's laptop, 144 Hz screen | tilted, solid, 3D ground | 133 fps, slowest 5% under 14 ms |

- Tilted with 3D ground is the first mode below the screen's refresh rate,
  and only on the laptop; the phone held 60.
- Not measured: tilted, translucent, with 3D ground.
- **The owner judged 30 m terrain "plenty"**, so the 1 m federal lidar is not
  needed (`docs/DECISIONS.md`, 2026-10-14).
