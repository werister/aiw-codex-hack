import type { ForecastResponse, HourForecast, OD } from "./forecast-types";

export const FORECAST_SUGGESTIONS = [
  "Summarize this hour",
  "Is runway 18 usable?",
  "Next change after this hour",
] as const;

const SUPPORTED_QUESTIONS =
  "I can summarize the selected hour, explain its direction or runway 18 call, and report the next direction change after it.";

type HourStamp = Pick<HourForecast, "time" | "local">;
type OrderedHour = { hour: HourForecast; index: number; instant: number };

function percent(value: number) {
  return `${Math.round(value * 100)}%`;
}

function localTime(value: string) {
  return `${value.slice(0, 10)} at ${value.slice(11, 16)}`;
}

function parseUtcInstant(value: string) {
  if (!/(?:Z|[+-]\d{2}:?\d{2})$/i.test(value)) return null;
  const instant = Date.parse(value);
  return Number.isFinite(instant) ? instant : null;
}

function parseBerlinWallTime(value: string) {
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?$/.test(value)) return null;
  const wallTime = value.length === 16 ? `${value}:00Z` : `${value}Z`;
  const instant = Date.parse(wallTime);
  return Number.isFinite(instant) ? instant : null;
}

export function forecastHourOffset(hour: HourStamp) {
  const utcInstant = parseUtcInstant(hour.time);
  const berlinWallTime = parseBerlinWallTime(hour.local);
  if (utcInstant === null || berlinWallTime === null) return "UTC offset unavailable";

  const offsetMinutes = Math.round((berlinWallTime - utcInstant) / 60_000);
  if (Math.abs(offsetMinutes) > 14 * 60) return "UTC offset unavailable";

  const sign = offsetMinutes < 0 ? "-" : "+";
  const absoluteMinutes = Math.abs(offsetMinutes);
  const hours = Math.floor(absoluteMinutes / 60);
  const minutes = absoluteMinutes % 60;
  return minutes === 0
    ? `UTC${sign}${hours}`
    : `UTC${sign}${hours}:${String(minutes).padStart(2, "0")}`;
}

export function formatForecastHour(hour: HourStamp) {
  return `${localTime(hour.local)} Europe/Berlin (${forecastHourOffset(hour)})`;
}

function orderedLaterHours(forecast: ForecastResponse, selectedHour: HourForecast) {
  const selectedInstant = parseUtcInstant(selectedHour.time);
  if (selectedInstant === null) return [];

  return forecast.hours
    .map((hour, index) => ({ hour, index, instant: parseUtcInstant(hour.time) }))
    .filter((item): item is OrderedHour => item.instant !== null && item.instant > selectedInstant)
    .sort((a, b) => a.instant - b.instant || a.index - b.index);
}

export function nextDirectionChangeAfter(
  forecast: ForecastResponse,
  selectedHour: HourForecast,
): { index: number; hour: HourForecast; from: OD; window: [string, string] | null } | null {
  const next = orderedLaterHours(forecast, selectedHour)
    .find(({ hour }) => hour.od !== selectedHour.od);
  if (!next) return null;

  const suppliedChange = forecast.next_change;
  const suppliedTime = suppliedChange ? parseUtcInstant(suppliedChange.time) : null;
  const window = suppliedTime === next.instant ? suppliedChange?.window_local ?? null : null;

  return { index: next.index, hour: next.hour, from: selectedHour.od, window };
}

function normalize(value: string) {
  return value.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim();
}

function explicitNonLocalTimezone(question: string) {
  const withoutBerlin = question.replace(/\b(?:europe\/berlin|berlin\s+time|local\s+time)\b/g, " ");
  return /\b(?:utc|gmt|zulu|cet|cest|eet|eest|bst|jst|kst|sgt|aest|aedt|est|edt|cst|cdt|mst|mdt|pst|pdt)\b|\b(?:utc|gmt)\s*[+-]\s*\d{1,2}(?::?\d{2})?\b|(?:^|\s)[+-]\d{2}:?\d{2}(?=\s|$|[.!?,])|\dZ\b|\b(?:new\s+york|london|tokyo|pacific|eastern|central|mountain)\s+time\b|\b[A-Za-z_]+\/[A-Za-z_+-]+(?:\/[A-Za-z_+-]+)*\b/i.test(withoutBerlin);
}

