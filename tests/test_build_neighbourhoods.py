"""src/build_neighbourhoods.py: the assignment rule on toy data, and the committed
neighbourhoods.json against the committed boundary files and address index."""
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from src import build_boundaries as bb  # noqa: E402
from src import build_neighbourhoods as bn  # noqa: E402

DATA = REPO / "site" / "public" / "data"


def square(x0, y0, size=0.01):
    return {"type": "Polygon", "coordinates": [[[x0, y0], [x0 + size, y0], [x0 + size, y0 + size],
                                                [x0, y0 + size], [x0, y0]]]}


def feature(num, name, geom):
    return {"type": "Feature", "geometry": geom,
            "properties": {"neighbourhood_number": num, "name": name.upper(), "descriptive_name": name}}


def rec(lat, lon, prov="provincial_riding:1"):
    return [lat, lon, "council_ward:a", "public_school_ward:X", "catholic_school_ward:1", prov, "federal_riding:1", 0]


FETCH = {"id": "coe_neighbourhoods", "landing_url": "https://data.edmonton.ca/d/65fr-66s6",
         "retrieved_at": "2026-10-17T02:31:26Z"}
FEATURES = [feature("1", "Alpha", square(-113.5, 53.5)), feature("2", "Beta", square(-113.49, 53.5))]


def test_a_single_address_on_a_second_side_divides_that_layer_only():
    recs = [rec(53.505, -113.495), rec(53.506, -113.495, "provincial_riding:2"), rec(53.505, -113.485)]
    rows = bn.build_rows(FEATURES, FETCH, bn.assign(FEATURES, recs))
    alpha, beta = rows
    assert alpha["districts"]["provincial_riding"] == ["provincial_riding:1", "provincial_riding:2"]
    assert alpha["districts"]["council_ward"] == ["council_ward:a"]
    assert beta["districts"]["provincial_riding"] == ["provincial_riding:1"]
    assert alpha["id"] == "neighbourhood:1" and alpha["last_verified"] == "2026-10-17"


def test_an_address_in_no_neighbourhood_stops():
    with pytest.raises(bb.BuildError, match="1 address records in no neighbourhood"):
        bn.assign(FEATURES, [rec(53.505, -113.495), rec(53.505, -113.485), rec(53.6, -113.4)])


def test_a_neighbourhood_with_no_address_stops():
    with pytest.raises(bb.BuildError, match="1 neighbourhoods hold no address"):
        bn.assign(FEATURES, [rec(53.505, -113.495)])


def test_duplicate_names_stop():
    feats = [FEATURES[0], feature("2", "Alpha", square(-113.49, 53.5))]
    per = bn.assign(feats, [rec(53.505, -113.495), rec(53.505, -113.485)])
    with pytest.raises(bb.BuildError, match="duplicate neighbourhood name"):
        bn.build_rows(feats, FETCH, per)


@pytest.fixture(scope="module")
def committed():
    return json.loads((DATA / "neighbourhoods.json").read_text(encoding="utf-8"))


def test_committed_file_shape(committed):
    assert len(committed) == 407  # expected_row_count of coe_neighbourhoods
    layers = [l["id"] for l in json.loads((DATA / "layers.json").read_text(encoding="utf-8"))]
    known = {f["properties"]["district_id"] for l in layers
             for f in json.loads((DATA / "boundaries" / f"{l}.geojson").read_text(encoding="utf-8"))["features"]}
    for r in committed:
        assert list(r["districts"]) == layers
        assert all(r["districts"][l] for l in layers), r["id"]
        assert set(sum(r["districts"].values(), [])) <= known, r["id"]
        assert r["source_url"].startswith("https://") and r["last_verified"]
        assert 53.3 < r["point"][0] < 53.8 and -113.8 < r["point"][1] < -113.2


def test_every_district_in_the_address_index_is_in_some_neighbourhood(committed):
    """The polygons are not published, so the per-neighbourhood rule is tested on toy data above."""
    recs = bn.read_records(DATA / "addresses")
    union = {lid: set() for lid in bn.LAYERS}
    for r in recs:
        for j, lid in enumerate(bn.LAYERS):
            union[lid].add(r[2 + j])
    for lid in bn.LAYERS:
        assert set().union(*(r["districts"][lid] for r in committed)) == union[lid]
