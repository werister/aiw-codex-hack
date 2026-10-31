"use client";

import type { ForecastResponse, HourForecast, OD } from "@/lib/forecast-types";
import { forecastCoverage, formatForecastInstant } from "@/lib/forecast-events";
import { RunwayMap } from "./RunwayMap";
import { SceneHero } from "./SceneHero";
import { useTower } from "./ThemeToggle";
import { cx, dayLabel, hhmm, isUnsure, pct, unsureReason } from "./ui";

const WAY: Record<OD, string> = { "25": "west", "07": "east" };
const WD = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
// Plain local time for the first screen, e.g. "Thu 29 Oct 07:00".
const when = (local: string) => `${dayLabel(local)} ${hhmm(local)}`;

export function PlainHero({
  f,
  compact,
  selected,
  onSelectHour,
}: {
  f: ForecastResponse;
  compact?: boolean;
  selected?: number;
  onSelectHour?: (index: number) => void;
}) {
  const tower = useTower();
  const selectedIndex = f.hours.length === 0 ? -1 : Math.max(0, Math.min(selected ?? 0, f.hours.length - 1));
  const hour = selectedIndex >= 0 ? f.hours[selectedIndex] : undefined;
  const r18Open = hour ? hour.p_18_usable >= 0.5 : false;
  const nc = f.next_change;
  const directionProbability = hour && (hour.od === "25" ? hour.p_od25 : 1 - hour.p_od25);
  const coverage = forecastCoverage(f.hours);
  // Plain bar title; the exact coverage text stays for incomplete files.
  const barTitle = coverage.count === 48 && !coverage.hasTimestampGaps ? "48-hour outlook" : coverage.label;
  const wind = hour?.wind_dir_deg == null ? undefined : { dir: hour.wind_dir_deg, kt: hour.wind_kt };

  return (
    <section
      className={cx(
        "relative flex flex-col gap-10 overflow-hidden rounded-card bg-panel-2 p-6 sm:p-10 md:block md:p-0",
        compact ? "min-h-[900px] md:min-h-[640px]" : "min-h-[960px] md:min-h-[680px]",
      )}
      aria-label="Forecast summary and hour selection"
    >
      {/* Scene sits right of the words on wide screens, below them on narrow ones. */}
      {hour && (
        <div className="relative order-2 h-[280px] md:absolute md:inset-x-0 md:bottom-[210px] md:left-[46%] md:top-0 md:h-auto">
          <SceneHero
            od={hour.od}
            r18Open={r18Open}
            wind={wind}
            forecastHour={hour}
            theme={tower ? "tower" : "light"}
            className="h-full w-full"
            fallback={
              <div className="absolute inset-y-0 right-0 flex w-full items-center opacity-60 md:w-[62%]">
                <RunwayMap
                  od={hour.od}
                  r18Open={r18Open}
                  windDir={hour.wind_dir_deg}
                  windKt={hour.wind_kt}
                  label={`Forecast · ${formatForecastInstant(hour.time, hour.local)}`}
                />
              </div>
            }
          />
        </div>
      )}

      <div className={cx("pointer-events-none contents md:relative md:flex md:h-full md:flex-col md:justify-between md:gap-10 md:p-10", "min-h-[inherit]")}>
        <div className="pointer-events-auto order-1 max-w-[760px] md:max-w-[44%]">
          <p className="text-[17px] text-ink">
            Frankfurt Airport <span className="text-muted">· forecast issued {when(f.issued_local)}</span>
          </p>
          <h2
            className={cx(
              "mt-4 font-light leading-[1.04] tracking-[-0.025em]",
              compact ? "text-[40px]" : "text-[40px] sm:text-[56px] xl:text-[68px]",
            )}
          >
            {"Issue-time direction: "}
            <span className={f.current_od === "25" ? "text-west" : "text-east"}>{WAY[f.current_od]}</span>.
          </h2>

          {hour ? (
            <div className="mt-6 space-y-3">
              <p className={cx("font-light leading-tight", compact ? "text-[24px]" : "text-[24px] sm:text-[32px]")}>
                {when(hour.local)}:{" "}
                <span className={hour.od === "25" ? "text-west" : "text-east"}>{WAY[hour.od]}</span>, {pct(directionProbability!)} support
              </p>
              <div className="flex flex-wrap gap-2.5">
                <Chip tone={r18Open ? "plain" : "alarm"}>Runway 18 {r18Open ? "likely usable" : "likely restricted"}</Chip>
                {isUnsure(hour) && <Chip tone="outline">Unsure: {unsureReason(hour)}</Chip>}
              </div>
            </div>
          ) : (
            <p className="mt-5 text-[15px] text-muted">Hourly forecast unavailable.</p>
          )}

          <p className="mt-6 text-[20px] leading-snug">
            {nc ? (
              <>
                Next change: <span className={nc.to === "25" ? "text-west" : "text-east"}>{WAY[nc.to]}</span> from{" "}
                {when(nc.local)}, {pct(nc.p)} direction support
              </>
            ) : (
              <span className="text-muted">No change expected in this forecast.</span>
            )}
          </p>

          {f.mode === "hindcast" && (
            <div className="mt-4 flex flex-wrap gap-2.5">
              <Chip tone="outline">Past day, replayed</Chip>
            </div>
          )}
        </div>

        <DayBar
          hours={f.hours}
          selectedIndex={selectedIndex}
          selectedHour={hour}
          coverage={barTitle}
          onSelectHour={onSelectHour}
        />
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

function DayBar({
  hours,
  selectedIndex,
  selectedHour,
  coverage,
  onSelectHour,
}: {
  hours: HourForecast[];
  selectedIndex: number;
  selectedHour?: HourForecast;
  coverage: string;
  onSelectHour?: (index: number) => void;
}) {
  return (
    <div className="pointer-events-auto order-3 rounded-card bg-bg/90 p-4 backdrop-blur sm:p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-2 text-[13px] text-muted">
        <span className="text-[15px] text-ink">{coverage}</span>
        <span className="flex items-center gap-4">
          <Dot cls="bg-west" label="west" />
          <Dot cls="bg-east" label="east" />
        </span>
        {selectedHour && (
          <span className="w-full tabular">
            Showing {when(selectedHour.local)}
          </span>
        )}
      </div>
      <div className="relative mt-3">
        <div className="flex h-9 overflow-hidden rounded-[6px]" role={onSelectHour ? undefined : "img"} aria-label={onSelectHour ? undefined : `Landing direction by hour · ${coverage}`}>
          {hours.map((hour, index) => {
            const segment = <span className={cx("block h-full w-full", hour.od === "25" ? "bg-west" : "bg-east")} />;
            const label = `${when(hour.local)}: ${WAY[hour.od]}, ${pct(hour.od === "25" ? hour.p_od25 : 1 - hour.p_od25)} sure; runway 18 ${hour.p_18_usable >= 0.5 ? "open" : "closed"}${isUnsure(hour) ? "; unsure" : ""}`;
            return onSelectHour ? (
              <button
                key={hour.time}
                type="button"
                className={cx("h-full min-w-0 flex-1 p-0", index === selectedIndex && "z-10 outline outline-2 outline-offset-[-2px] outline-ink")}
                title={label}
                aria-label={`Select forecast hour ${label}`}
                aria-pressed={index === selectedIndex}
                onClick={() => onSelectHour(index)}
              >
                {segment}
              </button>
            ) : (
              <span key={hour.time} className="h-full min-w-0 flex-1" title={label} aria-hidden="true">{segment}</span>
            );
          })}
        </div>
        {selectedIndex >= 0 && hours.length > 0 && (
          <div
            className="pointer-events-none absolute -top-1.5 bottom-[-6px] w-[3px] -translate-x-1/2 rounded-full bg-ink"
            style={{ left: `${((selectedIndex + 0.5) / hours.length) * 100}%` }}
            aria-hidden
          />
        )}
      </div>
      <div className="relative mt-2 h-4 text-[12px] text-muted tabular" aria-hidden="true">
        {hours.map((hour, index) =>
          index > 1 && index < hours.length - 2 && Number(hour.local.slice(11, 13)) % 6 === 0 ? (
            <span key={hour.time} className={cx("absolute -translate-x-1/2", Number(hour.local.slice(11, 13)) % 12 !== 0 && "hidden sm:block")} style={{ left: `${(index / hours.length) * 100}%` }}>
              {hour.local.slice(11, 13) === "00" ? WD[new Date(`${hour.local.slice(0, 10)}T00:00Z`).getUTCDay()].slice(0, 3) : hhmm(hour.local)}
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
