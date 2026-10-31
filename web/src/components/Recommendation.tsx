import type { ForecastResponse, OD } from "@/lib/forecast-types";
import { forecastEvents, formatForecastInstant } from "@/lib/forecast-events";
import type { DirectionEvent, Runway18Event } from "@/lib/forecast-events";
import { Arrow, OD_LABEL, cx, odBg, pct } from "./ui";

// This summary selects the earliest event in the supplied rows. Hourly calls are marginals;
// the absence of an event in these rows does not mean the probability of a later event is zero.
export const PLAN_POLICY =
  "Shows the earliest direction change or runway 18 restriction in this forecast. Probabilities describe the state at each hour, not the chance of a change between hours. Coverage ends with the last available forecast hour.";
export const CERTAINTY_DEF =
  "Certainty score = 100 × min(|2·P(25) − 1|, |2·P(18 usable) − 1|): the smaller of the two hourly probability margins. It is a margin score, not a probability.";

export type Plan =
  | { kind: "change"; time: string; to: OD; local: string; window: [string, string] | null; p: number; certainty: number | null; sourceLabel: string }
  | { kind: "closure"; time: string; start: string; end: { time: string; local: string } | null; openEnded: boolean; p: number; certainty: number | null; sourceLabel: string; lastTime: string | null; lastLocal: string | null }
  | { kind: "runway-calls"; time: string; start: string; last: { time: string; local: string }; firstUsable: { time: string; local: string } | null; ongoing: boolean; gapsPresent: boolean; p: number; certainty: number | null }
  | { kind: "hold"; time: string; od: OD; r18Open: boolean; p: number; certainty: number | null; coverage: string; hasHours: boolean };

export function planFrom(f: ForecastResponse): Plan {
  const events = forecastEvents(f);
  const candidates: ({ kind: "change"; event: DirectionEvent } | { kind: "runway"; event: Runway18Event })[] = [
    ...events.direction.map((event) => ({ kind: "change" as const, event })),
    ...events.runway18.map((event) => ({ kind: "runway" as const, event })),
  ];
  candidates.sort((a, b) => a.event.time.localeCompare(b.event.time));

  const candidate = candidates[0];
  if (candidate?.kind === "change") {
    const { event } = candidate;
    return {
      kind: "change",
      time: event.time,
      to: event.to,
      local: event.local,
      window: event.windowLocal ?? null,
      p: event.probability,
      certainty: f.hours.find((hour) => hour.time === event.time)?.certainty ?? null,
      sourceLabel: event.sourceLabel,
    };
  }

  if (candidate?.kind === "runway" && candidate.event.kind === "closure") {
    const { event } = candidate;
    const last = [...f.hours].sort((a, b) => a.time.localeCompare(b.time)).at(-1);
    return {
      kind: "closure",
      time: event.time,
      start: event.local,
      end: event.end ?? null,
      openEnded: event.ongoing,
      p: event.probability,
      certainty: f.hours.find((hour) => hour.time === event.time)?.certainty ?? null,
      sourceLabel: event.sourceLabel,
      lastTime: last?.time ?? null,
      lastLocal: last?.local ?? null,
    };
  }

  if (candidate?.kind === "runway" && candidate.event.kind === "hourly-call") {
    const { event } = candidate;
    return {
      kind: "runway-calls",
      time: event.time,
      start: event.local,
      last: event.lastClosedCall,
      firstUsable: event.firstUsableCall ?? null,
      ongoing: event.ongoing,
      gapsPresent: event.gapsPresent,
      p: event.probability,
      certainty: f.hours.find((hour) => hour.time === event.time)?.certainty ?? null,
    };
  }

  const first = f.hours[0];
  const probabilities = f.hours.flatMap((hour) => [
    f.current_od === "25" ? hour.p_od25 : 1 - hour.p_od25,
    first?.p_18_usable >= 0.5 ? hour.p_18_usable : 1 - hour.p_18_usable,
  ]);
  return {
    kind: "hold",
    time: first?.time ?? f.issued_at,
    od: f.current_od,
    r18Open: first ? first.p_18_usable >= 0.5 : false,
    p: probabilities.length ? Math.min(...probabilities) : 0,
    certainty: f.hours.length && f.hours.every((hour) => typeof hour.certainty === "number" && Number.isFinite(hour.certainty))
      ? Math.min(...f.hours.map((hour) => hour.certainty)) : null,
    coverage: events.coverage.label,
    hasHours: f.hours.length > 0,
  };
}

export function planWindow(plan: Plan) {
  if (plan.kind === "change") {
    const actual = formatForecastInstant(plan.time, plan.local);
    return plan.window
      ? `${actual} · forecast window (Berlin) ${formatLocal(plan.window[0])}–${formatLocal(plan.window[1])}`
      : actual;
  }
  if (plan.kind === "closure") {
    const startsAt = formatForecastInstant(plan.time, plan.start);
    if (plan.openEnded) {
      const last = plan.lastTime && plan.lastLocal ? ` through ${formatForecastInstant(plan.lastTime, plan.lastLocal)}` : " through the last forecast hour";
      return `Starts ${startsAt}${last}; reopening unknown`;
    }
    return plan.end ? `Starts ${startsAt} · reported interval end ${formatForecastInstant(plan.end.time, plan.end.local)}` : `Starts ${startsAt}`;
  }
  if (plan.kind === "runway-calls") {
    const span = `${formatForecastInstant(plan.time, plan.start)}–${formatForecastInstant(plan.last.time, plan.last.local)}`;
    if (plan.ongoing) return `${plan.gapsPresent ? "Closed samples" : "Closed calls"} ${span}; reopening unknown`;
    const end = plan.firstUsable ? ` · first usable sampled hour ${formatForecastInstant(plan.firstUsable.time, plan.firstUsable.local)}` : "";
    return `${plan.gapsPresent ? "Closed samples" : "Closed calls"} ${span}${end}${plan.gapsPresent ? " · missing hours not inferred" : ""}`;
  }
  return plan.coverage;
}

