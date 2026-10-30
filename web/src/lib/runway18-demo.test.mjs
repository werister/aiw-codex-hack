import assert from "node:assert/strict";
import test from "node:test";
import {
  RUNWAY18_DEMO_PRESETS,
  evaluateRunway18Weather,
  runway18Demo,
  runway18PreparationReview,
} from "./runway18-demo.ts";

test("synthetic tailwind case crosses the challenge 15 kt departure threshold", () => {
  const exactLimit = evaluateRunway18Weather({ windFromDeg: 0, windKt: 15, gustKt: 15 });
  const belowLimit = evaluateRunway18Weather({ windFromDeg: 0, windKt: 14.9, gustKt: 14.9 });
  const publishedExample = runway18Demo("tailwind");

  assert.equal(exactLimit.reason, "tailwind");
  assert.equal(exactLimit.unusableByChallengeRule, true);
  assert.equal(belowLimit.unusableByChallengeRule, false);
  assert.equal(publishedExample.hours.length, 6);
  assert.equal(publishedExample.hours[1].reason, "tailwind");
  assert.deepEqual(publishedExample.restrictionIntervals, [{ startHour: 1, endHourExclusive: 4 }]);
});

test("crosswind closure requires gust crosswind strictly above 40 kt", () => {
  const exactLimit = evaluateRunway18Weather({ windFromDeg: 270, windKt: 30, gustKt: 40 });
  const overLimit = evaluateRunway18Weather({ windFromDeg: 270, windKt: 30, gustKt: 40.1 });
  const preset = runway18Demo("crosswind");

  assert.equal(exactLimit.gustCrosswindKt, 40);
  assert.equal(exactLimit.unusableByChallengeRule, false);
  assert.ok(overLimit.gustCrosswindKt > 40);
  assert.equal(overLimit.reason, "crosswind");
  assert.equal(preset.hours[2].reason, "crosswind");
  assert.equal(preset.hours[2].windKt, 35);
  assert.equal(preset.hours[2].gustKt, 41);
  assert.deepEqual(preset.restrictionIntervals, [{ startHour: 2, endHourExclusive: 4 }]);
});

test("synthetic examples remain outside recorded forecasts and aggregate evidence", () => {
  for (const id of Object.keys(RUNWAY18_DEMO_PRESETS)) {
    const scenario = runway18Demo(id);

    assert.equal(scenario.evidence.kind, "synthetic-weather-rule-scenario");
    assert.equal(scenario.evidence.includedInHistoricalEvidence, false);
    assert.equal(scenario.evidence.includedInAggregateQuality, false);
    assert.equal("observed" in scenario, false);
    assert.equal(scenario.hours.length, 6);
    assert.ok(scenario.hours.every((hour) => !("observed" in hour) && !("p_18_usable" in hour)));
    assert.equal("p_18_usable" in scenario, false);
  }
});

test("preparation review handles empty, zero, partial lead, and beyond-horizon input", () => {
  const { restrictionIntervals } = runway18Demo("tailwind");

  assert.deepEqual(runway18PreparationReview(restrictionIntervals, null), { status: "input-required" });
  assert.deepEqual(runway18PreparationReview(restrictionIntervals, 0), {
    status: "review-time",
    availableLeadMinutes: 60,
    reviewMinute: 60,
    preparationMinutes: 0,
  });
  assert.deepEqual(runway18PreparationReview(restrictionIntervals, 30), {
    status: "review-time",
    availableLeadMinutes: 60,
    reviewMinute: 30,
    preparationMinutes: 30,
  });
  assert.deepEqual(runway18PreparationReview(restrictionIntervals, 61), {
    status: "insufficient-lead",
    availableLeadMinutes: 60,
  });
  assert.deepEqual(runway18PreparationReview(restrictionIntervals, 1.5), { status: "invalid-input" });
  assert.deepEqual(runway18PreparationReview([], 20), { status: "no-restriction" });
});

