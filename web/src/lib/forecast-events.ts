import type { ForecastResponse, HourForecast, OD } from "./forecast-types";

const HOUR_MS = 60 * 60 * 1000;

export interface ForecastCoverage {
  count: number;
  firstLead: number | null;
  lastLead: number | null;
  hasTimestampGaps: boolean;
  label: string;
}

export interface DirectionEvent {
  id: string;
  time: string;
  local: string;
  hourIndex: number | null;
  from: OD;
  to: OD;
  probability: number;
  probabilityLabel: string;
  sourceLabel: string;
  windowLocal?: [string, string];
}

export interface ClosureEvent {
  id: string;
  kind: "closure";
  time: string;
  local: string;
  hourIndex: number | null;
  probability: number;
  probabilityLabel: string;
  sourceLabel: string;
  end?: { time: string; local: string };
  ongoing: boolean;
}

export interface RunwayCallEvent {
  id: string;
  kind: "hourly-call";
  time: string;
  local: string;
  hourIndex: number;
  lastClosedCall: { time: string; local: string };
  firstUsableCall?: { time: string; local: string };
  closedSampleCount: number;
  gapsPresent: boolean;
  ongoing: boolean;
  probability: number;
  probabilityLabel: string;
  sourceLabel: string;
}

export type Runway18Event = ClosureEvent | RunwayCallEvent;

export function forecastCoverage(hours: HourForecast[]): ForecastCoverage {
  if (hours.length === 0) {
    return {
      count: 0,
      firstLead: null,
      lastLead: null,
      hasTimestampGaps: false,
      label: "No hourly forecast rows supplied.",
    };
  }

  const chronological = [...hours].sort((a, b) => a.time.localeCompare(b.time));
  const firstLead = chronological[0].lead_h;
  const lastLead = chronological[chronological.length - 1].lead_h;
  const hasTimestampGaps = chronological.some((hour, index) =>
    index > 0 && Date.parse(hour.time) - Date.parse(chronological[index - 1].time) !== HOUR_MS,
  );
  const unit = hasTimestampGaps ? "forecast row" : "hourly point";
  const count = `${hours.length} supplied ${unit}${hours.length === 1 ? "" : "s"}`;
  const span = firstLead === lastLead ? `T+${firstLead} h` : `T+${firstLead}–T+${lastLead} h`;
  const note = hasTimestampGaps ? " · timestamp gaps or irregular spacing" : "";

  return { count: hours.length, firstLead, lastLead, hasTimestampGaps, label: `${count} · ${span}${note}` };
}

export function formatForecastInstant(utc: string, local: string): string {
  const localMatch = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(local);
  const utcDate = new Date(utc);
  const localDate = localMatch
    ? `${Number(localMatch[3])} ${month(Number(localMatch[2]))} ${localMatch[1]} ${localMatch[4]}:${localMatch[5]}`
    : local.replace("T", " ");

  if (!localMatch || Number.isNaN(utcDate.getTime())) return `${localDate} (Europe/Berlin) · ${utc}`;

  const [, year, monthNumber, day, hour, minute] = localMatch;
  const localEpoch = Date.UTC(Number(year), Number(monthNumber) - 1, Number(day), Number(hour), Number(minute));
  const offsetMinutes = Math.round((localEpoch - utcDate.getTime()) / 60_000);
  const sign = offsetMinutes < 0 ? "−" : "+";
  const absoluteOffset = Math.abs(offsetMinutes);
  const offset = `UTC${sign}${pad(Math.floor(absoluteOffset / 60))}:${pad(absoluteOffset % 60)}`;
  const utcLabel = `${utcDate.getUTCFullYear()}-${pad(utcDate.getUTCMonth() + 1)}-${pad(utcDate.getUTCDate())} ${pad(utcDate.getUTCHours())}:${pad(utcDate.getUTCMinutes())}Z`;

  return `${localDate} (${offset}) · ${utcLabel}`;
}

