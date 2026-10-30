"use client";

import type { ForecastResponse, HourForecast, OD } from "@/lib/forecast-types";
import { forecastCoverage, formatForecastInstant } from "@/lib/forecast-events";
import { RunwayMap } from "./RunwayMap";
import { SceneHero } from "./SceneHero";
import { useTower } from "./ThemeToggle";
import { cx, hhmm, pct } from "./ui";

const WAY: Record<OD, string> = { "25": "west", "07": "east" };
const WD = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

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
          <p className="eyebrow text-muted">Operating direction at issue · {formatForecastInstant(f.issued_at, f.issued_local)}</p>
          <h2
            className={cx(
              "mt-3 font-light leading-[1.02] tracking-[-0.025em]",
              compact ? "text-[44px]" : "text-[44px] sm:text-[64px] xl:text-[80px]",
            )}
          >
            <span className={f.current_od === "25" ? "text-west" : "text-east"}>{WAY[f.current_od]} {f.current_od}</span>
          </h2>

          {hour ? (
            <div className="mt-5 space-y-2">
              <p className="text-[15px] leading-snug text-muted tabular">
                Forecast for {formatForecastInstant(hour.time, hour.local)} · T+{hour.lead_h} h
              </p>
              <p className={cx("font-light leading-tight", compact ? "text-[24px]" : "text-[24px] sm:text-[34px]")}>
                Direction {WAY[hour.od]} ({hour.od})
                <span className="text-muted"> · </span>
                Runway 18 likely {r18Open ? "usable" : "unusable"}
              </p>
              <p className="text-[14px] font-medium tabular">
                P(OD {hour.od} at this hour) · {pct(directionProbability!)}
                <span className="mx-2 text-muted">·</span>
                P(RWY 18 usable at this hour) · {pct(hour.p_18_usable)}
              </p>
            </div>
          ) : (
            <p className="mt-5 text-[15px] text-muted">Hourly forecast unavailable.</p>
          )}

          <div className="mt-6">
            <p className="eyebrow text-muted">Next forecast change</p>
            {nc ? (
              <p className="mt-2 text-[15px] leading-snug">
                {WAY[nc.to]} ({nc.to}) · {formatForecastInstant(nc.time, nc.local)}
                <span className="mx-2 text-muted">·</span>
                P(OD {nc.to} at this hour) {pct(nc.p)}
              </p>
            ) : (
              <p className="mt-2 text-[15px] leading-snug text-muted">
                No change window in this forecast. See hourly changes below.
              </p>
            )}
          </div>

          {f.mode === "hindcast" && (
            <div className="mt-4 flex flex-wrap gap-2.5">
              <Chip tone="outline">Historical forecast</Chip>
            </div>
          )}
        </div>

        <DayBar
          hours={f.hours}
          selectedIndex={selectedIndex}
          selectedHour={hour}
          coverage={coverage.label}
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
        <span className="eyebrow text-ink">Forecast · {coverage}</span>
        <span className="flex items-center gap-4">
          <Dot cls="bg-west" label="west" />
          <Dot cls="bg-east" label="east" />
        </span>
        {selectedHour && (
          <span className="w-full tabular">
            Selected · {formatForecastInstant(selectedHour.time, selectedHour.local)}
          </span>
        )}
      </div>
      <div className="relative mt-3">
        <div className="flex h-9 overflow-hidden rounded-[6px]" role={onSelectHour ? undefined : "img"} aria-label={onSelectHour ? undefined : `Operating direction by hour · ${coverage}`}>
          {hours.map((hour, index) => {
            const segment = <span className={cx("block h-full w-full", hour.od === "25" ? "bg-west" : "bg-east")} />;
            const label = `${formatForecastInstant(hour.time, hour.local)}: OD ${hour.od} ${WAY[hour.od]}; P(OD ${hour.od} at this hour) ${pct(hour.od === "25" ? hour.p_od25 : 1 - hour.p_od25)}; runway 18 ${hour.p_18_usable >= 0.5 ? "likely usable" : "likely unusable"}, P(usable) ${pct(hour.p_18_usable)}`;
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
