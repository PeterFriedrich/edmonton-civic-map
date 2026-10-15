// Checks the built site in dist/ before it is deployed (docs/WEB_CACHE_BUSTING.md,
// "Guard it"). Vite's content-hashed file names are the cache busting, so a .js,
// .mjs or .css file without a hash would be served stale after a deploy.
// Usage: node scripts/check_dist.mjs [dist] [site/public]
import { createHash } from "node:crypto";
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative } from "node:path";

const DIST = process.argv[2] || "dist";
const PUBLIC = process.argv[3] || "site/public";
const HASHED = /-[A-Za-z0-9_-]{8}\.(js|mjs|css)$/;
const errors = [];

function* walk(dir) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) yield* walk(p);
    else yield p;
  }
}
const sha = (p) => createHash("sha256").update(readFileSync(p)).digest("hex");

if (!existsSync(join(DIST, "index.html"))) {
  console.error(`check_dist: no ${DIST}/index.html; run npm run build first`);
  process.exit(1);
}

// 1. Code and styles carry a content hash. Published data (copied from
//    site/public) is exempt: its URLs are fixed, and it is revalidated instead.
for (const p of walk(DIST)) {
  const rel = relative(DIST, p);
  if (existsSync(join(PUBLIC, rel))) continue;
  if (/\.(js|mjs|css)$/.test(rel) && !HASHED.test(rel)) errors.push(`unhashed asset: ${rel}`);
}

// 2. Everything the page points at exists, and it points at no unhashed code.
const html = readFileSync(join(DIST, "index.html"), "utf8");
const refs = [...html.matchAll(/(?:src|href)="([^"]+)"/g)].map((m) => m[1]);
if (!refs.some((r) => /\.js$/.test(r))) errors.push("index.html loads no script");
if (!refs.some((r) => /\.css$/.test(r))) errors.push("index.html loads no stylesheet");
for (const r of refs) {
  if (/^[a-z]+:/i.test(r) || r.startsWith("#")) continue;
  const p = join(DIST, r.split(/[?#]/)[0]);
  if (!existsSync(p)) errors.push(`index.html points at a missing file: ${r}`);
  else if (/\.(js|mjs|css)$/.test(r) && !HASHED.test(r)) errors.push(`index.html loads unhashed: ${r}`);
}

// 3. The published data arrived whole: every file in site/public is in dist,
//    byte for byte.
let n = 0;
for (const p of walk(PUBLIC)) {
  const rel = relative(PUBLIC, p);
  const out = join(DIST, rel);
  if (!existsSync(out)) errors.push(`published file missing from ${DIST}: ${rel}`);
  else if (sha(p) !== sha(out)) errors.push(`published file changed in ${DIST}: ${rel}`);
  n++;
}
for (const need of ["licenses/maplibre-gl.txt", "licenses/pmtiles.txt", "data/layers.json", "data/buildings.pmtiles", "data/terrain.pmtiles", "data/addresses/streets.json"]) {
  if (!existsSync(join(DIST, need))) errors.push(`missing: ${need}`);
}

if (errors.length) {
  console.error(`check_dist: ${errors.length} problem(s)\n  ` + errors.join("\n  "));
  process.exit(1);
}
console.log(`check_dist: ok (${n} published files copied intact; code and styles hashed)`);
