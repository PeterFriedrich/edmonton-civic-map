"""scripts/check_refresh_diff.py: a passing refresh may move dates and addresses only."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import check_refresh_diff as crd  # noqa: E402

D = "site/public/data"
SEATS = [{"seat_id": "council_ward:a", "name": "Person A", "last_verified": "2026-10-16"}]
LAYERS = [{"id": "council_ward", "feature_count": 12, "last_verified": "2026-10-16",
           "source_sha256": "aa", "addresses_checked": 1000}]
NBHDS = [{"id": "neighbourhood:1", "name": "Alpha", "districts": {"council_ward": ["council_ward:a"]},
          "last_verified": "2026-10-16"}]


def _write(root, rel, data):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(data if isinstance(data, str) else json.dumps(data))


@pytest.fixture
def repo(tmp_path):
    git = lambda *a: subprocess.run(["git", *a], cwd=tmp_path, check=True, capture_output=True)  # noqa: E731
    git("init", "-q")
    _write(tmp_path, f"{D}/officeholders.json", SEATS)
    _write(tmp_path, f"{D}/layers.json", LAYERS)
    _write(tmp_path, f"{D}/neighbourhoods.json", NBHDS)
    _write(tmp_path, f"{D}/boundaries/council_ward.geojson", "{}")
    _write(tmp_path, f"{D}/addresses/manifest.txt", "parcel rows in: 1000\n")
    _write(tmp_path, f"{D}/addresses/main-street-nw.json", "{}")
    git("add", "-A")
    git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base")
    return tmp_path


def test_unchanged_passes(repo):
    assert crd.problems(repo) == []


def test_dates_and_addresses_pass(repo):
    _write(repo, f"{D}/officeholders.json", [dict(SEATS[0], last_verified="2026-10-23")])
    _write(repo, f"{D}/layers.json", [dict(LAYERS[0], last_verified="2026-10-23", source_sha256="bb",
                                           addresses_checked=1003)])
    _write(repo, f"{D}/neighbourhoods.json", [dict(NBHDS[0], last_verified="2026-10-23")])
    _write(repo, f"{D}/addresses/manifest.txt", "parcel rows in: 1003\n")
    _write(repo, f"{D}/addresses/main-street-nw.json", '{"1": []}')
    _write(repo, f"{D}/addresses/new-street-nw.json", '{"2": []}')
    assert crd.problems(repo) == []


def test_a_name_change_fails(repo):
    _write(repo, f"{D}/officeholders.json", [dict(SEATS[0], name="Person Z", last_verified="2026-10-23")])
    assert crd.problems(repo) == [f"{D}/officeholders.json: council_ward:a: name changed"]


def test_a_layer_field_change_fails(repo):
    _write(repo, f"{D}/layers.json", [dict(LAYERS[0], feature_count=13)])
    assert crd.problems(repo) == [f"{D}/layers.json: council_ward: feature_count changed"]


def test_a_neighbourhood_district_change_fails(repo):
    _write(repo, f"{D}/neighbourhoods.json", [dict(NBHDS[0], districts={"council_ward": ["council_ward:a", "council_ward:b"]})])
    assert crd.problems(repo) == [f"{D}/neighbourhoods.json: neighbourhood:1: districts changed"]


def test_a_seat_added_fails(repo):
    _write(repo, f"{D}/officeholders.json", SEATS + [dict(SEATS[0], seat_id="council_ward:b")])
    assert "added or removed" in crd.problems(repo)[0]


def test_a_boundary_file_change_fails(repo):
    _write(repo, f"{D}/boundaries/council_ward.geojson", '{"moved": 1}')
    assert crd.problems(repo) == [f"{D}/boundaries/council_ward.geojson: may not change in a passing refresh"]


def test_a_new_file_outside_addresses_fails(repo):
    _write(repo, "src/surprise.py", "")
    assert crd.problems(repo) == ["src/surprise.py: may not change in a passing refresh"]


def test_exit_code(repo):
    assert crd.main(["--root", str(repo)]) == 0
    _write(repo, f"{D}/boundaries/council_ward.geojson", '{"moved": 1}')
    assert crd.main(["--root", str(repo)]) == 6
