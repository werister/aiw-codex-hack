import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import {
  explainForecastQuestion,
  formatForecastHour,
  forecastHourOffset,
  nextDirectionChangeAfter,
} from "./forecast-explanation.ts";

const hour = {
  time: "2026-10-30T13:00Z",
  local: "2026-10-30T14:00",
  lead_h: 1,
  wind_dir_deg: 180,
  wind_kt: 8,
  gust_kt: 12,
  tailwind_25_kt: 1,
  tailwind_18_kt: 4,
  rule_od: "07",
  rule_18_usable: false,
  p_od25: 0.2,
  od: "07",
  p_18_usable: 0.1,
  certainty: 76,
};

const forecast = {
  issued_at: "2026-10-30T11:00Z",
  issued_local: "2026-10-30T12:00",
  mode: "live",
  current_od: "07",
  nwp: "Open-Meteo",
  model_version: "test",
  rules_version: "test",
  hours: [hour],
  next_change: {
    time: "2026-10-30T12:00Z",
    local: "2026-10-30T13:00",
    from: "25",
    to: "07",
    p: 0.9,
    window_local: ["2026-10-30T13:00", "2026-10-30T14:00"],
  },
  closures_18: [],
};

function makeHour(time, local, od, p_od25 = od === "25" ? 0.7 : 0.3) {
  return { ...hour, time, local, od, p_od25 };
}

function withHours(hours, next_change = null) {
  return { ...forecast, hours, next_change };
}

test("runway closure wording labels p_18_usable as probability of usability", () => {
  const answer = explainForecastQuestion(forecast, hour, "Is runway 18 closed?");
  assert.match(answer, /calls runway 18 closed/);
  assert.match(answer, /probability of usability is 10%/);
});

test("empty forecasts explain that an hour must be selected", () => {
  const answer = explainForecastQuestion({ ...forecast, hours: [] }, undefined, "Summarize this hour");
  assert.match(answer, /no selected forecast hour/);
});

test("summary intent stays within the selected forecast hour", () => {
  assert.match(explainForecastQuestion(forecast, hour, "Summarize this hour"), /certainty score is 76\/100/);
  assert.doesNotMatch(explainForecastQuestion(forecast, hour, "Summarize my email"), /OD 07/);
});

test("unsupported questions do not get an unrelated forecast answer", () => {
  const answer = explainForecastQuestion(forecast, hour, "Explain the weather");
  assert.match(answer, /I can summarize the selected hour/);
  assert.doesNotMatch(answer, /OD 07/);
  assert.match(answer, /2026-10-30 at 14:00 Europe\/Berlin \(UTC\+1\)/);
});

test("certainty is identified as a margin score, not joint correctness probability", () => {
  const answer = explainForecastQuestion(forecast, hour, "How certain is the direction?");
  assert.match(answer, /certainty margin score .*76\/100/);
  assert.match(answer, /not a probability that both calls are correct/);
});

test("an explicit time, date, or zone mismatch asks for a timeline selection", () => {
  for (const question of [
    "Is runway 18 usable at 15:00?",
    "Is runway 18 usable on 2026-10-31 at 14:00?",
    "Is runway 18 usable at 14:00 or 15:00?",
    "Is runway 18 usable at 14:00 on 2026-10-30 or 2026-10-31?",
    "Could you summarize tomorrow's direction?",
    "Is runway 18 usable at noon?",
    "Is runway 18 usable at 1pm?",
    "Will the direction change in two hours?",
    "Will the direction change in 2h?",
    "Ist Bahn 18 in zwei Stunden nutzbar?",
  ]) {
    assert.match(explainForecastQuestion(forecast, hour, question), /Select the exact date and hour/, question);
  }
  for (const question of ["Is runway 18 usable at 14:00 UTC?", "Is runway 18 usable at 14:00 Europe/Paris?"]) {
    assert.match(explainForecastQuestion(forecast, hour, question), /Europe\/Berlin local time/, question);
  }
});

test("matching Berlin local date and time remain answerable", () => {
  const answer = explainForecastQuestion(forecast, hour, "Is runway 18 usable at 14:00 Europe/Berlin?");
  assert.match(answer, /probability of usability is 10%/);
});

test("next change is after the selected hour and uses target-direction probability", () => {
  const later = makeHour("2026-10-30T14:00Z", "2026-10-30T15:00", "25", 0.72);
  const laterStill = makeHour("2026-10-30T15:00Z", "2026-10-30T16:00", "25", 0.8);
  const response = withHours([hour, later, laterStill], forecast.next_change);
  const answer = explainForecastQuestion(response, hour, "When is the next direction change?");

  assert.match(answer, /After the selected hour/);
  assert.match(answer, /2026-10-30 at 15:00 Europe\/Berlin \(UTC\+1\)/);
  assert.match(answer, /P\(OD 25\) is 72%/);
  assert.match(answer, /No matching change window is supplied/);
  assert.doesNotMatch(answer, /P\(OD 25\) is 90%/);
});

