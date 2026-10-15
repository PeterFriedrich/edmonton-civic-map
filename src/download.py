"""Download the map and address sources into data/raw/<source_id>/.

Each source lands in its own folder with a fetch.json holding the
docs/SPEC_data_schema.md §2 fields. A source whose row count disagrees with
the server's count or with the fixed expected count fails, and its folder is
left as it was: files are written to a .partial folder and swapped in only
when every check passes.

    python -m src.download                  # every source
    python -m src.download coe_wards ...    # some
    python -m src.download --out DIR        # somewhere other than data/raw
"""
import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import logging
import shutil
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

import certifi
import shapefile

log = logging.getLogger("download")

REPO = Path(__file__).resolve().parents[1]
SOCRATA = "https://data.edmonton.ca"
OGL_EDMONTON = "Open Government Licence – Edmonton"
# Elections Alberta answers 403 to Python's default User-Agent (data/DATA.md).
USER_AGENT = "edmonton-civic-map/0.1 (+https://github.com/PeterFriedrich/edmonton-civic-map)"
PAGE = 50_000  # 50,000-row pages return in ~9 s; one 300,000-row request stalled
PAUSE_S = 1.5  # between requests (docs/SPEC_data_schema.md §8)
RETRIES = 2  # extra tries on a network error only, never on a wrong count
TIMEOUT_S = 300

SOURCES = {
    "coe_parcels": {
        "kind": "socrata", "dataset": "ut27-nrpn", "format": "csv",
        "title": "City of Edmonton address points, PARCEL rows",
        "where": "object_type='PARCEL'",
        "select": "record_id,house_number,street_name,latitude,longitude",
        "licence": OGL_EDMONTON, "expected_row_count": None,
    },
    "coe_wards": {
        "kind": "socrata", "dataset": "b4er-5rp2", "format": "geojson",
        "title": "City of Edmonton Ward Boundary and Council Composition_Current",
        "licence": OGL_EDMONTON, "expected_row_count": 12,
    },
    "coe_public_school_wards": {
        "kind": "socrata", "dataset": "d7pj-rist", "format": "geojson",
        "title": "Edmonton Public School Board ward boundaries",
        "licence": OGL_EDMONTON, "expected_row_count": 9,
    },
    "coe_catholic_school_wards": {
        "kind": "socrata", "dataset": "pwzf-sjj2", "format": "geojson",
        "title": "Edmonton Catholic School Board ward boundaries",
        "licence": OGL_EDMONTON, "expected_row_count": 7,
    },
    "ab_ridings": {
        "kind": "zip", "publisher": "Elections Alberta",
        "title": "Electoral division boundaries enacted 2017 (in force 2019)",
        "landing_url": "https://www.elections.ab.ca/resources/maps/",
        "fetch_url": "https://www.elections.ab.ca/uploads/2019Boundaries_ED-Shapefiles.zip",
        "licence": None,  # none stated: TODO.md "Licence for the Elections Alberta boundary shapefile"
        "expected_row_count": 87,
    },
    "fed_ridings": {
        "kind": "zip", "publisher": "Elections Canada",
        "title": "Federal electoral districts, 2023 Representation Order",
        "landing_url": "https://open.canada.ca/data/en/dataset/18bf3ea7-1940-46ec-af52-9ba3f77ed708",
        "fetch_url": "https://www.elections.ca/res/cir/mapsCorner/edb/FederalElectoralDistricts_SHP.zip",
        "licence": "Open Government Licence – Canada",
        "expected_row_count": 343,
    },
}


class DownloadError(Exception):
    pass


_ssl = ssl.create_default_context(cafile=certifi.where())


def _get(url):
    """(body, headers) for a 200 response; DownloadError otherwise."""
    for attempt in range(RETRIES + 1):
        time.sleep(PAUSE_S)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=TIMEOUT_S, context=_ssl) as r:
                if r.status != 200:
                    raise DownloadError(f"HTTP {r.status} from {url}")
                return r.read(), dict(r.headers)
        except urllib.error.HTTPError as e:
            raise DownloadError(f"HTTP {e.code} from {url}") from e
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if attempt == RETRIES:
                raise DownloadError(f"{e} from {url}, after {RETRIES + 1} tries") from e
            log.warning("network error, retrying: %s (%s)", url, e)


def _get_json(url):
    return json.loads(_get(url)[0])


def _now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _check_expected(sid, src, n):
    want = src["expected_row_count"]
    if want is not None and n != want:
        raise DownloadError(f"{sid}: {n} rows, expected {want}")


