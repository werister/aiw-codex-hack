import type { ForecastResponse, HourForecast } from "./forecast-types";

export const HANDOVER_SUGGESTIONS = [
  "Brief next 6 hours",
  "Runway 18 restrictions",
  "Compare model and rules",
] as const;

export const HANDOVER_HOUR_COUNT = 6;
const HOUR_MS = 60 * 60 * 1000;

type HandoverIntent = "brief" | "restrictions" | "compare";

export interface HandoverAnswer {
  text: string;
  copyable: boolean;
}

interface CoveredWindow {
  hours: HourForecast[];
  stop: "complete" | "horizon" | "gap" | "invalid";
  expectedNext: number;
  foundNext?: string;
  error?: string;
}

function normalizeQuestion(value: string) {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim()
    .replace(/[.!?]+$/, "");
}

function classifyQuestion(rawQuestion: string): HandoverIntent | null {
  const question = normalizeQuestion(rawQuestion);
  const sixHourWindow = "(?:the )?next (?:6|six) hours";

  if (
    new RegExp(`^(?:please )?(?:brief|summari[sz]e) ${sixHourWindow}(?: from the selected hour)?$`).test(question) ||
    new RegExp(`^give me (?:a )?(?:brief|handover) for ${sixHourWindow}$`).test(question) ||
    new RegExp(`^handover(?: brief)? for ${sixHourWindow}$`).test(question)
  ) {
    return "brief";
  }

  if (
    new RegExp(`^(?:runway 18 restrictions?|(?:show|list) (?:the )?runway 18 restrictions?)(?: (?:in|for|over|during) ${sixHourWindow})?$`).test(question)
  ) {
    return "restrictions";
  }

  if (
    new RegExp(`^(?:compare (?:the )?model (?:and|with|vs) (?:the )?(?:rules?|rule baseline)|what do (?:the )?model and (?:the )?(?:rules?|rule baseline) disagree on)(?: (?:for|in|over) ${sixHourWindow})?$`).test(question)
  ) {
    return "compare";
  }

  return null;
}

function asTime(value: string) {
  if (!/(?:Z|[+-]\d{2}:?\d{2})$/i.test(value)) return null;
  const time = Date.parse(value);
  return Number.isFinite(time) ? time : null;
}

function utcIso(time: number) {
  return new Date(time).toISOString();
}

function formatHandoverTimestamp(value: string) {
  const time = asTime(value);
  if (time === null) return `${value} (timestamp unavailable)`;

  const iso = utcIso(time).replace(/:00\.000Z$/, "Z").replace(/\.000Z$/, "Z").replace("T", " ");
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Europe/Berlin",
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
    timeZoneName: "longOffset",
  }).formatToParts(new Date(time));
  const fields = Object.fromEntries(parts.map(({ type, value: part }) => [type, part]));
  const offsetMatch = /^GMT(?:([+-])(\d{2}):(\d{2}))?$/.exec(fields.timeZoneName ?? "");
  const offset = offsetMatch
    ? offsetMatch[1]
      ? `UTC${offsetMatch[1]}${offsetMatch[2]}:${offsetMatch[3]}`
      : "UTC+00:00"
    : "UTC offset unavailable";

  return `${fields.day} ${fields.month} ${fields.year} ${fields.hour}:${fields.minute} Europe/Berlin (${offset}; UTC ${iso})`;
}

function collectWindow(forecast: ForecastResponse, selected: HourForecast): CoveredWindow {
  const matchingIndices = forecast.hours.flatMap((hour, index) => hour.time === selected.time ? [index] : []);
  if (matchingIndices.length !== 1) {
    return {
      hours: [],
      stop: "invalid",
      expectedNext: 0,
      error: matchingIndices.length === 0
        ? "The selected hour is not present in this forecast. Select a published forecast hour and ask again."
        : "The selected timestamp appears more than once. The briefing cannot choose between duplicate rows.",
    };
  }

  const firstIndex = matchingIndices[0];
  const firstTime = asTime(selected.time);
  if (firstTime === null) {
    return { hours: [], stop: "invalid", expectedNext: 0, error: "The selected hour has an invalid UTC timestamp." };
  }

  const hours = [forecast.hours[firstIndex]];
  let expectedNext = firstTime + HOUR_MS;
  let stop: CoveredWindow["stop"] = "complete";
  let foundNext: string | undefined;

  while (hours.length < HANDOVER_HOUR_COUNT) {
    const candidate = forecast.hours[firstIndex + hours.length];
    if (!candidate) {
      stop = "horizon";
      break;
    }

    const candidateTime = asTime(candidate.time);
    if (candidateTime === null || candidateTime !== expectedNext) {
      stop = "gap";
      foundNext = candidate.time;
      break;
    }

    hours.push(candidate);
    expectedNext = candidateTime + HOUR_MS;
  }

  return { hours, stop, expectedNext, foundNext };
}

