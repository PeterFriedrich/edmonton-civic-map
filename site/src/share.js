// The view as a link, after the "#" so it never reaches the server
// (docs/DECISIONS.md, 2026-10-17, share link). Pure functions.
//
//   d=<district_id>,...    districts (a picked district, or an address's districts)
//   n=<number>             a neighbourhood
//   a=<address>            an address, only when the reader includes it
//   p=<lat>,<lon>          a map point, only when the reader includes it
//   lines=<layer id>       the boundary lines drawn
//   3d=1                   tilted
//
// A selection is { kind: "districts", ids } | { kind: "neighbourhood", id } |
// { kind: "address", label, ids } | { kind: "point", lat, lon, ids }; a view is
// { lines, tilt }. Unknown keys are ignored, so later lenses can add theirs.

const esc = (s) => encodeURIComponent(s).replace(/%3A/g, ":").replace(/%2C/g, ",").replace(/%20/g, "+");
const unesc = (s) => decodeURIComponent(s.replace(/\+/g, " "));

export function encode(sel, view = {}, withAddress = false) {
  const parts = [];
  if (sel?.kind === "neighbourhood") parts.push(["n", sel.id.replace(/^neighbourhood:/, "")]);
  else if (sel?.kind === "address" && withAddress) parts.push(["a", sel.label]);
  else if (sel?.kind === "point" && withAddress) parts.push(["p", `${sel.lat.toFixed(5)},${sel.lon.toFixed(5)}`]);
  else if (sel?.ids?.length) parts.push(["d", sel.ids.join(",")]);
  if (view.lines && view.lines !== "council_ward") parts.push(["lines", view.lines]);
  if (view.tilt) parts.push(["3d", "1"]);
  return parts.length ? "#" + parts.map(([k, v]) => `${k}=${esc(v)}`).join("&") : "";
}

export function decode(hash) {
  const q = {};
  for (const part of hash.replace(/^#/, "").split("&")) {
    const i = part.indexOf("=");
    if (i > 0) {
      try { q[part.slice(0, i)] = unesc(part.slice(i + 1)); } catch { /* malformed escape: skip the key */ }
    }
  }
  let sel = null;
  if (q.a) sel = { kind: "address", label: q.a.trim() };
  else if (q.p) {
    const [lat, lon] = q.p.split(",").map(Number);
    if (Number.isFinite(lat) && Number.isFinite(lon)) sel = { kind: "point", lat, lon };
  } else if (q.n) sel = { kind: "neighbourhood", id: "neighbourhood:" + q.n };
  else if (q.d) sel = { kind: "districts", ids: q.d.split(",").filter(Boolean) };
  return { sel, view: { lines: q.lines || null, tilt: q["3d"] === "1" } };
}
