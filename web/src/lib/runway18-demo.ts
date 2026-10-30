export const RUNWAY18_RULE_SOURCE = "ml/rules.json · fraalliance-brief-2026-10-30";

export const RUNWAY18_RULES = {
  runwayHeadingDeg: 180,
  departureTailwindLimitKt: 15,
  crosswindLimitKtIncludingGusts: 40,
} as const;

export const RUNWAY18_DEMO_PRESETS = {
  tailwind: {
    label: "Tailwind limit",
    hours: [
      { leadHour: 0, windFromDeg: 330, windKt: 16, gustKt: 18 },
      { leadHour: 1, windFromDeg: 330, windKt: 17.5, gustKt: 19 },
      { leadHour: 2, windFromDeg: 330, windKt: 20, gustKt: 20 },
      { leadHour: 3, windFromDeg: 330, windKt: 19, gustKt: 20 },
      { leadHour: 4, windFromDeg: 330, windKt: 17, gustKt: 18 },
      { leadHour: 5, windFromDeg: 330, windKt: 15, gustKt: 18 },
    ],
  },
  crosswind: {
    label: "Gust crosswind limit",
    hours: [
      { leadHour: 0, windFromDeg: 270, windKt: 35, gustKt: 39 },
      { leadHour: 1, windFromDeg: 270, windKt: 35, gustKt: 40 },
      { leadHour: 2, windFromDeg: 270, windKt: 35, gustKt: 41 },
      { leadHour: 3, windFromDeg: 270, windKt: 35, gustKt: 42 },
      { leadHour: 4, windFromDeg: 270, windKt: 35, gustKt: 40 },
      { leadHour: 5, windFromDeg: 270, windKt: 35, gustKt: 39 },
    ],
  },
} as const;

export type Runway18DemoPreset = keyof typeof RUNWAY18_DEMO_PRESETS;

export interface Runway18RestrictionInterval {
  startHour: number;
  endHourExclusive: number | null;
}

export type Runway18PreparationReview =
  | { status: "input-required" }
  | { status: "invalid-input" }
  | { status: "no-restriction" }
  | { status: "insufficient-lead"; availableLeadMinutes: number }
  | { status: "review-time"; availableLeadMinutes: number; reviewMinute: number; preparationMinutes: number };

export interface Runway18WeatherInput {
  windFromDeg: number;
  windKt: number;
  gustKt: number;
}

export interface Runway18WeatherResult extends Runway18WeatherInput {
  tailwindKt: number;
  gustCrosswindKt: number;
  unusableByChallengeRule: boolean;
  reason: "tailwind" | "crosswind" | null;
}

export function tailwindComponent(speedKt: number, windFromDeg: number, runwayHeadingDeg: number) {
  const radians = ((windFromDeg - runwayHeadingDeg - 180) * Math.PI) / 180;
  return speedKt * Math.cos(radians);
}

export function crosswindComponent(speedKt: number, windFromDeg: number, runwayHeadingDeg: number) {
  const radians = ((windFromDeg - runwayHeadingDeg) * Math.PI) / 180;
  return Math.abs(speedKt * Math.sin(radians));
}

export function evaluateRunway18Weather(input: Runway18WeatherInput): Runway18WeatherResult {
  const tailwindKt = tailwindComponent(input.windKt, input.windFromDeg, RUNWAY18_RULES.runwayHeadingDeg);
  const gustCrosswindKt = crosswindComponent(input.gustKt, input.windFromDeg, RUNWAY18_RULES.runwayHeadingDeg);
  const reason = tailwindKt >= RUNWAY18_RULES.departureTailwindLimitKt
    ? "tailwind"
    : gustCrosswindKt > RUNWAY18_RULES.crosswindLimitKtIncludingGusts
      ? "crosswind"
      : null;

  return {
    ...input,
    tailwindKt,
    gustCrosswindKt,
    unusableByChallengeRule: reason !== null,
    reason,
  };
}

/** A deterministic six-hour teaching case, kept outside ForecastResponse and all scoring inputs. */
export function runway18Demo(preset: Runway18DemoPreset) {
  const selected = RUNWAY18_DEMO_PRESETS[preset];
  const hours = selected.hours.map((hour) => ({
    ...hour,
    ...evaluateRunway18Weather(hour),
  }));
  const restrictionIntervals: Runway18RestrictionInterval[] = [];
  let startHour: number | null = null;
  for (const hour of hours) {
    if (hour.unusableByChallengeRule && startHour === null) startHour = hour.leadHour;
    if (!hour.unusableByChallengeRule && startHour !== null) {
      restrictionIntervals.push({ startHour, endHourExclusive: hour.leadHour });
      startHour = null;
    }
  }
  if (startHour !== null) restrictionIntervals.push({ startHour, endHourExclusive: null });

  return {
    preset,
    label: selected.label,
    hours,
    restrictionIntervals,
    evidence: {
      kind: "synthetic-weather-rule-scenario" as const,
      includedInHistoricalEvidence: false as const,
      includedInAggregateQuality: false as const,
    },
  };
}

/**
 * Convert a presenter-entered duration into a scenario-relative review time.
 * Negative times are never returned; long preparation durations are unavailable.
 */
export function runway18PreparationReview(
  intervals: Runway18RestrictionInterval[],
  preparationMinutes: number | null,
): Runway18PreparationReview {
  if (preparationMinutes === null) return { status: "input-required" };
  if (!Number.isInteger(preparationMinutes) || preparationMinutes < 0 || preparationMinutes > 1440) {
    return { status: "invalid-input" };
  }
  const firstRestriction = intervals[0];
  if (!firstRestriction) return { status: "no-restriction" };

  const availableLeadMinutes = firstRestriction.startHour * 60;
  const reviewMinute = availableLeadMinutes - preparationMinutes;
  if (reviewMinute < 0) return { status: "insufficient-lead", availableLeadMinutes };
  return {
    status: "review-time",
    availableLeadMinutes,
    reviewMinute,
    preparationMinutes,
  };
}
