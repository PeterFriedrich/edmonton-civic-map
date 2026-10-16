// The about page: the numbers it quotes come from the published files, so the
// text stays true after a refresh. The HTML carries the 2026-10-16 values as a
// fallback if a fetch fails.
const get = (path, as = "json") => fetch(path, { cache: "no-cache" }).then((r) => {
  if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
  return r[as]();
});
const set = (key, text) => document.querySelectorAll(`[data-v="${key}"]`).forEach((e) => (e.textContent = text));
const uniq = (xs) => [...new Set(xs)].join(" or ");

Promise.all([
  get("data/staleness.json"),
  get("data/layers.json"),
  get("data/officeholders.json"),
  get("data/addresses/manifest.txt", "text"),
]).then(([stale, layers, seats, manifest]) => {
  set("officeholders_days", stale.officeholders_days);
  set("boundaries_days", stale.boundaries_days);
  set("last_check", seats.map((s) => s.last_verified).concat(layers.map((l) => l.last_verified)).sort().at(-1));
  set("tolerance", uniq(layers.map((l) => l.simplification_tolerance_m)));
  set("near", uniq(layers.map((l) => l.near_boundary_m)));
  const split = manifest.match(/^split addresses: (\d+)$/m);
  if (split) set("split", split[1]);
  const list = document.getElementById("recheck");
  for (const r of stale.recheck_dates) {
    const li = document.createElement("li");
    const a = Object.assign(document.createElement("a"), { href: r.source_url, rel: "noopener", textContent: "source" });
    li.append(`${r.date}: ${r.what} (`, a, ")");
    list.append(li);
  }
}).catch((err) => console.error(err));
