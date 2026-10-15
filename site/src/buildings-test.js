import * as maplibregl from "maplibre-gl";
// The library builds its worker URL at run time, which Vite can't see, so the
// worker is emitted as its own content-hashed file and passed in.
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?url";
import "maplibre-gl/dist/maplibre-gl.css";
import { Protocol } from "pmtiles";

const TILES = new URL("data/buildings.pmtiles", location.href).href;
const TERRAIN = new URL("data/terrain.pmtiles", location.href).href;
const $ = (id) => document.getElementById(id);
const dark = matchMedia("(prefers-color-scheme: dark)").matches;
const colors = dark ? { bg: "#16181b", building: "#b9b4a8", shadow: "#000000", light: "#3a3d42" }
                   : { bg: "#f4f3ef", building: "#8a8478", shadow: "#6b665c", light: "#ffffff" };

maplibregl.setWorkerUrl(workerUrl);
const protocol = new Protocol();
maplibregl.addProtocol("pmtiles", protocol.tile);

const map = new maplibregl.Map({
  container: "map",
  center: [-113.4938, 53.5444],
  zoom: 14,
  minZoom: 10,
  maxPitch: 70,
  attributionControl: false,
  style: {
    version: 8,
    sources: {
      buildings: { type: "vector", url: "pmtiles://" + TILES },
      // MapLibre's guidance is a separate source each for hillshade and 3D terrain.
      terrain: { type: "raster-dem", url: "pmtiles://" + TERRAIN, encoding: "mapbox", tileSize: 256 },
      shading: { type: "raster-dem", url: "pmtiles://" + TERRAIN, encoding: "mapbox", tileSize: 256 },
    },
    layers: [
      { id: "bg", type: "background", paint: { "background-color": colors.bg } },
      { id: "hillshade", type: "hillshade", source: "shading", layout: { visibility: "none" },
        paint: { "hillshade-shadow-color": colors.shadow, "hillshade-highlight-color": colors.light,
                 "hillshade-accent-color": colors.shadow, "hillshade-exaggeration": 0.6 } },
      { id: "buildings", type: "fill-extrusion", source: "buildings", "source-layer": "buildings",
        paint: { "fill-extrusion-color": colors.building, "fill-extrusion-height": ["get", "h"],
                 "fill-extrusion-base": 0, "fill-extrusion-opacity": 1 } },
    ],
  },
});
map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "bottom-right");

map.once("idle", () => {
  $("loaded").textContent = (performance.now() / 1000).toFixed(2) + " s after the page started";
});

function tileBytes() {
  const entries = performance.getEntriesByType("resource").filter((e) => e.name.endsWith(".pmtiles"));
  const total = entries.reduce((s, e) => s + (e.transferSize || e.encodedBodySize || 0), 0);
  $("bytes").textContent = (total / 1e6).toFixed(2) + " MB in " + entries.length + " requests";
}
map.on("idle", tileBytes);
const showZoom = () => ($("zoom").textContent = map.getZoom().toFixed(1) + ", pitch " + Math.round(map.getPitch()) + "°");
map.on("move", showZoom);
showZoom();

// Answers "does the host serve this file in pieces?" directly: 206 and no content-encoding.
fetch(TILES, { headers: { Range: "bytes=0-15" }, cache: "no-store" }).then((r) => {
  const enc = r.headers.get("content-encoding") || "none";
  $("range").textContent = r.status + (r.status === 206 ? " (partial, works)" : " (NOT partial)") + ", encoding " + enc;
}).catch((e) => ($("range").textContent = "failed: " + e.message));

function press(on, off) { $(on).setAttribute("aria-pressed", "true"); $(off).setAttribute("aria-pressed", "false"); }
$("flat").onclick = () => { press("flat", "tilted"); map.easeTo({ pitch: 0, bearing: 0 }); };
$("tilted").onclick = () => { press("tilted", "flat"); map.easeTo({ pitch: 60, bearing: -20 }); };
$("solid").onclick = () => { press("solid", "ghost"); map.setPaintProperty("buildings", "fill-extrusion-opacity", 1); };
$("ghost").onclick = () => { press("ghost", "solid"); map.setPaintProperty("buildings", "fill-extrusion-opacity", 0.35); };
function ground(mode) {
  for (const id of ["t-off", "t-shade", "t-3d"]) $(id).setAttribute("aria-pressed", String(id === mode));
  map.setLayoutProperty("hillshade", "visibility", mode === "t-off" ? "none" : "visible");
  map.setTerrain(mode === "t-3d" ? { source: "terrain", exaggeration: 1 } : null);
}
$("t-off").onclick = () => ground("t-off");
$("t-shade").onclick = () => ground("t-shade");
$("t-3d").onclick = () => ground("t-3d");
$("toggle").onclick = () => {
  const min = $("panel").classList.toggle("min");
  $("toggle").textContent = min ? "Show" : "Hide";
  $("toggle").setAttribute("aria-expanded", String(!min));
};

// The same 10-second camera path on every device, so numbers compare across phones.
$("bench").onclick = () => {
  const b = $("bench"); b.disabled = true; $("fps").textContent = "measuring…";
  const frames = []; let last = performance.now(), running = true;
  const tick = (t) => { frames.push(t - last); last = t; if (running) requestAnimationFrame(tick); };
  requestAnimationFrame(tick);
  const start = { center: map.getCenter(), zoom: map.getZoom(), pitch: map.getPitch(), bearing: map.getBearing() };
  map.easeTo({ center: [-113.47, 53.535], zoom: 15, bearing: start.bearing + 120, duration: 5000, essential: true });
  map.once("moveend", () => {
    map.easeTo({ center: start.center, zoom: start.zoom, bearing: start.bearing, duration: 5000, essential: true });
    map.once("moveend", () => {
      running = false; b.disabled = false;
      const d = frames.slice(1).sort((x, y) => x - y);
      const mean = 1000 / (d.reduce((s, x) => s + x, 0) / d.length);
      const p95 = d[Math.floor(d.length * 0.95)];
      const style = ($("tilted").getAttribute("aria-pressed") === "true" ? "tilted" : "flat") + ", " +
                    ($("ghost").getAttribute("aria-pressed") === "true" ? "translucent" : "solid") + ", " +
                    { "t-off": "no terrain", "t-shade": "shading", "t-3d": "3D ground" }[
                      ["t-off", "t-shade", "t-3d"].find((id) => $(id).getAttribute("aria-pressed") === "true")];
      $("fps").textContent = mean.toFixed(0) + " fps average, slowest 5% of frames over " + p95.toFixed(0) + " ms (" + style + ")";
    });
  });
};
