"""Measure a build-time per-address district index (docs/SPEC_data_schema.md §9).

Assigns every City parcel address to its five districts at full resolution,
reports the addresses that sit on more than one parcel row and whether those
rows ever disagree, and sizes the proposed one-file-per-street index.
Not the build: nothing is written but a printed report.

Usage: python prototype/address_districts.py <dir>
<dir> holds parcels.csv, the three City layers as <id>.geojson, and the two
shapefile zips unpacked into ab/ and fed/ (see prototype/README.md).
"""
import collections
import csv
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import shapefile
import shapely
from pyproj import Transformer

d = Path(sys.argv[1])
METRIC = "EPSG:3776"  # NAD83 / Alberta 3TM 114W
NEAR_M = 20.0  # near_boundary_m in docs/SPEC_data_schema.md §3


def _to_metric(g, t):
    return shapely.transform(g, lambda c: np.column_stack(t.transform(c[:, 0], c[:, 1])))


def from_geojson(fn, key):
    t = Transformer.from_crs("EPSG:4326", METRIC, always_xy=True)
    return {str(f["properties"][key]): _to_metric(shapely.geometry.shape(f["geometry"]), t)
            for f in json.load(open(d / fn))["features"]}


def from_shp(path, key):
    t = Transformer.from_crs(path.with_suffix(".prj").read_text(), METRIC, always_xy=True)
    return {str(sr.record[key]): shapely.make_valid(_to_metric(shapely.geometry.shape(sr.shape.__geo_interface__), t))
            for sr in shapefile.Reader(str(path)).iterShapeRecords()}


layers = {
    "council_ward": from_geojson("b4er-5rp2.geojson", "name_1"),
    "public_school_ward": from_geojson("d7pj-rist.geojson", "name"),
    "catholic_school_ward": from_geojson("pwzf-sjj2.geojson", "name"),
    "provincial_riding": from_shp(next(d.glob("ab/*.shp")), "EDNumber20"),
    "federal_riding": from_shp(next(d.glob("fed/*/*.shp")), "ED_CF_NUM"),
}
names = list(layers)
rows = list(csv.DictReader(open(d / "parcels.csv")))
lon = np.array([float(r["longitude"]) for r in rows])
lat = np.array([float(r["latitude"]) for r in rows])
x, y = Transformer.from_crs("EPSG:4326", METRIC, always_xy=True).transform(lon, lat)
pts = shapely.points(x, y)
print("parcel rows", len(rows))

dist = {}
near = np.zeros((len(rows), len(names)), bool)
for j, (name, polys) in enumerate(layers.items()):
    keys = list(polys)
    pi, gi = shapely.STRtree([polys[k] for k in keys]).query(pts, predicate="intersects")
    hits = collections.defaultdict(list)
    for p, g in zip(pi, gi):
        hits[p].append(keys[g])
    n0 = len(rows) - len(hits)
    n2 = sum(1 for v in hits.values() if len(v) > 1)
    code = np.array([v[0] if len(v) == 1 else "" for v in (hits.get(i, []) for i in range(len(rows)))], object)
    dist[name] = code
    for k in keys:
        m = code == k
        if m.any():
            near[m, j] = shapely.distance(pts[m], shapely.boundary(polys[k])) < NEAR_M
    print(f"{name}: districts holding addresses {len(set(code) - {''})}, in none {n0}, "
          f"in more than one {n2}, within {NEAR_M:.0f} m of an edge {near[:, j].sum()}")
print("addresses within 20 m of an edge on any layer", near.any(1).sum())

groups = collections.defaultdict(list)
for i, r in enumerate(rows):
    groups[(r["street_name"], r["house_number"])].append(i)
dup = {k: v for k, v in groups.items() if len(v) > 1}
big = max(dup, key=lambda k: len(dup[k]))
print("distinct house number + street pairs", len(groups), "| on more than one row", len(dup),
      "| extra rows", sum(len(v) - 1 for v in dup.values()), "| largest", big, len(dup[big]))
spread = np.array([float(shapely.distance(p[:, None], p[None, :]).max())
                   for p in (shapely.points(x[v], y[v]) for v in dup.values())])
print("spread between rows of one pair, m: median %.1f, p90 %.1f, max %.1f; over 500 m %d" % (
    np.median(spread), np.percentile(spread, 90), spread.max(), (spread > 500).sum()))
split = {k: v for k, v in dup.items() if any(len(set(dist[n][v])) > 1 for n in names)}
print("pairs whose rows fall in different districts", len(split))
for k, v in sorted(split.items()):
    sets = collections.Counter(tuple(dist[n][i] for n in names) for i in v)
    print("  ", " ".join(reversed(k)), dict(sets))


def medoid(ii):
    p = np.column_stack([x[ii], y[ii]])
    return ii[int(np.argmin(((p - p.mean(0)) ** 2).sum(1)))]


# Proposed record: [lat, lon, five districts, near-edge bitmask]; one per distinct
# district set, its point the row nearest the group's centre.
streets = collections.defaultdict(dict)
for (st, hn), v in groups.items():
    sets = collections.defaultdict(list)
    for i in v:
        sets[tuple(dist[n][i] for n in names)].append(i)
    streets[st][hn] = [[round(lat[medoid(ii)], 5), round(lon[medoid(ii)], 5), *combo,
                        int(sum(1 << j for j in range(len(names)) if near[ii, j].any()))]
                       for combo, ii in sets.items()]
sz = sorted((len(gzip.compress(json.dumps(h, separators=(",", ":"), ensure_ascii=False).encode(), 9)), st)
            for st, h in streets.items())
sl = gzip.compress(json.dumps(sorted(streets), separators=(",", ":")).encode(), 9)
print("index: streets %d, records %d, total %.2f MB gzipped; per street median %d B, largest %d B (%s); "
      "street list %.1f kB gzipped" % (len(streets), sum(len(r) for s in streets.values() for r in s.values()),
                                       sum(s for s, _ in sz) / 1e6, sz[len(sz) // 2][0], sz[-1][0], sz[-1][1], len(sl) / 1e3))