function coverageLines(window: CoveredWindow) {
  const count = window.hours.length;
  const first = window.hours[0];
  const last = window.hours[count - 1];
  const lines = [
    `Coverage: ${count} of ${HANDOVER_HOUR_COUNT} consecutive UTC forecast hours${first && last ? `, from ${formatHandoverTimestamp(first.time)} through ${formatHandoverTimestamp(last.time)}` : ""}.`,
  ];

  if (window.stop === "horizon") {
    lines.push(`The published forecast ends before the next requested hour at ${formatHandoverTimestamp(utcIso(window.expectedNext))}.`);
  } else if (window.stop === "gap") {
    lines.push(`Coverage stops at the missing or non-consecutive UTC hour ${formatHandoverTimestamp(utcIso(window.expectedNext))}${window.foundNext ? `; the next row is ${formatHandoverTimestamp(window.foundNext)}` : ""}. Later rows are not bridged.`);
  }

  return lines;
}

function provenanceLines(forecast: ForecastResponse) {
  const lines = [
    `Issued: ${formatHandoverTimestamp(forecast.issued_at)} · mode ${forecast.mode}.`,
    `Model ${forecast.model_version} · weather source ${forecast.nwp} · rules ${forecast.rules_version}.`,
  ];
  const evidence = forecast.evidence;

  if (!evidence) {
    lines.push("Run-level source availability and model-artifact provenance are not included in this forecast.");
    return lines;
  }

  lines.push(
    `Run ${evidence.run_id} · artifact ${evidence.model_artifact.version} · trained through ${formatHandoverTimestamp(evidence.model_artifact.trained_through)} · recorded publication lag ${evidence.publication_lag_h} h.`,
  );
  const missingSources = evidence.sources.filter((source) => source.missing).map((source) => source.name);
  const sourcesWithoutAvailability = evidence.sources.filter((source) => !source.missing && asTime(source.available_at) === null).length;
  const lateSources = evidence.sources.filter((source) => {
    if (source.missing) return false;
    const availableAt = asTime(source.available_at);
    const issueAt = asTime(forecast.issued_at);
    return availableAt !== null && issueAt !== null && availableAt > issueAt;
  }).length;
  const missingLabel = missingSources.length ? `missing: ${missingSources.join(", ")}` : "no feeds marked missing";
  lines.push(`Recorded source metadata: ${missingLabel}; ${lateSources} feed${lateSources === 1 ? "" : "s"} recorded available after issue time; ${sourcesWithoutAvailability} without a usable availability timestamp.`);
  return lines;
}

function probability(value: number) {
  return Number.isFinite(value) && value >= 0 && value <= 1
    ? `${Math.round(value * 100)}%`
    : "unavailable";
}

function directionProbability(hour: HourForecast) {
  return hour.od === "25" ? hour.p_od25 : 1 - hour.p_od25;
}

function hourSummary(hour: HourForecast) {
  const modelRunway18 = hour.p_18_usable >= 0.5 ? "likely usable" : "likely closed";
  const ruleRunway18 = hour.rule_18_usable ? "usable" : "closed";
  return `- ${formatHandoverTimestamp(hour.time)} (+${hour.lead_h} h): model OD ${hour.od} (${probability(directionProbability(hour))} for that call); Runway 18 ${modelRunway18} (P usable ${probability(hour.p_18_usable)}); certainty score ${Math.round(hour.certainty)}/100. Official rule baseline: OD ${hour.rule_od}; Runway 18 ${ruleRunway18}.`;
}

function briefingText(forecast: ForecastResponse, window: CoveredWindow) {
  return [
    `Six-hour forecast briefing starting at the selected hour. This is a forecast window, not an assumed shift duration.`,
    ...coverageLines(window),
    ...provenanceLines(forecast),
    ...window.hours.map(hourSummary),
    "Certainty is the producer's 0–100 margin score, not a probability that both calls are correct.",
    "No operational cause, flight demand, staffing impact, or savings are included in this forecast.",
  ].join("\n");
}

