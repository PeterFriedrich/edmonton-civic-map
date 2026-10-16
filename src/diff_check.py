"""Compare a fresh build against the published data (docs/SPEC_data_schema.md §5, §9.4).

The refresh rebuilds into a scratch directory; this compares it with what is
committed and says whether the new files may be published:

    exit 0  pass    nothing moved but last_verified / retrieved_at / hashes
    exit 1  review  the new files exist but wait for a person
    exit 2  stop    nothing from this run is published

Rules and their severities are in data/diff_rules.json. Checks the builders
already enforce (feature counts, cross-check disagreement, rows accounted for,
an address in no district) are not repeated here: a build that broke one never
produces a directory to compare.

    python -m src.diff_check --new <scratch> [--old site/public/data] [--report <dir>]

The scratch build is made with each builder's --out pointing at it, in order:
build_boundaries, build_address_index, build_officeholders.
"""
import argparse
import json
import logging
import math
import re
import sys
from collections import Counter
from pathlib import Path

import shapely
from pyproj import Transformer

from src.build_boundaries import METRIC

log = logging.getLogger("diff_check")

REPO = Path(__file__).resolve().parents[1]
RULES = REPO / "data" / "diff_rules.json"
EXIT = {"pass": 0, "review": 1, "stop": 2}
SHOWN = 20  # items per rule in report.md; report.json keeps all

NAME_FIELDS = ("name", "vacant")
CONTACT_FIELDS = ("contact_url", "affiliation", "affiliation_source_id")
SEAT_IGNORED = ("last_verified",)
LAYER_DATES = ("effective_from", "effective_to", "file")


def load_rules(path=RULES):
    rules = json.loads(path.read_text(encoding="utf-8"))
    bad = {k: v for k, v in rules["severity"].items() if v not in EXIT}
    if bad:
        raise ValueError(f"{path}: unknown severity {bad}")
    return rules


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def diff_seats(old, new):
    old = {s["seat_id"]: s for s in old}
    new = {s["seat_id"]: s for s in new}
    out = {"seat_added_or_removed": [], "seat_name_or_vacant": [],
           "seat_contact_or_affiliation": [], "seat_other_field": []}
    for sid in sorted(old.keys() - new.keys()):
        out["seat_added_or_removed"].append(f"{sid}: removed (was {old[sid]['name']})")
    for sid in sorted(new.keys() - old.keys()):
        out["seat_added_or_removed"].append(f"{sid}: added ({new[sid]['name']})")
    for sid in sorted(old.keys() & new.keys()):
        a, b = old[sid], new[sid]
        for k in sorted((a.keys() | b.keys()) - set(SEAT_IGNORED)):
            if a.get(k) == b.get(k):
                continue
            rule = ("seat_name_or_vacant" if k in NAME_FIELDS else
                    "seat_contact_or_affiliation" if k in CONTACT_FIELDS else "seat_other_field")
            out[rule].append(f"{sid}: {k} {json.dumps(a.get(k))} -> {json.dumps(b.get(k))}")
    return out


def _features(path):
    return {f["properties"]["district_id"]: f for f in _json(path)["features"]}


def diff_layers(old_dir, new_dir, threshold_m2):
    """Returns (findings, ids of layers whose boundaries moved)."""
    old = {l["id"]: l for l in _json(old_dir / "layers.json")}
    new = {l["id"]: l for l in _json(new_dir / "layers.json")}
    out = {"layer_added_removed_or_dates": [], "district_id_or_name": [], "district_geometry": []}
    moved = set()
    for lid in sorted(old.keys() ^ new.keys()):
        out["layer_added_removed_or_dates"].append(f"{lid}: {'removed' if lid in old else 'added'}")
        moved.add(lid)
    to_m = Transformer.from_crs("EPSG:4326", METRIC, always_xy=True)
    for lid in sorted(old.keys() & new.keys()):
        a, b = old[lid], new[lid]
        for k in LAYER_DATES:
            if a.get(k) != b.get(k):
                out["layer_added_removed_or_dates"].append(f"{lid}: {k} {a.get(k)} -> {b.get(k)}")
        fa, fb = _features(old_dir / a["file"]), _features(new_dir / b["file"])
        for d in sorted(fa.keys() - fb.keys()):
            out["district_id_or_name"].append(f"{d}: removed")
        for d in sorted(fb.keys() - fa.keys()):
            out["district_id_or_name"].append(f"{d}: added")
        if fa.keys() != fb.keys():
            moved.add(lid)
        for d in sorted(fa.keys() & fb.keys()):
            na, nb = fa[d]["properties"]["name"], fb[d]["properties"]["name"]
            if na != nb:
                out["district_id_or_name"].append(f"{d}: name {na!r} -> {nb!r}")
            if fa[d]["geometry"] == fb[d]["geometry"]:
                continue
            ga, gb = (shapely.transform(shapely.from_geojson(json.dumps(f["geometry"])),
                                        lambda xy: list(zip(*to_m.transform(xy[:, 0], xy[:, 1]))))
                      for f in (fa[d], fb[d]))
            area = shapely.symmetric_difference(ga, gb).area
            if area > threshold_m2:
                out["district_geometry"].append(f"{d}: {area:,.0f} m² moved")
                moved.add(lid)
    return out, moved


def _addresses(adir):
    """{(street file, house number): its records, [lat, lon, *district_ids, near]}."""
    got = {}
    for f in sorted(adir.glob("*.json")):
        if f.name == "streets.json":
            continue
        for num, recs in _json(f).items():
            got[(f.name, num)] = recs
    return got


