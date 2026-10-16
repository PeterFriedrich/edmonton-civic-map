"""The MIT grant must not silently swallow data that is not ours to license.

Adapted from edmonton-tax-viz (its tests/test_license.py, 2026-09-20). LICENSE
carves the prose (CC BY), the published data and the third-party licence texts
out of the MIT grant. The carve-out list is read out of LICENSE itself, so a new
data directory that nobody declares fails here instead of being swept under MIT.
The README restates the CC BY scope in a table; the last test ties the two
together, because either direction of drift is wrong in public.
"""
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# Unambiguously data payloads. `.json` is absent: config and data share it.
DATA_SUFFIXES = {".csv", ".geojson", ".gpkg", ".shp", ".parquet", ".topojson", ".pmtiles", ".tif"}
CARVE_OUT_PATH = re.compile(r"^ {4}([A-Za-z][\w./-]*/?)\s*$", re.M)
README_SELF = "this README"


def tracked_files():
    return subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()


@pytest.fixture(scope="module")
def licence_text():
    path = ROOT / "LICENSE"
    assert path.is_file(), "LICENSE is missing: the repo is public and needs one"
    return path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def prose_paths():
    text = (ROOT / "LICENSE-docs").read_text(encoding="utf-8")
    section = re.search(r"^## What this covers\n(.*?)^##", text, re.M | re.S)
    assert section, "LICENSE-docs has no '## What this covers' block to parse"
    paths = set(CARVE_OUT_PATH.findall(section.group(1)))
    assert paths
    return paths


def test_prose_licence_covers_only_paths_that_exist(prose_paths):
    tracked = tracked_files()
    missing = sorted(p for p in prose_paths if not any(f == p.rstrip("/") or f.startswith(p) for f in tracked))
    assert not missing, f"LICENSE-docs grants CC BY over paths with no tracked files: {missing}"


def test_readme_licence_table_matches_the_prose_licence(prose_paths):
    rows = [l for l in (ROOT / "README.md").read_text(encoding="utf-8").splitlines()
            if l.startswith("|") and "](LICENSE-docs)" in l]
    assert len(rows) == 1, f"expected one README table row pointing at LICENSE-docs, found {len(rows)}"
    cell = rows[0].split("|")[1]
    readme = set(re.findall(r"`([^`]+)`", cell)) | ({"README.md"} if README_SELF in cell else set())
    assert readme == prose_paths, (f"README claims, LICENSE-docs does not cover: {sorted(readme - prose_paths)}; "
                                   f"LICENSE-docs covers, README omits: {sorted(prose_paths - readme)}")


def test_licence_declares_the_data_directories(licence_text):
    """Guard the guard: an unparsed carve-out list would pass the check below."""
    assert {"site/public/data/", "data/name_variants.csv"} <= set(CARVE_OUT_PATH.findall(licence_text))


def test_no_data_file_outside_the_carve_out(licence_text):
    declared = tuple(sorted(CARVE_OUT_PATH.findall(licence_text)))
    escaped = [f for f in tracked_files() if Path(f).suffix.lower() in DATA_SUFFIXES and not f.startswith(declared)]
    assert not escaped, ("Data-shaped files outside every LICENSE carve-out, so the repo claims MIT over them:\n  "
                         + "\n  ".join(escaped))