export function forecastEvents(f: ForecastResponse): {
  coverage: ForecastCoverage;
  direction: DirectionEvent[];
  runway18: Runway18Event[];
} {
  const indexedHours = f.hours.map((hour, index) => ({ hour, index }));
  const byTime = [...indexedHours].sort((a, b) => a.hour.time.localeCompare(b.hour.time));
  const coverage = forecastCoverage(f.hours);

  const direction: DirectionEvent[] = [];
  for (let index = 0; index < byTime.length; index += 1) {
    const { hour, index: sourceIndex } = byTime[index];
    const previous = index === 0 ? null : byTime[index - 1].hour;
    const from = previous ? previous.od : f.current_od;
    if (hour.od === from) continue;

    const supplied = f.next_change?.time === hour.time && f.next_change.to === hour.od ? f.next_change : null;
    const probability = supplied ? supplied.p : probabilityForOD(hour, hour.od);
    const gap = previous ? Date.parse(hour.time) - Date.parse(previous.time) !== HOUR_MS : false;
    const sourceLabel = supplied
      ? "Supplied next-change forecast"
      : !previous
        ? "First supplied call differs from issue direction; transition time unknown"
        : gap
          ? "First differing available call after a timestamp gap; transition time unknown"
          : "Transition in supplied hourly calls";

    direction.push({
      id: `direction-${sourceIndex}`,
      time: hour.time,
      local: hour.local,
      hourIndex: sourceIndex,
      from,
      to: hour.od,
      probability,
      probabilityLabel: `P(OD ${hour.od} at this hour)`,
      sourceLabel,
      ...(supplied ? { windowLocal: supplied.window_local } : {}),
    });
  }

  if (f.next_change && !direction.some((event) => event.time === f.next_change?.time && event.to === f.next_change?.to)) {
    direction.push({
      id: `direction-supplied-${f.next_change.time}`,
      time: f.next_change.time,
      local: f.next_change.local,
      hourIndex: exactHourIndex(indexedHours, f.next_change.time),
      from: f.next_change.from,
      to: f.next_change.to,
      probability: f.next_change.p,
      probabilityLabel: `P(OD ${f.next_change.to} at this hour)`,
      sourceLabel: "Supplied next-change forecast",
      windowLocal: f.next_change.window_local,
    });
  }
  direction.sort((a, b) => a.time.localeCompare(b.time));

  const latestClosureStart = f.closures_18.reduce((latest, closure) => closure.start > latest ? closure.start : latest, "");
  const runway18: Runway18Event[] = f.closures_18.length > 0
    ? f.closures_18.map((closure, index) => {
        const last = byTime.at(-1)?.hour;
        const startsInCoverage = !!last && closure.start <= last.time;
        const isFinalClosure = closure.start === latestClosureStart;
        const finalCallStillUnusable = isFinalClosure && !!last && last.p_18_usable < 0.5 && closure.end >= last.time;
        const ongoing = startsInCoverage && isFinalClosure && (!!last && closure.end > last.time || finalCallStillUnusable);
        return {
          id: `closure-${index}`,
          kind: "closure",
          time: closure.start,
          local: closure.local_start,
          hourIndex: exactHourIndex(indexedHours, closure.start),
          probability: clamp(1 - closure.min_p_usable),
          probabilityLabel: "P(RWY 18 unusable), worst interval hour",
          sourceLabel: "Supplied runway 18 closure interval",
          ...(!ongoing ? { end: { time: closure.end, local: closure.local_end } } : {}),
          ongoing,
        };
      })
    : hourlyRunwayClosures(byTime);

  runway18.sort((a, b) => a.time.localeCompare(b.time));
  return { coverage, direction, runway18 };
}

function hourlyRunwayClosures(hours: { hour: HourForecast; index: number }[]): RunwayCallEvent[] {
  const events: RunwayCallEvent[] = [];
  let closed: { hour: HourForecast; index: number }[] = [];
  let gapsPresent = false;

  const finish = (firstUsableCall?: HourForecast) => {
    if (closed.length === 0) return;
    const first = closed[0];
    const last = closed[closed.length - 1];
    events.push({
      id: `runway-calls-${first.index}`,
      kind: "hourly-call",
      time: first.hour.time,
      local: first.hour.local,
      hourIndex: first.index,
      lastClosedCall: { time: last.hour.time, local: last.hour.local },
      ...(firstUsableCall ? { firstUsableCall: { time: firstUsableCall.time, local: firstUsableCall.local } } : {}),
      closedSampleCount: closed.length,
      gapsPresent,
      ongoing: !firstUsableCall,
      probability: Math.min(...closed.map(({ hour }) => clamp(1 - hour.p_18_usable))),
      probabilityLabel: "Lowest P(RWY 18 unusable) among these supplied calls",
      sourceLabel: "Hourly calls; no closure interval supplied",
    });
    closed = [];
    gapsPresent = false;
  };

  for (let index = 0; index < hours.length; index += 1) {
    const entry = hours[index];
    const previous = index > 0 ? hours[index - 1].hour : null;
    if (previous && entry.hour.p_18_usable < 0.5 && previous.p_18_usable < 0.5 && Date.parse(entry.hour.time) - Date.parse(previous.time) !== HOUR_MS) {
      gapsPresent = true;
    }

    if (entry.hour.p_18_usable < 0.5) {
      closed.push(entry);
    } else if (closed.length > 0) {
      if (Date.parse(entry.hour.time) - Date.parse(closed[closed.length - 1].hour.time) !== HOUR_MS) gapsPresent = true;
      finish(entry.hour);
    }
  }
  finish();
  return events;
}

function exactHourIndex(hours: { hour: HourForecast; index: number }[], time: string): number | null {
  return hours.find((entry) => entry.hour.time === time)?.index ?? null;
}

function probabilityForOD(hour: HourForecast, od: OD): number {
  return clamp(od === "25" ? hour.p_od25 : 1 - hour.p_od25);
}

function clamp(value: number): number {
  return Math.max(0, Math.min(1, value));
}

function month(value: number): string {
  return ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][value - 1] ?? "???";
}

function pad(value: number): string {
  return String(value).padStart(2, "0");
}
