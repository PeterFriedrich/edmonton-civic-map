"""Build site/public/data/neighbourhoods.json: each neighbourhood's districts, for search.

A neighbourhood's districts in a layer are those of the published address
records inside it, so a neighbourhood answer never disagrees with an address
lookup. More than one district in a layer means the neighbourhood is divided
there, by any number of addresses, and the page asks for an address for that
layer (docs/DECISIONS.md, 2026-10-17, neighbourhood search). Runs after
src.build_address_index, against the same --out.

Points are tested in longitude/latitude, as published: no reprojection, so the
answer does not depend on the machine's PROJ floats (session-summary S6, §3).

    python -m src.build_neighbourhoods [--raw data/raw] [--out site/public/data]
"""
import argparse
import collections
import json
import logging
import sys
from pathlib import Path

import numpy as np
import shapely

from src import build_boundaries as bb

log = logging.getLogger("build_neighbourhoods")

REPO = Path(__file__).resolve().parents[1]
LAYERS = list(bb.LAYERS)  # address record column order
DECIMALS = 5  # ~1 m: the point only moves the map


def read_neighbourhoods(raw):
    d = raw / "coe_neighbourhoods"
    fetch = json.loads((d / "fetch.json").read_text(encoding="utf-8"))
    fc = json.loads((d / fetch["file"]).read_text(encoding="utf-8"))
    return fc["features"], fetch


def read_records(adir):
    """Every published address record, [lat, lon, *district_ids, near]."""
    return [r for f in sorted(adir.glob("*.json")) if f.name != "streets.json"
            for recs in json.loads(f.read_text(encoding="utf-8")).values() for r in recs]


def assign(features, records):
    """{feature index: {layer: set of district_ids}}. Every record must land in exactly one feature."""
    geoms = [shapely.geometry.shape(f["geometry"]) for f in features]
    pts = shapely.points(np.array([r[1] for r in records]), np.array([r[0] for r in records]))
    pi, gi = shapely.STRtree(geoms).query(pts, predicate="within")
    hits = collections.Counter(pi.tolist())
    none = len(records) - len(hits)
    many = sum(1 for n in hits.values() if n > 1)
    if none or many:
        raise bb.BuildError(f"{none} address records in no neighbourhood and {many} in more than one")
    out = collections.defaultdict(lambda: {lid: set() for lid in LAYERS})
    for p, g in zip(pi.tolist(), gi.tolist()):
        for j, lid in enumerate(LAYERS):
            out[g][lid].add(records[p][2 + j])
    empty = [features[g]["properties"]["descriptive_name"] for g in range(len(features)) if g not in out]
    if empty:
        raise bb.BuildError(f"{len(empty)} neighbourhoods hold no address: {empty[:10]}")
    return out


def build_rows(features, fetch, per):
    rows = []
    for g, f in enumerate(features):
        p = f["properties"]
        pt = shapely.geometry.shape(f["geometry"]).representative_point()
        rows.append({
            "id": f"neighbourhood:{p['neighbourhood_number']}",
            "name": p["descriptive_name"],
            "point": [round(pt.y, DECIMALS), round(pt.x, DECIMALS)],
            "districts": {lid: sorted(per[g][lid]) for lid in LAYERS},
            "source_id": fetch["id"],
            "source_url": fetch["landing_url"],
            "last_verified": fetch["retrieved_at"][:10],
        })
    for key in ("id", "name"):
        seen = collections.Counter(r[key] for r in rows)
        dup = [k for k, n in seen.items() if n > 1]
        if dup:
            raise bb.BuildError(f"duplicate neighbourhood {key}: {dup}")
    return sorted(rows, key=lambda r: r["name"])


def build(raw, out):
    features, fetch = read_neighbourhoods(raw)
    records = read_records(out / "addresses")
    rows = build_rows(features, fetch, assign(features, records))
    divided = {lid: sum(len(r["districts"][lid]) > 1 for r in rows) for lid in LAYERS}
    log.info("%d address records -> %d neighbourhoods; divided: %s", len(records), len(rows), divided)
    (out / "neighbourhoods.json").write_text(
        json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


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
