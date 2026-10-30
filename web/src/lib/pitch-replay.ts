import type { ForecastResponse, OD } from "./forecast-types.ts";

export interface ReplayScore {
  matchedHours: number;
  totalHours: number;
  modelCorrect: number;
  ruleCorrect: number;
  persistenceCorrect: number;
}

export interface RecordedOpposite {
  time: string;
  od: OD;
  /** Last post-issue recorded hour still matching current_od, if available. */
  previousMatchingTime: string | null;
}

export type PreparationTimingStatus = "before-recorded-change-interval" | "late" | "unknown" | "insufficient-lead";

export interface PlanningEvent {
  kind: "direction" | "runway18";
  time: string;
}

const isOD = (value: unknown): value is OD => value === "25" || value === "07";
const isTime = (value: unknown): value is string => typeof value === "string" && Number.isFinite(Date.parse(value));

function uniqueValues<T>(values: T[]): T | null {
  const distinct = [...new Set(values)];
  return distinct.length === 1 ? distinct[0] : null;
}

/**
 * Compare OD predictions only where a unique, valid recorded OD label matches
 * a unique forecast hour. All three scores share that same timestamp set.
 * Runway 18 labels are intentionally excluded: they are inferred separately.
 */
export function scoreReplay(f: ForecastResponse): ReplayScore {
  const result: ReplayScore = {
    matchedHours: 0,
    totalHours: Array.isArray(f.hours) ? f.hours.length : 0,
    modelCorrect: 0,
    ruleCorrect: 0,
    persistenceCorrect: 0,
  };

  if (!Array.isArray(f.hours) || !Array.isArray(f.observed) || !isOD(f.current_od)) return result;

  const forecastRows = new Map<string, { model: OD[]; rule: OD[] }>();
  for (const hour of f.hours) {
    if (!isTime(hour.time) || !isOD(hour.od) || !isOD(hour.rule_od)) continue;
    const rows = forecastRows.get(hour.time) ?? { model: [], rule: [] };
    rows.model.push(hour.od);
    rows.rule.push(hour.rule_od);
    forecastRows.set(hour.time, rows);
  }

  const labels = new Map<string, OD[]>();
  for (const row of f.observed) {
    if (!isTime(row.time) || !isOD(row.od)) continue;
    const values = labels.get(row.time) ?? [];
    values.push(row.od);
    labels.set(row.time, values);
  }

  for (const [time, values] of labels) {
    const forecast = forecastRows.get(time);
    const label = uniqueValues(values);
    const model = forecast && uniqueValues(forecast.model);
    const rule = forecast && uniqueValues(forecast.rule);
    if (!label || !model || !rule) continue;

    result.matchedHours += 1;
    if (model === label) result.modelCorrect += 1;
    if (rule === label) result.ruleCorrect += 1;
    if (f.current_od === label) result.persistenceCorrect += 1;
  }

  return result;
}

/**
 * Find the first post-issue recorded OD that differs from the issue direction.
 * The preceding matching sample bounds the possible switch; neither endpoint
 * is asserted to be the exact transition time.
 */
export function firstRecordedOpposite(f: ForecastResponse): RecordedOpposite | null {
  if (!Array.isArray(f.observed) || !isTime(f.issued_at) || !isOD(f.current_od)) return null;
  const issueTime = Date.parse(f.issued_at);
  const byTime = new Map<string, OD[]>();

  for (const row of f.observed) {
    if (!isTime(row.time) || Date.parse(row.time) <= issueTime || !isOD(row.od)) continue;
    const values = byTime.get(row.time) ?? [];
    values.push(row.od);
    byTime.set(row.time, values);
  }

  const sorted = [...byTime.entries()]
    .filter(([, values]) => uniqueValues(values) !== null)
    .sort(([a], [b]) => Date.parse(a) - Date.parse(b));
  const firstIndex = sorted.findIndex(([, values]) => uniqueValues(values) !== f.current_od);
  if (firstIndex < 0) return null;

  const [time, values] = sorted[firstIndex];
  const previousMatching = sorted
    .slice(0, firstIndex)
    .reverse()
    .find(([, priorValues]) => uniqueValues(priorValues) === f.current_od);
  return {
    time,
    od: uniqueValues(values)!,
    previousMatchingTime: previousMatching?.[0] ?? null,
  };
}

/** Compare a scenario review deadline with the available hourly OD evidence. */
export function preparationTimingStatus(
  issuedAt: string,
  reviewAt: string,
  opposite: RecordedOpposite | null,
): PreparationTimingStatus {
  if (!isTime(issuedAt) || !isTime(reviewAt)) return "unknown";
  const issueMs = Date.parse(issuedAt);
  const reviewMs = Date.parse(reviewAt);
  if (reviewMs < issueMs) return "insufficient-lead";
  if (!opposite || !isTime(opposite.time)) return "unknown";

  const firstDifferentMs = Date.parse(opposite.time);
  // A review at/after the first differing recorded hour is late even when
  // the historical coverage has no earlier matching sample to bound the gap.
  if (reviewMs >= firstDifferentMs) return "late";
  if (!opposite.previousMatchingTime || !isTime(opposite.previousMatchingTime)) return "unknown";

  const previousMatchingMs = Date.parse(opposite.previousMatchingTime);
  if (firstDifferentMs <= previousMatchingMs) return "unknown";
  if (reviewMs <= previousMatchingMs) return "before-recorded-change-interval";
  return "unknown";
}

/** Earliest forecast direction-change window or Runway 18 closure after issue time. */
export function planningEvent(f: ForecastResponse): PlanningEvent | null {
  if (!isTime(f.issued_at)) return null;
  const issueTime = Date.parse(f.issued_at);
  const candidates: PlanningEvent[] = [];

  if (f.next_change && isTime(f.next_change.time)) {
    const earliestLocal = Array.isArray(f.next_change.window_local) ? f.next_change.window_local[0] : undefined;
    const matchingHours = typeof earliestLocal === "string" && Array.isArray(f.hours)
      ? f.hours.filter((hour) => hour.local === earliestLocal && isTime(hour.time) && Date.parse(hour.time) > issueTime)
      : [];
    // A repeated local hour during the autumn clock change has two UTC mappings.
    const mappedHour = matchingHours.length === 1 ? matchingHours[0] : undefined;
    const time = mappedHour && isTime(mappedHour.time) ? mappedHour.time : f.next_change.time;
    if (isTime(time) && Date.parse(time) > issueTime) candidates.push({ kind: "direction", time });
  }

  for (const closure of f.closures_18 ?? []) {
    if (isTime(closure.start) && Date.parse(closure.start) > issueTime) {
      candidates.push({ kind: "runway18", time: closure.start });
    }
  }

  candidates.sort((a, b) => Date.parse(a.time) - Date.parse(b.time));
  return candidates[0] ?? null;
}

/** Format an ISO timestamp as day.month and hour:minute in Berlin local time. */
export function formatPitchTime(utcISO: string): string {
  if (!isTime(utcISO)) return "—";
  return new Intl.DateTimeFormat("de-DE", {
    timeZone: "Europe/Berlin",
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).format(new Date(utcISO));
}

/** Format a Berlin timestamp with its UTC offset so repeated DST hours differ. */
export function formatPitchTimeWithOffset(utcISO: string): string {
  if (!isTime(utcISO)) return "—";
  return new Intl.DateTimeFormat("de-DE", {
    timeZone: "Europe/Berlin",
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    timeZoneName: "shortOffset",
    hourCycle: "h23",
  }).format(new Date(utcISO));
}