def _moved_m(a, b):
    """What changed in an address whose districts did not, for the report."""
    if len(a) != len(b):
        return f"{len(a)} -> {len(b)} parcel rows"
    d = max(math.hypot((rb[0] - ra[0]) * 111_320, (rb[1] - ra[1]) * 111_320 * math.cos(math.radians(ra[0])))
            for ra, rb in zip(sorted(a), sorted(b)))
    return f"point moved {d:,.0f} m" if d >= 0.5 else "near-edge flags changed"


def _parcel_rows(adir):
    m = re.search(r"^parcel rows in: (\d+)$", (adir / "manifest.txt").read_text(encoding="utf-8"), re.M)
    if not m:
        raise ValueError(f"{adir / 'manifest.txt'}: no 'parcel rows in' line")
    return int(m.group(1))


def diff_addresses(old_dir, new_dir, layer_ids, moved_layers, max_change):
    out = {"parcel_rows_moved": [], "address_district_without_boundary_move": [],
           "address_district_with_boundary_move": [], "split_addresses": [], "addresses_added_or_removed": [],
           "address_point_moved": []}
    ra, rb = _parcel_rows(old_dir / "addresses"), _parcel_rows(new_dir / "addresses")
    if ra and abs(rb - ra) / ra > max_change:
        out["parcel_rows_moved"].append(f"parcel rows {ra} -> {rb} ({(rb - ra) / ra:+.2%})")
    old_recs, new_recs = _addresses(old_dir / "addresses"), _addresses(new_dir / "addresses")
    old = {k: {tuple(r[2:-1]) for r in v} for k, v in old_recs.items()}
    new = {k: {tuple(r[2:-1]) for r in v} for k, v in new_recs.items()}
    gone, added = old.keys() - new.keys(), new.keys() - old.keys()
    if gone or added:
        out["addresses_added_or_removed"].append(f"{len(added)} added, {len(gone)} removed")
    per_district = Counter()
    for key in sorted(old.keys() & new.keys()):
        a, b = old[key], new[key]
        if (len(a) > 1) != (len(b) > 1) or (len(a) > 1 and a != b):
            out["split_addresses"].append(f"{key[0]} {key[1]}: {sorted(a)} -> {sorted(b)}")
            continue
        if a == b:
            if old_recs[key] != new_recs[key]:
                out["address_point_moved"].append(f"{key[0]} {key[1]}: {_moved_m(old_recs[key], new_recs[key])}, same districts")
            continue
        (ta,), (tb,) = a, b
        for i, lid in enumerate(layer_ids):
            if ta[i] == tb[i]:
                continue
            if lid in moved_layers:
                per_district[f"{ta[i]} -> {tb[i]}"] += 1
            else:
                out["address_district_without_boundary_move"].append(f"{key[0]} {key[1]}: {ta[i]} -> {tb[i]}")
    for k in sorted(added):
        if len(new[k]) > 1:
            out["split_addresses"].append(f"{k[0]} {k[1]}: new, split {sorted(new[k])}")
    for k in sorted(gone):
        if len(old[k]) > 1:
            out["split_addresses"].append(f"{k[0]} {k[1]}: removed, was split")
    out["address_district_with_boundary_move"] = [f"{k}: {n} addresses" for k, n in sorted(per_district.items())]
    return out


def compare(old_dir, new_dir, rules):
    findings = diff_seats(_json(old_dir / "officeholders.json"), _json(new_dir / "officeholders.json"))
    layers, moved = diff_layers(old_dir, new_dir, rules["geometry_threshold_m2"])
    findings |= layers
    layer_ids = [l["id"] for l in _json(new_dir / "layers.json")]
    findings |= diff_addresses(old_dir, new_dir, layer_ids, moved, rules["parcel_rows_max_change"])
    missing = findings.keys() - rules["severity"].keys()
    if missing:
        raise ValueError(f"no severity configured for {sorted(missing)}")
    hits = [{"rule": r, "severity": rules["severity"][r], "items": items}
            for r, items in findings.items() if items]
    result = max((h["severity"] for h in hits), key=EXIT.get, default="pass")
    return {"result": result, "findings": hits}


def markdown(report, old_dir, new_dir):
    lines = [f"# Diff check: {report['result'].upper()}", "",
             f"Published: `{old_dir}`  ", f"Rebuilt: `{new_dir}`", ""]
    if not report["findings"]:
        lines.append("Nothing moved.")
    for h in sorted(report["findings"], key=lambda h: -EXIT[h["severity"]]):
        lines += [f"## {h['rule']} ({h['severity']}, {len(h['items'])})", ""]
        lines += [f"- {i}" for i in h["items"][:SHOWN]]
        if len(h["items"]) > SHOWN:
            lines.append(f"- … {len(h['items']) - SHOWN} more in report.json")
        lines.append("")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--old", type=Path, default=REPO / "site" / "public" / "data")
    ap.add_argument("--new", type=Path, required=True)
    ap.add_argument("--rules", type=Path, default=RULES)
    ap.add_argument("--report", type=Path, help="write report.md and report.json here (default: report.md to stdout)")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    report = compare(args.old, args.new, load_rules(args.rules))
    md = markdown(report, args.old, args.new)
    if args.report:
        args.report.mkdir(parents=True, exist_ok=True)
        (args.report / "report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        (args.report / "report.md").write_text(md, encoding="utf-8")
    else:
        print(md)
    log.info("diff check: %s (%s)", report["result"],
             ", ".join(f"{h['rule']} {len(h['items'])}" for h in report["findings"]) or "nothing moved")
    return EXIT[report["result"]]


if __name__ == "__main__":
    sys.exit(main())
