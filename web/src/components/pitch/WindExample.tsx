"use client";

import { useState } from "react";
import {
  RUNWAY18_DEMO_PRESETS,
  RUNWAY18_RULES,
  RUNWAY18_RULE_SOURCE,
  runway18Demo,
  runway18PreparationReview,
  tailwindComponent,
  type Runway18DemoPreset,
} from "@/lib/runway18-demo";
import { RunwayMap } from "../RunwayMap";
import { Panel, cx } from "../ui";

const OD25_HEADING_DEG = 250;

function componentLabel(value: number) {
  if (Math.abs(value) < 0.05) return "0.0 kt · calm along runway";
  return value > 0
    ? `+${value.toFixed(1)} kt · tailwind`
    : `−${Math.abs(value).toFixed(1)} kt · headwind`;
}

function scenarioTime(hour: number) {
  return `H+${String(hour).padStart(2, "0")}:00`;
}

function scenarioMinute(minute: number) {
  const hours = Math.floor(minute / 60);
  const minutes = minute % 60;
  return `H+${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
}

export function WindExample({ onContinue }: { onContinue?: () => void }) {
  const [preset, setPreset] = useState<Runway18DemoPreset>("tailwind");
  const [selectedLeadHour, setSelectedLeadHour] = useState(0);
  const [preparation, setPreparation] = useState("");
  const scenario = runway18Demo(preset);
  const selectedHour = scenario.hours.find((hour) => hour.leadHour === selectedLeadHour) ?? scenario.hours[0];
  const od25Tailwind = tailwindComponent(selectedHour.windKt, selectedHour.windFromDeg, OD25_HEADING_DEG);
  const interval = scenario.restrictionIntervals[0];
  const restrictedSamples = interval
    ? scenario.hours.filter((hour) => hour.unusableByChallengeRule && hour.leadHour >= interval.startHour && (interval.endHourExclusive === null || hour.leadHour < interval.endHourExclusive))
    : [];
  const lastRestrictedSample = restrictedSamples.at(-1)?.leadHour;
  const parsedPreparation = preparation.trim() === "" ? null : Number(preparation);
  const validPreparation = parsedPreparation === null || (
    Number.isFinite(parsedPreparation) && parsedPreparation >= 0 && parsedPreparation <= 1440
  );
  const review = validPreparation
    ? runway18PreparationReview(scenario.restrictionIntervals, parsedPreparation)
    : { status: "invalid-input" as const };
  const weatherUsable = !selectedHour.unusableByChallengeRule;

  function selectPreset(next: Runway18DemoPreset) {
    setPreset(next);
    setSelectedLeadHour(0);
  }

  return (
    <Panel
      title="Runway 18 · a separate wind restriction"
      aside={<span className="rounded-full border border-ink px-3 py-1 text-[13px] text-ink">Synthetic rule demo</span>}
    >
      <div className="space-y-4">
        <div className="rounded-card border border-line bg-panel-2 p-4 sm:p-5">
          <p className="text-[17px] text-ink">Simulation · six synthetic hourly wind inputs</p>
          <p className="mt-1 text-sm leading-5 text-ink-2">
            Choose a rule scenario and select an hour. This is not an airport status, model probability, observed closure, or evaluation sample.
          </p>
        </div>

        <div role="group" aria-label="Choose a synthetic Runway 18 weather scenario" className="grid gap-2 sm:grid-cols-2">
          <ExampleButton selected={preset === "tailwind"} onClick={() => selectPreset("tailwind")}>
            Northerly tailwind profile
          </ExampleButton>
          <ExampleButton selected={preset === "crosswind"} onClick={() => selectPreset("crosswind")}>
            Gust crosswind profile
          </ExampleButton>
        </div>

        <div className="grid gap-4 lg:grid-cols-[minmax(0,1.15fr)_minmax(18rem,0.85fr)]">
          <div className="min-w-0 space-y-4">
            <div className="overflow-x-auto rounded-lg border border-line bg-panel-2">
              <table className="w-full min-w-[580px] text-left text-xs tabular">
                <caption className="p-3 text-left text-sm font-semibold text-ink">Synthetic six-hour weather sequence · {RUNWAY18_DEMO_PRESETS[preset].label}</caption>
                <thead className="border-y border-line text-muted">
                  <tr><th className="p-2">Scenario time</th><th>Wind</th><th>Tailwind</th><th>Gust crosswind</th><th>Rule result</th></tr>
                </thead>
                <tbody>
                  {scenario.hours.map((hour) => (
                    <tr key={hour.leadHour} className="border-b border-line last:border-0">
                      <td className="p-2">
                        <button
                          type="button"
                          aria-pressed={selectedLeadHour === hour.leadHour}
                          onClick={() => setSelectedLeadHour(hour.leadHour)}
                          className="min-h-9 rounded px-2 text-left font-semibold text-ink underline decoration-line underline-offset-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-west"
                        >
                          {scenarioTime(hour.leadHour)}
                        </button>
                      </td>
                      <td>from {hour.windFromDeg}° · {hour.windKt} kt / {hour.gustKt} kt</td>
                      <td>{hour.tailwindKt.toFixed(1)} kt</td>
                      <td>{hour.gustCrosswindKt.toFixed(1)} kt</td>
                      <td className={hour.unusableByChallengeRule ? "font-semibold text-bad" : "text-ink"}>
                        {hour.unusableByChallengeRule ? "Limit crossed" : "Within limits"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <Metric label="Parallel system · OD 25" value={componentLabel(od25Tailwind)} detail="Illustrative heading 250°" tone="west" />
              <Metric
                label={`Runway 18 · ${scenarioTime(selectedHour.leadHour)}`}
                value={componentLabel(selectedHour.tailwindKt)}
                detail={`${RUNWAY18_RULES.departureTailwindLimitKt} kt tailwind limit · gust crosswind ${selectedHour.gustCrosswindKt.toFixed(1)} / ${RUNWAY18_RULES.crosswindLimitKtIncludingGusts} kt`}
                tone={weatherUsable ? "ok" : "bad"}
              />
            </div>

            <div
              className={cx(
                "rounded-lg border p-4",
                weatherUsable ? "border-line bg-panel-2" : "border-bad/60 bg-bad-soft",
              )}
              aria-live="polite"
            >
              <div className="text-[13px] font-medium text-ink-2">Challenge weather-rule result · Runway 18</div>
              <div className={cx("mt-1 text-2xl font-bold tracking-tight", weatherUsable ? "text-ink" : "text-bad")}>
                {weatherUsable ? "WITHIN WEATHER LIMITS" : "RULE LIMIT CROSSED"}
              </div>
              <p className="mt-1 text-sm leading-5 text-ink-2">
                {selectedHour.reason === "tailwind"
                  ? `${selectedHour.tailwindKt.toFixed(1)} kt tailwind meets or exceeds the ${RUNWAY18_RULES.departureTailwindLimitKt} kt limit; this synthetic hour is weather-unusable by the challenge rule.`
                  : selectedHour.reason === "crosswind"
                    ? `${selectedHour.gustCrosswindKt.toFixed(1)} kt gust crosswind exceeds the ${RUNWAY18_RULES.crosswindLimitKtIncludingGusts} kt limit; this synthetic hour is weather-unusable by the challenge rule.`
                    : `Below the ${RUNWAY18_RULES.departureTailwindLimitKt} kt tailwind and ${RUNWAY18_RULES.crosswindLimitKtIncludingGusts} kt gust-crosswind limits in this synthetic hour.`}
              </p>
              <p className="mt-2 text-xs text-muted">Rule source: {RUNWAY18_RULE_SOURCE}. This calculation does not state whether the airport actually restricted Runway 18.</p>
            </div>

            <details className="rounded-lg border border-line bg-panel-2 p-3 text-xs text-ink-2">
              <summary className="cursor-pointer font-semibold">Formula and threshold</summary>
              <p className="mt-2">Tailwind = mean wind × cos(radians(wind-from − runway heading − 180°)). Gust crosswind = gust × |sin(radians(wind-from − runway heading))|. Runway 18 uses heading 180°; at least 15 kt tailwind or more than 40 kt crosswind including gusts crosses the rule limit.</p>
            </details>
          </div>

          <div className="min-w-0 space-y-4">
            <div className="rounded-lg border border-line bg-panel-2 p-3">
              <h3 className="text-sm font-semibold">Restriction interval in this scenario</h3>
              <p className="mt-2 text-sm text-ink-2">
                {interval
                  ? interval.endHourExclusive === null
                    ? `Rule limit is crossed at hourly samples from ${scenarioTime(interval.startHour)} through ${scenarioTime(lastRestrictedSample ?? interval.startHour)}; no later within-limit sample is shown.`
                    : `Rule limit is crossed at hourly samples from ${scenarioTime(interval.startHour)} through ${scenarioTime(lastRestrictedSample ?? interval.startHour)}. The first following within-limit sample is ${scenarioTime(interval.endHourExclusive)}.`
                  : "No Runway 18 restriction is derived in these six synthetic hours."}
              </p>
              <p className="mt-2 text-xs text-muted">These are hourly synthetic rule samples, not continuous airport-status observations. This interval is derived only from the sequence above.</p>
            </div>

            <div className="rounded-lg border border-line bg-panel-2 p-3">
              <h3 className="text-sm font-semibold">Conditional preparation check</h3>
              <p className="mt-1 text-xs leading-5 text-ink-2">Enter a preparation duration chosen for this demonstration. It assumes no team SOP, and it measures no staffing savings or operational benefit.</p>
              <label htmlFor="runway18-preparation" className="mt-3 flex flex-wrap items-center gap-3 text-sm">
                Preparation time (minutes)
                <input
                  id="runway18-preparation"
                  type="number"
                  min="0"
                  max="1440"
                  step="1"
                  value={preparation}
                  onChange={(event) => setPreparation(event.currentTarget.value)}
                  placeholder="Enter scenario duration"
                  className="w-48 max-w-full rounded-lg border border-line bg-panel px-3 py-2 text-ink"
                />
              </label>
              <p className="mt-3 text-sm text-ink-2" aria-live="polite">
                {review.status === "input-required"
                  ? "Enter 0–1,440 minutes to calculate a scenario review time."
                  : review.status === "invalid-input"
                    ? "Enter a whole preparation duration from 0 to 1,440 minutes."
                    : review.status === "no-restriction"
                      ? "No restriction is derived in this scenario, so no review time is calculated."
                      : review.status === "insufficient-lead"
                        ? `This duration requires review before H+00:00; the scenario offers only ${review.availableLeadMinutes} minutes before the first restriction. No negative time is shown.`
                        : review.preparationMinutes === 0
                          ? `Review at ${scenarioMinute(review.reviewMinute)}, the restriction start; zero minutes remain for preparation.`
                          : review.reviewMinute === 0
                          ? `Conditional review at H+00:00, the first scenario sample. The entered duration uses all ${review.availableLeadMinutes} minutes before the first restricted sample.`
                            : `Conditional review by ${scenarioMinute(review.reviewMinute)} for a restriction first shown at ${scenarioTime(interval!.startHour)}.`}
              </p>
            </div>

            <div className="min-w-0 overflow-hidden rounded-lg border border-line bg-panel-2 p-2 sm:p-3">
              <RunwayMap
                od="25"
                r18Open={weatherUsable}
                windDir={selectedHour.windFromDeg}
                windKt={selectedHour.windKt}
                label={`SIMULATION · synthetic rule hour ${scenarioTime(selectedHour.leadHour)}`}
              />
            </div>
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
      <div className="text-[13px] font-medium text-muted">{label}</div>
      <div className={cx("mt-2 break-words text-lg font-bold tabular", tone === "west" && "text-west", tone === "ok" && "text-ink", tone === "bad" && "text-bad")}>
        {value}
      </div>
      <div className="mt-1 text-xs leading-4 text-ink-2">{detail}</div>
    </div>
  );
}