export function planHeadline(plan: Plan) {
  if (plan.kind === "change") return `Forecast change to ${plan.to} ${OD_LABEL[plan.to]}`;
  if (plan.kind === "closure") return "Runway 18 closure forecast";
  if (plan.kind === "runway-calls") return "Runway 18 likely unusable at these hours";
  return plan.hasHours ? "No event in the available forecast hours" : "Hourly forecast unavailable";
}

// Leads the page: summarize the earliest available signal with its marginal probability and source.
export function Recommendation({
  f,
  compact,
  onShowEvidence,
}: {
  f: ForecastResponse;
  compact?: boolean;
  onShowEvidence?: () => void;
}) {
  const plan = planFrom(f);

  return (
    <section className={cx("rounded-card bg-select p-5 text-ink", !compact && "sm:p-6")} aria-label="Forecast summary">
      <h2 className="eyebrow">Forecast summary</h2>

      <p className={cx("font-light leading-[1.15] tracking-[-0.01em]", compact ? "mt-2 text-[26px]" : "mt-4 text-[28px] sm:text-[40px]")}>
        {plan.kind === "change" && <>Forecast change to <Chip od={plan.to} /></>}
        {plan.kind === "closure" && <>Runway&nbsp;18 closure forecast</>}
        {plan.kind === "runway-calls" && <>Runway&nbsp;18 likely unusable at these hours</>}
        {plan.kind === "hold" && (plan.hasHours ? "No event in the available forecast hours" : "Hourly forecast unavailable")}
      </p>

      <dl className={cx("grid gap-x-6 gap-y-4", compact ? "mt-3 grid-cols-2" : "mt-5 grid-cols-2 lg:grid-cols-5")}>
        <Fact k={plan.kind === "hold" ? "Coverage" : "Forecast timing"}>{planWindow(plan)}</Fact>
        <Fact k={probLabel(plan)}>{plan.kind === "hold" && !plan.hasHours ? "Unavailable" : pct(plan.p)}</Fact>
        <Fact k={plan.kind === "hold" ? "Lowest hourly certainty score" : "Certainty score"} hint={CERTAINTY_DEF}>
          {plan.certainty == null || !Number.isFinite(plan.certainty) ? "Unavailable" : `${plan.certainty}/100`}
        </Fact>
        <Fact k="Issued">{formatForecastInstant(f.issued_at, f.issued_local)}</Fact>
        <Fact k="Traffic data">
          <span className="flex items-center gap-2">
            <span className="h-3 w-5 shrink-0 rounded-[2px] border border-dashed border-muted" aria-hidden />
            <span className="min-w-0">Demand data unavailable</span>
          </span>
        </Fact>
        {!compact && (
          <div className="col-span-2 flex items-end lg:col-span-1 lg:justify-end">
            {onShowEvidence && (
              <button type="button" onClick={onShowEvidence} className="pill-btn bg-accent text-accent-ink [--btn-ring:var(--accent)]">
                Show evidence <Arrow />
              </button>
            )}
          </div>
        )}
      </dl>

      <p className={cx("text-[13px] leading-snug text-ink-2", compact ? "mt-3" : "mt-5")}>
        {sourceLabel(plan)} Operational decisions remain with the responsible team.
        {!compact && " Flight demand data is unavailable."}
      </p>
    </section>
  );
}

function sourceLabel(plan: Plan) {
  if (plan.kind === "change" || plan.kind === "closure") return plan.sourceLabel;
  if (plan.kind === "runway-calls") return "Based on hourly calls; no continuous closure interval is available.";
  return "Based on the available forecast hours.";
}

export function probLabel(plan: Plan) {
  if (plan.kind === "change") return `P(OD ${plan.to} at this hour)`;
  if (plan.kind === "closure") return "P(RWY 18 unusable), worst interval hour";
  if (plan.kind === "runway-calls") return "Lowest hourly P(RWY 18 unusable)";
  return plan.hasHours ? "Lowest hourly marginal support (OD / runway 18)" : "Hourly marginal support unavailable";
}

function formatLocal(local: string) {
  return `${local.slice(0, 10)} ${local.slice(11, 16)}`;
}

function Chip({ od }: { od: OD }) {
  return <span className={cx("inline-block whitespace-nowrap rounded-full px-[0.4em] text-on-signal", odBg(od))}>{od} {OD_LABEL[od]}</span>;
}

function Fact({ k, hint, children }: { k: string; hint?: string; children: React.ReactNode }) {
  return (
    <div className="min-w-0 [overflow-wrap:anywhere]" title={hint}>
      <dt className={cx("mb-1 text-[12px] text-muted", hint && "w-fit cursor-help underline decoration-dotted underline-offset-2")}>{k}</dt>
      <dd className="text-[17px] leading-snug tabular">{children}</dd>
    </div>
  );
}
