"""src/diff_check.py: one small published/rebuilt pair per rule (docs/SPEC_data_schema.md
§5, §9.4), the committed data against itself, and the published staleness thresholds."""
import copy
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from src import diff_check as dc  # noqa: E402

DATA = REPO / "site" / "public" / "data"
RULES = dc.load_rules()


def square(x0, y0, size=0.01):
    return {"type": "Polygon", "coordinates": [[[x0, y0], [x0 + size, y0], [x0 + size, y0 + size],
                                                [x0, y0 + size], [x0, y0]]]}


BASE = {
    "seats": [
        {"seat_id": "council_ward:a", "name": "Person A", "vacant": False, "contact_url": "https://x/a",
         "affiliation": None, "affiliation_source_id": None, "role": "Councillor", "last_verified": "2026-10-16"},
        {"seat_id": "council_ward:b", "name": "Person B", "vacant": False, "contact_url": "https://x/b",
         "affiliation": None, "affiliation_source_id": None, "role": "Councillor", "last_verified": "2026-10-16"},
    ],
    "layers": [
        {"id": "council_ward", "effective_from": "2021-10-18", "effective_to": None,
         "file": "boundaries/council_ward.geojson", "last_verified": "2026-10-15", "source_sha256": "aa"},
        {"id": "public_school_ward", "effective_from": "2021-10-18", "effective_to": None,
         "file": "boundaries/public_school_ward.geojson", "last_verified": "2026-10-15", "source_sha256": "bb"},
    ],
    "districts": {
        "council_ward": {"council_ward:a": ("A", square(-113.5, 53.5)), "council_ward:b": ("B", square(-113.49, 53.5))},
        "public_school_ward": {"public_school_ward:X": ("X", square(-113.5, 53.5, 0.02))},
    },
    # street file -> house number -> records [lat, lon, *districts, near]
    "streets": {
        "main-street.json": {
            "1": [[53.505, -113.495, "council_ward:a", "public_school_ward:X", 0]],
            "2": [[53.505, -113.485, "council_ward:b", "public_school_ward:X", 0]],
        },
    },
    "parcel_rows": 1000,
}


def write(root, d):
    (root / "boundaries").mkdir(parents=True)
    (root / "addresses").mkdir()
    (root / "officeholders.json").write_text(json.dumps(d["seats"]))
    (root / "layers.json").write_text(json.dumps(d["layers"]))
    for lid, ds in d["districts"].items():
        fc = {"type": "FeatureCollection", "features": [
            {"type": "Feature", "properties": {"district_id": k, "name": n}, "geometry": g} for k, (n, g) in ds.items()]}
        (root / "boundaries" / f"{lid}.geojson").write_text(json.dumps(fc))
    (root / "addresses" / "streets.json").write_text(json.dumps(list(d["streets"])))
    for f, recs in d["streets"].items():
        (root / "addresses" / f).write_text(json.dumps(recs))
    (root / "addresses" / "manifest.txt").write_text(f"## Counts\nparcel rows in: {d['parcel_rows']}\n")
    return root


def run(tmp_path, change):
    new = copy.deepcopy(BASE)
    change(new)
    report = dc.compare(write(tmp_path / "old", BASE), write(tmp_path / "new", new), RULES)
    return report["result"], {h["rule"]: h["items"] for h in report["findings"]}


def test_unchanged_but_dates_passes(tmp_path):
    def f(d):
        for s in d["seats"]:
            s["last_verified"] = "2026-10-23"
        for l in d["layers"]:
            l["last_verified"], l["source_sha256"] = "2026-10-23", "cc"
    assert run(tmp_path, f) == ("pass", {})


def test_seat_removed_stops(tmp_path):
    result, hits = run(tmp_path, lambda d: d["seats"].pop())
    assert result == "stop" and hits["seat_added_or_removed"] == ["council_ward:b: removed (was Person B)"]


def test_seat_added_stops(tmp_path):
    def f(d):
        d["seats"].append(dict(d["seats"][0], seat_id="council_ward:c"))
    assert run(tmp_path, f)[0] == "stop"


