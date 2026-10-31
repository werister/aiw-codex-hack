import assert from "node:assert/strict";
import test from "node:test";
import { answerHandoverQuestion } from "./forecast-handover.ts";

const baseHour = {
  time: "2026-10-24T22:00Z",
  local: "2026-10-25T00:00",
  lead_h: 1,
  wind_dir_deg: 180,
  wind_kt: 8,
  gust_kt: 12,
  tailwind_25_kt: 1,
  tailwind_18_kt: 4,
  rule_od: "07",
  rule_18_usable: false,
  p_od25: 0.8,
  od: "25",
  p_18_usable: 0.3,
  certainty: 60,
};

function makeHour(time, local, overrides = {}) {
  return { ...baseHour, time, local, ...overrides };
}

function makeForecast(hours, overrides = {}) {
  return {
    issued_at: "2026-10-24T20:00Z",
    issued_local: "2026-10-24T22:00",
    mode: "hindcast",
    current_od: "07",
    nwp: "Open-Meteo archived runs",
    model_version: "walk-forward-v5",
    rules_version: "fra-rules-v1",
    hours,
    next_change: null,
    closures_18: [],
    ...overrides,
  };
}

function dstHours(count = 6) {
  const hours = [];
  const localByUtc = ["02:00", "02:00", "03:00", "04:00", "05:00", "06:00"];
  for (let index = 0; index < count; index += 1) {
    const utc = new Date(Date.parse("2026-10-25T00:00Z") + index * 3_600_000).toISOString().replace(".000", "");
    hours.push(makeHour(utc, `2026-10-25T${localByUtc[index]}`, { lead_h: index + 1 }));
  }
  return hours;
}

test("six-hour briefing follows consecutive UTC rows across the autumn DST repeat", () => {
  const hours = dstHours();
  const answer = answerHandoverQuestion(makeForecast(hours), hours[0], "Brief next 6 hours");
  assert.ok(answer);
  assert.match(answer.text, /Coverage: 6 of 6 consecutive UTC forecast hours/);
  assert.match(answer.text, /25 Oct 2026 02:00 Europe\/Berlin \(UTC\+02:00; UTC 2026-10-25 00:00Z\)/);
  assert.match(answer.text, /25 Oct 2026 02:00 Europe\/Berlin \(UTC\+01:00; UTC 2026-10-25 01:00Z\)/);
  assert.equal((answer.text.match(/\+\d+ h\): model OD/g) ?? []).length, 6);
  assert.match(answer.text, /certainty score 60\/100/);
  assert.match(answer.text, /not a probability that both calls are correct/);
  assert.equal(answer.copyable, true);
});

test("partial coverage and gaps are explicit and later rows are not bridged", () => {
  const first = makeHour("2026-10-25T00:00Z", "2026-10-25T02:00");
  const second = makeHour("2026-10-25T01:00Z", "2026-10-25T02:00");
  const later = makeHour("2026-10-25T03:00Z", "2026-10-25T04:00");
  const answer = answerHandoverQuestion(makeForecast([first, second, later]), first, "Brief next 6 hours");
  assert.ok(answer);
  assert.match(answer.text, /Coverage: 2 of 6 consecutive UTC forecast hours/);
  assert.match(answer.text, /Coverage stops at the missing or non-consecutive UTC hour .*2026-10-25 02:00Z/);
  assert.match(answer.text, /the next row is .*2026-10-25 03:00Z/);
  assert.doesNotMatch(answer.text, /2026-10-25 03:00Z \(\+4 h\)/);
});

test("short horizon reports its supplied partial coverage", () => {
  const [first, second] = dstHours(2);
  const answer = answerHandoverQuestion(makeForecast([first, second]), first, "Brief next 6 hours");
  assert.ok(answer);
  assert.match(answer.text, /Coverage: 2 of 6 consecutive UTC forecast hours/);
  assert.match(answer.text, /published forecast ends before the next requested hour/);
});

