// Address matching against the street list (site/public/data/addresses/streets.json).
// Pure functions: nothing here touches the network, and the typed text is never
// stored or sent anywhere.

// Street-type abbreviations people write that are not a prefix of the full word
// (AVE, ST, PL and CL already are). Applied only to the word after the street
// name's first word, so "ST ALBERT TRAIL" keeps its ST.
const TYPES = {
  RD: "ROAD", DR: "DRIVE", BLVD: "BOULEVARD", CT: "COURT", LN: "LANE", PT: "POINT",
  TRL: "TRAIL", GRN: "GREEN", LDG: "LANDING", HTS: "HEIGHTS", PKWY: "PARKWAY",
  TERR: "TERRACE", CRT: "COURT", WY: "WAY", LK: "LINK", CV: "COVE", CMN: "COMMON",
};
const STREET_TYPES = ["AVENUE", "STREET", "ROAD", "DRIVE", "BOULEVARD", "CRESCENT", "TRAIL", "WAY"];
const QUADRANTS = new Set(["NW", "SW", "NE", "SE"]);

export function normalise(text) {
  return text
    .toUpperCase()
    .normalize("NFKD").replace(/[̀-ͯ]/g, "")
    .replace(/[.,#]/g, " ")
    .replace(/\b(\d+)(ST|ND|RD|TH)\b/g, "$1") // 104th -> 104
    .split(/\s+/).filter(Boolean);
}

// A word that only says what kind of street, or where: AVE, AV, STREET, NW.
function isTypeWord(w) {
  return QUADRANTS.has(w) || w in TYPES || STREET_TYPES.some((t) => t.startsWith(w));
}

// "10220 104 Ave NW" -> { house: "10220", words: ["104", "AVE", "NW"] }. A leading
// number is the house unless only a street type follows it ("104 Ave" is a street).
// House numbers are digits only in the index. A unit written "301-10220 104 Ave"
// or "#301 10220 104 Ave" is dropped.
export function parse(text) {
  let words = normalise(text.replace(/^\s*#?\s*\d+[A-Z]?\s*-\s*(?=\d)/i, ""));
  // "#301 10220 104 Ave": three numbers in a row means the first is a unit
  if (words.length > 2 && words.slice(0, 3).every((w) => /^\d/.test(w))) words = words.slice(1);
  let house = null;
  if (words.length > 1 && /^\d+$/.test(words[0]) && !words.slice(1).every(isTypeWord)) {
    house = words[0];
    words = words.slice(1);
  }
  return { house, words };
}

function wordMatches(q, w) {
  if (q === w) return 2;
  if (/^\d/.test(q)) return 0; // street numbers match exactly: 104 is not 1040
  return w.startsWith(q) ? 1 : 0;
}

// Streets matching the typed words, best first. Every typed word must match a
// distinct word of the street name; a missing quadrant prefers NW, where most
// addresses are.
export function matchStreets(words, streets, limit = 8) {
  if (!words.length) return [];
  const query = words.map((w, i) => (i > 0 && TYPES[w]) || w);
  const typedQuadrant = query.some((w) => QUADRANTS.has(w));
  const scored = [];
  for (const [name, file] of streets) {
    const parts = name.split(" ");
    const used = new Set();
    let score = 0;
    for (const q of query) {
      let best = 0, at = -1;
      parts.forEach((w, i) => {
        if (used.has(i)) return;
        const s = wordMatches(q, w);
        if (s > best) { best = s; at = i; }
      });
      if (!best) { score = -1; break; }
      used.add(at); score += best;
    }
    if (score < 0) continue;
    if (!typedQuadrant && parts.at(-1) === "NW") score += 0.5;
    scored.push({ name, file, score });
  }
  scored.sort((a, b) => b.score - a.score || a.name.length - b.name.length || a.name.localeCompare(b.name));
  return scored.slice(0, limit);
}

// "104 AVENUE NW" -> "104 Avenue NW" for display.
export function titleStreet(name) {
  return name.split(" ").map((w) => (QUADRANTS.has(w) || /^\d/.test(w) ? w : w[0] + w.slice(1).toLowerCase())).join(" ");
}

// "Hollick-Kenyon", "River's Edge": a hyphen splits words and an apostrophe joins them.
const nameWords = (text) => normalise(text.replace(/-/g, " ").replace(/['’]/g, ""));

// Neighbourhoods (site/public/data/neighbourhoods.json) whose name has a distinct
// word starting with each typed word, case and accents ignored, best first.
export function matchNeighbourhoods(text, hoods, limit = 3) {
  const query = nameWords(text);
  if (!query.length) return [];
  const scored = [];
  for (const h of hoods) {
    const parts = (h._words ??= nameWords(h.name));
    const used = new Set();
    let score = 0;
    for (const q of query) {
      const at = parts.findIndex((w, i) => !used.has(i) && w.startsWith(q));
      if (at < 0) { score = -1; break; }
      used.add(at); score += parts[at] === q ? 2 : 1;
    }
    if (score >= 0) scored.push({ hood: h, score: score - parts.length / 100 });
  }
  scored.sort((a, b) => b.score - a.score || a.hood.name.localeCompare(b.hood.name));
  return scored.slice(0, limit).map((s) => s.hood);
}
