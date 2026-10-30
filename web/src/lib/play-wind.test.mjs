import assert from "node:assert/strict";
import test from "node:test";
import { playWind } from "./play-wind.ts";

test("10 kt tailwind on the landing direction flips it, 9.9 kt does not", () => {
  // Wind from 070 at 10 kt is a 10 kt tailwind for landings toward 250.
  assert.equal(playWind("25", 70, 10).od, "07");
  const held = playWind("25", 70, 9.9);
  assert.equal(held.od, "25");
  assert.equal(held.tolerated, true);
});

test("headwind keeps the direction and is not a tolerated tailwind", () => {
  const r = playWind("25", 250, 20);
  assert.equal(r.od, "25");
  assert.equal(r.tolerated, false);
});

test("runway 18 closes at 15 kt tailwind from the north", () => {
  assert.equal(playWind("25", 0, 15).r18Open, false);
  assert.equal(playWind("25", 0, 14.9).r18Open, true);
});

test("calm keeps the current direction", () => {
  assert.equal(playWind("07", 0, 0).od, "07");
});
