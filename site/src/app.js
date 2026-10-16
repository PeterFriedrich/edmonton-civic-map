// The lookup page: address or district in, one card per office holder out.
// The cards never wait for the map; the map is a separate chunk loaded after.
import { matchStreets, parse, titleStreet } from "./address.js";
import { distanceToBoundary, locate } from "./pip.js";

const $ = (id) => document.getElementById(id);
// Published data keeps fixed URLs across deploys, so it is revalidated, not
// stamped (docs/DECISIONS.md, 2026-10-15, Vite).
const getJSON = (path) => fetch(path, { cache: "no-cache" }).then((r) => {
  if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
  return r.json();
});

const BODIES = {
  edmonton_council: "Edmonton City Council",
  edmonton_public_schools: "Edmonton Public Schools board",
  edmonton_catholic_schools: "Edmonton Catholic Schools board",
  legislative_assembly_of_alberta: "Legislative Assembly of Alberta",
  house_of_commons: "House of Commons",
};
const SOURCES = {
  coe_wards: "City of Edmonton open data, ward layer",
  coe_council_contacts: "City of Edmonton open data, council contacts",
  coe_election_results_2025: "City of Edmonton, 2025 official election results",
  epsb_trustees: "Edmonton Public Schools, Board of Trustees page",
  ecsd_trustees: "Edmonton Catholic Schools, Board of Trustees page",
  ab_mlas: "Legislative Assembly of Alberta, MLA contact list",
  ab_mla_list: "Legislative Assembly of Alberta, members page",
  ca_mps: "House of Commons, list of members",
};
// How each layer's district reads in a sentence.
const NOUN = {
  council_ward: "council ward", public_school_ward: "public school ward", catholic_school_ward: "Catholic school ward",
  provincial_riding: "provincial electoral division", federal_riding: "federal electoral district",
};
const AFFILIATION_LABEL = { ab_mlas: "Caucus", ca_mps: "Political affiliation" };
// Each body's own address lookup, for an address near a line. Checked 2026-10-16.
const OFFICIAL_LOOKUP = {
  council_ward: ["City of Edmonton ward maps", "https://www.edmonton.ca/city_government/municipal_elections/ward-maps"],
  public_school_ward: ["Edmonton Public Schools, Find My Trustee", "https://www.epsb.ca/ourdistrict/board/trustees/findmytrustee/"],
  catholic_school_ward: ["Edmonton Catholic Schools trustees and ward maps", "https://www.ecsd.net/ecsd-trustees"],
  provincial_riding: ["Elections Alberta, Where to Vote", "https://www.elections.ab.ca/where-to-vote-tool/"],
  federal_riding: ["Elections Canada, Find your electoral district", "https://www.elections.ca/Scripts/vis/FindED?L=e"],
};

const state = { layers: null, seats: null, stale: null, names: {}, boundaries: {}, streets: null, files: new Map(), map: null, last: null };

const ready = Promise.all([
  getJSON("data/layers.json"),
  getJSON("data/officeholders.json"),
  getJSON("data/staleness.json"), // thresholds: docs/SPEC_data_schema.md §6, §7 point 3
]).then(([layers, seats, stale]) => {
  state.layers = layers;
  state.stale = stale;
  state.seats = new Map(seats.map((s) => [s.seat_id, s]));
  $("built").textContent = seats.map((s) => s.last_verified).sort().at(-1);
});
// District names come from the boundary files, which the map also draws.
const boundariesReady = ready.then(() => Promise.all(state.layers.map(async (l) => {
  const fc = await getJSON("data/" + l.file);
  state.boundaries[l.id] = fc;
  for (const f of fc.features) state.names[f.properties.district_id] = f.properties.name;
})));
const streetsReady = getJSON("data/addresses/streets.json").then((s) => (state.streets = s));

function fail(err) {
  console.error(err);
  $("results").innerHTML = `<p class="notice">The data did not load. Try reloading the page.</p>`;
}
Promise.all([ready, boundariesReady]).then(fillPicker).catch(fail);

// --- cards --------------------------------------------------------------------

const el = (tag, attrs = {}, ...kids) => {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  e.append(...kids.filter((k) => k !== null && k !== undefined));
  return e;
};
const link = (href, text) => el("a", { href, rel: "noopener" }, text);
const daysSince = (iso) => Math.floor((Date.now() - Date.parse(iso + "T00:00:00Z")) / 864e5);

