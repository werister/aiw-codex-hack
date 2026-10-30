import assert from "node:assert/strict";
import test from "node:test";
import { mkdtempSync, readFileSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { execFileSync } from "node:child_process";
import { planningReviewFor, planningAssetPath, preparationTime } from "./planning-decisions.ts";

const source = new URL("../../public/forecasts/2026-10-29.json", import.meta.url);
const forecast = JSON.parse(readFileSync(source, "utf8"));
const directory = mkdtempSync(join(tmpdir(), "planning-review-contract-"));
const input = join(directory, "case.json");
writeFileSync(input, JSON.stringify(forecast));
execFileSync("python3", [new URL("../../../tools/forecast_decisions.py", import.meta.url).pathname,
  input, "--offline", "--output-dir", join(directory, "reviews")]);
const review = JSON.parse(readFileSync(join(directory, "reviews/case.json"), "utf8"));
rmSync(directory, { recursive: true });

test("producer review binds to exact forecast values, not merely filename and issue time", () => {
  assert.ok(planningReviewFor(review, forecast));
  const changed = structuredClone(forecast);
  changed.hours[0].p_od25 = .123456;
  assert.equal(planningReviewFor(review, changed), null);
});

test("later observed outcomes neither enter nor invalidate the planning review", () => {
  assert.equal("observed" in review.forecast_basis, false);
  assert.ok(planningReviewFor(review, { ...forecast, observed: [] }));
});

test("invalid selections, indices and mismatched times cannot reach the UI", () => {
  const changed = structuredClone(review);
  changed.selections.ground_operations.candidate_id = "fabricated";
  assert.equal(planningReviewFor(changed, forecast), null);
  const badIndex = structuredClone(review);
  badIndex.candidates[0].hour_indices = [-1];
  assert.equal(planningReviewFor(badIndex, forecast), null);
  const badTime = structuredClone(review);
  badTime.candidates[0].time = "2027-01-01T00:00Z";
  assert.equal(planningReviewFor(badTime, forecast), null);
});

test("preparation uses UTC across daylight saving and exposes insufficient lead", () => {
  assert.deepEqual(preparationTime("2026-10-25T02:00Z", "60", "2026-10-25T00:00Z"),
    { time: "2026-10-25T01:00:00.000Z", enoughLead: true });
  assert.equal(preparationTime("2026-10-25T02:00Z", "180", "2026-10-25T00:00Z").enoughLead, false);
  for (const value of ["", "-1", "1.5", "1441", "NaN"]) assert.equal(preparationTime(forecast.hours[0].time, value, forecast.issued_at), null);
});

test("only published forecast filenames become review URLs", () => {
  assert.equal(planningAssetPath("latest.json"), "/decisions/latest.json");
  assert.equal(planningAssetPath("2026-10-29.json"), "/decisions/2026-10-29.json");
  for (const value of [null, "../secret.json", "https://external.example/test.json"]) assert.equal(planningAssetPath(value), null);
});
