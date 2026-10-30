// Contract between the ML pipeline (ml/: Kai and our agents) and the UI (web/: head agent).
// The CLI writes ForecastResponse JSON (`python -m ml.forecast --day ... --json`),
// the web app reads it from web/public/forecasts/. Change shapes only together.

export type OD = "25" | "07"; // operating direction: 25 = toward 250°T (west), 07 = toward 070°T (east)

export interface HourForecast {
  time: string; // UTC ISO hour, "2026-10-31T12:00Z"
  local: string; // Europe/Berlin local, "2026-10-31T13:00"
  lead_h: number; // hours after issued_at, 1..48
  wind_dir_deg: number | null; // forecast 10 m wind direction (from); null if calm
  wind_kt: number; // forecast 10 m mean wind
  gust_kt: number; // forecast 10 m gusts
  tailwind_25_kt: number; // tailwind on OD 25 (negative = headwind)
  tailwind_18_kt: number; // tailwind on runway 18 (negative = headwind)
  rule_od: OD; // baseline: official rules (with the 30-min hysteresis) on the forecast wind
  rule_18_usable: boolean;
  p_od25: number; // model probability that OD 25 is in use, 0..1
  od: OD; // model call: 25 if p_od25 >= 0.5
  p_18_usable: number; // model probability that runway 18 is usable for departures, 0..1
  certainty: number; // 0..100, how sure the model is about this hour (both calls combined)
}

export interface NextChange {
  time: string; // UTC ISO, first hour of the new OD
  local: string;
  from: OD;
  to: OD;
  p: number; // model probability of the new OD at that hour
  window_local: [string, string]; // plausible window (earliest, latest) for the change
}

export interface Closure18 {
  start: string; // UTC ISO, first hour runway 18 is likely unusable
  end: string; // UTC ISO, first usable hour after it
  local_start: string;
  local_end: string;
  min_p_usable: number;
}

export interface ForecastResponse {
  issued_at: string; // UTC ISO: only information available at this time was used
  issued_local: string;
  mode: "live" | "hindcast"; // hindcast = a past day forecast with archived weather-model runs
  current_od: OD; // OD at issue time, from the latest observations (METAR + rules)
  nwp: string; // weather-model source, e.g. "Open-Meteo previous runs (best_match)"
  model_version: string;
  rules_version: string; // ml/rules.json version
  hours: HourForecast[]; // 48, lead 1..48
  next_change: NextChange | null;
  closures_18: Closure18[];
  observed?: { time: string; od: OD; r18_usable: boolean }[]; // hindcast only: what the rules say happened
}

export interface SkillAtLead {
  lead_h: 1 | 6 | 24 | 48;
  n: number;
  model_acc: number;
  rule_acc: number; // official rules on the forecast wind, starting from the state at issue time
  persistence_acc: number; // state at issue time carried forward
  model_brier: number;
  rule_brier: number;
  persistence_brier: number;
}

export interface BacktestResult {
  train_period: { start: string; end: string };
  test_period: { start: string; end: string };
  labels: string; // how labels were made, and whether validated against flown ODs
  rules_version: string;
  base_rates: { od25_share: number; changes_per_year: number; r18_closed_share: number };
  od: SkillAtLead[];
  r18: SkillAtLead[];
  drivers: { feature: string; importance: number }[]; // top features, for the model card
}