function card(seat, notes = [], warns = []) {
  const name = seat.district_id ? state.names[seat.district_id] : "City-wide";
  const level = `${BODIES[seat.body]} · ${seat.district_id?.startsWith("council_ward:") ? "Ward " + name : name}`;
  const showAff = $("affiliation").checked && seat.affiliation;
  const stale = daysSince(seat.last_verified) > state.stale.officeholders_days;
  return el("article", { class: "card" },
    el("p", { class: "level" }, level),
    el("h3", {}, seat.vacant ? "Seat vacant" : seat.name),
    el("p", { class: "role" }, seat.role),
    showAff ? el("p", { class: "aff" }, `${AFFILIATION_LABEL[seat.affiliation_source_id] || "Affiliation"}: ${seat.affiliation} (${SOURCES[seat.affiliation_source_id]})`) : null,
    seat.contact_url ? el("p", {}, link(seat.contact_url, "Official page and contact")) : null,
    el("p", { class: "meta" }, "Source: ", link(seat.source_url, SOURCES[seat.source_id] || seat.source_id),
      ` · last checked ${seat.last_verified}`),
    stale ? el("p", { class: "note warn" }, `Not re-checked against its source for ${daysSince(seat.last_verified)} days. Check the official page.`) : null,
    ...notes.map((n) => el("p", { class: "note" }, ...n)),
    ...warns.map((n) => el("p", { class: "note warn" }, ...n)),
  );
}

// One entry per layer: { layer, ids: [district_id...], near: bool, kind: "split"|"overlap"|"gap"|null }
function render(title, perLayer, point, what = "This address") {
  const out = $("results");
  out.replaceChildren(el("h2", { tabindex: "-1" }, title));
  for (const { layer, ids, near, kind } of perLayer) {
    const noun = NOUN[layer.id];
    const [lookupName, lookupUrl] = OFFICIAL_LOOKUP[layer.id];
    const notes = [], warns = [];
    const age = daysSince(layer.last_verified);
    if (age > state.stale.boundaries_days) warns.push([`The ${noun} boundaries were last checked against their source ${age} days ago. Confirm with the official lookup: `, link(lookupUrl, lookupName), "."]);
    if (kind === "split") notes.push([`This address has parcels in more than one ${noun}. Each is shown.`]);
    if (kind === "overlap") notes.push([`This point falls where two ${noun}s overlap in the published boundaries. Both are shown.`]);
    if (near) notes.push([`${what} is within ${layer.near_boundary_m} m of a ${noun} boundary. Confirm with the official lookup: `, link(lookupUrl, lookupName), "."]);
    if (!ids.length) {
      out.append(el("p", { class: "notice" }, `No ${noun} found at this point; it may sit in a small gap between published boundaries. Check `, link(lookupUrl, lookupName), "."));
    }
    for (const id of ids) {
      const seat = state.seats.get(id);
      out.append(seat ? card(seat, notes, warns) : el("p", { class: "notice" }, `No office holder is listed for ${id}.`));
    }
    if (layer.id === "council_ward") out.append(card(state.seats.get("edmonton_council:mayor")));
  }
  const ids = perLayer.flatMap((p) => p.ids);
  state.last = { title, perLayer, point, what };
  state.map?.show(point, ids);
  out.querySelector("h2").focus({ preventScroll: true });
}

// --- address search -----------------------------------------------------------

const input = $("q"), list = $("suggestions");
let options = [], active = -1, seq = 0;

async function streetFile(file) {
  if (!state.files.has(file)) state.files.set(file, getJSON("data/addresses/" + file));
  return state.files.get(file);
}

function showOptions(items, note) {
  options = items; active = -1;
  list.replaceChildren(...items.map((o, i) => el("li", { id: `opt-${i}`, role: "option", "aria-selected": "false" }, o.label)));
  if (note) list.append(el("li", { class: "note", role: "presentation" }, note));
  const open = items.length > 0 || Boolean(note);
  list.hidden = !open;
  input.setAttribute("aria-expanded", String(open));
  input.removeAttribute("aria-activedescendant");
}

async function suggest() {
  const my = ++seq;
  const text = input.value.trim();
  if (text.length < 2) return showOptions([]);
  await streetsReady;
  const { house, words } = parse(text);
  const streets = matchStreets(words, state.streets, house ? 4 : 8);
  if (!streets.length) return showOptions([], "No Edmonton street matches that.");
  if (!house) {
    return showOptions(streets.map((s) => ({ label: titleStreet(s.name), street: s })),
      "Add the house number to look up an address.");
  }
  const found = [];
  for (const s of streets) {
    const recs = (await streetFile(s.file))[house];
    if (recs) found.push({ label: `${house} ${titleStreet(s.name)}`, street: s, house, recs });
  }
  if (my !== seq) return; // a newer keystroke won
  showOptions(found, found.length ? null : `No address ${house} on ${titleStreet(streets[0].name)}${streets.length > 1 ? " or similar streets" : ""}.`);
}

