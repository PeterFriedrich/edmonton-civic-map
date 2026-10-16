"""Build the published boundary files from data/raw (docs/SPEC_data_schema.md §3).

Reads the five downloaded layers, clips the provincial and federal ridings to
the city (the union of the council wards; no City boundary file is sourced),
simplifies each layer as a coverage so neighbours keep shared edges, and
writes site/public/data/boundaries/<layer>.geojson and site/public/data/layers.json.

Stops, writing nothing, if any parcel address changes district between the
full-resolution source and the published file, or falls in no district or in
more than one. A failure means the tolerance comes down, never that the check
loosens. Publisher overlaps and gaps are kept as published and their areas
recorded (docs/DATA_ISSUES.md).

    python -m src.build_boundaries [--raw data/raw] [--out site/public/data]
"""
import argparse
import csv
import itertools
import json
import logging
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import shapefile
import shapely
from pyproj import Transformer

log = logging.getLogger("build_boundaries")

REPO = Path(__file__).resolve().parents[1]
METRIC = "EPSG:3776"  # NAD83 / Alberta 3TM 114W
TOLERANCE_M = 5.0  # no address changed district even at 10 m on any layer (2026-10-15)
NEAR_BOUNDARY_M = 20.0
DECIMALS = 6  # ~0.1 m in latitude; well under the tolerance

LAYERS = {
    "council_ward": {
        "label": "City Council ward", "body": "edmonton_council", "source_id": "coe_wards",
        "key": "name_1", "name": "name_1", "effective_from_field": "effective_start_date",
        "expected": 12,
    },
    "public_school_ward": {
        "label": "Edmonton Public Schools ward", "body": "edmonton_public_schools", "source_id": "coe_public_school_wards",
        "key": "name", "name": "descriptive_name", "effective_from_field": "effective_start_date",
        "expected": 9,
    },
    "catholic_school_ward": {
        "label": "Edmonton Catholic Schools ward", "body": "edmonton_catholic_schools", "source_id": "coe_catholic_school_wards",
        "key": "name", "name": "descriptive_name", "effective_from_field": "effective_start_date",
        "expected": 7,
    },
    "provincial_riding": {
        "label": "Provincial electoral division", "body": "legislative_assembly_of_alberta", "source_id": "ab_ridings",
        "key": "EDNUMBER", "name": "EDNAME", "effective_from": "2019-03-19",  # in force (data/DATA.md)
        "clip": True, "must_include": ("Edmonton-", 20),
    },
    "federal_riding": {
        "label": "Federal electoral district", "body": "house_of_commons", "source_id": "fed_ridings",
        "key": "ED_CF_NUM", "name": "ED_NAMEE", "effective_from": "2025-04-28",  # first general election on this map
        "clip": True, "must_include": ("Edmonton ", 9),
    },
}


class BuildError(Exception):
    pass


def slug(s):
    """district_id suffix: 'O-day'min' -> 'odaymin', 'pihêsiwin' -> 'pihesiwin', '71' -> '71'."""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _keep_case(s):
    """Codes like 'A' keep their case; names are slugged."""
    return str(s) if re.fullmatch(r"[A-Z]|\d+", str(s)) else slug(s)


def _transform(g, t):
    return shapely.transform(g, lambda c: np.column_stack(t.transform(c[:, 0], c[:, 1])))


