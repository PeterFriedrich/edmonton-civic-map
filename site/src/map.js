// The map: ghost buildings for context, one boundary layer's lines at a time,
// the selected districts filled, and the looked-up point. Loaded after the
// cards, as its own chunk, so a slow device still gets its answer first.
import * as maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?url";
import { Protocol } from "pmtiles";

maplibregl.setWorkerUrl(workerUrl);
maplibregl.addProtocol("pmtiles", new Protocol().tile);

const SHORT = { council_ward: "Council", public_school_ward: "Public school", catholic_school_ward: "Catholic school",
  provincial_riding: "Provincial", federal_riding: "Federal" };
const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

function bbox(fc) {
  let w = Infinity, s = Infinity, e = -Infinity, n = -Infinity;
  for (const f of fc.features) {
    const polys = f.geometry.type === "Polygon" ? [f.geometry.coordinates] : f.geometry.coordinates;
    for (const p of polys) for (const [x, y] of p[0]) { w = Math.min(w, x); e = Math.max(e, x); s = Math.min(s, y); n = Math.max(n, y); }
  }
  return [[w, s], [e, n]];
}

export function createMap({ container, layers, boundaries, buttons, tilt, status, onClick }) {
  const cityBounds = bbox(boundaries.council_ward);
  const sources = {
    buildings: { type: "vector", url: "pmtiles://" + new URL("data/buildings.pmtiles", location.href).href },
    point: { type: "geojson", data: { type: "FeatureCollection", features: [] } },
  };
  const style = [
    { id: "bg", type: "background", paint: { "background-color": css("--map-bg") } },
    { id: "buildings", type: "fill-extrusion", source: "buildings", "source-layer": "buildings",
      paint: { "fill-extrusion-color": css("--building"), "fill-extrusion-height": ["get", "h"], "fill-extrusion-opacity": 0.3 } },
  ];
  for (const l of layers) {
    sources[l.id] = { type: "geojson", data: boundaries[l.id] };
    const visibility = l.id === "council_ward" ? "visible" : "none";
    style.push(
      { id: `${l.id}-selected`, type: "fill", source: l.id, filter: ["in", ["get", "district_id"], ["literal", []]],
        layout: { visibility: "visible" }, paint: { "fill-color": css("--boundary"), "fill-opacity": 0.14 } },
      { id: `${l.id}-line`, type: "line", source: l.id, layout: { visibility },
        paint: { "line-color": css("--boundary"), "line-width": 1.6 } },
      { id: `${l.id}-selected-line`, type: "line", source: l.id, filter: ["in", ["get", "district_id"], ["literal", []]],
        layout: { visibility }, paint: { "line-color": css("--boundary"), "line-width": 3.5 } },
    );
  }
  style.push({ id: "point", type: "circle", source: "point",
    paint: { "circle-radius": 7, "circle-color": css("--point"), "circle-stroke-width": 2, "circle-stroke-color": "#ffffff" } });

  const map = new maplibregl.Map({
    container, bounds: cityBounds, fitBoundsOptions: { padding: 30 }, maxPitch: 65, minZoom: 8,
    attributionControl: false, style: { version: 8, sources, layers: style },
  });
  map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "bottom-right");
  map.addControl(new maplibregl.AttributionControl({
    compact: true,
    customAttribution: "Buildings: City of Edmonton Rooflines (2019) · Boundaries: City of Edmonton, Government of Alberta, Elections Canada",
  }));
  map.on("click", (e) => onClick(e.lngLat.lng, e.lngLat.lat));
  map.getCanvas().style.cursor = "crosshair";

  let shown = "council_ward";
  function showLayer(id) {
    shown = id;
    for (const l of layers) {
      const v = l.id === id ? "visible" : "none";
      map.setLayoutProperty(`${l.id}-line`, "visibility", v);
      map.setLayoutProperty(`${l.id}-selected-line`, "visibility", v);
      map.setLayoutProperty(`${l.id}-selected`, "visibility", v);
    }
    for (const b of buttons.children) b.setAttribute("aria-pressed", String(b.dataset.layer === id));
  }
  for (const l of layers) {
    const b = document.createElement("button");
    b.type = "button"; b.dataset.layer = l.id; b.textContent = SHORT[l.id] || l.label;
    b.setAttribute("aria-label", l.label);
    b.setAttribute("aria-pressed", String(l.id === shown));
    b.onclick = () => showLayer(l.id);
    buttons.append(b);
  }
  tilt.onclick = () => {
    const on = tilt.getAttribute("aria-pressed") !== "true";
    tilt.setAttribute("aria-pressed", String(on));
    map.easeTo({ pitch: on ? 55 : 0, bearing: on ? -15 : 0 });
  };

  return new Promise((resolve) => map.once("load", () => {
    status.textContent = "";
    // The compact attribution opens on load and would cover a phone-sized map; the (i) button reopens it.
    container.querySelector(".maplibregl-ctrl-attrib")?.classList.remove("maplibregl-compact-show");
    showLayer(shown);
    resolve({
      // point: [lon, lat] or null; ids: the selected district ids in every layer.
      show(point, ids) {
        for (const l of layers) {
          const mine = ids.filter((id) => id.startsWith(l.id + ":"));
          const f = ["in", ["get", "district_id"], ["literal", mine]];
          map.setFilter(`${l.id}-selected`, f);
          map.setFilter(`${l.id}-selected-line`, f);
        }
        const only = ids.length === 1 && ids[0].split(":")[0];
        if (only && only !== shown) showLayer(only);
        map.getSource("point").setData({ type: "FeatureCollection",
          features: point ? [{ type: "Feature", properties: {}, geometry: { type: "Point", coordinates: point } }] : [] });
        if (point) map.easeTo({ center: point, zoom: Math.max(map.getZoom(), 13) });
        else if (only) map.fitBounds(bbox({ features: boundaries[only].features.filter((f) => f.properties.district_id === ids[0]) }), { padding: 40 });
      },
    });
  }));
}
