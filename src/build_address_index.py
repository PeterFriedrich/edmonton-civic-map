"""Build the per-street address index (docs/SPEC_data_schema.md §9).

For every City parcel address, the five districts at full resolution and a
near-edge bitmask, written as one file per street under site/public/data/addresses/
with streets.json and manifest.txt beside them. Runs after src.build_boundaries.

Before anything is written, two checks run every parcel row through
prototype/pip.js under node, a second implementation of the lookup:
1. against the full-resolution source layers: must match the stored districts;
2. against the published, simplified boundary files: every record's point must
   give its stored districts, so a click on an address agrees with typing it.
Either failing stops the build. So does a parcel row left unaccounted for.

    python -m src.build_address_index [--raw data/raw] [--out site/public/data]
"""
import argparse
import collections
import csv
import hashlib
import json
import logging
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

import numpy as np
import shapely
from pyproj import Transformer

from src import build_boundaries as bb

log = logging.getLogger("build_address_index")

REPO = Path(__file__).resolve().parents[1]
PIP_JS = REPO / "prototype" / "pip.js"
LAYERS = list(bb.LAYERS)  # record column order, as in layers.json
DECIMALS = 6  # ~0.1 m: a 5-decimal point (~1 m) could cross a line near an edge


def street_file(street):
    """'124 STREET NW' -> '124-street-nw.json'; 'MASKÊKOSIHK TRAIL NW' -> 'maskekosihk-trail-nw.json'."""
    s = "".join(c for c in unicodedata.normalize("NFKD", street) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") + ".json"


def read_parcels(raw):
    d = raw / "coe_parcels"
    fetch = json.loads((d / "fetch.json").read_text(encoding="utf-8"))
    with open(d / fetch["file"], newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    lon = np.array([float(r["longitude"]) for r in rows])
    lat = np.array([float(r["latitude"]) for r in rows])
    return rows, lon, lat, fetch


def assign_all(pts, layers):
    """{layer: district_id per point} and a near-edge bitmask per point, at full resolution."""
    dist = {}
    near = np.zeros(len(pts), int)
    for j, lid in enumerate(LAYERS):
        features = layers[lid]
        a = bb.assign(pts, features)
        none, many = int((a == "").sum()), int((a == "*").sum())
        if none or many:
            raise bb.BuildError(f"{lid}: {none} addresses in no district and {many} in more than one")
        dist[lid] = a
        for k, (_, g) in features.items():
            m = a == k
            if m.any():
                near[m] |= (shapely.distance(pts[m], shapely.boundary(g)) < bb.NEAR_BOUNDARY_M).astype(int) << j
    return dist, near


def build_records(rows, lon, lat, x, y, dist, near):
    """{street: {house: [record, ...]}}, one record per distinct district set; plus split addresses."""
    groups = collections.defaultdict(list)
    for i, r in enumerate(rows):
        groups[(r["street_name"], r["house_number"])].append(i)
    streets = collections.defaultdict(dict)
    split, accounted = [], 0
    for (street, house), ii in groups.items():
        sets = collections.defaultdict(list)
        for i in ii:
            sets[tuple(dist[lid][i] for lid in LAYERS)].append(i)
        recs = []
        for combo, members in sets.items():
            p = np.column_stack([x[members], y[members]])
            m = members[int(np.argmin(((p - p.mean(0)) ** 2).sum(1)))]  # a real point, nearest the centre
            mask = 0
            for i in members:
                mask |= int(near[i])
            recs.append([round(float(lat[m]), DECIMALS), round(float(lon[m]), DECIMALS), *combo, mask])
            accounted += len(members)
        recs.sort()
        streets[street][house] = recs
        if len(recs) > 1:
            split.append((street, house, len(ii), recs))
    if accounted != len(rows):
        raise bb.BuildError(f"{len(rows)} parcel rows in, {accounted} accounted for in the index")
    return streets, sorted(split)


def _node_locate(fc, lonlat):
    """Feature indices hit per point, by prototype/pip.js."""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "layer.geojson"
        p.write_text(json.dumps(fc), encoding="utf-8")
        text = "".join(f"{float(lo)!r},{float(la)!r}\n" for lo, la in lonlat)
        try:
            out = subprocess.run(["node", str(PIP_JS), str(p)], input=text, capture_output=True,
                                 text=True, check=True).stdout
        except FileNotFoundError as e:
            raise bb.BuildError("node not found: the pip.js cross-check cannot run") from e
    lines = out.split("\n")[:len(lonlat)]
    return [ln.split("|") if ln else [] for ln in lines]


def _ids(fc, hits):
    return ["" if not h else "*" if len(h) > 1 else fc["features"][int(h[0])]["properties"]["district_id"] for h in hits]


def check_full_resolution(layers, lon, lat, dist):
    """Check 1: pip.js on the unsimplified layers agrees with the build on every parcel row.
    Ridings are clipped to the city first: the same answer inside it, and 1.1 million
    federal vertices become about 14,000, which pip.js's plain scan can manage."""
    to_ll = Transformer.from_crs(bb.METRIC, "EPSG:4326", always_xy=True)
    city = shapely.union_all([g for _, g in layers["council_ward"].values()])
    for lid in LAYERS:
        features = bb.clip(layers[lid], city) if bb.LAYERS[lid].get("clip") else layers[lid]
        fc = {"type": "FeatureCollection", "features": [
            {"type": "Feature", "properties": {"district_id": k},
             "geometry": json.loads(shapely.to_geojson(bb._transform(g, to_ll)))}
            for k, (_, g) in sorted(features.items())]}
        got = np.array(_ids(fc, _node_locate(fc, list(zip(lon, lat)))), object)
        bad = int((got != dist[lid]).sum())
        if bad:
            raise bb.BuildError(f"{lid}: pip.js disagrees with the build on {bad} parcel rows at full resolution")
        log.info("check 1, %s: pip.js agrees on all %d parcel rows", lid, len(lon))


def check_published(streets, boundaries_dir):
    """Check 2: each record's stored point, through pip.js on the published files, gives its districts."""
    recs = [r for houses in streets.values() for rs in houses.values() for r in rs]
    lonlat = [(r[1], r[0]) for r in recs]
    for j, lid in enumerate(LAYERS):
        fc = json.loads((boundaries_dir / f"{lid}.geojson").read_text(encoding="utf-8"))
        got = _ids(fc, _node_locate(fc, lonlat))
        bad = [(r, g) for r, g in zip(recs, got) if r[2 + j] != g]
        if bad:
            raise bb.BuildError(f"{lid}: {len(bad)} records resolve differently on the published boundaries, "
                                f"e.g. {bad[:3]}; lower the boundary tolerance")
        log.info("check 2, %s: all %d records agree with the published boundaries", lid, len(recs))


def manifest(parcel_fetch, layer_fetches, rows, streets, split, dist, near, files):
    n_recs = sum(len(rs) for h in streets.values() for rs in h.values())
    lines = [
        "# site/public/data/addresses: built by src/build_address_index.py (docs/SPEC_data_schema.md §9)",
        "",
        "## Sources",
        f"coe_parcels  sha256 {parcel_fetch['sha256']}  retrieved {parcel_fetch['retrieved_at']}",
        *(f"{lid}  source {f['id']}  sha256 {f['sha256']}  retrieved {f['retrieved_at']}"
          for lid, f in layer_fetches.items()),
        "",
        "## Counts",
        f"parcel rows in: {len(rows)}",
        f"parcel rows accounted for: {len(rows)}",
        f"streets: {len(streets)}",
        f"addresses (house number + street): {sum(len(h) for h in streets.values())}",
        f"records: {n_recs}",
        f"split addresses: {len(split)}",
        "",
        "## Split addresses (rows in more than one district set; every set is kept)",
        *(f"{house} {street}  rows {n}  sets: " + " | ".join(" ".join(r[2:7]) for r in recs)
          for street, house, n, recs in split),
        "",
        "## Parcel rows within 20 m of an edge of their own district",
        *(f"{lid}: {int(((near >> j) & 1).sum())}" for j, lid in enumerate(LAYERS)),
        f"any layer: {int((near > 0).sum())}",
        "",
        "## Parcel rows per district",
    ]
    for lid in LAYERS:
        for k, n in sorted(collections.Counter(dist[lid]).items()):
            lines.append(f"{k}: {n}")
    h = hashlib.sha256()
    for name in sorted(files):
        h.update(name.encode() + b"\0" + files[name].encode() + b"\0")
    lines += ["", "## Street files", f"sha256 over all files, sorted by name: {h.hexdigest()}", ""]
    return "\n".join(lines)


def build(raw, out):
    rows, lon, lat, parcel_fetch = read_parcels(raw)
    x, y = Transformer.from_crs("EPSG:4326", bb.METRIC, always_xy=True).transform(lon, lat)
    pts = shapely.points(x, y)
    layers, fetches = {}, {}
    for lid in LAYERS:
        layers[lid], fetches[lid], _ = bb.read_layer(lid, raw)  # unclipped: a city edge is no district edge
    dist, near = assign_all(pts, layers)
    streets, split = build_records(rows, lon, lat, x, y, dist, near)
    log.info("%d parcel rows -> %d streets, %d split addresses", len(rows), len(streets), len(split))

    check_full_resolution(layers, lon, lat, dist)
    check_published(streets, out / "boundaries")

    files, index = {}, []
    for street in sorted(streets):
        name = street_file(street)
        houses = streets[street]
        files[name] = json.dumps({h: houses[h] for h in sorted(houses, key=lambda s: (len(s), s))},
                                 ensure_ascii=False, separators=(",", ":")) + "\n"
        index.append([street, name])
    if len({n for _, n in index}) != len(index):
        raise bb.BuildError("two streets map to the same file name")
    files["streets.json"] = json.dumps(index, ensure_ascii=False, separators=(",", ":")) + "\n"
    man = manifest(parcel_fetch, fetches, rows, streets, split, dist, near,
                   {k: v for k, v in files.items() if k != "streets.json"})

    # swap the whole folder, so a street that disappeared loses its file
    final = out / "addresses"
    partial = out / "addresses.partial"
    shutil.rmtree(partial, ignore_errors=True)
    partial.mkdir(parents=True)
    for name, text in files.items():
        (partial / name).write_text(text, encoding="utf-8")
    (partial / "manifest.txt").write_text(man, encoding="utf-8")
    shutil.rmtree(final, ignore_errors=True)
    partial.rename(final)
    log.info("wrote %d files to %s", len(files) + 1, final)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", type=Path, default=REPO / "data" / "raw")
    ap.add_argument("--out", type=Path, default=REPO / "site" / "public" / "data")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    try:
        build(args.raw, args.out)
    except bb.BuildError as e:
        log.error("FAILED: %s", e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