def read_layer(lid, raw):
    """{district_id: (name, metric geometry)}, plus the source's fetch record and effective_from."""
    spec = LAYERS[lid]
    d = raw / spec["source_id"]
    fetch = json.loads((d / "fetch.json").read_text(encoding="utf-8"))
    path = d / fetch["file"]
    feats, eff = {}, set()
    if path.suffix == ".geojson":
        t = Transformer.from_crs("EPSG:4326", METRIC, always_xy=True)
        for f in json.loads(path.read_text(encoding="utf-8"))["features"]:
            p = f["properties"]
            rec = (p[spec["name"]], _transform(shapely.geometry.shape(f["geometry"]), t))
            feats.setdefault(f"{lid}:{_keep_case(p[spec['key']])}", []).append(rec)
            if "effective_from_field" in spec:
                eff.add((p.get(spec["effective_from_field"]) or "")[:10])
    else:
        t = Transformer.from_crs(path.with_suffix(".prj").read_text(), METRIC, always_xy=True)
        with shapefile.Reader(str(path)) as r:
            for sr in r.iterShapeRecords():
                rec = sr.record.as_dict()
                g = shapely.make_valid(_transform(shapely.geometry.shape(sr.shape.__geo_interface__), t))
                feats.setdefault(f"{lid}:{_keep_case(rec[spec['key']])}", []).append((rec[spec["name"]], g))
    dupes = [k for k, v in feats.items() if len(v) > 1]
    if dupes:
        raise BuildError(f"{lid}: district_id not unique: {dupes}")
    if "effective_from" in spec:
        effective_from = spec["effective_from"]
    elif len(eff) == 1 and "" not in eff:
        effective_from = eff.pop()
    else:
        raise BuildError(f"{lid}: features disagree on effective_from: {sorted(eff)}")
    return {k: v[0] for k, v in feats.items()}, fetch, effective_from


def clip(features, city):
    """Keep every district that shares area with the city, cut to it."""
    out = {}
    for k, (name, g) in features.items():
        c = shapely.intersection(g, city)
        c = shapely.get_parts(c)
        c = [p for p in c if p.geom_type == "Polygon" and p.area > 0]  # drop lines and points left on the edge
        if c:
            out[k] = (name, shapely.multipolygons(c) if len(c) > 1 else c[0])
    return out


def simplify(features, tol):
    """Coverage-simplify, then round to DECIMALS in lon/lat. Returns metric geometry
    re-projected from the rounded lon/lat, so every later check sees what is published."""
    keys = sorted(features)
    simp = shapely.coverage_simplify([features[k][1] for k in keys], tol)
    to_ll = Transformer.from_crs(METRIC, "EPSG:4326", always_xy=True)
    to_m = Transformer.from_crs("EPSG:4326", METRIC, always_xy=True)
    out, dropped = {}, [0, 0.0]
    for k, g in zip(keys, simp):
        ll = shapely.transform(g, lambda c: np.round(np.column_stack(to_ll.transform(c[:, 0], c[:, 1])), DECIMALS))
        # Rounding to 0.1 m can pinch a ring or collapse a clip sliver (under 1 m²,
        # where a riding line nearly meets the city edge). Repair, keep the area,
        # and count what went.
        if not ll.is_valid:
            ll = shapely.make_valid(ll)
        # make_valid can return a collection holding a MultiPolygon: flatten twice
        parts = [q for q in shapely.get_parts(shapely.get_parts(ll)) if q.geom_type == "Polygon" and q.area > 0]
        if not parts:
            raise BuildError(f"{k}: nothing left after simplifying at {tol} m and rounding")
        m = _transform(shapely.multipolygons(parts) if len(parts) > 1 else parts[0], to_m)
        dropped[0] += max(0, len(shapely.get_parts(g)) - len(parts))
        dropped[1] += abs(g.area - m.area)
        out[k] = (features[k][0], m)
    return out, dropped[0], round(dropped[1], 2)


def assign(points, features):
    """district_id per point; '' for none, '*' for more than one."""
    keys = list(features)
    pi, gi = shapely.STRtree([features[k][1] for k in keys]).query(points, predicate="intersects")
    out = np.full(len(points), "", object)
    n = np.bincount(pi, minlength=len(points))
    out[pi] = np.array(keys, object)[gi]
    out[n > 1] = "*"
    return out


def check_addresses(lid, points, full, published):
    a, b = assign(points, full), assign(points, published)
    for label, arr in (("full resolution", a), ("published", b)):
        none, many = int((arr == "").sum()), int((arr == "*").sum())
        if none or many:
            raise BuildError(f"{lid}: at {label}, {none} addresses in no district and {many} in more than one")
    changed = int((a != b).sum())
    if changed:
        raise BuildError(f"{lid}: {changed} addresses change district after simplifying; lower TOLERANCE_M")
    return len(points)


