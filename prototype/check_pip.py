"""Measure the point-in-polygon prototype against every City parcel address.

Not part of the pipeline. Needs shapely>=2.1, pyproj and numpy (not yet in
requirements.txt) and node. Inputs are downloaded by hand; see README.md here.

    python prototype/check_pip.py --wards wards.geojson --addresses 'parcels*.csv'

For each simplification tolerance it reports the layer size and how many
addresses land in a different ward than they do at full resolution.
"""
import argparse
import csv
import glob
import gzip
import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pyproj
import shapely
from shapely.geometry import mapping, shape

PIP = Path(__file__).with_name("pip.js")
# NAD83 / Alberta 3TM ref merid 114 W: metres, so tolerances mean what they say.
METRIC_CRS = 3776


def run_js(layer_path, lonlat_text):
    out = subprocess.run(["node", str(PIP), str(layer_path)], input=lonlat_text,
                         capture_output=True, text=True, check=True).stdout
    # -1 = no ward, -2 = more than one ward
    return np.array([-1 if not v else -2 if "|" in v else int(v) for v in out.split("\n")[:-1]])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wards", required=True)
    ap.add_argument("--addresses", required=True, help="glob of CSVs with latitude, longitude")
    ap.add_argument("--tolerances", default="1,2,5,10,25,50")
    args = ap.parse_args()

    fc = json.loads(Path(args.wards).read_text(encoding="utf-8"))
    fwd = pyproj.Transformer.from_crs(4326, METRIC_CRS, always_xy=True)
    inv = pyproj.Transformer.from_crs(METRIC_CRS, 4326, always_xy=True)
    wards = np.array([shapely.transform(shape(f["geometry"]),
                                        lambda c: np.column_stack(fwd.transform(c[:, 0], c[:, 1])))
                      for f in fc["features"]])

    rows = []
    for path in sorted(glob.glob(args.addresses)):
        with open(path, encoding="utf-8") as fh:
            rows += list(csv.DictReader(fh))
    lon = np.array([float(r["longitude"]) for r in rows])
    lat = np.array([float(r["latitude"]) for r in rows])
    pts = shapely.points(*fwd.transform(lon, lat))
    lonlat_text = "\n".join(f"{a:.7f},{b:.7f}" for a, b in zip(lon, lat))

    pi, gi = shapely.STRtree(wards).query(pts, predicate="within")
    ref = np.full(len(pts), -1)
    ref[pi] = gi
    print(f"addresses {len(pts)} | shapely full-res: unmatched {(ref < 0).sum()}, "
          f"multi-match {len(pi) - len(set(pi.tolist()))}")
    print(f"pip.js vs shapely at full resolution: {(run_js(args.wards, lonlat_text) != ref).sum()} disagreements")

    with tempfile.TemporaryDirectory() as tmp:
        for tol in [float(t) for t in args.tolerances.split(",")]:
            simplified = shapely.coverage_simplify(wards, tol)
            out = {"type": "FeatureCollection", "features": [
                {"type": "Feature", "properties": f["properties"], "geometry": mapping(
                    shapely.transform(g, lambda c: np.round(np.column_stack(inv.transform(c[:, 0], c[:, 1])), 6)))}
                for f, g in zip(fc["features"], simplified)]}
            for feat in out["features"]:
                feat["properties"] = {"name": feat["properties"].get("name_1")}
            blob = json.dumps(out, separators=(",", ":"), ensure_ascii=False).encode()
            path = Path(tmp) / f"wards_{tol:g}m.geojson"
            path.write_bytes(blob)
            got = run_js(path, lonlat_text)
            print(f"tolerance {tol:>4g} m | vertices {sum(shapely.get_num_coordinates(simplified)):>6} | "
                  f"{len(blob) / 1e3:6.1f} kB, {len(gzip.compress(blob)) / 1e3:5.1f} kB gzipped | "
                  f"addresses changed {(got != ref).sum():>3} (no ward {(got == -1).sum()}, two wards {(got == -2).sum()})")


if __name__ == "__main__":
    main()
