import assert from "node:assert/strict";
import test from "node:test";
import { firstRecordedOpposite, formatPitchTime, planningEvent, scoreReplay } from "./pitch-replay.ts";

function hour(time, od, rule_od = od, local = time.slice(0, 16)) {
  return { time, local, od, rule_od };
}

function forecast(overrides = {}) {
  return {
    issued_at: "2026-10-27T23:00:00Z",
    current_od: "25",
    hours: [],
    observed: [],
    next_change: null,
    closures_18: [],
    ...overrides,
  };
}

test("scores model, rule, and persistence on one unique matched-hour denominator", () => {
  const f = forecast({
    hours: [
      hour("2026-10-28T00:00:00Z", "25"),
      hour("2026-10-28T01:00:00Z", "07", "25"),
      hour("2026-10-28T02:00:00Z", "07", "07"),
      hour("2026-10-28T03:00:00Z", "25"),
      hour("2026-10-28T04:00:00Z", "invalid"),
    ],
    observed: [
      { time: "2026-10-28T00:00:00Z", od: "25", r18_usable: true },
      { time: "2026-10-28T01:00:00Z", od: "25", r18_usable: true },
      { time: "2026-10-28T02:00:00Z", od: "07", r18_usable: true },
      { time: "2026-10-28T04:00:00Z", od: "25", r18_usable: false },
      { time: "2026-10-28T05:00:00Z", od: "07", r18_usable: true },
      { time: "2026-10-28T00:00:00Z", od: "25", r18_usable: true },
    ],
  });

  assert.deepEqual(scoreReplay(f), {
    matchedHours: 3,
    totalHours: 5,
    modelCorrect: 2,
    ruleCorrect: 3,
    persistenceCorrect: 2,
  });
});

test("returns a zero score when no recorded valid OD labels are available", () => {
  const f = forecast({
    hours: [hour("2026-10-28T00:00:00Z", "25")],
    observed: [{ time: "2026-10-28T00:00:00Z", od: null, r18_usable: null }],
  });

  assert.deepEqual(scoreReplay(f), {
    matchedHours: 0,
    totalHours: 1,
    modelCorrect: 0,
    ruleCorrect: 0,
    persistenceCorrect: 0,
  });
});

test("does not choose between conflicting labels or duplicate forecasts for one hour", () => {
  const f = forecast({
    hours: [
      hour("2026-10-28T00:00:00Z", "25"),
      hour("2026-10-28T00:00:00Z", "07"),
      hour("2026-10-28T01:00:00Z", "25"),
    ],
    observed: [
      { time: "2026-10-28T00:00:00Z", od: "25", r18_usable: true },
      { time: "2026-10-28T01:00:00Z", od: "25", r18_usable: true },
      { time: "2026-10-28T01:00:00Z", od: "07", r18_usable: true },
    ],
  });

  assert.deepEqual(scoreReplay(f), {
    matchedHours: 0,
    totalHours: 3,
    modelCorrect: 0,
    ruleCorrect: 0,
    persistenceCorrect: 0,
  });
});

test("returns the earliest recorded opposite OD after issue time, not an exact transition claim", () => {
  const f = forecast({
    observed: [
      { time: "2026-10-27T23:00:00Z", od: "07", r18_usable: true },
      { time: "2026-10-28T02:00:00Z", od: "25", r18_usable: true },
      { time: "2026-10-28T03:00:00Z", od: "07", r18_usable: true },
    ],
  });

  assert.deepEqual(firstRecordedOpposite(f), { time: "2026-10-28T03:00:00Z", od: "07" });
});

test("chooses the earliest planning event and maps the local window to its forecast UTC hour", () => {
  const f = forecast({
    hours: [
      hour("2026-10-29T08:00:00Z", "25", "25", "2026-10-29T09:00"),
      hour("2026-10-29T09:00:00Z", "25", "25", "2026-10-29T10:00"),
    ],
    next_change: {
      time: "2026-10-29T09:00:00Z",
      window_local: ["2026-10-29T09:00", "2026-10-29T10:00"],
    },
    closures_18: [{ start: "2026-10-29T07:30:00Z" }],
  });

  assert.deepEqual(planningEvent(f), { kind: "runway18", time: "2026-10-29T07:30:00Z" });
  f.closures_18 = [];
  assert.deepEqual(planningEvent(f), { kind: "direction", time: "2026-10-29T08:00:00Z" });
});

test("uses the actual change time if its local window cannot map to a future forecast hour", () => {
  const f = forecast({
    next_change: {
      time: "2026-10-28T02:00:00Z",
      window_local: ["2030-01-01T01:00", "2030-01-01T02:00"],
    },
  });

  assert.deepEqual(planningEvent(f), { kind: "direction", time: "2026-10-28T02:00:00Z" });
});

test("falls back when an autumn clock-change local hour maps to two UTC hours", () => {
  const f = forecast({
    hours: [
      hour("2026-10-25T00:00:00Z", "25", "25", "2026-10-25T02:00"),
      hour("2026-10-25T01:00:00Z", "25", "25", "2026-10-25T02:00"),
    ],
    issued_at: "2026-10-24T23:00:00Z",
    next_change: {
      time: "2026-10-25T02:00:00Z",
      window_local: ["2026-10-25T02:00", "2026-10-25T03:00"],
    },
  });

  assert.deepEqual(planningEvent(f), { kind: "direction", time: "2026-10-25T02:00:00Z" });
});

test("formats UTC timestamps in Berlin local day, month, hour, and minute", () => {
  assert.equal(formatPitchTime("2026-10-28T00:00:00Z"), "28.10., 01:00");
  assert.equal(formatPitchTime("not-a-time"), "—");
});