test("next change lookup follows UTC order and excludes the selected event", () => {
  const h08 = makeHour("2026-10-30T07:00Z", "2026-10-30T08:00", "25");
  const h09 = makeHour("2026-10-30T08:00Z", "2026-10-30T09:00", "07");
  const h10 = makeHour("2026-10-30T09:00Z", "2026-10-30T10:00", "07");
  const h11 = makeHour("2026-10-30T10:00Z", "2026-10-30T11:00", "25");
  const h12 = makeHour("2026-10-30T11:00Z", "2026-10-30T12:00", "07");
  const change = {
    time: h09.time,
    local: h09.local,
    from: "25",
    to: "07",
    p: 0.9,
    window_local: ["2026-10-30T08:00", "2026-10-30T10:00"],
  };
  const response = withHours([h08, h11, h09, h10, h12], change);

  const before = nextDirectionChangeAfter(response, h08);
  assert.deepEqual(before, { index: 2, hour: h09, from: "25", window: change.window_local });

  const atFirstChange = nextDirectionChangeAfter(response, h09);
  assert.deepEqual(atFirstChange, { index: 1, hour: h11, from: "07", window: null });

  const afterFirstChange = nextDirectionChangeAfter(response, h11);
  assert.deepEqual(afterFirstChange, { index: 4, hour: h12, from: "25", window: null });
  assert.equal(nextDirectionChangeAfter(response, h12), null);
});

test("short and final horizons describe only supplied coverage", () => {
  const selected = makeHour("2026-10-30T13:00Z", "2026-10-30T14:00", "07");
  const final = makeHour("2026-10-30T14:00Z", "2026-10-30T15:00", "07");
  const shortForecast = withHours([selected, final]);
  const throughShortHorizon = explainForecastQuestion(shortForecast, selected, "When is the next direction change?");
  assert.match(throughShortHorizon, /No later direction change is supplied/);
  assert.match(throughShortHorizon, /through the final supplied forecast hour 2026-10-30 at 15:00/);

  const finalHour = explainForecastQuestion(shortForecast, final, "When is the next direction change?");
  assert.match(finalHour, /No later forecast hours were supplied after the selected hour/);
});

test("repeated Berlin 02:00 hours remain distinct through their UTC offsets", () => {
  const first = makeHour("2026-10-25T00:00Z", "2026-10-25T02:00", "07", 0.1);
  const second = makeHour("2026-10-25T01:00Z", "2026-10-25T02:00", "25", 0.8);
  const response = withHours([first, second], {
    time: second.time,
    local: second.local,
    from: first.od,
    to: second.od,
    p: second.p_od25,
    window_local: [first.local, second.local],
  });
  const change = nextDirectionChangeAfter(response, first);

  assert.deepEqual(change, { index: 1, hour: second, from: "07", window: [first.local, second.local] });
  assert.equal(forecastHourOffset(first), "UTC+2");
  assert.equal(forecastHourOffset(second), "UTC+1");
  assert.match(formatForecastHour(first), /02:00 Europe\/Berlin \(UTC\+2\)/);
  assert.match(formatForecastHour(second), /02:00 Europe\/Berlin \(UTC\+1\)/);
  const answer = explainForecastQuestion(response, first, "When is the next direction change?");
  assert.match(answer, /02:00 Europe\/Berlin \(UTC\+1\)/);
  assert.match(answer, /its repeated Berlin time is ambiguous/);
});

test("real Oct 2 forecast selects the first later transition, not the issue-time change", () => {
  const realForecast = JSON.parse(
    fs.readFileSync(new URL("../../public/forecasts/2026-10-02.json", import.meta.url), "utf8"),
  );
  const selected = realForecast.hours.find((item) => item.local === "2026-10-02T09:00");
  const change = nextDirectionChangeAfter(realForecast, selected);
  assert.ok(change);
  assert.equal(selected.time, "2026-10-02T07:00Z");
  assert.equal(change.hour.time, "2026-10-03T20:00Z");
  assert.equal(change.hour.local, "2026-10-03T22:00");
  assert.match(
    explainForecastQuestion(realForecast, selected, "When is the next direction change?"),
    /2026-10-03 at 22:00 Europe\/Berlin \(UTC\+2\)/,
  );
});
