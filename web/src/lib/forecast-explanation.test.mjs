import assert from "node:assert/strict";
import test from "node:test";
import { explainForecastQuestion } from "./forecast-explanation.ts";

const hour = {
  time: "2026-10-30T12:00Z",
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
  issued_at: "2026-10-30T10:00Z",
  issued_local: "2026-10-30T12:00",
  mode: "live",
  current_od: "07",
  nwp: "Open-Meteo",
  model_version: "test",
  rules_version: "test",
  hours: [hour],
  next_change: {
    time: "2026-10-30T11:00Z",
    local: "2026-10-30T13:00",
    from: "07",
    to: "25",
    p: 0.7,
    window_local: ["2026-10-30T12:00", "2026-10-30T15:00"],
  },
  closures_18: [],
};

test("runway closure wording labels p_18_usable as probability of usability", () => {
  const answer = explainForecastQuestion(forecast, hour, "Is runway 18 closed?");
  assert.match(answer, /calls runway 18 closed/);
  assert.match(answer, /probability of usability is 10%/);
});

test("an explicit different clock time asks the user to select that hour", () => {
  const answer = explainForecastQuestion(forecast, hour, "Is runway 18 usable at 15:00?");
  assert.match(answer, /Select the exact date and hour/);
});

test("empty forecasts explain that an hour must be selected", () => {
  const answer = explainForecastQuestion({ ...forecast, hours: [] }, undefined, "Summarize this hour");
  assert.match(answer, /no selected forecast hour/);
});

test("next-change answer says when the change relates to the selected hour", () => {
  const answer = explainForecastQuestion(forecast, hour, "When is the next direction change?");
  assert.match(answer, /2026-10-30 at 13:00 local time/);
  assert.match(answer, /This change is before the selected hour/);
  assert.match(answer, /2026-10-30 at 12:00 local time to 2026-10-30 at 15:00 local time/);
});

test("unsupported questions do not get an unrelated forecast answer", () => {
  const answer = explainForecastQuestion(forecast, hour, "Explain the weather");
  assert.match(answer, /I can summarize the selected hour/);
  assert.doesNotMatch(answer, /OD 07/);
});

test("summary intent stays within the selected forecast hour", () => {
  assert.match(explainForecastQuestion(forecast, hour, "Summarize this hour"), /certainty score is 76\/100/);
  assert.doesNotMatch(explainForecastQuestion(forecast, hour, "Summarize my email"), /OD 07/);
});

test("unanchored dates and times require an explicit timeline selection", () => {
  for (const question of [
    "Could you summarize tomorrow's direction?",
    "Is runway 18 usable at noon?",
    "Is runway 18 usable at 1pm?",
    "Will the direction change in two hours?",
    "Will the direction change in 2h?",
    "Ist Bahn 18 in zwei Stunden nutzbar?",
  ]) {
    assert.match(explainForecastQuestion(forecast, hour, question), /Select the exact date and hour/, question);
  }
});
