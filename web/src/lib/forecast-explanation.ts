import type { ForecastResponse, HourForecast } from "./forecast-types";

export const FORECAST_SUGGESTIONS = [
  "Summarize this hour",
  "Is runway 18 usable?",
  "When is the next direction change?",
] as const;

const SUPPORTED_QUESTIONS =
  "I can summarize the selected hour, explain its direction or runway 18 call, and report the forecast’s next direction change.";

function percent(value: number) {
  return `${Math.round(value * 100)}%`;
}

function localTime(value: string) {
  return `${value.slice(0, 10)} at ${value.slice(11, 16)} local time`;
}

function normalize(value: string) {
  return value.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}

function requestedHourMismatch(question: string, hour: HourForecast) {
  const clock = question.match(/\b(?:at|um|gegen)\s+(\d{1,2})(?::(\d{2}))?\b/) ??
    question.match(/\b(\d{1,2}):(\d{2})\b/);
  const date = question.match(/\b(20\d{2}-\d{2}-\d{2})\b/);
  const relativeDate =
    /\b(today|tomorrow|yesterday|tonight|this evening|heute|morgen|gestern|heute abend|heute nacht)\b/.test(question) ||
    /\b(mon|tue|wed|thu|fri|sat|sun)(?:day)?\b|\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|weekend|next week)\b/.test(question) ||
    /\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\b/.test(question);
  const unanchoredTime =
    /\b(noon|midday|midnight|mittag|mitternacht|morgens|abends|montag|dienstag|mittwoch|donnerstag|freitag|samstag|sonntag)\b/.test(question) ||
    /\b\d{1,2}(?::\d{2})?\s*[ap]\.?m\.?\b/.test(question) ||
    /\b(?:in|within|after|before|vor|nach|innerhalb)\s+(?:\d+|one|two|three|four|a|an|einer?|zwei|drei|vier)\s*(?:hours?|minutes?|h|min|stunden?|minuten?)\b/.test(question);

  if (relativeDate || unanchoredTime) return true;
  if (date && (!clock || date[1] !== hour.local.slice(0, 10))) return true;
  if (clock) {
    const requestedTime = `${clock[1].padStart(2, "0")}:${(clock[2] ?? "00").padStart(2, "0")}`;
    if (requestedTime !== hour.local.slice(11, 16)) return true;
  }
  return Boolean(date && !clock);
}

function summary(hour: HourForecast) {
  const directionChance = hour.od === "25" ? hour.p_od25 : 1 - hour.p_od25;
  const usable = hour.p_18_usable >= 0.5;
  return `For ${localTime(hour.local)}, the model calls OD ${hour.od} (${hour.od === "25" ? "west" : "east"}) with ${percent(directionChance)} probability. It calls runway 18 ${usable ? "usable" : "closed"} for departures; the probability of usability is ${percent(hour.p_18_usable)}. The certainty score is ${Math.round(hour.certainty)}/100. The official rule baseline calls OD ${hour.rule_od} and runway 18 ${hour.rule_18_usable ? "usable" : "closed"}.`;
}

export function explainForecastQuestion(
  forecast: ForecastResponse,
  hour: HourForecast | undefined,
  rawQuestion: string,
) {
  if (!hour || forecast.hours.length === 0) {
    return "There is no selected forecast hour yet. Choose an hour in the timeline, then ask about it.";
  }

  const question = normalize(rawQuestion).trim().replace(/[.!?]+$/, "");
  if (!question) return SUPPORTED_QUESTIONS;
  if (requestedHourMismatch(question, hour)) {
    return "I answer only for the selected forecast hour. Select the exact date and hour in the timeline, then ask again.";
  }

  if (/\b(summarize|summarise|summary|overview|zusammenfassung|ueberblick)\b/.test(question)) {
    const asksSelectedSummary =
      /^(?:(?:please|could you|can you)\s+)?summari[sz]e\s+(?:this|the selected|the current)\s+hour$/.test(question) ||
      /^(?:summary|overview)\s+of\s+(?:this|the selected|the current)\s+hour$/.test(question) ||
      /^(?:zusammenfassung|ueberblick)\s+(?:der|zur)\s+(?:ausgewahlten|aktuellen)\s+stunde$/.test(question);
    return asksSelectedSummary ? summary(hour) : SUPPORTED_QUESTIONS;
  }

  const asksNextChange =
    /\b(next|upcoming|naechst|wann|when|what time)\b.*\b(change|switch|direction|operating direction|od|wechsel|richtung)\b/.test(question) ||
    /\b(naechste|naechsten)\s+(richtung|wechsel)\b|\bwann\s+(wechselt|aendert)\b/.test(question);
  if (asksNextChange) {
    const change = forecast.next_change;
    if (!change) return "The forecast identifies no direction change in its 48-hour horizon.";
    const [start, end] = change.window_local;
    const window = `${localTime(start)} to ${localTime(end)}`;
    const relation = change.local < hour.local
      ? `This change is before the selected hour (${localTime(hour.local)}).`
      : change.local === hour.local
        ? "This is the selected hour."
        : `This change is after the selected hour (${localTime(hour.local)}).`;
    return `The forecast issued ${localTime(forecast.issued_local)} predicts its first direction change from OD ${change.from} to OD ${change.to} at ${localTime(change.local)}. Its plausible window is ${window}, with ${percent(change.p)} probability for the new direction. ${relation}`;
  }

  const mentionsRunway18 = /\b(?:runway|rwy|bahn)\s*18\b|\br18\b/.test(question);
  const asksRunwayStatus = /\b(usable|open|closed|available|status|chance|probability|nutzbar|offen|geschlossen|verfuegbar|ist|wird)\b/.test(question);
  if (mentionsRunway18 && asksRunwayStatus) {
    return `For ${localTime(hour.local)}, the model calls runway 18 ${hour.p_18_usable >= 0.5 ? "usable" : "closed"} for departures; the probability of usability is ${percent(hour.p_18_usable)}. The official rule baseline calls it ${hour.rule_18_usable ? "usable" : "closed"}.`;
  }

  if (/\b(certainty|confidence|how sure|sicherheit|sicher)\b/.test(question)) {
    return `For ${localTime(hour.local)}, the model’s combined certainty score for its direction and runway 18 calls is ${Math.round(hour.certainty)}/100.`;
  }

  if (/\b(operating direction|direction|\bod\b|betriebsrichtung|richtung)\b/.test(question)) {
    const chance = hour.od === "25" ? hour.p_od25 : 1 - hour.p_od25;
    return `For ${localTime(hour.local)}, the model calls OD ${hour.od} (${hour.od === "25" ? "west" : "east"}) with ${percent(chance)} probability. The official rule baseline calls OD ${hour.rule_od}.`;
  }

  return `${SUPPORTED_QUESTIONS} Select another timeline hour before asking about a different time.`;
}