function requestedTimes(question: string) {
  const times = new Set<string>();
  const meridiemPattern = /\b(\d{1,2})(?::(\d{2}))?\s*([ap])\.?m\.?\b/gi;
  const withoutMeridiem = question.replace(meridiemPattern, " ");

  for (const match of question.matchAll(meridiemPattern)) {
    const rawHour = Number(match[1]);
    const minute = Number(match[2] ?? "0");
    if (rawHour < 1 || rawHour > 12 || minute > 59) {
      times.add("invalid");
      continue;
    }
    const hour = rawHour % 12 + (match[3].toLowerCase() === "p" ? 12 : 0);
    times.add(`${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`);
  }

  for (const match of withoutMeridiem.matchAll(/(?<!\d)(\d{1,2}):(\d{2})(?!\d)/g)) {
    const hour = Number(match[1]);
    const minute = Number(match[2]);
    times.add(hour > 23 || minute > 59
      ? "invalid"
      : `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`);
  }

  const contextualTimePattern = /\b(?:at|um|gegen|around|about)\s+(\d{1,2})(?::(\d{2}))?\b/gi;
  for (const match of withoutMeridiem.matchAll(contextualTimePattern)) {
    const hour = Number(match[1]);
    const minute = Number(match[2] ?? "0");
    times.add(hour > 23 || minute > 59
      ? "invalid"
      : `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`);
  }

  if (/\b(noon|midday|mittag)\b/.test(question)) times.add("12:00");
  if (/\b(midnight|mitternacht)\b/.test(question)) times.add("00:00");
  return times;
}

type TimeMismatch = "timezone" | "selection" | null;

function requestedHourMismatch(question: string, hour: HourForecast): TimeMismatch {
  if (explicitNonLocalTimezone(question)) return "timezone";

  const dates = [...question.matchAll(/\b(20\d{2}-\d{2}-\d{2})\b/g)].map((match) => match[1]);
  const relativeDate =
    /\b(today|tomorrow|yesterday|tonight|this evening|heute|morgen|gestern|heute abend|heute nacht)\b/.test(question) ||
    /\b(mon|tue|wed|thu|fri|sat|sun)(?:day)?\b|\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|weekend|next week)\b/.test(question) ||
    /\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\b/.test(question);
  const relativeTime =
    /\b(?:in|within|after|before|vor|nach|innerhalb)\s+(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|a|an|einer?|einem|zwei|drei|vier|funf|sechs|sieben|acht|neun|zehn)\s*(?:hours?|hrs?|h|minutes?|mins?|min|stunden?|minuten?)\b/.test(question) ||
    /\b(?:morning|afternoon|evening|morgens|vormittags|nachmittags|abends)\b/.test(question);
  const times = requestedTimes(question);
  const selectedDate = hour.local.slice(0, 10);
  const selectedTime = hour.local.slice(11, 16);

  if (relativeDate || relativeTime) return "selection";
  if (dates.some((date) => date !== selectedDate) || (dates.length > 0 && times.size === 0)) {
    return "selection";
  }
  if ([...times].some((time) => time === "invalid" || time !== selectedTime)) {
    return "selection";
  }
  return null;
}

function summary(hour: HourForecast) {
  const directionChance = hour.od === "25" ? hour.p_od25 : 1 - hour.p_od25;
  const usable = hour.p_18_usable >= 0.5;
  return `For ${formatForecastHour(hour)}, the model calls OD ${hour.od} (${hour.od === "25" ? "west" : "east"}) with ${percent(directionChance)} probability. It calls runway 18 ${usable ? "usable" : "closed"} for departures; the probability of usability is ${percent(hour.p_18_usable)}. The certainty score is ${Math.round(hour.certainty)}/100. The official rule baseline calls OD ${hour.rule_od} and runway 18 ${hour.rule_18_usable ? "usable" : "closed"}.`;
}

function isSelectedHourSummary(question: string) {
  return /^(?:(?:please|could you|can you)\s+)?summari[sz]e\s+(?:this|the selected|the current)\s+hour$/.test(question) ||
    /^(?:summary|overview)\s+of\s+(?:this|the selected|the current)\s+hour$/.test(question) ||
    /^(?:zusammenfassung|ueberblick)\s+(?:der|zur)\s+(?:ausgewaehlten|aktuellen)\s+stunde$/.test(question);
}

function noLaterChangeAnswer(forecast: ForecastResponse, hour: HourForecast) {
  const lastLaterHour = orderedLaterHours(forecast, hour).at(-1)?.hour;
  if (!lastLaterHour) {
    return `No later forecast hours were supplied after the selected hour ${formatForecastHour(hour)}, so this guide cannot report a later direction change.`;
  }
  return `No later direction change is supplied after ${formatForecastHour(hour)} through the final supplied forecast hour ${formatForecastHour(lastLaterHour)}.`;
}

