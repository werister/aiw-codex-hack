import type { ForecastResponse } from "@/lib/forecast-types";
import { OD_LABEL, cx, dayLabel, hhmm, odText, pct } from "./ui";

// Tower-staff view: three answers in large type, nothing else.
export function NowPanel({ f, compact }: { f: ForecastResponse; compact?: boolean }) {
  const first = f.hours[0];
  const r18Open = first.p_18_usable >= 0.5;
  const nextClosure = f.closures_18[0];
  const nc = f.next_change;
  const big = compact ? "text-4xl" : "text-5xl sm:text-6xl";

  return (
    <div className="grid gap-3 md:grid-cols-3">
      <Tile label="Operating direction">
        <div className={cx(big, "font-bold tracking-tight tabular", odText(f.current_od))}>
          {f.current_od} <span className="text-2xl font-semibold sm:text-3xl">{OD_LABEL[f.current_od]}</span>
        </div>
        <div className="mt-1 text-sm text-ink-2">
          {first.od === f.current_od ? "Holding" : `Turning to ${first.od}`} · confidence {first.certainty}%
        </div>
      </Tile>

      <Tile label="Runway 18 departures" tone={r18Open ? "ok" : "bad"}>
        <div className={cx(big, "font-bold tracking-tight", r18Open ? "text-ok" : "text-bad")}>
          {r18Open ? "OPEN" : "CLOSED"}
        </div>
        <div className="mt-1 text-sm text-ink-2">
          {nextClosure
            ? `${r18Open ? "Closes" : "Closed"} ${dayLabel(nextClosure.local_start)} ${hhmm(nextClosure.local_start)}–${hhmm(nextClosure.local_end)}`
            : `Open for the next 48 h · P(usable) ${pct(first.p_18_usable)}`}
        </div>
      </Tile>

      <Tile label="Next direction change" tone={nc ? "warn" : undefined}>
        {nc ? (
          <>
            <div className={cx(big, "font-bold tracking-tight tabular")}>
              <span className={odText(nc.to)}>{nc.to}</span>{" "}
              <span className="text-ink">{hhmm(nc.local)}</span>
            </div>
            <div className="mt-1 text-sm text-ink-2">
              {dayLabel(nc.local)} · window {hhmm(nc.window_local[0])}–{hhmm(nc.window_local[1])} · {pct(nc.p)} likely
            </div>
          </>
        ) : (
          <>
            <div className={cx(big, "font-bold tracking-tight text-ink-2")}>None</div>
            <div className="mt-1 text-sm text-ink-2">No change expected in the next 48 h</div>
          </>
        )}
      </Tile>
    </div>
  );
}

function Tile({
  label,
  tone,
  children,
}: {
  label: string;
  tone?: "ok" | "bad" | "warn";
  children: React.ReactNode;
}) {
  return (
    <div
      className={cx(
        "rounded-xl border bg-panel p-4",
        tone === "ok" && "border-ok/40",
        tone === "bad" && "border-bad/60 bg-bad-soft",
        tone === "warn" && "border-warn/50",
        !tone && "border-line",
      )}
    >
      <div className="text-xs font-semibold uppercase tracking-wider text-muted">{label}</div>
      <div className="mt-2">{children}</div>
    </div>
  );
}
