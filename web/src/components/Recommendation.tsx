import type { ForecastResponse, OD } from "@/lib/forecast-types";
import { Arrow, OD_LABEL, cx, dayLabel, hhmm, odBg, pct } from "./ui";

// Planning policy v1: one suggestion from the forecast fields, no new data.
export const UNCERTAIN_BELOW = 0.6;
export const PLAN_POLICY =
  "Policy v1: the earliest forecast change of operating direction or runway 18 closure in the next 48 h. Flagged uncertain when its probability is below 60%, or, with no change, when any hour's call is below 60%.";

export type Plan =
  | { kind: "change"; time: string; to: OD; local: string; window: [string, string]; p: number }
  | { kind: "closure"; time: string; start: string; end: string; openEnded: boolean; p: number }
  | { kind: "hold"; time: string; od: OD; r18Open: boolean; minCertainty: number };

export function planFrom(f: ForecastResponse): Plan {
  const nc = f.next_change;
  const cl = f.closures_18[0];
  // UTC ISO strings sort as text.
  if (cl && (!nc || cl.start < nc.time)) {
    // Still closed at the last hour: the reopening is beyond the forecast.
    const openEnded = f.closures_18.length === 1 && f.hours[f.hours.length - 1].p_18_usable < 0.5;
    return { kind: "closure", time: cl.start, start: cl.local_start, end: cl.local_end, openEnded, p: 1 - cl.min_p_usable };
  }
  if (nc) return { kind: "change", time: nc.time, to: nc.to, local: nc.local, window: nc.window_local, p: nc.p };
  return {
    kind: "hold",
    time: f.hours[0].time,
    od: f.current_od,
    r18Open: f.hours[0].p_18_usable >= 0.5,
    minCertainty: Math.min(...f.hours.map((h) => h.certainty)),
  };
}

export function planWindow(plan: Plan) {
  if (plan.kind === "change") return `${dayLabel(plan.window[0])} ${hhmm(plan.window[0])}–${hhmm(plan.window[1])}`;
  if (plan.kind === "closure")
    return plan.openEnded
      ? `${dayLabel(plan.start)} from ${hhmm(plan.start)}, reopening unknown`
      : `${dayLabel(plan.start)} ${hhmm(plan.start)}–${hhmm(plan.end)}`;
  return "Next 48 h";
}

export function planHeadline(plan: Plan) {
  if (plan.kind === "change") return `Suggest preparing for a switch to ${plan.to} ${OD_LABEL[plan.to]}`;
  if (plan.kind === "closure") return "Suggest preparing for runway 18 to close for departures";
  return `No change forecast: ${plan.od} ${OD_LABEL[plan.od]} through the next 48 h`;
}

// Leads the page: what to prepare for, where, when, how likely, and from which issue.
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
  // Certainty score 20/100 is a 60% call (score = 100 × |2p − 1|).
  const uncertain = plan.kind === "hold" ? plan.minCertainty < 20 : plan.p < UNCERTAIN_BELOW;

  return (
    <section className={cx("rounded-card bg-select p-5 text-ink", !compact && "sm:p-6")} aria-label="Planning recommendation">
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <h2 className="eyebrow">Planning recommendation</h2>
        <span className="eyebrow inline-flex items-center gap-2 rounded-full border border-ink px-3 py-1.5">
          <span className={cx("size-2 rounded-full", uncertain ? "border border-ink" : "bg-ink")} />
          {uncertain ? "Uncertain · review at next issue" : "Firm"}
        </span>
      </div>

      <p
        className={cx(
          "font-light leading-[1.15] tracking-[-0.01em]",
          compact ? "mt-2 text-[26px]" : "mt-4 text-[28px] sm:text-[40px]",
        )}
      >
        {plan.kind === "change" && (
          <>
            Suggest preparing for a switch to <Chip od={plan.to} />
          </>
        )}
        {plan.kind === "closure" && <>Suggest preparing for runway&nbsp;18 to close for departures</>}
        {plan.kind === "hold" && (
          <>
            No change forecast: <Chip od={plan.od} /> and runway&nbsp;18 {plan.r18Open ? "open" : "closed"} through the next 48&nbsp;h
          </>
        )}
      </p>

      <dl className={cx("grid gap-x-6 gap-y-4", compact ? "mt-3 grid-cols-4" : "mt-5 grid-cols-2 lg:grid-cols-5")}>
        <Fact k="Window">{planWindow(plan)}</Fact>
        <Fact k={probLabel(plan)}>{plan.kind === "hold" ? `${plan.minCertainty}/100` : pct(plan.p)}</Fact>
        <Fact k="Issued">
          {dayLabel(f.issued_local)} {hhmm(f.issued_local)}
        </Fact>
        <Fact k="Traffic in window">
          <span className="inline-flex items-center gap-2">
            <span className="h-3 w-5 rounded-[2px] border border-dashed border-muted" aria-hidden />
            Demand data unavailable
          </span>
        </Fact>
        {!compact && (
          <div className="col-span-2 flex items-end lg:col-span-1 lg:justify-end">
            {onShowEvidence && (
              <button
                type="button"
                onClick={onShowEvidence}
                className="pill-btn bg-accent text-accent-ink [--btn-ring:var(--accent)]"
              >
                Show evidence <Arrow />
              </button>
            )}
          </div>
        )}
      </dl>

      <p className={cx("text-[13px] leading-snug text-ink-2", compact ? "mt-3" : "mt-5")}>
        A planning aid, not an instruction: the shift supervisor decides.
        {!compact &&
          ` ${PLAN_POLICY} No Frankfurt flight-demand feed is connected, so exposed flights are unknown, not zero.`}
      </p>
    </section>
  );
}

// Name the event the number belongs to.
export function probLabel(plan: Plan) {
  if (plan.kind === "change") return `P(${plan.to} ${OD_LABEL[plan.to]} at ${hhmm(plan.local)})`;
  if (plan.kind === "closure") return "P(runway 18 unusable), worst hour";
  return "Lowest certainty score";
}

function Chip({ od }: { od: OD }) {
  return (
    <span className={cx("inline-block whitespace-nowrap rounded-full px-[0.4em] text-on-signal", odBg(od))}>
      {od} {OD_LABEL[od]}
    </span>
  );
}

function Fact({ k, children }: { k: string; children: React.ReactNode }) {
  return (
    <div>
      <dt className="mb-1 text-[12px] text-muted">{k}</dt>
      <dd className="text-[17px] leading-snug tabular">{children}</dd>
    </div>
  );
}
