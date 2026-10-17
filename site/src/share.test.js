// node --test site/src: the share link.
import assert from "node:assert/strict";
import { test } from "node:test";
import { decode, encode } from "./share.js";

const ids = ["council_ward:metis", "public_school_ward:D", "catholic_school_ward:75", "provincial_riding:33", "federal_riding:48022"];
const address = { kind: "address", label: "6203 100 Avenue NW", ids };
const point = { kind: "point", lat: 53.540029, lon: -113.428509, ids };

test("by default an address or a map point is shared as its districts only", () => {
  for (const sel of [address, point]) {
    const h = encode(sel, { lines: "federal_riding", tilt: true });
    assert.equal(h, "#d=council_ward:metis,public_school_ward:D,catholic_school_ward:75,provincial_riding:33,federal_riding:48022&lines=federal_riding&3d=1");
    assert.doesNotMatch(h, /6203|53\.54|113\.42/);
    assert.deepEqual(decode(h), { sel: { kind: "districts", ids }, view: { lines: "federal_riding", tilt: true } });
  }
});

test("an address or point is in the link only when the reader includes it", () => {
  assert.equal(encode(address, {}, true), "#a=6203+100+Avenue+NW");
  assert.deepEqual(decode("#a=6203+100+Avenue+NW").sel, { kind: "address", label: "6203 100 Avenue NW" });
  assert.equal(encode(point, {}, true), "#p=53.54003,-113.42851");
  assert.deepEqual(decode("#p=53.54003,-113.42851").sel, { kind: "point", lat: 53.54003, lon: -113.42851 });
});

test("districts and neighbourhoods round-trip, diacritics included", () => {
  const d = { kind: "districts", ids: ["council_ward:pihesiwin"] };
  assert.deepEqual(decode(encode(d)).sel, d);
  const n = { kind: "neighbourhood", id: "neighbourhood:6662" };
  assert.equal(encode(n), "#n=6662");
  assert.deepEqual(decode(encode(n)).sel, n);
  const a = { kind: "address", label: "1 Maskêkosihk Trail NW", ids };
  assert.deepEqual(decode(encode(a, {}, true)).sel, { kind: "address", label: a.label });
});

test("the default view adds nothing; bad or unknown input is ignored", () => {
  assert.equal(encode(null, { lines: "council_ward", tilt: false }), "");
  assert.deepEqual(decode(""), { sel: null, view: { lines: null, tilt: false } });
  assert.deepEqual(decode("#lens=density&zzz"), { sel: null, view: { lines: null, tilt: false } });
  assert.equal(decode("#p=abc").sel, null);
  assert.equal(decode("#a=%E0%A4").sel, null);
});