function restrictionsText(forecast: ForecastResponse, window: CoveredWindow) {
  const firstTime = asTime(window.hours[0].time)!;
  const endExclusive = asTime(window.hours[window.hours.length - 1].time)! + HOUR_MS;
  const chronologicalHours = forecast.hours
    .flatMap((hour) => {
      const time = asTime(hour.time);
      return time === null ? [] : [{ hour, time }];
    })
    .sort((a, b) => a.time - b.time);
  const finalHour = chronologicalHours.at(-1);
  const latestClosureStart = forecast.closures_18.reduce((latest, closure) => {
    const time = asTime(closure.start);
    return time !== null && time > latest ? time : latest;
  }, -Infinity);
  const reachesForecastEnd = (start: number, end: number) =>
    finalHour !== undefined &&
    start === latestClosureStart &&
    finalHour.hour.p_18_usable < 0.5 &&
    end >= finalHour.time &&
    start <= finalHour.time;
  const validClosures = forecast.closures_18.flatMap((closure) => {
    const start = asTime(closure.start);
    const end = asTime(closure.end);
    const truncatedFinalClosure = start !== null && end !== null && reachesForecastEnd(start, end) &&
      finalHour!.time >= firstTime && finalHour!.time < endExclusive;
    return start !== null && end !== null && end >= start &&
      ((start < endExclusive && end > firstTime) || (start === end && start >= firstTime && start < endExclusive) || truncatedFinalClosure)
      ? [{ closure, start, end }]
      : [];
  });
  const invalidCount = forecast.closures_18.filter((closure) => {
    const start = asTime(closure.start);
    const end = asTime(closure.end);
    return start === null || end === null || end < start;
  }).length;
  const lines = [
    "Runway 18 restriction intervals supplied by the forecast. The start is inclusive; reopening is reported only when a matching forecast hour calls the runway likely usable. Final intervals may be truncated by the forecast horizon.",
    ...coverageLines(window),
  ];

  if (validClosures.length === 0) {
    lines.push("No supplied Runway 18 restriction interval overlaps these covered forecast hours.");
    const closedRuns: { hours: HourForecast[]; laterUsable?: HourForecast }[] = [];
    let activeRun: HourForecast[] = [];
    for (const hour of window.hours) {
      if (hour.p_18_usable < 0.5) {
        activeRun.push(hour);
      } else if (activeRun.length > 0) {
        closedRuns.push({ hours: activeRun, laterUsable: hour });
        activeRun = [];
      }
    }
    if (activeRun.length > 0) closedRuns.push({ hours: activeRun });

    if (closedRuns.length > 0) {
      lines.push("Hourly calls only; these samples do not establish a supplied closure interval or continuous state between hours.");
      for (const run of closedRuns) {
        const first = run.hours[0];
        const last = run.hours[run.hours.length - 1];
        const minUsable = Math.min(...run.hours.map((hour) => hour.p_18_usable));
        const count = run.hours.length;
        const later = run.laterUsable
          ? ` First later usable sampled call: ${formatHandoverTimestamp(run.laterUsable.time)} (P usable ${probability(run.laterUsable.p_18_usable)}).`
          : " No later usable call appears in this covered window; reopening is unknown from these hourly calls.";
        lines.push(`- ${count} likely-unusable hourly call${count === 1 ? "" : "s"}; first ${formatHandoverTimestamp(first.time)}, last ${formatHandoverTimestamp(last.time)}; minimum P usable ${probability(minUsable)}.${later}`);
      }
    }
  } else {
    lines.push(`${validClosures.length} restriction interval${validClosures.length === 1 ? " overlaps" : "s overlap"} the covered forecast hours:`);
    for (const { closure, start, end } of validClosures) {
      const when = start < firstTime
        ? `Already ongoing at the selected hour; interval began ${formatHandoverTimestamp(closure.start)}`
        : `Starts${start === firstTime ? " at" : ""} ${formatHandoverTimestamp(closure.start)}`;
      let ending: string;
      const endHour = chronologicalHours.find(({ time }) => time === end)?.hour;
      if (reachesForecastEnd(start, end)) {
        ending = `It reaches the final supplied hour ${formatHandoverTimestamp(finalHour!.hour.time)}, whose model P(Runway 18 usable) is ${probability(finalHour!.hour.p_18_usable)}; reopening is unknown beyond this forecast.`;
      } else if (endHour && endHour.p_18_usable >= 0.5) {
        ending = end >= endExclusive
          ? `It continues through this briefing window; the matching first usable forecast call is ${formatHandoverTimestamp(closure.end)} (P usable ${probability(endHour.p_18_usable)}).`
          : `The matching first usable forecast call is ${formatHandoverTimestamp(closure.end)} (P usable ${probability(endHour.p_18_usable)}).`;
      } else if (endHour) {
        ending = `The interval end matches a forecast row that still calls Runway 18 likely closed (P usable ${probability(endHour.p_18_usable)}); reopening is not confirmed.`;
      } else {
        ending = end > endExclusive
          ? `It continues beyond this briefing window and ends at ${formatHandoverTimestamp(closure.end)}, but no matching usable forecast row confirms reopening.`
          : `The interval ends at ${formatHandoverTimestamp(closure.end)}, but no matching usable forecast row confirms reopening.`;
      }
      lines.push(`- ${when}. Minimum forecast P(Runway 18 usable): ${probability(closure.min_p_usable)}. ${ending}`);
    }
  }

  if (invalidCount > 0) {
    lines.push(`${invalidCount} supplied restriction interval${invalidCount === 1 ? " has" : "s have"} invalid timestamps and could not be placed in this window.`);
  }
  lines.push("This forecast does not provide current runway status or an operational cause.");
  return lines.join("\n");
}

