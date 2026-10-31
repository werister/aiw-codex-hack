"use client";

import type { ForecastResponse, HourForecast } from "@/lib/forecast-types";
import { cx, dayLabel, hhmm, isUnsure, odBg, unsureReason } from "./ui";

// 48 hourly columns. Rows: OD, runway 18, certainty, wind, and (for past days) the recorded direction.
export function Timeline({
  f,
  selected,
  onSelect,
  rows = ["od", "unsure", "r18", "conf", "wind", "observed"],
}: {
  f: ForecastResponse;
  selected: number;
  onSelect: (i: number) => void;
  rows?: ("od" | "unsure" | "r18" | "conf" | "wind" | "observed")[];
}) {
  const H = f.hours;
  const observed = new Map((f.observed ?? []).map((o) => [o.time, o]));
  const changeIdx = f.next_change ? H.findIndex((h) => h.time === f.next_change!.time) : -1;
  const anyUnsure = H.some(isUnsure);
  const show = (r: string) =>
    rows.includes(r as never) && (r !== "observed" || observed.size > 0) && (r !== "unsure" || anyUnsure);

  return (
    <>
    <div className="overflow-x-auto">
      <div className="min-w-[760px]">
        {/* hour axis */}
        <Row label="">
          {H.map((h, i) => {
            const newDay = i === 0 || h.local.slice(0, 10) !== H[i - 1].local.slice(0, 10);
            return (
              <div key={h.time} className="relative h-9 text-[11px] text-muted">
                {newDay && (
                  <span className={cx("absolute -top-0.5 whitespace-nowrap font-medium text-ink", i >= H.length - 3 ? "right-0" : "left-0")}>
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
              <Cell key={h.time} i={i} h={h} sel={selected} onSelect={onSelect} change={i === changeIdx}>
                <div
                  className={cx("relative h-10 w-full rounded-[2px]", odBg(h.od))}
                  style={{ opacity: 0.35 + 0.65 * Math.abs(2 * h.p_od25 - 1) }}
                  title={`${hhmm(h.local)} OD ${h.od} · P(25) ${Math.round(h.p_od25 * 100)}%`}
                >
                  {(i === 0 || H[i - 1].od !== h.od) && (
                    <span className="absolute left-1 top-1 text-[11px] font-medium leading-none text-on-signal">{h.od}</span>
                  )}
                </div>
              </Cell>
            ))}
          </Row>
        )}

        {show("unsure") && (
          <Row label="Unsure">
            {H.map((h, i) => (
              <Cell key={h.time} i={i} h={h} sel={selected} onSelect={onSelect} change={i === changeIdx}>
                <div className="flex h-5 items-center justify-center">
                  {isUnsure(h) && (
                    <span
                      className="flex size-4 items-center justify-center rounded-full bg-ink text-[10px] font-medium text-bg"
                      title={`Unsure: ${unsureReason(h)}`}
                    >
                      ?
                    </span>
                  )}
                </div>
              </Cell>
            ))}
          </Row>
        )}

        {show("r18") && (
          <Row label="Runway 18">
            {H.map((h, i) => (
              <Cell key={h.time} i={i} h={h} sel={selected} onSelect={onSelect} change={i === changeIdx}>
                <div
                  className={cx("h-6 w-full rounded-[2px]", h.p_18_usable >= 0.5 ? "bg-ok" : "stripes bg-bad")}
                  style={{ opacity: 0.3 + 0.7 * Math.abs(2 * h.p_18_usable - 1) }}
                  title={`${hhmm(h.local)} runway 18 usable ${Math.round(h.p_18_usable * 100)}%`}
                />
              </Cell>
            ))}
          </Row>
        )}

        {show("conf") && (
          <Row label="Certainty">
            {H.map((h, i) => (
              <Cell key={h.time} i={i} h={h} sel={selected} onSelect={onSelect} change={i === changeIdx}>
                <div className="flex h-7 items-end">
                  <div
                    className={cx("w-full rounded-t-[2px]", h.certainty >= 60 ? "bg-muted" : "border border-b-0 border-muted")}
                    style={{ height: `${Math.max(6, h.certainty)}%` }}
                    title={`Certainty score ${h.certainty}/100`}
                  />
                </div>
              </Cell>
            ))}
          </Row>
        )}

        {show("wind") && (
          <Row label="Wind (kt)">
            {H.map((h, i) => (
              <Cell key={h.time} i={i} h={h} sel={selected} onSelect={onSelect} change={i === changeIdx}>
                <WindGlyph h={h} />
              </Cell>
            ))}
          </Row>
        )}

        {show("observed") && (
          <Row label="Recorded">
            {H.map((h, i) => {
              const o = observed.get(h.time);
              return (
                <Cell key={h.time} i={i} h={h} sel={selected} onSelect={onSelect} change={i === changeIdx}>
                  {o ? (
                    <div
                      className={cx(
                        "flex h-6 w-full items-center justify-center rounded-[2px] text-[10px] font-medium text-on-signal",
                        odBg(o.od),
                        o.od !== h.od && "ring-2 ring-ink ring-inset",
                      )}
                      title={`Recorded ${o.od} · forecast ${h.od}`}
                    >
                      {o.od === h.od ? "" : "✕"}
                    </div>
                  ) : (
                    <div className="h-6 rounded-[2px] border border-dashed border-muted/60" title="No record for this hour" />
                  )}
                </Cell>
              );
            })}
          </Row>
        )}

        <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2 pl-24 text-[13px] text-ink-2">
          <Key cls="bg-west" label="25 West" />
          <Key cls="bg-east" label="07 East" />
          <Key cls="bg-ok" label="18 open" />
          <Key cls="stripes bg-bad" label="18 closed" />
          <span className="text-muted">Paler = less sure</span>
          {anyUnsure && rows.includes("unsure") && (
            <span className="inline-flex items-center gap-1.5">
              <span className="flex size-3.5 items-center justify-center rounded-full bg-ink text-[9px] text-bg">?</span>
              unsure, under 60%
            </span>
          )}
          {show("observed") && (
            <>
              <Key cls="border border-dashed border-muted" label="no record" />
              <span className="inline-flex items-center gap-1.5">
                <span className="flex size-3.5 items-center justify-center rounded-[2px] text-[9px] ring-2 ring-ink ring-inset">✕</span>
                forecast differs from record
              </span>
            </>
          )}
          {changeIdx >= 0 && (
            <span className="inline-flex items-center gap-1.5">
              <span className="h-3.5 w-0.5 bg-ink" />
              next change
            </span>
          )}
        </div>
      </div>
    </div>
    {show("observed") && (
      <p className="mt-3 max-w-[110ch] text-[13px] leading-snug text-muted">
        Recorded: the DFLD.de log, a public proxy, not a certified record. It leaves out change hours. Runway 18 has
        no public record; it is inferred from METAR and the rules.
      </p>
    )}
    </>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[96px_1fr] items-center">
      <div className="pr-2 text-[13px] text-ink-2">{label}</div>
      <div className="grid grid-cols-[repeat(48,minmax(0,1fr))] gap-[2px]">{children}</div>
    </div>
  );
}

function Cell({
  i,
  h,
  sel,
  onSelect,
  change,
  children,
}: {
  i: number;
  h: HourForecast;
  sel: number;
  onSelect: (i: number) => void;
  change: boolean;
  children: React.ReactNode;
}) {
  const label = `${dayLabel(h.local)} ${hhmm(h.local)}: OD ${h.od}, runway 18 ${h.p_18_usable >= 0.5 ? "usable" : "closed"}, probability of usability ${Math.round(h.p_18_usable * 100)}%, certainty ${h.certainty}/100${isUnsure(h) ? `, unsure: ${unsureReason(h)}` : ""}`;
  return (
    <button
      type="button"
      tabIndex={i === sel ? 0 : -1}
      onClick={() => onSelect(i)}
      onKeyDown={(event) => {
        const cells = event.currentTarget.parentElement?.querySelectorAll<HTMLButtonElement>("button");
        if (!cells?.length) return;
        const next = event.key === "ArrowRight" ? Math.min(i + 1, cells.length - 1)
          : event.key === "ArrowLeft" ? Math.max(0, i - 1)
          : event.key === "Home" ? 0
          : event.key === "End" ? cells.length - 1 : null;
        if (next === null) return;
        event.preventDefault();
        onSelect(next);
        cells[next].focus();
      }}
      className={cx(
        "relative cursor-pointer py-1 transition-colors duration-150 hover:bg-select/60 focus-visible:z-10 focus-visible:outline-2 focus-visible:outline-ink motion-reduce:transition-none",
        i === sel && "bg-select",
        change && "before:absolute before:inset-y-0 before:-left-[2px] before:w-0.5 before:bg-ink",
      )}
      aria-label={label}
      aria-pressed={i === sel}
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
        <svg viewBox="0 0 10 10" className="size-3 text-ink" style={{ transform: `rotate(${rot}deg)` }}>
          <path d="M5 1 L8 7 L5 5.5 L2 7 Z" fill="currentColor" />
        </svg>
      )}
      <span className="text-[10px] tabular text-muted">{Math.round(h.wind_kt)}</span>
    </div>
  );
}

function Key({ cls, label }: { cls: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={cx("size-2.5 rounded-full", cls)} />
      {label}
    </span>
  );
}
