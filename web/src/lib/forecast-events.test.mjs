import assert from "node:assert/strict";
import test from "node:test";
import { forecastCoverage, forecastEvents, formatForecastInstant } from "./forecast-events.ts";

const issue = {
  issued_at: "2026-10-30T11:00Z",
  issued_local: "2026-10-30T12:00",
  mode: "live",
  current_od: "25",
  nwp: "Open-Meteo",
  model_version: "test",
  rules_version: "test",
  hours: [],
  next_change: null,
  closures_18: [],
};

function hour(utcHour, lead, { od = "25", p25 = 0.8, p18 = 0.9 } = {}) {
  const date = new Date(Date.parse("2026-10-30T11:00Z") + lead * 60 * 60 * 1000);
  const time = `${date.toISOString().slice(0, 16)}Z`;
  const local = new Date(date.getTime() + 60 * 60 * 1000).toISOString().slice(0, 16);
  assert.equal(Number(time.slice(11, 13)), utcHour);
  return {
    time,
    local,
    lead_h: lead,
    wind_dir_deg: 180,
    wind_kt: 8,
    gust_kt: 12,
    tailwind_25_kt: 1,
    tailwind_18_kt: 4,
    rule_od: od,
    rule_18_usable: p18 >= 0.5,
    p_od25: p25,
    od,
    p_18_usable: p18,
    certainty: 70,
  };
}

test("direction and runway risks at the same hour remain visible on separate tracks", () => {
  const hours = [
    hour(12, 1),
    hour(13, 2, { od: "07", p25: 0.28, p18: 0.12 }),
    hour(14, 3, { od: "07", p25: 0.2, p18: 0.9 }),
    hour(15, 4, { od: "25", p25: 0.68, p18: 0.9 }),
  ];
  const f = {
    ...issue,
    hours,
    next_change: {
      time: hours[1].time,
      local: hours[1].local,
      from: "25",
      to: "07",
      p: 0.72,
      window_local: ["2026-10-30T13:00", "2026-10-30T15:00"],
    },
    closures_18: [{
      start: hours[1].time,
      end: hours[2].time,
      local_start: hours[1].local,
      local_end: hours[2].local,
      min_p_usable: 0.1,
    }],
  };

  const result = forecastEvents(f);
  assert.equal(result.direction.length, 2);
  assert.equal(result.runway18.length, 1);
  assert.equal(result.direction[0].time, result.runway18[0].time);
  assert.equal(result.direction[0].probability, 0.72);
  assert.equal(result.direction[0].probabilityLabel, "P(OD 07 at this hour)");
  assert.deepEqual(result.direction[0].windowLocal, ["2026-10-30T13:00", "2026-10-30T15:00"]);
  assert.equal(result.direction[1].probability, 0.68);
  assert.equal(result.direction[1].probabilityLabel, "P(OD 25 at this hour)");
  assert.equal(result.direction[1].windowLocal, undefined);
  assert.equal(result.runway18[0].probability, 0.9);
});

test("last supplied closed row keeps reopening unknown even when interval end equals it", () => {
  const hours = [hour(12, 1), hour(13, 2, { p18: 0.2 })];
  const result = forecastEvents({
    ...issue,
    hours,
    closures_18: [{
      start: hours[1].time,
      end: hours[1].time,
      local_start: hours[1].local,
      local_end: hours[1].local,
      min_p_usable: 0.2,
    }],
  });

  assert.equal(result.runway18[0].kind, "closure");
  assert.equal(result.runway18[0].ongoing, true);
  assert.equal(result.runway18[0].end, undefined);
});

test("hourly fallback shows the whole closed sampled span and does not infer across gaps", () => {
  const hours = [
    hour(12, 1, { p18: 0.2 }),
    hour(13, 2, { p18: 0.15 }),
    hour(15, 4, { p18: 0.1 }),
  ];
  const result = forecastEvents({ ...issue, hours });
  const event = result.runway18[0];

  assert.equal(result.runway18.length, 1);
  assert.equal(event.kind, "hourly-call");
  assert.equal(event.closedSampleCount, 3);
  assert.equal(event.lastClosedCall.time, hours[2].time);
  assert.equal(event.ongoing, true);
  assert.equal(event.gapsPresent, true);
  assert.equal(event.probability, 0.8);
  assert.equal(event.probabilityLabel, "Lowest P(RWY 18 unusable) among these supplied calls");
});

test("direction changes across a timestamp gap name the first differing call and never jump selection", () => {
  const hours = [hour(12, 1), hour(15, 4, { od: "07", p25: 0.2 })];
  const result = forecastEvents({
    ...issue,
    hours,
    next_change: {
      time: "2026-10-30T16:00Z",
      local: "2026-10-30T17:00",
      from: "07",
      to: "25",
      p: 0.61,
      window_local: ["2026-10-30T16:00", "2026-10-30T18:00"],
    },
  });

  assert.match(result.direction[0].sourceLabel, /timestamp gap; transition time unknown/);
  assert.equal(result.direction[0].hourIndex, 1);
  assert.equal(result.direction[0].probability, 0.8);
  assert.equal(result.direction[0].windowLocal, undefined);
  assert.equal(result.direction[1].hourIndex, null);
});

test("coverage reports actual supplied rows and uses UTC timestamp deltas", () => {
  assert.equal(forecastCoverage([]).count, 0);
  assert.match(forecastCoverage([]).label, /No hourly forecast rows/);

  const one = forecastCoverage([hour(18, 7)]);
  assert.equal(one.label, "1 supplied hourly point · T+7 h");

  const partialDay = Array.from({ length: 24 }, (_, index) => {
    const totalHour = 12 + index;
    return hour(totalHour % 24, index + 1);
  });
  const dayCoverage = forecastCoverage(partialDay);
  assert.equal(dayCoverage.count, 24);
  assert.match(dayCoverage.label, /24 supplied hourly points/);
  assert.match(dayCoverage.label, /T\+1–T\+24 h/);
  assert.doesNotMatch(dayCoverage.label, /48/);

  const timestampGap = forecastCoverage([
    hour(12, 1),
    { ...hour(13, 2), time: "2026-10-30T14:00Z", local: "2026-10-30T15:00" },
  ]);
  assert.equal(timestampGap.hasTimestampGaps, true);
  assert.match(timestampGap.label, /timestamp gaps or irregular spacing/);
});

test("full local date, UTC offset, and UTC instant distinguish the repeated DST hour", () => {
  assert.match(formatForecastInstant("2026-10-25T00:00Z", "2026-10-25T02:00"), /25 Oct 2026 02:00 \(UTC\+02:00\).*00:00Z/);
  assert.match(formatForecastInstant("2026-10-25T01:00Z", "2026-10-25T02:00"), /25 Oct 2026 02:00 \(UTC\+01:00\).*01:00Z/);
});
