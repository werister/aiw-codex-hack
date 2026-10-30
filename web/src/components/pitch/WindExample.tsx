"use client";

import { useState } from "react";
import { RunwayMap } from "../RunwayMap";
import { Panel, cx } from "../ui";

// HACK: Synthetic pitch-demo inputs keep this illustration self-contained for static-host builds.
const WIND_SPEED_KT = 20;
const WIND_GUST_KT = 20;
const WIND_MIN_DEG = 250;
const WIND_MAX_DEG = 330;

// HACK: Demo constants mirror the rule fields used here from ml/rules.json.
const ILLUSTRATION_RULES = {
  version: "fraalliance-brief-2026-10-30",
  runway_heading_deg: { "25": 250, "18": 180 },
  departure_tailwind_limit_kt: 15,
  crosswind_limit_kt_incl_gusts: 40,
} as const;

function radians(degrees: number) {
  return (degrees * Math.PI) / 180;
}

function tailwind(speedKt: number, windFromDeg: number, runwayHeadingDeg: number) {
  return speedKt * Math.cos(radians(windFromDeg - runwayHeadingDeg - 180));
}

function crosswind(speedKt: number, windFromDeg: number, runwayHeadingDeg: number) {
  return Math.abs(speedKt * Math.sin(radians(windFromDeg - runwayHeadingDeg)));
}

function componentLabel(value: number) {
  if (Math.abs(value) < 0.05) return "0.0 kt · calm along runway";
  return value > 0
    ? `+${value.toFixed(1)} kt · tailwind`
    : `−${Math.abs(value).toFixed(1)} kt · headwind`;
}

