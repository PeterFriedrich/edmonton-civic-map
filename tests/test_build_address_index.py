"""Guards on src/build_address_index.py and on the committed index.

The two pip.js cross-checks (docs/SPEC_data_schema.md §9.5, checks 1 and 2)
need the downloaded sources and node, so they run inside the build. Here: the
pieces they rest on, and §9.5 check 4, the shape of what is committed."""
import importlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
ai = importlib.import_module("src.build_address_index")
bb = importlib.import_module("src.build_boundaries")

ADDR = REPO / "site" / "public" / "data" / "addresses"


def test_street_file_names():
    assert ai.street_file("124 STREET NW") == "124-street-nw.json"
    assert ai.street_file("MASKÊKOSIHK TRAIL NW") == "maskekosihk-trail-nw.json"
    assert ai.street_file("AUSTIN O'BRIEN ROAD NW") == "austin-o-brien-road-nw.json"


def _records(rows, layers_per_row, near=None):
    lon = np.array([-113.5 + i * 1e-4 for i in range(len(rows))])
    lat = np.array([53.5] * len(rows))
    x, y = lon * 1e5, lat * 1e5
    dist = {lid: np.array([r[j] for r in layers_per_row], object) for j, lid in enumerate(ai.LAYERS)}
    near = np.array(near if near is not None else [0] * len(rows))
    return ai.build_records(rows, lon, lat, x, y, dist, near)


def test_rows_of_one_address_in_the_same_districts_become_one_record():
    rows = [{"street_name": "A ST", "house_number": "1"}] * 3
    streets, split = _records(rows, [("w", "s", "c", "p", "f")] * 3, near=[0, 2, 1])
    (rec,) = streets["A ST"]["1"]
    assert rec[2:7] == ["w", "s", "c", "p", "f"]
    assert rec[7] == 3  # the near-edge bits of all its rows
    assert split == []


def test_split_address_keeps_every_district_set():
    rows = [{"street_name": "A ST", "house_number": "1"}] * 3
    streets, split = _records(rows, [("w", "s", "c", "p1", "f"), ("w", "s", "c", "p2", "f"), ("w", "s", "c", "p1", "f")])
    assert sorted(r[5] for r in streets["A ST"]["1"]) == ["p1", "p2"]
    assert len(split) == 1 and split[0][:3] == ("A ST", "1", 3)


def test_record_point_is_one_of_the_rows():
    rows = [{"street_name": "A ST", "house_number": "1"}] * 3
    streets, _ = _records(rows, [("w", "s", "c", "p", "f")] * 3)
    (rec,) = streets["A ST"]["1"]
    assert rec[1] in [round(-113.5 + i * 1e-4, ai.DECIMALS) for i in range(3)]


# --- §9.5 check 4: the committed files -----------------------------------------


@pytest.fixture(scope="module")
def committed():
    if not (ADDR / "streets.json").exists():
        pytest.skip("no committed index")
    layers = json.loads((REPO / "site" / "public" / "data" / "layers.json").read_text(encoding="utf-8"))
    ids = {}
    for layer in layers:
        fc = json.loads((REPO / "site" / "public" / "data" / layer["file"]).read_text(encoding="utf-8"))
        ids[layer["id"]] = {f["properties"]["district_id"] for f in fc["features"]}
    return json.loads((ADDR / "streets.json").read_text(encoding="utf-8")), layers, ids


def test_every_listed_street_has_its_file_and_no_file_is_unlisted(committed):
    streets, _, _ = committed
    listed = {f for _, f in streets}
    on_disk = {p.name for p in ADDR.glob("*.json")} - {"streets.json"}
    assert listed == on_disk
    assert len(listed) == len(streets)


def test_every_record_names_districts_that_exist_in_layer_order(committed):
    streets, layers, ids = committed
    order = [layer["id"] for layer in layers]
    assert order == ai.LAYERS
    for _, name in streets:
        for house, recs in json.loads((ADDR / name).read_text(encoding="utf-8")).items():
            assert house.isdigit() and recs
            for r in recs:
                assert len(r) == 8
                assert 53.3 < r[0] < 53.8 and -113.8 < r[1] < -113.2
                for lid, d in zip(order, r[2:7]):
                    assert d in ids[lid], (name, house, d)
                assert 0 <= r[7] < 32


def test_manifest_accounts_for_every_parcel_row(committed):
    text = (ADDR / "manifest.txt").read_text(encoding="utf-8")
    rows_in = int(text.split("parcel rows in: ")[1].split("\n")[0])
    accounted = int(text.split("parcel rows accounted for: ")[1].split("\n")[0])
    assert rows_in == accounted > 0
