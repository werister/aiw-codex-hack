import type { ReactNode } from "react";
import type { ForecastResponse, HourForecast } from "@/lib/forecast-types";
import { Provenance } from "./Provenance";
import { UNCERTAIN_BELOW, planFrom, planWindow } from "./Recommendation";
import { Arrow, OD_LABEL, cx, dayLabel, hhmm, isUnsure, odText, pct, unsureReason } from "./ui";

// Above the fold: what is flown now, what changes next, what to prepare for. One glance.
export function Hero({
  f,
  scene,
  compact,
  onEvidence,
}: {
  f: ForecastResponse;
  scene: ReactNode;
  compact?: boolean;
  onEvidence?: () => void;
}) {
  const first = f.hours[0];
  const r18Open = first.p_18_usable >= 0.5;
  const nc = f.next_change;
  const changeHour = nc ? f.hours.find((h) => h.time === nc.time) : undefined;
  const plan = planFrom(f);
  const uncertain = plan.p < UNCERTAIN_BELOW;

  return (
    <section
      className={cx(
        "grid items-center gap-6",
        compact ? "md:grid-cols-[1fr_1fr]" : "py-4 lg:min-h-[520px] lg:grid-cols-[1fr_1.1fr] lg:gap-10",
      )}
      aria-label="Now and next"
    >
      <div className="min-w-0">
        <Provenance f={f} compact />

        <p className="eyebrow mt-6 text-muted">Now</p>
        <h2
          className={cx(
            "mt-2 font-light leading-[1.02] tracking-[-0.02em]",
            compact ? "text-[40px]" : "text-[44px] sm:text-[60px] xl:text-[68px]",
          )}
        >
          <span className={cx(odText(f.current_od), !compact && "block")}>
            {OD_LABEL[f.current_od]} {f.current_od}
          </span>
          {compact && <span className="text-muted"> · </span>}
          <span className="whitespace-nowrap">
            Runway 18 <span className={r18Open ? "" : "text-bad"}>{r18Open ? "open" : "closed"}</span>
          </span>
        </h2>
        <Unsure h={first} />

        <p className="eyebrow mt-7 text-muted">Next</p>
        <p className={cx("mt-2 font-light leading-tight", compact ? "text-[24px]" : "text-[26px] sm:text-[32px]")}>
          {nc ? (
            <>
              <span className={odText(nc.to)}>
                {OD_LABEL[nc.to]} {nc.to}
              </span>{" "}
              from {hhmm(nc.local)} <span className="text-muted">·</span> {pct(nc.p)} likely
            </>
          ) : (
            "No change in the next 48 h"
          )}
        </p>
        {nc && (
          <p className="mt-1 text-[15px] text-muted tabular">
            {dayLabel(nc.local)} · window {hhmm(nc.window_local[0])}–{hhmm(nc.window_local[1])}
          </p>
        )}
        {changeHour && <Unsure h={changeHour} />}

        <div className={cx("flex flex-wrap items-center gap-x-4 gap-y-3 border-t border-line pt-5", compact ? "mt-5" : "mt-8")}>
          <span className="eyebrow inline-flex items-center gap-2 rounded-full border border-ink px-3 py-1.5">
            <span className={cx("size-2 rounded-full", uncertain ? "border border-ink" : "bg-ink")} />
            {uncertain ? "Uncertain" : "Firm"}
          </span>
          <span className="text-[17px]">
            {plan.kind === "change" && `Prepare for ${OD_LABEL[plan.to]} ${plan.to} · ${planWindow(plan)}`}
            {plan.kind === "closure" && `Prepare for runway 18 closure · ${planWindow(plan)}`}
            {plan.kind === "hold" && "Nothing to prepare for in the next 48 h"}
          </span>
        </div>
        <p className="mt-2 text-[13px] text-muted">Planning aid. The supervisor decides. Traffic demand data unavailable.</p>

        {onEvidence && (
          <div className="mt-6 flex flex-wrap gap-2">
            <button type="button" onClick={onEvidence} className="pill-btn bg-accent text-accent-ink [--btn-ring:var(--accent)]">
              Why? See evidence <Arrow />
            </button>
            <a href="#timeline" className="pill-btn border border-line text-ink [--btn-ring:var(--line)]">
              Next 48 h
            </a>
          </div>
        )}
      </div>

      <div className="min-w-0 overflow-hidden rounded-card bg-panel-2 p-2">
        {scene}
      </div>
    </section>
  );
}

// Explicit flag when the call behind an hour is under 60%, with the reason from the file.
function Unsure({ h }: { h: HourForecast }) {
  if (!isUnsure(h)) return null;
  return (
    <p className="mt-3 inline-flex items-center gap-2 text-[15px]">
      <span className="eyebrow rounded-full bg-ink px-2.5 py-1 text-bg">Unsure</span>
      {hhmm(h.local)}: {unsureReason(h)}
    </p>
  );
}
