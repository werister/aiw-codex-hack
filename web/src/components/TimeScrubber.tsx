"use client";

import type { ForecastResponse, HourForecast } from "@/lib/forecast-types";
import { forecastHourOffset, formatForecastHour, nextDirectionChangeAfter } from "@/lib/forecast-explanation";
import { dayLabel } from "./ui";
import "./TimeScrubber.css";

export function TimeScrubber({
  f,
  selected,
  onSelect,
}: {
  f: ForecastResponse;
  selected: number;
  onSelect: (index: number) => void;
}) {
  const hours = f.hours;
  const lastIndex = Math.max(0, hours.length - 1);
  const activeIndex = hours.length
    ? Math.min(lastIndex, Math.max(0, Number.isFinite(selected) ? Math.trunc(selected) : 0))
    : 0;
  const hour = hours[activeIndex];
  const change = hour ? nextDirectionChangeAfter(f, hour) : null;

  return (
    <section className="forecast-scrubber-root" aria-label="Forecast hour selector">
      {hour ? (
        <>
          <div className="forecast-scrubber-selection">
            <div className="forecast-scrubber-when">
              <span className="forecast-scrubber-date">{fullLocalDate(hour.local)}</span>
              <span className="forecast-scrubber-time">{hour.local.slice(11, 16)}</span>
              <span className="forecast-scrubber-date">Europe/Berlin · {forecastHourOffset(hour)}</span>
            </div>
            <div className="forecast-scrubber-metrics">
              <span className="forecast-scrubber-direction">
                <span className={hour.od === "25" ? "forecast-scrubber-west-dot" : "forecast-scrubber-east-dot"} aria-hidden="true" />
                OD {hour.od} · {hour.od === "25" ? "West" : "East"}
              </span>
              <span className={hour.p_18_usable >= 0.5 ? "forecast-scrubber-usable" : "forecast-scrubber-closed"}>
                <span className="forecast-scrubber-status-dot" aria-hidden="true" />
                18 likely {hour.p_18_usable >= 0.5 ? "usable" : "closed"} · {percent(hour.p_18_usable)} usable
              </span>
              <span className="forecast-scrubber-certainty">Certainty score {Math.round(hour.certainty)}/100</span>
            </div>
          </div>

          {hours.length > 1 ? (
            <div className="forecast-scrubber-controls">
              <button
                type="button"
                className="forecast-scrubber-step-button"
                onClick={() => onSelect(Math.max(0, activeIndex - 1))}
                disabled={activeIndex === 0}
                aria-label="Previous forecast hour"
              >
                <Chevron direction="left" />
              </button>

              <div className="forecast-scrubber-range-column">
                <input
                  className="forecast-scrubber-range"
                  type="range"
                  min={0}
                  max={lastIndex}
                  step={1}
                  value={activeIndex}
                  onChange={(event) => onSelect(Number(event.currentTarget.value))}
                  aria-label="Forecast hour"
                  aria-valuetext={rangeValueText(hour)}
                />
                <div className="forecast-scrubber-range-labels" aria-hidden="true">
                  <span>{dayLabel(hours[0].local)} · {hours[0].local.slice(11, 16)} {forecastHourOffset(hours[0])}</span>
                  <span>{dayLabel(hours[lastIndex].local)} · {hours[lastIndex].local.slice(11, 16)} {forecastHourOffset(hours[lastIndex])}</span>
                </div>
              </div>

              <button
                type="button"
                className="forecast-scrubber-step-button"
                onClick={() => onSelect(Math.min(lastIndex, activeIndex + 1))}
                disabled={activeIndex === lastIndex}
                aria-label="Next forecast hour"
              >
                <Chevron direction="right" />
              </button>

              {change && (
                <button
                  type="button"
                  className="forecast-scrubber-change-button"
                  onClick={() => onSelect(change.index)}
                  aria-label={`Jump to next hourly direction change after the selected hour: ${change.from} to ${change.hour.od}, ${formatForecastHour(change.hour)}.`}
                >
                  <span className="forecast-scrubber-change-full-label">Next change</span>
                  <span className="forecast-scrubber-change-mobile-label">Change</span>
                  <span className="forecast-scrubber-change-time">{change.from} to {change.hour.od} · {dayLabel(change.hour.local)} {change.hour.local.slice(11, 16)} {forecastHourOffset(change.hour)}</span>
                </button>
              )}
            </div>
          ) : (
            <p className="forecast-scrubber-empty">{hours.length ? "Only one forecast hour available" : "No forecast hours available"}</p>
          )}
        </>
      ) : (
        <p className="forecast-scrubber-empty">No forecast hours available</p>
      )}
    </section>
  );
}

function fullLocalDate(local: string) {
  const [year, month, day] = local.slice(0, 10).split("-").map(Number);
  if (!year || !month || !day) return local.slice(0, 10);

  return new Intl.DateTimeFormat("en-GB", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(Date.UTC(year, month - 1, day)));
}

function percent(value: number) {
  return `${Math.round(value * 100)}%`;
}

function rangeValueText(hour: HourForecast) {
  const usability = hour.p_18_usable >= 0.5 ? "likely usable" : "likely closed";
  const direction = hour.od === "25" ? "25 west" : "07 east";
  return `${formatForecastHour(hour)}, direction ${direction}, runway 18 ${usability} with ${percent(hour.p_18_usable)} probability of being usable, certainty score ${Math.round(hour.certainty)} out of 100.`;
}

function Chevron({ direction }: { direction: "left" | "right" }) {
  return (
    <svg viewBox="0 0 8 12" className="forecast-scrubber-chevron" aria-hidden="true">
      <path d={direction === "left" ? "M7 1 2 6l5 5" : "M1 1l5 5-5 5"} />
    </svg>
  );
}