@pytest.mark.parametrize("field,value,rule", [
    ("name", "Person Z", "seat_name_or_vacant"),
    ("vacant", True, "seat_name_or_vacant"),
    ("contact_url", "https://x/new", "seat_contact_or_affiliation"),
    ("affiliation", "NDP", "seat_contact_or_affiliation"),
    ("role", "Mayor", "seat_other_field"),
])
def test_seat_field_change_reviews(tmp_path, field, value, rule):
    result, hits = run(tmp_path, lambda d: d["seats"][0].__setitem__(field, value))
    assert result == "review" and list(hits) == [rule]


def test_district_renamed_reviews(tmp_path):
    def f(d):
        d["districts"]["council_ward"]["council_ward:a"] = ("A2", square(-113.5, 53.5))
    result, hits = run(tmp_path, f)
    assert result == "review" and hits == {"district_id_or_name": ["council_ward:a: name 'A' -> 'A2'"]}


def test_layer_dates_review(tmp_path):
    result, hits = run(tmp_path, lambda d: d["layers"][0].__setitem__("effective_to", "2027-10-18"))
    assert result == "review" and list(hits) == ["layer_added_removed_or_dates"]


def test_geometry_under_threshold_passes(tmp_path):
    # 1e-6 degrees of one edge is well under 10 m² at this size
    def f(d):
        g = square(-113.5, 53.5)
        g["coordinates"][0][2] = [-113.49 + 1e-7, 53.51]
        d["districts"]["council_ward"]["council_ward:a"] = ("A", g)
    assert run(tmp_path, f) == ("pass", {})


def test_boundary_move_reviews_and_counts_addresses(tmp_path):
    # ward a grows over house 2, which changes ward with it
    def f(d):
        d["districts"]["council_ward"]["council_ward:a"] = ("A", square(-113.5, 53.5, 0.02))
        d["streets"]["main-street.json"]["2"][0][2] = "council_ward:a"
    result, hits = run(tmp_path, f)
    assert result == "review"
    assert list(hits) == ["district_geometry", "address_district_with_boundary_move"]
    assert hits["address_district_with_boundary_move"] == ["council_ward:b -> council_ward:a: 1 addresses"]


def test_address_moves_without_boundary_move_reviews(tmp_path):
    result, hits = run(tmp_path, lambda d: d["streets"]["main-street.json"]["2"][0].__setitem__(2, "council_ward:a"))
    assert result == "review"
    assert hits == {"address_district_without_boundary_move": ["main-street.json 2: council_ward:b -> council_ward:a"]}


def test_new_split_address_reviews(tmp_path):
    def f(d):
        d["streets"]["main-street.json"]["2"].append([53.505, -113.495, "council_ward:a", "public_school_ward:X", 0])
    result, hits = run(tmp_path, f)
    assert result == "review" and list(hits) == ["split_addresses"]


def test_addresses_added_pass_with_count(tmp_path):
    def f(d):
        d["streets"]["main-street.json"]["3"] = [[53.505, -113.495, "council_ward:a", "public_school_ward:X", 0]]
        d["parcel_rows"] = 1001
    assert run(tmp_path, f) == ("pass", {"addresses_added_or_removed": ["1 added, 0 removed"]})


def test_parcel_rows_over_one_percent_stops(tmp_path):
    result, hits = run(tmp_path, lambda d: d.__setitem__("parcel_rows", 1011))
    assert result == "stop" and list(hits) == ["parcel_rows_moved"]


def test_committed_data_against_itself_passes():
    assert dc.compare(DATA, DATA, RULES) == {"result": "pass", "findings": []}


def test_staleness_thresholds_match_the_decision():
    """docs/SPEC_data_schema.md §7 point 3: office holders 45 days, boundaries 180."""
    s = json.loads((DATA / "staleness.json").read_text(encoding="utf-8"))
    assert (s["officeholders_days"], s["boundaries_days"]) == (45, 180)
    assert all(r["date"] and r["what"] and r["source_url"].startswith("https://") for r in s["recheck_dates"])
