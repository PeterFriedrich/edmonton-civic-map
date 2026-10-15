"""scripts/check_dist.mjs, the build guard that stands in for cache-busting
stamps (docs/WEB_CACHE_BUSTING.md "Guard it"): passes a good dist, and fails a
dist with an unhashed script or with published data missing or changed."""
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


def run(dist, public):
    return subprocess.run(["node", str(REPO / "scripts" / "check_dist.mjs"), str(dist), str(public)],
                          capture_output=True, text=True)


@pytest.fixture
def site(tmp_path):
    public = tmp_path / "public" / "data"
    public.mkdir(parents=True)
    for name in ["layers.json", "buildings.pmtiles", "terrain.pmtiles", "addresses/streets.json"]:
        (public / name).parent.mkdir(parents=True, exist_ok=True)
        (public / name).write_text(name)
    (public.parent / "licenses").mkdir()
    for lib in ["maplibre-gl", "pmtiles"]:
        (public.parent / "licenses" / f"{lib}.txt").write_text(lib)
    dist = tmp_path / "dist"
    shutil.copytree(tmp_path / "public", dist)
    (dist / "assets").mkdir()
    (dist / "assets" / "index-Bh1Xiy5i.js").write_text("")
    (dist / "assets" / "index-DBE96hFo.css").write_text("")
    (dist / "index.html").write_text(
        '<link rel="stylesheet" href="./assets/index-DBE96hFo.css">'
        '<script type="module" src="./assets/index-Bh1Xiy5i.js"></script>')
    return dist, tmp_path / "public"


def test_check_dist_passes_a_good_build(site):
    r = run(*site)
    assert r.returncode == 0, r.stderr


def test_check_dist_flags_an_unhashed_file(site):
    dist, public = site
    (dist / "assets" / "app.js").write_text("")
    r = run(dist, public)
    assert r.returncode == 1 and "unhashed asset: assets/app.js" in r.stderr


def test_check_dist_flags_published_data_missing_or_changed(site):
    dist, public = site
    (dist / "data" / "layers.json").write_text("stale")
    (dist / "data" / "terrain.pmtiles").unlink()
    r = run(dist, public)
    assert r.returncode == 1
    assert "changed in" in r.stderr and "data/layers.json" in r.stderr
    assert "missing from" in r.stderr and "data/terrain.pmtiles" in r.stderr
