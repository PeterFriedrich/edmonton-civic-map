"""Read the Edmonton window of MRDEM-30 and pack it as elevation PMTiles.

    python prototype/terrain.py WARDS_GEOJSON OUT_DIR

Range-reads only the window it needs from the national file, writes
OUT_DIR/edmonton_mrdem30_dtm.tif (the window, native CRS) and
OUT_DIR/terrain.pmtiles: 256 px PNG tiles in Mapbox Terrain-RGB encoding
(height = -10000 + (R*65536 + G*256 + B) * 0.1 m), covering the city's
bounding box at z9-z12. z12 is 22.7 m a pixel at Edmonton's latitude, the
nearest zoom to the source's 30 m.
"""
import io
import json
import math
import sys
from collections import Counter

import numpy as np
import rasterio
import shapely
from PIL import Image
from pmtiles.tile import Compression, TileType, zxy_to_tileid
from pmtiles.writer import Writer
from rasterio.warp import Resampling, reproject, transform_bounds
from rasterio.windows import from_bounds

SRC = "/vsicurl/https://canelevation-dem.s3.ca-central-1.amazonaws.com/mrdem-30/mrdem-30-dtm.tif"
NODATA = -32767.0
ZOOMS = range(9, 13)
SIZE = 256
R = 6378137.0


def tile_range(z, lon0, lat0, lon1, lat1):
    n = 2 ** z
    x = lambda lon: int((lon + 180) / 360 * n)
    y = lambda lat: int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
    return range(x(lon0), x(lon1) + 1), range(y(lat1), y(lat0) + 1)


def tile_bounds_3857(z, x, y):
    span = 2 * math.pi * R / 2 ** z
    left, top = -math.pi * R + x * span, math.pi * R - y * span
    return left, top - span, left + span, top


def encode(h):
    v = np.round((h.astype(np.float64) + 10000) * 10).astype(np.uint32)
    rgb = np.dstack([(v >> 16) & 255, (v >> 8) & 255, v & 255]).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(rgb, "RGB").save(buf, "PNG", optimize=True)
    return buf.getvalue()


def decode(png):
    a = np.asarray(Image.open(io.BytesIO(png))).astype(np.float64)
    return -10000 + (a[..., 0] * 65536 + a[..., 1] * 256 + a[..., 2]) * 0.1


def main(wards_path, out_dir):
    city = shapely.union_all([shapely.geometry.shape(f["geometry"])
                              for f in json.load(open(wards_path))["features"]])
    lon0, lat0, lon1, lat1 = city.bounds
    tiles = [(z, x, y) for z in ZOOMS for xs, ys in [tile_range(z, lon0, lat0, lon1, lat1)]
             for x in xs for y in ys]
    # Read enough to fill every tile of the coarsest zoom, which reach furthest past the city.
    z0 = [t for t in tiles if t[0] == ZOOMS[0]]
    b3857 = [tile_bounds_3857(*t) for t in z0]
    need = (min(b[0] for b in b3857), min(b[1] for b in b3857), max(b[2] for b in b3857), max(b[3] for b in b3857))
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"):
        with rasterio.open(SRC) as ds:
            w = from_bounds(*transform_bounds("EPSG:3857", ds.crs, *need, densify_pts=51), ds.transform)
            # A few cells of margin so bilinear sampling at the edge has neighbours.
            w = rasterio.windows.Window(w.col_off - 8, w.row_off - 8, w.width + 16, w.height + 16)
            w = w.round_offsets().round_lengths()
            src = ds.read(1, window=w)
            src_t, src_crs = ds.window_transform(w), ds.crs
    if (src == NODATA).any():
        raise SystemExit(f"{int((src == NODATA).sum())} no-data cells in the window")
    with rasterio.open(out_dir + "/edmonton_mrdem30_dtm.tif", "w", driver="GTiff", width=src.shape[1],
                       height=src.shape[0], count=1, dtype="float32", crs=src_crs, transform=src_t,
                       nodata=NODATA, compress="deflate", tiled=True) as o:
        o.write(src, 1)

    sizes, counts, worst = Counter(), Counter(), 0.0
    blobs = []
    for z, x, y in tiles:
        dst = np.full((SIZE, SIZE), np.nan, dtype=np.float32)
        left, bottom, right, top = tile_bounds_3857(z, x, y)
        reproject(src, dst, src_transform=src_t, src_crs=src_crs, src_nodata=NODATA,
                  dst_transform=rasterio.transform.from_bounds(left, bottom, right, top, SIZE, SIZE),
                  dst_crs="EPSG:3857", dst_nodata=np.nan, resampling=Resampling.bilinear)
        if np.isnan(dst).any():
            raise SystemExit(f"tile {z}/{x}/{y} has {int(np.isnan(dst).sum())} empty pixels")
        png = encode(dst)
        worst = max(worst, float(np.abs(decode(png) - dst).max()))
        blobs.append((zxy_to_tileid(z, x, y), png))
        sizes[z] += len(png)
        counts[z] += 1

    with open(out_dir + "/terrain.pmtiles", "wb") as f:
        writer = Writer(f)
        for tid, png in sorted(blobs):
            writer.write_tile(tid, png)
        writer.finalize(
            {"tile_type": TileType.PNG, "tile_compression": Compression.NONE,
             "min_lon_e7": int(lon0 * 1e7), "min_lat_e7": int(lat0 * 1e7),
             "max_lon_e7": int(lon1 * 1e7), "max_lat_e7": int(lat1 * 1e7),
             "center_zoom": 11, "center_lon_e7": int(-113.4938e7), "center_lat_e7": int(53.5444e7)},
            {"name": "terrain", "encoding": "mapbox", "tileSize": SIZE,
             "description": "MRDEM-30 DTM (Natural Resources Canada), Edmonton window, Terrain-RGB 0.1 m",
             "attribution": "Contains information licensed under the Open Government Licence - Canada"})
    print(json.dumps({"window_cells": list(src.shape), "window_min_m": float(src.min()),
                      "window_max_m": float(src.max()), "worst_round_trip_error_m": round(worst, 3),
                      "per_zoom": {f"z{z}": {"tiles": counts[z], "bytes": sizes[z]} for z in sorted(counts)},
                      "total_bytes": sum(sizes.values())}, indent=2))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