export function WindExample({ onContinue }: { onContinue?: () => void }) {
  const [windFromDeg, setWindFromDeg] = useState(WIND_MIN_DEG);
  const heading25 = ILLUSTRATION_RULES.runway_heading_deg["25"];
  const heading18 = ILLUSTRATION_RULES.runway_heading_deg["18"];
  const od25Tailwind = tailwind(WIND_SPEED_KT, windFromDeg, heading25);
  const r18Tailwind = tailwind(WIND_SPEED_KT, windFromDeg, heading18);
  const r18CrosswindGust = crosswind(WIND_GUST_KT, windFromDeg, heading18);
  const r18ClosedByTailwind = r18Tailwind >= ILLUSTRATION_RULES.departure_tailwind_limit_kt;
  const r18ClosedByCrosswind = r18CrosswindGust > ILLUSTRATION_RULES.crosswind_limit_kt_incl_gusts;
  const r18WeatherUsable = !r18ClosedByTailwind && !r18ClosedByCrosswind;

  return (
    <Panel
      title="Runway 18 is a separate wind decision"
      aside={<span className="rounded-full border border-warn/40 bg-panel-2 px-2.5 py-1 text-[11px] font-semibold text-warn">Wind example</span>}
    >
      <div className="space-y-4">
        <div className="rounded-lg border border-warn/40 bg-panel-2 p-3 sm:p-4">
          <p className="text-sm font-bold text-warn">Rule illustration · not a model forecast</p>
          <p className="mt-1 text-sm leading-5 text-ink-2">
            Hold wind speed and gusts at 20 kt. Slide wind-from direction from 250° to 330° to see Runway 18 cross its departure limit while OD 25 stays headwind.
          </p>
        </div>

        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(18rem,0.9fr)]">
          <div className="min-w-0 space-y-4">
            <div className="rounded-lg border border-line bg-panel-2 p-3 sm:p-4">
              <div className="flex flex-wrap items-end justify-between gap-x-3 gap-y-1">
                <label htmlFor="wind-example-direction" className="text-xs font-semibold uppercase tracking-wider text-muted">
                  Wind from
                </label>
                <div className="tabular text-2xl font-bold tracking-tight text-ink" aria-live="polite">
                  {windFromDeg}° <span className="text-sm font-medium text-ink-2">· 20 kt · gust 20 kt</span>
                </div>
              </div>
              <input
                id="wind-example-direction"
                type="range"
                min={WIND_MIN_DEG}
                max={WIND_MAX_DEG}
                step={1}
                value={windFromDeg}
                onChange={(event) => setWindFromDeg(Number(event.currentTarget.value))}
                aria-label="Wind-from direction"
                aria-valuetext={`Wind from ${windFromDeg} degrees, 20 knots with 20 knot gusts`}
                className="mt-3 h-8 w-full cursor-pointer accent-west focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-west focus-visible:ring-offset-2 focus-visible:ring-offset-panel-2"
              />
              <div className="mt-1 flex justify-between text-xs tabular text-muted">
                <span>250°</span>
                <span>330°</span>
              </div>
              <div role="group" aria-label="Choose a wind example" className="mt-3 grid grid-cols-2 gap-2">
                <ExampleButton selected={windFromDeg === WIND_MIN_DEG} onClick={() => setWindFromDeg(WIND_MIN_DEG)}>
                  A · 250°
                </ExampleButton>
                <ExampleButton selected={windFromDeg === WIND_MAX_DEG} onClick={() => setWindFromDeg(WIND_MAX_DEG)}>
                  B · 330°
                </ExampleButton>
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <Metric label="Parallel system · OD 25" value={componentLabel(od25Tailwind)} detail="Runway heading 250°" tone="west" />
              <Metric
                label="Runway 18 · departures"
                value={componentLabel(r18Tailwind)}
                detail={`${ILLUSTRATION_RULES.departure_tailwind_limit_kt} kt tailwind limit · gust crosswind ${r18CrosswindGust.toFixed(1)} / ${ILLUSTRATION_RULES.crosswind_limit_kt_incl_gusts} kt`}
                tone={r18WeatherUsable ? "ok" : "bad"}
              />
            </div>

            <div
              className={cx(
                "rounded-lg border p-4",
                r18WeatherUsable ? "border-ok/50 bg-ok-soft" : "border-bad/60 bg-bad-soft",
              )}
              aria-live="polite"
            >
              <div className="text-xs font-semibold uppercase tracking-wider text-ink-2">Runway 18 · weather-rule result</div>
              <div className={cx("mt-1 text-3xl font-bold tracking-tight", r18WeatherUsable ? "text-ok" : "text-bad")}>
                {r18WeatherUsable ? "WEATHER-USABLE" : "WEATHER-UNUSABLE"}
              </div>
              <p className="mt-1 text-sm leading-5 text-ink-2">
                {r18ClosedByTailwind
                  ? `${r18Tailwind.toFixed(1)} kt tailwind meets or exceeds the ${ILLUSTRATION_RULES.departure_tailwind_limit_kt} kt limit.`
                  : r18ClosedByCrosswind
                    ? `${r18CrosswindGust.toFixed(1)} kt gust crosswind exceeds the ${ILLUSTRATION_RULES.crosswind_limit_kt_incl_gusts} kt limit.`
                    : `Below the ${ILLUSTRATION_RULES.departure_tailwind_limit_kt} kt tailwind and ${ILLUSTRATION_RULES.crosswind_limit_kt_incl_gusts} kt gust-crosswind limits.`}
              </p>
            </div>
          </div>

          <div className="min-w-0 overflow-hidden rounded-lg border border-line bg-panel-2 p-2 sm:p-3">
            <RunwayMap
              od="25"
              r18Open={r18WeatherUsable}
              windDir={windFromDeg}
              windKt={WIND_SPEED_KT}
              label={`Rule example · synthetic wind from ${windFromDeg}°`}
            />
          </div>
        </div>

        {onContinue && (
          <div className="flex justify-end border-t border-line pt-4">
            <button
              type="button"
              onClick={onContinue}
              className="min-h-11 rounded-lg bg-west px-4 py-2 text-sm font-semibold text-bg transition hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-west focus-visible:ring-offset-2 focus-visible:ring-offset-panel"
            >
              Continue
            </button>
          </div>
        )}
      </div>
    </Panel>
  );
}

function ExampleButton({
  selected,
  onClick,
  children,
}: {
  selected: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      aria-pressed={selected}
      onClick={onClick}
      className={cx(
        "min-h-11 rounded-lg border px-3 py-2 text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-west focus-visible:ring-offset-2 focus-visible:ring-offset-panel-2",
        selected ? "border-west bg-west-soft text-ink" : "border-line bg-panel text-ink-2 hover:border-west/60 hover:text-ink",
      )}
    >
      {children}
    </button>
  );
}

function Metric({
  label,
  value,
  detail,
  tone,
}: {
  label: string;
  value: string;
  detail: string;
  tone: "west" | "ok" | "bad";
}) {
  return (
    <div className="min-w-0 rounded-lg border border-line bg-panel p-3">
      <div className="text-xs font-semibold uppercase tracking-wider text-muted">{label}</div>
      <div className={cx("mt-2 break-words text-lg font-bold tabular", tone === "west" && "text-west", tone === "ok" && "text-ok", tone === "bad" && "text-bad")}>
        {value}
      </div>
      <div className="mt-1 text-xs leading-4 text-ink-2">{detail}</div>
    </div>
  );
}
