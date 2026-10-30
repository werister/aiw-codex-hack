"use client";

import type { ForecastResponse, HourForecast } from "@/lib/forecast-types";
import { cx, dayLabel, hhmm, odBg } from "./ui";

// 48 hourly columns. Rows: OD, runway 18, confidence, wind, and (for past days) what was flown.
export function Timeline({
  f,
  selected,
  onSelect,
  rows = ["od", "r18", "conf", "wind", "observed"],
}: {
  f: ForecastResponse;
  selected: number;
  onSelect: (i: number) => void;
  rows?: ("od" | "r18" | "conf" | "wind" | "observed")[];
}) {
  const H = f.hours;
  const observed = new Map((f.observed ?? []).map((o) => [o.time, o]));
  const changeIdx = f.next_change ? H.findIndex((h) => h.time === f.next_change!.time) : -1;
  const show = (r: string) => rows.includes(r as never) && (r !== "observed" || observed.size > 0);

  return (
    <div className="overflow-x-auto">
      <div className="min-w-[760px]">
        {/* hour axis */}
        <Row label="">
          {H.map((h, i) => {
            const newDay = i === 0 || h.local.slice(0, 10) !== H[i - 1].local.slice(0, 10);
            return (
              <div key={h.time} className="relative h-8 text-[10px] text-muted">
                {newDay && (
                  <span className="absolute -top-0.5 left-0 whitespace-nowrap font-semibold text-ink-2">
                    {dayLabel(h.local)}
                  </span>
                )}
                {i % 3 === 0 && <span className="absolute bottom-0 left-0 tabular">{hhmm(h.local)}</span>}
              </div>
            );
          })}
        </Row>

        {show("od") && (
          <Row label="Direction">
            {H.map((h, i) => (
              <Cell key={h.time} i={i} sel={selected} onSelect={onSelect} change={i === changeIdx}>
                <div
                  className={cx("h-9 w-full rounded-[3px]", odBg(h.od))}
                  style={{ opacity: 0.35 + 0.65 * Math.abs(2 * h.p_od25 - 1) }}
                  title={`${hhmm(h.local)} OD ${h.od} · P(25) ${Math.round(h.p_od25 * 100)}%`}
                />
              </Cell>
            ))}
          </Row>
        )}

        {show("r18") && (
          <Row label="Runway 18">
            {H.map((h, i) => (
              <Cell key={h.time} i={i} sel={selected} onSelect={onSelect} change={i === changeIdx}>
                <div
                  className={cx("h-6 w-full rounded-[3px]", h.p_18_usable >= 0.5 ? "bg-ok" : "bg-bad")}
                  style={{ opacity: 0.3 + 0.7 * Math.abs(2 * h.p_18_usable - 1) }}
                  title={`${hhmm(h.local)} runway 18 usable ${Math.round(h.p_18_usable * 100)}%`}
                />
              </Cell>
            ))}
          </Row>
        )}

        {show("conf") && (
          <Row label="Confidence">
            {H.map((h, i) => (
              <Cell key={h.time} i={i} sel={selected} onSelect={onSelect} change={i === changeIdx}>
                <div className="flex h-7 items-end">
                  <div
                    className={cx("w-full rounded-t-[2px]", h.certainty >= 60 ? "bg-ink-2" : "bg-warn")}
                    style={{ height: `${Math.max(6, h.certainty)}%` }}
                    title={`${h.certainty}% confidence`}
                  />
                </div>
              </Cell>
            ))}
          </Row>
        )}

        {show("wind") && (
          <Row label="Wind (kt)">
            {H.map((h, i) => (
              <Cell key={h.time} i={i} sel={selected} onSelect={onSelect} change={i === changeIdx}>
                <WindGlyph h={h} />
              </Cell>
            ))}
          </Row>
        )}

        {show("observed") && (
          <Row label="Flown">
            {H.map((h, i) => {
              const o = observed.get(h.time);
              return (
                <Cell key={h.time} i={i} sel={selected} onSelect={onSelect} change={i === changeIdx}>
                  {o ? (
                    <div
                      className={cx(
                        "flex h-6 w-full items-center justify-center rounded-[3px] text-[9px] font-bold",
                        odBg(o.od),
                        o.od === h.od ? "text-bg" : "text-bad ring-2 ring-bad ring-inset",
                      )}
                      title={`Flown ${o.od} · forecast ${h.od}`}
                    >
                      {o.od === h.od ? "" : "✕"}
                    </div>
                  ) : (
                    <div className="h-6" />
                  )}
                </Cell>
              );
            })}
          </Row>
        )}

        <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 pl-24 text-[11px] text-muted">
          <Key cls="bg-west" label="25 West" />
          <Key cls="bg-east" label="07 East" />
          <Key cls="bg-ok" label="18 usable" />
          <Key cls="bg-bad" label="18 closed" />
          <span>Paler = less sure</span>
          {changeIdx >= 0 && <span className="text-warn">│ next change</span>}
        </div>
      </div>
    </div>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[96px_1fr] items-center">
      <div className="pr-2 text-[11px] font-medium text-muted">{label}</div>
      <div className="grid grid-cols-[repeat(48,minmax(0,1fr))] gap-px">{children}</div>
    </div>
  );
}

function Cell({
  i,
  sel,
  onSelect,
  change,
  children,
}: {
  i: number;
  sel: number;
  onSelect: (i: number) => void;
  change: boolean;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={() => onSelect(i)}
      className={cx(
        "relative py-0.5 outline-none",
        i === sel && "bg-panel-2",
        change && "before:absolute before:inset-y-0 before:-left-px before:w-0.5 before:bg-warn",
      )}
      aria-label={`Hour ${i + 1}`}
    >
      {children}
    </button>
  );
}

function WindGlyph({ h }: { h: HourForecast }) {
  // Arrow points where the wind blows to (from + 180).
  const rot = h.wind_dir_deg == null ? 0 : h.wind_dir_deg + 180;
  return (
    <div className="flex h-9 flex-col items-center justify-center" title={`${h.wind_dir_deg ?? "VRB"}° ${h.wind_kt} kt, gusts ${h.gust_kt}`}>
      {h.wind_dir_deg != null && (
        <svg viewBox="0 0 10 10" className="size-3 text-ink-2" style={{ transform: `rotate(${rot}deg)` }}>
          <path d="M5 1 L8 7 L5 5.5 L2 7 Z" fill="currentColor" />
        </svg>
      )}
      <span className="text-[9px] tabular text-muted">{Math.round(h.wind_kt)}</span>
    </div>
  );
}

function Key({ cls, label }: { cls: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1">
      <span className={cx("size-2.5 rounded-sm", cls)} />
      {label}
    </span>
  );
}
