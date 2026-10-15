"""Guards on src/download.py. The network is a fake: these pin that a short or
miscounted download fails, leaves the previous good copy in place, and that a
good one writes the §2 fields of docs/SPEC_data_schema.md."""
import importlib.util
import io
import json
import urllib.error
import urllib.parse
import zipfile
from pathlib import Path

import pytest
import shapefile

REPO = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("download", REPO / "src" / "download.py")
dl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dl)


@pytest.fixture
def net(monkeypatch):
    """Route URLs to canned (body, headers). A handler may raise."""
    routes = []
    seen = []

    def get(url):
        seen.append(url)
        for match, handler in routes:
            if match(url):
                out = handler(url)
                return out if isinstance(out, tuple) else (out, {})
        raise AssertionError(f"unexpected URL {url}")

    monkeypatch.setattr(dl, "PAUSE_S", 0)
    monkeypatch.setattr(dl, "_get", get)
    return routes, seen


def _socrata(routes, ds, count, pages, fmt="geojson"):
    """pages: rows returned per page request, in order."""
    it = iter(pages)
    routes.append((lambda u: u.startswith(f"{dl.SOCRATA}/api/views/{ds}.json"),
                   lambda u: json.dumps({"rowsUpdatedAt": 1759622400}).encode()))
    routes.append((lambda u: f"/resource/{ds}.json?" in u and "count" in u,
                   lambda u: json.dumps([{"count": str(count)}]).encode()))

    def page(u):
        n = next(it)
        if fmt == "csv":
            return ("h1,h2\n" + "".join(f"{i},x\n" for i in range(n))).encode()
        return json.dumps({"features": [{"type": "Feature", "properties": {"i": i}, "geometry": None}
                                        for i in range(n)]}).encode()
    routes.append((lambda u: f"/resource/{ds}.{fmt}?" in u, page))


def _shp_zip(n):
    shp, shx, dbf = io.BytesIO(), io.BytesIO(), io.BytesIO()
    with shapefile.Writer(shp=shp, shx=shx, dbf=dbf, shapeType=shapefile.POLYGON) as w:
        w.field("ID", "N")
        for i in range(n):
            w.poly([[[0, 0], [0, 1], [1, 1], [0, 0]]])
            w.record(i)
    z = io.BytesIO()
    with zipfile.ZipFile(z, "w") as zf:
        for ext, b in (("shp", shp), ("shx", shx), ("dbf", dbf)):
            zf.writestr(f"inner/ED.{ext}", b.getvalue())
    return z.getvalue()


def test_good_socrata_download_writes_fetch_json(net, tmp_path):
    routes, _ = net
    _socrata(routes, "b4er-5rp2", 12, [12])
    dl.download("coe_wards", tmp_path)
    rec = json.loads((tmp_path / "coe_wards" / "fetch.json").read_text())
    for k in ("id", "publisher", "title", "landing_url", "fetch_url", "licence", "attribution",
              "retrieved_at", "publisher_updated_at", "sha256", "row_count", "expected_row_count"):
        assert k in rec
    assert rec["row_count"] == rec["expected_row_count"] == 12
    assert rec["publisher_updated_at"] == "2025-10-05"
    assert len(json.loads((tmp_path / "coe_wards" / rec["file"]).read_text())["features"]) == 12


def test_paging_runs_until_a_short_page_and_orders_on_id(net, tmp_path, monkeypatch):
    routes, seen = net
    monkeypatch.setattr(dl, "PAGE", 3)
    _socrata(routes, "ut27-nrpn", 7, [3, 3, 1], fmt="csv")
    rec = dl.download("coe_parcels", tmp_path)
    assert rec["row_count"] == 7
    pages = [urllib.parse.parse_qs(urllib.parse.urlsplit(u).query) for u in seen if "/resource/ut27-nrpn.csv?" in u]
    assert [p["$offset"] for p in pages] == [["0"], ["3"], ["6"]]
    assert all(p["$order"] == [":id"] and p["$where"] == ["object_type='PARCEL'"] for p in pages)
    lines = (tmp_path / "coe_parcels" / "ut27-nrpn.csv").read_text().splitlines()
    assert lines[0] == "h1,h2" and len(lines) == 8


def test_truncated_download_fails_against_the_server_count(net, tmp_path):
    routes, _ = net
    _socrata(routes, "ut27-nrpn", 298453, [1000], fmt="csv")
    with pytest.raises(dl.DownloadError, match="server count"):
        dl.download("coe_parcels", tmp_path)


def test_fixed_count_mismatch_fails(net, tmp_path):
    routes, _ = net
    _socrata(routes, "b4er-5rp2", 13, [13])
    with pytest.raises(dl.DownloadError, match="expected 12"):
        dl.download("coe_wards", tmp_path)


def test_zero_rows_fails(net, tmp_path):
    routes, _ = net
    _socrata(routes, "ut27-nrpn", 0, [0], fmt="csv")
    with pytest.raises(dl.DownloadError, match="zero rows"):
        dl.download("coe_parcels", tmp_path)


def test_failure_keeps_the_previous_good_copy(net, tmp_path):
    routes, _ = net
    good = tmp_path / "coe_wards"
    good.mkdir()
    (good / "fetch.json").write_text("previous")
    _socrata(routes, "b4er-5rp2", 11, [11])
    with pytest.raises(dl.DownloadError):
        dl.download("coe_wards", tmp_path)
    assert (good / "fetch.json").read_text() == "previous"
    assert not (tmp_path / "coe_wards.partial").exists()


def test_zip_source_counts_shapefile_rows(net, tmp_path):
    routes, _ = net
    routes.append((lambda u: u.endswith(".zip"),
                   lambda u: (_shp_zip(87), {"last-modified": "Wed, 11 Sep 2024 16:00:00 GMT"})))
    rec = dl.download("ab_ridings", tmp_path)
    assert rec["row_count"] == 87 and rec["publisher_updated_at"] == "2024-09-11"
    assert rec["file"] == "inner/ED.shp"


def test_zip_source_with_wrong_count_fails(net, tmp_path):
    routes, _ = net
    routes.append((lambda u: u.endswith(".zip"), lambda u: _shp_zip(86)))
    with pytest.raises(dl.DownloadError, match="expected 87"):
        dl.download("ab_ridings", tmp_path)


def test_network_errors_retry_but_http_errors_do_not(monkeypatch):
    monkeypatch.setattr(dl, "PAUSE_S", 0)
    calls = []

    def flaky(req, timeout, context):
        calls.append(req.full_url)
        raise urllib.error.URLError("reset")
    monkeypatch.setattr(dl.urllib.request, "urlopen", flaky)
    with pytest.raises(dl.DownloadError, match="after 3 tries"):
        dl._get("https://example.test/a")
    assert len(calls) == dl.RETRIES + 1

    calls.clear()

    def forbidden(req, timeout, context):
        calls.append(req.full_url)
        raise urllib.error.HTTPError(req.full_url, 403, "Forbidden", {}, None)
    monkeypatch.setattr(dl.urllib.request, "urlopen", forbidden)
    with pytest.raises(dl.DownloadError, match="HTTP 403"):
        dl._get("https://example.test/a")
    assert len(calls) == 1


def test_main_reports_failure_with_exit_code(net, tmp_path):
    routes, _ = net
    _socrata(routes, "b4er-5rp2", 13, [13])
    assert dl.main(["coe_wards", "--out", str(tmp_path)]) == 1