def fetch_socrata(sid, src, dest):
    ds = src["dataset"]
    meta = _get_json(f"{SOCRATA}/api/views/{ds}.json")
    count_q = {"$select": "count(*)"}
    if "where" in src:
        count_q["$where"] = src["where"]
    server_count = int(_get_json(f"{SOCRATA}/resource/{ds}.json?" + urllib.parse.urlencode(count_q))[0]["count"])

    fetch_url = f"{SOCRATA}/resource/{ds}.{src['format']}"
    rows, header = [], None
    offset = 0
    while True:
        # :id is the only stable order: record_id repeats within ut27-nrpn (data/DATA.md)
        q = {"$order": ":id", "$limit": PAGE, "$offset": offset}
        for k in ("where", "select"):
            if k in src:
                q["$" + k] = src[k]
        body = _get(fetch_url + "?" + urllib.parse.urlencode(q))[0]
        if src["format"] == "csv":
            page = list(csv.reader(io.StringIO(body.decode("utf-8"))))
            header, page = page[0], page[1:]
        else:
            page = json.loads(body)["features"]
        rows += page
        log.info("%s: offset %d, %d rows", sid, offset, len(page))
        if len(page) < PAGE:
            break
        offset += PAGE

    # A capped or truncated download returns exactly what it was asked for, silently.
    if len(rows) != server_count:
        raise DownloadError(f"{sid}: fetched {len(rows)} rows, server count(*) says {server_count}")
    if not rows:
        raise DownloadError(f"{sid}: zero rows")
    _check_expected(sid, src, len(rows))

    out = dest / f"{ds}.{src['format']}"
    if src["format"] == "csv":
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(rows)
    else:
        out.write_text(json.dumps({"type": "FeatureCollection", "features": rows}), encoding="utf-8")
    updated = meta.get("rowsUpdatedAt")
    return {
        "publisher": "City of Edmonton",
        "landing_url": f"{SOCRATA}/d/{ds}",
        "fetch_url": fetch_url,
        "publisher_updated_at": dt.datetime.fromtimestamp(updated, dt.timezone.utc).strftime("%Y-%m-%d") if updated else None,
        "file": out.name,
        "sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "row_count": len(rows),
        "server_row_count": server_count,
    }


def fetch_zip(sid, src, dest):
    body, headers = _get(src["fetch_url"])
    try:
        zf = zipfile.ZipFile(io.BytesIO(body))
    except zipfile.BadZipFile as e:
        raise DownloadError(f"{sid}: not a zip file") from e
    zf.extractall(dest)
    shps = sorted(p for p in dest.rglob("*.shp"))
    if len(shps) != 1:
        raise DownloadError(f"{sid}: expected one .shp in the zip, found {len(shps)}")
    with shapefile.Reader(str(shps[0])) as r:
        n = len(r)
    if n == 0:
        raise DownloadError(f"{sid}: zero rows")
    _check_expected(sid, src, n)
    modified = {k.lower(): v for k, v in headers.items()}.get("last-modified")  # servers vary the case
    return {
        "publisher": src["publisher"],
        "landing_url": src["landing_url"],
        "fetch_url": src["fetch_url"],
        "publisher_updated_at": (dt.datetime.strptime(modified, "%a, %d %b %Y %H:%M:%S %Z").strftime("%Y-%m-%d")
                                 if modified else None),
        "file": str(shps[0].relative_to(dest)),
        "sha256": hashlib.sha256(body).hexdigest(),  # of the zip as fetched
        "row_count": n,
    }


def download(sid, out_root):
    src = SOURCES[sid]
    final = out_root / sid
    partial = out_root / f"{sid}.partial"
    shutil.rmtree(partial, ignore_errors=True)
    partial.mkdir(parents=True)
    retrieved_at = _now()
    try:
        rec = (fetch_socrata if src["kind"] == "socrata" else fetch_zip)(sid, src, partial)
        rec = {"id": sid, "title": src["title"], **rec, "licence": src["licence"],
               "attribution": None,  # TODO.md "Exact attribution text"
               "retrieved_at": retrieved_at, "expected_row_count": src["expected_row_count"]}
        (partial / "fetch.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except BaseException:
        shutil.rmtree(partial, ignore_errors=True)
        raise
    shutil.rmtree(final, ignore_errors=True)
    partial.rename(final)
    log.info("%s: ok, %d rows, sha256 %s", sid, rec["row_count"], rec["sha256"][:12])
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sources", nargs="*", help=f"any of: {', '.join(SOURCES)} (default: all)")
    ap.add_argument("--out", type=Path, default=REPO / "data" / "raw")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    unknown = [s for s in args.sources if s not in SOURCES]
    if unknown:
        ap.error(f"unknown source(s): {', '.join(unknown)}")
    failed = []
    for sid in args.sources or SOURCES:
        try:
            download(sid, args.out)
        except DownloadError as e:
            log.error("%s: FAILED: %s", sid, e)
            failed.append(sid)
    if failed:
        log.error("failed: %s", ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
