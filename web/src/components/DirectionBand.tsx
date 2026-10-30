import type { ForecastResponse } from "@/lib/forecast-types";
import { forecastHourOffset } from "@/lib/forecast-explanation";
import { cx, dayLabel, hhmm, OD_LABEL, odSoft, odText, pct } from "./ui";

export function DirectionBand({ f, compact }: { f: ForecastResponse; compact?: boolean }) {
  const first = f.hours[0];
  const issue = { time: f.issued_at, local: f.issued_local };
  const ruleDifferences = first ? [
    first.od !== first.rule_od && "direction",
    (first.p_18_usable >= 0.5) !== first.rule_18_usable && "runway 18",
  ].filter(Boolean) : [];

  return (
    <div className={cx("mt-6 rounded-card px-4 py-4 text-ink sm:px-5", odSoft(f.current_od))}>
      <div className="flex flex-wrap items-center justify-between gap-x-5 gap-y-2">
        <h2 className={cx("flex items-center gap-3 font-light leading-none tracking-[-0.02em]", compact ? "text-[36px]" : "text-[44px] sm:text-[52px]")}>
          <svg
            viewBox="0 0 48 24"
            fill="none"
            aria-hidden="true"
            className={cx("h-6 w-12 shrink-0", odText(f.current_od), f.current_od === "25" && "rotate-180")}
          >
            <path d="M2 12h42M33 2l11 10-11 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <span>{f.current_od} {OD_LABEL[f.current_od]}</span>
        </h2>
        <p className="text-[12px] leading-snug tabular">
          Direction at issue<br />
          {dayLabel(issue.local)} · {hhmm(issue.local)} {forecastHourOffset(issue)}
        </p>
      </div>

      {first && (
        <div className="mt-4 flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 border-t border-current/15 pt-3">
          <p className="text-[15px] font-medium">
            Runway 18 likely {first.p_18_usable >= 0.5 ? "usable" : "unusable"}
          </p>
          <p className="text-[12px] tabular">P(usable) {pct(first.p_18_usable)}</p>
          <p className="w-full text-[12px] leading-snug tabular">
            Forecast for {dayLabel(first.local)} · {hhmm(first.local)} {forecastHourOffset(first)} · Europe/Berlin
          </p>
          <p className="mt-1 w-full text-[13px] leading-snug">
            {ruleDifferences.length
              ? `At this forecast hour, model and rule baseline differ on ${ruleDifferences.join(" and ")}.`
              : "At this forecast hour, model and rule baseline agree on both calls."}
          </p>
        </div>
      )}
    </div>
  );
}