test("model and rules disagreements are separated by OD and Runway 18", () => {
  const hours = [
    makeHour("2026-10-25T00:00Z", "2026-10-25T02:00", {
      od: "25", p_od25: 0.81, rule_od: "07", p_18_usable: 0.25, rule_18_usable: true,
    }),
    makeHour("2026-10-25T01:00Z", "2026-10-25T02:00", {
      od: "07", p_od25: 0.2, rule_od: "25", p_18_usable: 0.85, rule_18_usable: true,
    }),
    makeHour("2026-10-25T02:00Z", "2026-10-25T03:00", {
      od: "07", p_od25: 0.1, rule_od: "07", p_18_usable: 0.4, rule_18_usable: true,
    }),
  ];
  const answer = answerHandoverQuestion(makeForecast(hours), hours[0], "Compare model and rules");
  assert.ok(answer);
  assert.match(answer.text, /Operating direction disagreements \(2\/3 covered hours\)/);
  assert.match(answer.text, /model OD 07 \(80% for that call\); official rules OD 25/);
  assert.match(answer.text, /Runway 18 disagreements \(2\/3 covered hours\)/);
  assert.match(answer.text, /model says likely closed \(P usable 25%\); official rules say usable/);
  assert.match(answer.text, /model says likely closed \(P usable 40%\); official rules say usable/);
  assert.match(answer.text, /does not infer a cause/);
});

test("restriction intervals are start-inclusive, end-exclusive, and distinguish window from horizon", () => {
  const hours = Array.from({ length: 8 }, (_, index) => makeHour(
    new Date(Date.parse("2026-10-25T00:00Z") + index * 3_600_000).toISOString().replace(".000", ""),
    `2026-10-25T${String(index < 2 ? index + 2 : index + 1).padStart(2, "0")}:00`,
    { lead_h: index + 1, p_18_usable: index === 3 || index === 6 ? 0.8 : 0.3 },
  ));
  const answer = answerHandoverQuestion(makeForecast(hours, {
    closures_18: [
      { start: "2026-10-24T23:00Z", end: "2026-10-25T03:00Z", min_p_usable: 0.12 },
      { start: "2026-10-25T04:00Z", end: "2026-10-25T06:00Z", min_p_usable: 0.2 },
      { start: "2026-10-25T05:00Z", end: "2026-10-25T07:00Z", min_p_usable: 0.08 },
      { start: "2026-10-24T18:00Z", end: "2026-10-25T00:00Z", min_p_usable: 0.01 },
    ],
  }), hours[0], "Runway 18 restrictions");
  assert.ok(answer);
  assert.match(answer.text, /3 restriction intervals overlap/);
  assert.match(answer.text, /Already ongoing at the selected hour/);
  assert.match(answer.text, /continues through this briefing window; the matching first usable forecast call is/);
  assert.match(answer.text, /reopening is unknown beyond this forecast/);
  assert.doesNotMatch(answer.text, /2026-10-24T18:00:00.000Z/);
  assert.doesNotMatch(answer.text, /2026-10-25T06:00:00.000Z \(\+7 h\)/);
});

test("no overlapping restrictions and malformed intervals are reported honestly", () => {
  const hours = dstHours();
  const forecast = makeForecast(hours, {
    closures_18: [
      { start: "2026-10-25T06:00Z", end: "2026-10-25T07:00Z", min_p_usable: 0.2 },
      { start: "not-a-time", end: "2026-10-25T02:00Z", min_p_usable: 0.1 },
    ],
  });
  const answer = answerHandoverQuestion(forecast, hours[0], "Runway 18 restrictions");
  assert.ok(answer);
  assert.match(answer.text, /No supplied Runway 18 restriction interval overlaps/);
  assert.match(answer.text, /1 supplied restriction interval has invalid timestamps/);
});

test("hourly closed calls without supplied intervals show unknown reopening or a later usable sample", () => {
  const first = makeHour("2026-10-30T10:00Z", "2026-10-30T12:00", { p_18_usable: 0.2 });
  const second = makeHour("2026-10-30T11:00Z", "2026-10-30T13:00", { p_18_usable: 0.1 });
  const laterUsable = makeHour("2026-10-30T12:00Z", "2026-10-30T14:00", { p_18_usable: 0.8 });

  const ongoing = answerHandoverQuestion(makeForecast([first, second]), first, "Runway 18 restrictions");
  assert.ok(ongoing);
  assert.match(ongoing.text, /Hourly calls only; these samples do not establish a supplied closure interval or continuous state/);
  assert.match(ongoing.text, /2 likely-unusable hourly calls; first .*UTC 2026-10-30 10:00Z\), last .*UTC 2026-10-30 11:00Z\);/);
  assert.match(ongoing.text, /No later usable call appears in this covered window; reopening is unknown/);

  const reopened = answerHandoverQuestion(makeForecast([first, second, laterUsable]), first, "Runway 18 restrictions");
  assert.ok(reopened);
  assert.match(reopened.text, /First later usable sampled call: .*UTC 2026-10-30 12:00Z\) \(P usable 80%\)/);
  assert.doesNotMatch(reopened.text, /reopening is unknown/);
});

