import type { ForecastResponse } from "@/lib/forecast-types";
import { OD_LABEL, cx, dayLabel, hhmm, odBg, pct } from "./ui";

// Tower-staff view: three answers in large type, nothing else.
export function NowPanel({ f, compact }: { f: ForecastResponse; compact?: boolean }) {
  const first = f.hours[0];
  const r18Open = first.p_18_usable >= 0.5;
  const nextClosure = f.closures_18[0];
  const nc = f.next_change;
  const big = compact ? "text-[64px]" : "text-[64px] sm:text-[88px]";
  const value = cx(big, "leading-[0.95] tracking-[-0.03em] tabular");

  return (
    <div className="grid gap-2.5 md:grid-cols-3">
      <Tile label="Operating direction" compact={compact} className={cx(odBg(f.current_od), "text-on-signal")}>
        <div className={value}>
          {f.current_od}{" "}
          <span className="text-[28px] font-light tracking-normal sm:text-[34px]">{OD_LABEL[f.current_od]}</span>
        </div>
        <Sub>
          {first.od === f.current_od ? "Holding" : `Turning to ${first.od}`} · confidence {first.certainty}%
        </Sub>
      </Tile>

      <Tile
        label="Runway 18 departures"
        compact={compact}
        className={r18Open ? "bg-ok-soft text-ink" : "bg-bad text-on-signal"}
      >
        <div className={cx(value, "flex items-center gap-3", r18Open && "text-ok")}>
          <StatusIcon open={r18Open} />
          {r18Open ? "Open" : "Closed"}
        </div>
        <Sub>
          {nextClosure
            ? `${r18Open ? "Closes" : "Closed"} ${dayLabel(nextClosure.local_start)} ${hhmm(nextClosure.local_start)}–${hhmm(nextClosure.local_end)}`
            : `Open for the next 48 h · P(usable) ${pct(first.p_18_usable)}`}
        </Sub>
      </Tile>

      <Tile label="Next direction change" compact={compact} className="bg-panel-2 text-ink">
        {nc ? (
          <>
            <div className={value}>{hhmm(nc.local)}</div>
            <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-2 text-[20px] leading-none">
              <span className={cx("rounded-full px-3 py-1.5 text-[15px] text-on-signal", odBg(nc.to))}>
                to {nc.to} {OD_LABEL[nc.to]}
              </span>
              <span className="tabular">{pct(nc.p)} likely</span>
            </div>
            <Sub>
              {dayLabel(nc.local)} · window {hhmm(nc.window_local[0])}–{hhmm(nc.window_local[1])}
            </Sub>
          </>
        ) : (
          <>
            <div className={cx(value, "font-light")}>None</div>
            <Sub>No change expected in the next 48 h</Sub>
          </>
        )}
      </Tile>
    </div>
  );
}

function Tile({
  label,
  compact,
  className,
  children,
}: {
  label: string;
  compact?: boolean;
  className: string;
  children: React.ReactNode;
}) {
  return (
    <div
      className={cx(
        "flex flex-col justify-between gap-6 rounded-card p-5 transition-colors duration-300 sm:p-6",
        compact ? "min-h-[176px]" : "min-h-[200px] sm:min-h-[240px]",
        className,
      )}
    >
      <div className="eyebrow">{label}</div>
      <div>{children}</div>
    </div>
  );
}

function Sub({ children }: { children: React.ReactNode }) {
  return <div className="mt-3 text-[15px] leading-snug opacity-90 tabular">{children}</div>;
}

// Second cue next to the colour: a tick when open, a bar when closed.
function StatusIcon({ open }: { open: boolean }) {
  return (
    <svg viewBox="0 0 40 40" className="size-[0.62em] shrink-0" fill="none" aria-hidden>
      <circle cx="20" cy="20" r="18" stroke="currentColor" strokeWidth="2.5" />
      {open ? (
        <path d="m12 20.5 5.5 5.5L28.5 14" stroke="currentColor" strokeWidth="2.5" />
      ) : (
        <path d="M11 20h18" stroke="currentColor" strokeWidth="3.5" />
      )}
    </svg>
  );
}
