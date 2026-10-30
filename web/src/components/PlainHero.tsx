"use client";

import type { ForecastResponse, HourForecast, OD } from "@/lib/forecast-types";
import { RunwayMap } from "./RunwayMap";
import { SceneHero } from "./SceneHero";
import { useTower } from "./ThemeToggle";
import { cx, hhmm, isUnsure, pct } from "./ui";

const WAY: Record<OD, string> = { "25": "west", "07": "east" };
const WD = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

// "Today", "Tomorrow" or the weekday, counted from the day the forecast was made.
function dayWord(local: string, issuedLocal: string) {
  const d = (s: string) => Date.UTC(+s.slice(0, 4), +s.slice(5, 7) - 1, +s.slice(8, 10));
  const diff = Math.round((d(local) - d(issuedLocal)) / 86_400_000);
  if (diff === 0) return "Today";
  if (diff === 1) return "Tomorrow";
  return WD[new Date(d(local)).getUTCDay()];
}

// First screen for anyone: which way planes land now, what changes next, how sure. No codes.
export function PlainHero({ f, compact }: { f: ForecastResponse; compact?: boolean }) {
  const tower = useTower();
  const first = f.hours[0];
  const r18Open = first.p_18_usable >= 0.5;
  const nc = f.next_change;
  const live = f.mode === "live";
  const now = WAY[f.current_od];

  return (
    <section
      className={cx(
        "relative overflow-hidden rounded-card bg-panel-2",
        compact ? "min-h-[560px]" : "min-h-[calc(100svh-96px)] lg:min-h-[640px]",
      )}
      aria-label="Now and next"
    >
      {/* Scene sits right of the words on wide screens, below them on narrow ones. */}
      <div className="absolute inset-x-0 bottom-[150px] top-[38%] md:inset-y-0 md:left-[30%] md:top-0">
        <SceneHero
          od={first.od}
          r18Open={r18Open}
          wind={first.wind_dir_deg == null ? undefined : { dir: first.wind_dir_deg, kt: first.wind_kt }}
          theme={tower ? "tower" : "light"}
          className="absolute inset-0"
          fallback={
            <div className="absolute inset-y-0 right-0 flex w-full items-center opacity-60 md:w-[62%]">
              <RunwayMap
                od={first.od}
                r18Open={r18Open}
                windDir={first.wind_dir_deg}
                windKt={first.wind_kt}
                label={`${hhmm(first.local)}`}
              />
            </div>
          }
        />
      </div>
      {/* Keeps the words readable over the scene. */}
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-panel-2 from-30% to-transparent to-55% md:bg-gradient-to-r md:from-35% md:to-60%" />

      <div className={cx("relative flex h-full flex-col justify-between gap-10 p-6 sm:p-10", compact ? "min-h-[560px]" : "min-h-[inherit]")}>
        <div className="max-w-[760px]">
          <h2
            className={cx(
              "font-light leading-[1.02] tracking-[-0.025em]",
              compact ? "text-[44px]" : "text-[44px] sm:text-[64px] xl:text-[80px]",
            )}
          >
            {live ? "Right now planes land toward the " : `At ${hhmm(f.issued_local)} planes landed toward the `}
            <span className={f.current_od === "25" ? "text-west" : "text-east"}>{now}</span>.
          </h2>
          <p className={cx("mt-6 font-light leading-tight", compact ? "text-[24px]" : "text-[24px] sm:text-[34px]")}>
            {nc ? (
              <>
                {dayWord(nc.local, f.issued_local)} from {hhmm(nc.local)}:{" "}
                <span className={nc.to === "25" ? "text-west" : "text-east"}>{WAY[nc.to]}</span>
                <span className="text-muted"> · </span>
                {pct(nc.p)} sure
              </>
            ) : (
              <>No change expected for the next 2 days.</>
            )}
          </p>
          <div className="mt-8 flex flex-wrap gap-2.5">
            <Chip tone={r18Open ? "plain" : "alarm"}>Runway 18 {r18Open ? "open" : "closed"}</Chip>
            <Chip tone={isUnsure(first) ? "outline" : "plain"}>
              {isUnsure(first) ? "Unsure right now" : `How sure now: ${first.certainty} of 100`}
            </Chip>
            {!live && <Chip tone="outline">Past day, replayed</Chip>}
          </div>
        </div>

        <DayBar hours={f.hours} />
      </div>
    </section>
  );
}

function Chip({ tone, children }: { tone: "plain" | "outline" | "alarm"; children: React.ReactNode }) {
  return (
    <span
      className={cx(
        "inline-flex items-center rounded-full px-4 py-2 text-[15px]",
        tone === "plain" && "bg-bg text-ink",
        tone === "outline" && "border border-ink text-ink",
        tone === "alarm" && "bg-bad text-on-signal",
      )}
    >
      {children}
    </span>
  );
}

// The next 48 hours as one west/east bar, with a "now" marker and plain hour labels.
function DayBar({ hours }: { hours: HourForecast[] }) {
  return (
    <div className="rounded-card bg-bg/90 p-4 backdrop-blur sm:p-5">
      <div className="flex items-center justify-between text-[13px] text-muted">
        <span className="eyebrow text-ink">Next 2 days</span>
        <span className="flex items-center gap-4">
          <Dot cls="bg-west" label="west" />
          <Dot cls="bg-east" label="east" />
          <Dot cls="bg-ink/30" label="pale = unsure" />
        </span>
      </div>
      <div className="relative mt-3">
        <div className="flex h-9 overflow-hidden rounded-[6px]">
          {hours.map((h) => (
            <div
              key={h.time}
              className={cx("h-full flex-1", h.od === "25" ? "bg-west" : "bg-east", isUnsure(h) && "opacity-35")}
              title={`${hhmm(h.local)}: ${WAY[h.od]}${isUnsure(h) ? ", unsure" : ""}`}
            />
          ))}
        </div>
        <div className="absolute -top-1.5 bottom-[-6px] left-0 w-[3px] rounded-full bg-ink" aria-hidden />
      </div>
      <div className="relative mt-2 h-4 text-[12px] text-muted tabular">
        <span className="absolute left-0 font-medium text-ink">now</span>
        {hours.map((h, i) =>
          i > 1 && i < hours.length - 2 && +h.local.slice(11, 13) % 6 === 0 ? (
            <span key={h.time} className="absolute -translate-x-1/2" style={{ left: `${(i / hours.length) * 100}%` }}>
              {h.local.slice(11, 13) === "00" ? WD[new Date(h.local.slice(0, 10) + "T00:00Z").getUTCDay()].slice(0, 3) : hhmm(h.local)}
            </span>
          ) : null,
        )}
      </div>
    </div>
  );
}

function Dot({ cls, label }: { cls: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={cx("size-2.5 rounded-full", cls)} />
      {label}
    </span>
  );
}