test("a zero-length final closed interval is a valid truncated event with unknown reopening", () => {
  const last = makeHour("2026-10-25T07:00Z", "2026-10-25T08:00", { p_18_usable: 0.2 });
  const answer = answerHandoverQuestion(makeForecast([last], {
    closures_18: [{ start: last.time, end: last.time, min_p_usable: 0.1 }],
  }), last, "Runway 18 restrictions");
  assert.ok(answer);
  assert.match(answer.text, /1 restriction interval overlaps/);
  assert.match(answer.text, /final supplied hour .*P\(Runway 18 usable\) is 20%; reopening is unknown/);
  assert.doesNotMatch(answer.text, /invalid timestamps/);
});

test("a final closed interval ending at the selected last row is included as ongoing", () => {
  const hours = [
    makeHour("2026-10-25T05:00Z", "2026-10-25T06:00", { p_18_usable: 0.2 }),
    makeHour("2026-10-25T06:00Z", "2026-10-25T07:00", { p_18_usable: 0.2 }),
    makeHour("2026-10-25T07:00Z", "2026-10-25T08:00", { p_18_usable: 0.2 }),
  ];
  const answer = answerHandoverQuestion(makeForecast(hours, {
    closures_18: [{ start: hours[0].time, end: hours[2].time, min_p_usable: 0.1 }],
  }), hours[2], "Runway 18 restrictions");
  assert.ok(answer);
  assert.match(answer.text, /1 restriction interval overlaps/);
  assert.match(answer.text, /Already ongoing at the selected hour/);
  assert.match(answer.text, /final supplied hour .*P\(Runway 18 usable\) is 20%; reopening is unknown/);
});

test("an interval end without a matching usable hourly call is not called a reopening", () => {
  const hours = dstHours();
  const answer = answerHandoverQuestion(makeForecast(hours, {
    closures_18: [{ start: "2026-10-25T01:00Z", end: "2026-10-25T03:30Z", min_p_usable: 0.1 }],
  }), hours[0], "Runway 18 restrictions");
  assert.ok(answer);
  assert.match(answer.text, /no matching usable forecast row confirms reopening/);
  assert.doesNotMatch(answer.text, /first usable forecast call is/);
});

test("missing run evidence is disclosed and supported prompts require exact intent", () => {
  const hours = dstHours();
  const forecast = makeForecast(hours);
  const answer = answerHandoverQuestion(forecast, hours[0], "Brief next 6 hours");
  assert.ok(answer);
  assert.match(answer.text, /Run-level source availability and model-artifact provenance are not included/);
  for (const unsupported of [
    "Brief next 6 hours and tell me why",
    "Will the runway be safe?",
    "Tell me about runway 18 and staffing savings",
    "What happens during the next six hours?",
  ]) {
    assert.equal(answerHandoverQuestion(forecast, hours[0], unsupported), null, unsupported);
  }
});

test("evidence lists artifact, issue inputs, source availability and missing feeds", () => {
  const hours = dstHours();
  const answer = answerHandoverQuestion(makeForecast(hours, {
    evidence: {
      run_id: "0123456789ab",
      model_artifact: { version: "wf5", file: "model.joblib", sha256: "abc", trained_through: "2026-09-30T00:00Z" },
      feature_set: "winds-v2",
      rules_version: "rules-v1",
      publication_lag_h: 3,
      issue_inputs: {
        metar_time: "2026-10-24T20:00Z", metar_wind_dir_deg: 210, metar_wind_kt: 9,
        metar_gust_kt: 12, od_at_issue: "07", od_source: "METAR + rules", hours_since_change: null,
      },
      sources: [
        { name: "METAR", available_at: "2026-10-24T20:05Z", issued_at: "2026-10-24T20:00Z" },
        { name: "Ensemble", available_at: "2026-10-24T19:00Z", missing: true },
      ],
    },
  }), hours[0], "Brief next 6 hours");
  assert.ok(answer);
  assert.match(answer.text, /Run 0123456789ab · artifact wf5/);
  assert.match(answer.text, /Recorded source metadata/);
  assert.match(answer.text, /missing: Ensemble/);
  assert.match(answer.text, /1 feed recorded available after issue time/);
});

test("missing selection gives a prompt to select an hour", () => {
  const answer = answerHandoverQuestion(makeForecast([]), undefined, "Brief next 6 hours");
  assert.ok(answer);
  assert.match(answer.text, /Select a forecast hour first/);
  assert.equal(answer.copyable, false);
});
