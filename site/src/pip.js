// Point-in-polygon lookup against a GeoJSON FeatureCollection of (Multi)Polygons.
// Pure function, no network, no storage: the point never leaves the caller.
// The site's map clicks run this file, and src/build_address_index.py runs it
// under node (through prototype/pip.js) to cross-check every address.

function inRing(lon, lat, ring) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const xi = ring[i][0], yi = ring[i][1], xj = ring[j][0], yj = ring[j][1];
    if ((yi > lat) !== (yj > lat) && lon < ((xj - xi) * (lat - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

function inPolygon(lon, lat, rings) {
  if (!inRing(lon, lat, rings[0])) return false;
  for (let k = 1; k < rings.length; k++) if (inRing(lon, lat, rings[k])) return false;
  return true;
}

// Returns the index of every feature containing the point. Zero hits means
// outside the layer; more than one means the layer overlaps there. Callers
// must surface both rather than pick one.
export function locate(lon, lat, fc) {
  const hits = [];
  fc.features.forEach((f, i) => {
    const g = f.geometry;
    const polys = g.type === 'Polygon' ? [g.coordinates] : g.coordinates;
    if (polys.some((rings) => inPolygon(lon, lat, rings))) hits.push(i);
  });
  return hits;
}

// Metres from the point to the nearest boundary vertex-to-vertex segment
// (equirectangular approximation; fine at city scale). Used for the
// "near a boundary, check the official lookup" note.
export function distanceToBoundary(lon, lat, fc) {
  const kx = 111320 * Math.cos((lat * Math.PI) / 180), ky = 110574;
  let best = Infinity;
  for (const f of fc.features) {
    const g = f.geometry;
    const polys = g.type === 'Polygon' ? [g.coordinates] : g.coordinates;
    for (const rings of polys) for (const ring of rings) {
      for (let i = 0; i < ring.length - 1; i++) {
        const ax = (ring[i][0] - lon) * kx, ay = (ring[i][1] - lat) * ky;
        const bx = (ring[i + 1][0] - lon) * kx, by = (ring[i + 1][1] - lat) * ky;
        const dx = bx - ax, dy = by - ay, len2 = dx * dx + dy * dy;
        const t = len2 ? Math.max(0, Math.min(1, -(ax * dx + ay * dy) / len2)) : 0;
        const d = Math.hypot(ax + t * dx, ay + t * dy);
        if (d < best) best = d;
      }
    }
  }
  return best;
}
