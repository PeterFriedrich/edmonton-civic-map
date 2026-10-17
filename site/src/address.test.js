// node --test site/src: the address matcher against the real street list.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { matchNeighbourhoods, matchStreets, parse, titleStreet } from "./address.js";

const streets = JSON.parse(readFileSync(new URL("../public/data/addresses/streets.json", import.meta.url), "utf8"));
const top = (text) => matchStreets(parse(text).words, streets)[0]?.name;

test("house number and street are split the way Edmontonians write them", () => {
  assert.deepEqual(parse("10220 104 Ave NW"), { house: "10220", words: ["104", "AVE", "NW"] });
  assert.deepEqual(parse("10220 104th avenue"), { house: "10220", words: ["104", "AVENUE"] });
  assert.deepEqual(parse("1650 Hector Rd"), { house: "1650", words: ["HECTOR", "RD"] });
  assert.deepEqual(parse("104 Ave"), { house: null, words: ["104", "AVE"] });
  assert.deepEqual(parse("301-10220 104 Ave"), { house: "10220", words: ["104", "AVE"] });
  assert.deepEqual(parse("#301 10220 104 Ave"), { house: "10220", words: ["104", "AVE"] });
});

test("streets match abbreviations, ordinals and a missing quadrant", () => {
  assert.equal(top("10220 104 Ave"), "104 AVENUE NW");
  assert.equal(top("10220 104 st"), "104 STREET NW");
  assert.equal(top("3705 141 street sw"), "141 STREET SW");
  assert.equal(top("1650 hector rd"), "HECTOR ROAD NW");
  assert.equal(top("12702 st albert trail"), "ST ALBERT TRAIL NW");
  assert.equal(top("100a st"), "100A STREET NW");
});

test("a street number never matches a longer number", () => {
  assert.ok(matchStreets(["104", "AVENUE"], streets).every((s) => s.name.split(" ")[0] === "104"));
  assert.deepEqual(matchStreets(["NOSUCHSTREET"], streets), []);
});

test("street names display in title case with numbers and quadrants kept", () => {
  assert.equal(titleStreet("ST ALBERT TRAIL NW"), "St Albert Trail NW");
  assert.equal(titleStreet("100A STREET NW"), "100A Street NW");
});

const hoods = JSON.parse(readFileSync(new URL("../public/data/neighbourhoods.json", import.meta.url), "utf8"));
const hood = (text) => matchNeighbourhoods(text, hoods).map((h) => h.name);

test("neighbourhood names match by word prefix, ignoring case, accents and punctuation", () => {
  assert.equal(hood("walker")[0], "Walker");
  assert.equal(hood("wihkwentowin")[0], "Wîhkwêntôwin");
  assert.equal(hood("rivers edge")[0], "River's Edge");
  assert.equal(hood("kenyon")[0], "Hollick-Kenyon");
  assert.equal(hood("orchards")[0], "The Orchards At Ellerslie");
  assert.deepEqual(hood("104 ave"), []);
});