function choose(o) {
  showOptions([]);
  if (!o.house) {
    input.value = titleStreet(o.street.name) + " ";
    input.setSelectionRange(0, 0);
    input.focus();
    return;
  }
  input.value = o.label;
  lookupAddress(o.label, o.recs);
}

function lookupAddress(label, recs) {
  Promise.all([ready, boundariesReady]).then(() => {
    const perLayer = state.layers.map((layer, i) => {
      const ids = [...new Set(recs.map((r) => r[2 + i]))];
      const near = recs.some((r) => r[7] & (1 << i));
      return { layer, ids, near, kind: ids.length > 1 ? "split" : null };
    });
    render(label, perLayer, [recs[0][1], recs[0][0]]);
  }).catch(fail);
}

function move(d) {
  if (!options.length) return;
  active = (active + d + options.length) % options.length;
  list.querySelectorAll('[role="option"]').forEach((li, i) => li.setAttribute("aria-selected", String(i === active)));
  input.setAttribute("aria-activedescendant", `opt-${active}`);
  list.querySelector(`#opt-${active}`).scrollIntoView({ block: "nearest" });
}

input.addEventListener("input", () => suggest().catch(fail));
input.addEventListener("keydown", (e) => {
  if (e.key === "ArrowDown") { e.preventDefault(); move(1); }
  else if (e.key === "ArrowUp") { e.preventDefault(); move(-1); }
  else if (e.key === "Escape") showOptions([]);
});
$("search").addEventListener("submit", (e) => {
  e.preventDefault();
  const o = options[active >= 0 ? active : 0];
  if (o) choose(o);
});
list.addEventListener("mousedown", (e) => e.preventDefault()); // keep focus in the input
list.addEventListener("click", (e) => {
  const li = e.target.closest('[role="option"]');
  if (li) choose(options[Number(li.id.slice(4))]);
});
input.addEventListener("blur", () => setTimeout(() => showOptions([]), 100));

// --- choose a district from a list ---------------------------------------------

function fillPicker() {
  const pick = $("pick");
  for (const layer of state.layers) {
    const group = el("optgroup", { label: layer.label });
    const feats = [...state.boundaries[layer.id].features]
      .filter((f) => state.seats.has(f.properties.district_id))
      .sort((a, b) => a.properties.name.localeCompare(b.properties.name, "en", { numeric: true }));
    for (const f of feats) group.append(el("option", { value: f.properties.district_id }, f.properties.name));
    pick.append(group);
  }
  pick.addEventListener("change", () => {
    const id = pick.value;
    if (!id) return;
    const layer = state.layers.find((l) => id.startsWith(l.id + ":"));
    render(`${layer.label}: ${state.names[id]}`, [{ layer, ids: [id], near: false, kind: null }], null);
  });
}

// --- map clicks -----------------------------------------------------------------

function lookupPoint(lon, lat) {
  const perLayer = state.layers.map((layer) => {
    const fc = state.boundaries[layer.id];
    const ids = locate(lon, lat, fc).map((i) => fc.features[i].properties.district_id);
    const near = distanceToBoundary(lon, lat, fc) <= layer.near_boundary_m;
    return { layer, ids, near, kind: ids.length > 1 ? "overlap" : null };
  });
  if (!perLayer[0].ids.length) {
    $("results").replaceChildren(el("p", { class: "notice" }, "That point is outside the City of Edmonton. This map covers Edmonton addresses only."));
    state.map?.show([lon, lat], []);
    return;
  }
  render(`Map point ${lat.toFixed(5)}, ${lon.toFixed(5)}`, perLayer, [lon, lat], "This point");
}

$("affiliation").addEventListener("change", () => {
  if (state.last) render(state.last.title, state.last.perLayer, state.last.point, state.last.what);
});

// --- the map, after the cards ------------------------------------------------------

Promise.all([ready, boundariesReady]).then(async () => {
  const { createMap } = await import("./map.js");
  state.map = await createMap({
    container: $("map"), layers: state.layers, boundaries: state.boundaries,
    buttons: $("layer-buttons"), tilt: $("tilt"), status: $("map-status"),
    onClick: lookupPoint,
  });
  if (state.last) state.map.show(state.last.point, state.last.perLayer.flatMap((p) => p.ids));
}).catch((e) => {
  console.error(e);
  $("map-status").textContent = "The map could not load. The lookup still works.";
});