function hasAmbiguousWindowEndpoint(forecast: ForecastResponse, window: [string, string]) {
  return window.some((endpoint) => {
    const instants = forecast.hours
      .filter((hour) => hour.local === endpoint)
      .map((hour) => parseUtcInstant(hour.time))
      .filter((instant): instant is number => instant !== null);
    return new Set(instants).size > 1;
  });
}

function nextChangeAnswer(forecast: ForecastResponse, hour: HourForecast) {
  const change = nextDirectionChangeAfter(forecast, hour);
  if (!change) return noLaterChangeAnswer(forecast, hour);

  const targetProbability = change.hour.od === "25"
    ? change.hour.p_od25
    : 1 - change.hour.p_od25;
  const window = change.window
    ? ` The producer supplied a plausible window of ${localTime(change.window[0])} to ${localTime(change.window[1])} Europe/Berlin.${hasAmbiguousWindowEndpoint(forecast, change.window) ? " The supplied window has no UTC offsets, so its repeated Berlin time is ambiguous." : ""}`
    : " No matching change window is supplied for this later event.";
  return `After the selected hour ${formatForecastHour(hour)}, the next supplied direction change is from OD ${change.from} to OD ${change.hour.od} at ${formatForecastHour(change.hour)}. P(OD ${change.hour.od}) is ${percent(targetProbability)} at that hour.${window}`;
}

export function explainForecastQuestion(
  forecast: ForecastResponse,
  hour: HourForecast | undefined,
  rawQuestion: string,
) {
  if (!hour || forecast.hours.length === 0) {
    return "There is no selected forecast hour yet. Choose an hour in the timeline, then ask about it.";
  }

  const question = normalize(rawQuestion).replace(/[.!?]+$/, "");
  if (!question) return `${SUPPORTED_QUESTIONS} Selected hour: ${formatForecastHour(hour)}.`;

  const mismatch = requestedHourMismatch(question, hour);
  if (mismatch === "timezone") {
    return `This guide uses Europe/Berlin local time. The selected hour is ${formatForecastHour(hour)}; convert other time zones or select the matching timeline hour.`;
  }
  if (mismatch === "selection") {
    return `I answer only for the selected Europe/Berlin hour (${formatForecastHour(hour)}). Select the exact date and hour in the timeline, then ask again.`;
  }

  if (/\b(summarize|summarise|summary|overview|zusammenfassung|ueberblick)\b/.test(question)) {
    return isSelectedHourSummary(question)
      ? summary(hour)
      : `${SUPPORTED_QUESTIONS} Selected hour: ${formatForecastHour(hour)}.`;
  }

  const asksNextChange =
    /\b(next|upcoming|naechst|wann|when|what time)\b.*\b(change|switch|direction|operating direction|od|wechsel|richtung)\b/.test(question) ||
    /\b(naechste|naechsten)\s+(richtung|wechsel)\b|\bwann\s+(wechselt|aendert)\b/.test(question);
  if (asksNextChange) return nextChangeAnswer(forecast, hour);

  const mentionsRunway18 = /\b(?:runway|rwy|bahn)\s*18\b|\br18\b/.test(question);
  const asksRunwayStatus = /\b(usable|open|closed|available|status|chance|probability|nutzbar|offen|geschlossen|verfuegbar|ist|wird)\b/.test(question);
  if (mentionsRunway18 && asksRunwayStatus) {
    return `For ${formatForecastHour(hour)}, the model calls runway 18 ${hour.p_18_usable >= 0.5 ? "usable" : "closed"} for departures; the probability of usability is ${percent(hour.p_18_usable)}. The official rule baseline calls it ${hour.rule_18_usable ? "usable" : "closed"}.`;
  }

  if (/\b(certainty|certain|confidence|how sure|sicherheit|sicher)\b/.test(question)) {
    return `For ${formatForecastHour(hour)}, the producer-defined certainty margin score for its direction and runway 18 calls is ${Math.round(hour.certainty)}/100. It is the smaller probability margin, not a probability that both calls are correct.`;
  }

  if (/\b(operating direction|direction|\bod\b|betriebsrichtung|richtung)\b/.test(question)) {
    const chance = hour.od === "25" ? hour.p_od25 : 1 - hour.p_od25;
    return `For ${formatForecastHour(hour)}, the model calls OD ${hour.od} (${hour.od === "25" ? "west" : "east"}) with ${percent(chance)} probability. The official rule baseline calls OD ${hour.rule_od}.`;
  }

  return `${SUPPORTED_QUESTIONS} Selected hour: ${formatForecastHour(hour)}.`;
}