def coverage_defects(features):
    """(overlap m², gap m²) between districts, gaps being holes inside the layer's union."""
    gs = [g for _, g in features.values()]
    tree = shapely.STRtree(gs)
    overlap = sum(shapely.intersection(gs[i], gs[j]).area
                  for i, j in zip(*tree.query(gs, predicate="intersects")) if i < j)
    u = shapely.union_all(gs)
    gaps = sum(shapely.Polygon(r).area for p in shapely.get_parts(u) for r in p.interiors)
    return round(overlap, 1), round(gaps, 1)


def to_geojson(features):
    t = Transformer.from_crs(METRIC, "EPSG:4326", always_xy=True)
    lines = []
    for k in sorted(features):
        name, g = features[k]
        ll = shapely.transform(g, lambda c: np.round(np.column_stack(t.transform(c[:, 0], c[:, 1])), DECIMALS))  # idempotent on simplify()'s output
        lines.append(json.dumps({"type": "Feature", "properties": {"district_id": k, "name": name},
                                 "geometry": json.loads(shapely.to_geojson(ll))}, ensure_ascii=False, separators=(",", ":")))
    # one feature per line, so a moved district shows as one changed line
    return '{"type":"FeatureCollection","features":[\n' + ",\n".join(lines) + "\n]}\n"


def _check_counts(lid, features):
    spec = LAYERS[lid]
    if "expected" in spec and len(features) != spec["expected"]:
        raise BuildError(f"{lid}: {len(features)} districts, expected {spec['expected']}")
    if "must_include" in spec:
        prefix, n = spec["must_include"]
        have = sum(1 for name, _ in features.values() if str(name).startswith(prefix))
        if have != n:
            raise BuildError(f"{lid}: {have} districts named '{prefix}…', expected {n}")


def parcel_points(raw):
    d = raw / "coe_parcels"
    fetch = json.loads((d / "fetch.json").read_text(encoding="utf-8"))
    with open(d / fetch["file"], newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    x, y = Transformer.from_crs("EPSG:4326", METRIC, always_xy=True).transform(
        np.array([float(r["longitude"]) for r in rows]), np.array([float(r["latitude"]) for r in rows]))
    return shapely.points(x, y)


def build(raw, out):
    points = parcel_points(raw)
    read = {lid: read_layer(lid, raw) for lid in LAYERS}
    city = shapely.union_all([g for _, g in read["council_ward"][0].values()])
    files, entries = {}, []
    for lid, (features, fetch, effective_from) in read.items():
        if LAYERS[lid].get("clip"):
            features = clip(features, city)
        _check_counts(lid, features)
        published, parts_dropped, area_dropped = simplify(features, TOLERANCE_M)
        n = check_addresses(lid, points, features, published)
        overlap, gaps = coverage_defects(published)
        files[f"boundaries/{lid}.geojson"] = to_geojson(published)
        entries.append({
            "id": lid, "label": LAYERS[lid]["label"], "body": LAYERS[lid]["body"],
            "source_id": LAYERS[lid]["source_id"], "source_sha256": fetch["sha256"],
            "effective_from": effective_from, "effective_to": None,
            "simplification_tolerance_m": TOLERANCE_M, "near_boundary_m": NEAR_BOUNDARY_M,
            "feature_count": len(published), "addresses_checked": n,
            "overlap_m2": overlap, "gap_m2": gaps,
            "parts_dropped_by_rounding": parts_dropped, "area_change_by_rounding_m2": area_dropped,
            "last_verified": fetch["retrieved_at"][:10],
            "file": f"boundaries/{lid}.geojson",
        })
        log.info("%s: %d districts, %d addresses unchanged at %.0f m, overlap %.1f m2, gaps %.1f m2, "
                 "rounding dropped %d parts, changed area by %.1f m2", lid, len(published), n, TOLERANCE_M, overlap, gaps,
                 parts_dropped, area_dropped)
    # everything checked: only now touch the published files
    for rel, text in files.items():
        p = out / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    (out / "layers.json").write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return entries


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", type=Path, default=REPO / "data" / "raw")
    ap.add_argument("--out", type=Path, default=REPO / "site" / "public" / "data")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    try:
        build(args.raw, args.out)
    except BuildError as e:
        log.error("FAILED: %s", e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
