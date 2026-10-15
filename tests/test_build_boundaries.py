"""Guards on src/build_boundaries.py, on small made-up shapes in metres. The
real-data check (no parcel address changes district) runs inside the build;
these pin the pieces it is made of."""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest
import shapely
from shapely.geometry import Polygon, box

REPO = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("build_boundaries", REPO / "src" / "build_boundaries.py")
bb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bb)

# Somewhere inside Edmonton in EPSG:3776, so the lon/lat round trip is realistic.
X0, Y0 = 30_000, 5_930_000


def sq(x, y, w, h):
    return box(X0 + x, Y0 + y, X0 + x + w, Y0 + y + h)


def test_slug_matches_the_schema_examples():
    assert bb.slug("O-day'min") == "odaymin"
    assert bb.slug("pihêsiwin") == "pihesiwin"
    assert bb.slug("Nakota Isga") == "nakotaisga"
    assert bb._keep_case("A") == "A" and bb._keep_case("71") == "71" and bb._keep_case("Métis") == "metis"


def test_clip_keeps_a_sliver_neighbour_and_drops_one_outside():
    city = sq(0, 0, 1000, 1000)
    feats = {
        "r:in": ("In", sq(0, 0, 1000, 1000)),
        "r:sliver": ("Sliver", sq(999, 0, 500, 1000)),  # 1 m strip inside the city
        "r:touch": ("Touch", sq(1000, 0, 500, 1000)),  # shares only an edge
        "r:out": ("Out", sq(2000, 0, 500, 500)),
    }
    out = bb.clip(feats, city)
    assert set(out) == {"r:in", "r:sliver"}
    assert out["r:sliver"][1].area == pytest.approx(1000)


def test_simplify_keeps_shared_edges_shared():
    # two districts sharing a zig-zag edge with 1 m teeth
    zig = [(500 + (1 if i % 2 else 0), i * 10) for i in range(101)]
    left = Polygon([(0, 0)] + zig + [(0, 1000)])
    right = Polygon([(1000, 0)] + zig + [(1000, 1000)])
    left, right = (shapely.transform(g, lambda c: c + [X0, Y0]) for g in (left, right))
    out, _, _ = bb.simplify({"a:l": ("L", left), "a:r": ("R", right)}, 5)
    gs = [g for _, g in out.values()]
    assert shapely.get_num_coordinates(gs[0]) < shapely.get_num_coordinates(left)
    assert shapely.intersection(*gs).area < 1  # no overlap opened
    u = shapely.union_all(gs)
    assert u.geom_type == "Polygon" and not u.interiors  # no gap opened between them
    assert u.area == pytest.approx(1_000_000, rel=1e-4)  # only rounding at the outer edge


def test_address_that_changes_district_stops_the_build():
    full = {"a:1": ("1", sq(0, 0, 500, 1000)), "a:2": ("2", sq(500, 0, 500, 1000))}
    moved = {"a:1": ("1", sq(0, 0, 510, 1000)), "a:2": ("2", sq(510, 0, 490, 1000))}
    pts = shapely.points([X0 + 505, X0 + 100], [Y0 + 500, Y0 + 500])
    assert bb.check_addresses("a", pts, full, full) == 2
    with pytest.raises(bb.BuildError, match="1 addresses change district"):
        bb.check_addresses("a", pts, full, moved)


def test_address_in_no_district_or_two_stops_the_build():
    feats = {"a:1": ("1", sq(0, 0, 500, 1000)), "a:2": ("2", sq(400, 0, 600, 1000))}
    with pytest.raises(bb.BuildError, match="0 addresses in no district and 1 in more than one"):
        bb.check_addresses("a", shapely.points([X0 + 450], [Y0 + 500]), feats, feats)
    with pytest.raises(bb.BuildError, match="1 addresses in no district"):
        bb.check_addresses("a", shapely.points([X0 + 5000], [Y0 + 500]), feats, feats)


def test_count_checks():
    with pytest.raises(bb.BuildError, match="expected 12"):
        bb._check_counts("council_ward", {f"c:{i}": ("x", None) for i in range(11)})
    feats = {f"p:{i}": (f"Edmonton-{i}", None) for i in range(19)} | {"p:x": ("St. Albert", None)}
    with pytest.raises(bb.BuildError, match="19 districts named 'Edmonton-…', expected 20"):
        bb._check_counts("provincial_riding", feats)


def test_geojson_has_only_id_and_name_one_feature_per_line():
    feats = {"a:2": ("Two", sq(500, 0, 500, 1000)), "a:1": ("Métis", sq(0, 0, 500, 1000))}
    text = bb.to_geojson(feats)
    fc = json.loads(text)
    assert [f["properties"] for f in fc["features"]] == [
        {"district_id": "a:1", "name": "Métis"}, {"district_id": "a:2", "name": "Two"}]
    assert len(text.splitlines()) == 4
    lon, lat = np.array(fc["features"][0]["geometry"]["coordinates"][0]).T
    assert -114 < lon.min() < -113 and 53 < lat.min() < 54


def test_coverage_defects_measures_overlap_and_holes():
    a, b = sq(0, 0, 510, 1000), sq(500, 0, 500, 1000)
    ring = shapely.difference(sq(1000, 0, 1000, 1000), sq(1400, 400, 10, 10))
    overlap, gaps = bb.coverage_defects({"a": ("", a), "b": ("", b), "c": ("", ring)})
    assert overlap == pytest.approx(10_000) and gaps == pytest.approx(100)
