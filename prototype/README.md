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