function comparisonText(forecast: ForecastResponse, window: CoveredWindow) {
  const directionDisagreements = window.hours.filter((hour) => hour.od !== hour.rule_od);
  const runwayDisagreements = window.hours.filter((hour) => (hour.p_18_usable >= 0.5) !== hour.rule_18_usable);
  const lines = [
    "Model-to-rule comparison for the selected hour and following consecutive UTC forecast hours.",
    ...coverageLines(window),
    `Rules version: ${forecast.rules_version}. The comparison reports differences only; it does not infer a cause.`,
    `Operating direction disagreements (${directionDisagreements.length}/${window.hours.length} covered hours):`,
  ];

  if (directionDisagreements.length === 0) {
    lines.push("- None in the covered hours.");
  } else {
    lines.push(...directionDisagreements.map((hour) =>
      `- ${formatHandoverTimestamp(hour.time)}: model OD ${hour.od} (${probability(directionProbability(hour))} for that call); official rules OD ${hour.rule_od}.`,
    ));
  }

  lines.push(`Runway 18 disagreements (${runwayDisagreements.length}/${window.hours.length} covered hours):`);
  if (runwayDisagreements.length === 0) {
    lines.push("- None in the covered hours.");
  } else {
    lines.push(...runwayDisagreements.map((hour) =>
      `- ${formatHandoverTimestamp(hour.time)}: model says ${hour.p_18_usable >= 0.5 ? "likely usable" : "likely closed"} (P usable ${probability(hour.p_18_usable)}); official rules say ${hour.rule_18_usable ? "usable" : "closed"}.`,
    ));
  }

  lines.push("No operational cause or flight-demand context is present in the forecast payload.");
  return lines.join("\n");
}

export function answerHandoverQuestion(
  forecast: ForecastResponse,
  selected: HourForecast | undefined,
  rawQuestion: string,
): HandoverAnswer | null {
  const intent = classifyQuestion(rawQuestion);
  if (!intent) return null;

  if (!selected) {
    return {
      text: "Select a forecast hour first. The six-hour briefing begins at that selected hour and uses only following consecutive UTC forecast rows.",
      copyable: false,
    };
  }

  const window = collectWindow(forecast, selected);
  if (window.stop === "invalid") {
    return { text: window.error ?? "The selected forecast hour is unavailable.", copyable: false };
  }

  let text: string;
  if (intent === "brief") text = briefingText(forecast, window);
  else if (intent === "restrictions") text = [
    ...provenanceLines(forecast),
    restrictionsText(forecast, window),
  ].join("\n");
  else text = [
    ...provenanceLines(forecast),
    comparisonText(forecast, window),
  ].join("\n");

  return { text, copyable: true };
}
