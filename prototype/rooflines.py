"""Download the 2019 rooflines (`jpxi-a9a5`), check them, write a height-only copy.

    python prototype/rooflines.py OUT_DIR

Writes OUT_DIR/rooflines.ndjson (as published) and OUT_DIR/heights.ndjson (one
`h` attribute, metres), the input to the tippecanoe build in README.md. Exits
non-zero if the row count is short or any row lacks a height or an outline.
"""
import collections
import json
import sys
import time
import urllib.parse
import urllib.request

import numpy as np
import shapely

BASE = "https://data.edmonton.ca"
PAGE = 50000


def get(url):
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=300) as r:
                return json.load(r)
        except OSError as e:
            print("retry", attempt, e, flush=True)
            time.sleep(5 * (attempt + 1))
    raise SystemExit("failed " + url)


def download(path):
    total = int(get(BASE + "/resource/jpxi-a9a5.json?$select=count(*)")[0]["count"])
    n = offset = 0
    with open(path, "w") as f:
        while True:
            # :id is the only stable paging order (data/DATA.md, paging quirk)
            q = urllib.parse.urlencode({"$order": ":id", "$limit": PAGE, "$offset": offset})
            feats = get(BASE + "/resource/jpxi-a9a5.geojson?" + q)["features"]
            for ft in feats:
                f.write(json.dumps(ft, separators=(",", ":")) + "\n")
            n += len(feats)
            if len(feats) < PAGE:
                break
            offset += PAGE
    if n != total:
        raise SystemExit(f"row count mismatch: wrote {n}, count(*) says {total}")
    return n


def check(src, dst):
    problems = collections.Counter()
    geoms, heights = [], []
    with open(src) as f, open(dst, "w") as out:
        for line in f:
            ft = json.loads(line)
            g = ft["geometry"]
            try:
                h = float(ft["properties"]["building_height"])
            except (KeyError, TypeError, ValueError):
                problems["no height"] += 1
                continue
            if g is None:
                problems["no outline"] += 1
                continue
            geoms.append(shapely.geometry.shape(g))
            heights.append(h)
            out.write(json.dumps({"type": "Feature", "properties": {"h": round(h, 1)}, "geometry": g},
                                 separators=(",", ":")) + "\n")
    G, h = np.array(geoms), np.array(heights)
    report = {
        "rows": len(G),
        "problems": dict(problems),
        "invalid_outlines": int((~shapely.is_valid(G)).sum()),
        "empty_outlines": int(shapely.is_empty(G).sum()),
        "vertices": int(shapely.get_num_coordinates(G).sum()),
        "height_min": float(h.min()),
        "height_median": float(np.median(h)),
        "height_max": float(h.max()),
        "over_20m": int((h > 20).sum()),
    }
    print(json.dumps(report, indent=2))
    if problems:
        raise SystemExit("rows without a height or an outline; not written to heights.ndjson")


if __name__ == "__main__":
    out_dir = sys.argv[1]
    print("rows downloaded", download(out_dir + "/rooflines.ndjson"))
    check(out_dir + "/rooflines.ndjson", out_dir + "/heights.ndjson")
