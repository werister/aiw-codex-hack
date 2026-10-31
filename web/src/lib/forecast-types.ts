// Contract between the forecast pipeline (ml/) and the dashboard (web/).
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
  inputs?: HourInputs; // evidence: the values this hour's probability was computed from (absent in older files)
}

// Per-hour evidence, written by ml/predict.py. Missing values are null, never filled from another source.
export interface HourInputs {
  nwp_offset_days: number;
  wind_kt_metar_scaled: number;
  ens_tailwind_25_mean: number | null;
  ens_tailwind_25_std: number | null;
  ens_tailwind_18_mean: number | null;
  ens_dir_spread: number | null;
  ens_votes_25: number | null;
  rule_od25_ens: 0 | 1;
  dp_ns_hpa: number | null;
  dp_ew_hpa: number | null;
  blend_key: string; // e.g. "6:night"
  blend_weight: number;
  p_od25_raw: number;
  p_18_usable_raw?: number | null;
  r18_blend_weight?: number | null;
}

// Run-level evidence: which artifact and inputs produced this file.
export interface ForecastEvidence {
  run_id: string; // 12 hex of sha256(issued_at + artifact sha + input values)
  model_artifact: { version: string; file: string; sha256: string; trained_through: string };
  feature_set: string;
  rules_version: string;
  publication_lag_h: number;
  issue_inputs: {
    metar_time: string;
    metar_wind_dir_deg: number | null;
    metar_wind_kt: number;
    metar_gust_kt: number;
    od_at_issue: OD;
    od_source: string;
    hours_since_change: number | null;
  };
  sources: { name: string; issued_at?: string; retrieved_at?: string; available_at: string; missing?: boolean }[];
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
  observed?: { time: string; od: OD; r18_usable: boolean | null }[]; // hindcast OD; null R18 label if weather unavailable
  evidence?: ForecastEvidence; // absent in files written before evidence capture
}

export interface SkillAtLead {
  model_acc_ci_7d?: [number, number] | null;
  rule_acc_ci_7d?: [number, number] | null;
  persistence_acc_ci_7d?: [number, number] | null;
  lead_h: 1 | 6 | 24 | 48;
  n: number;
  model_acc: number;
  rule_acc: number; // official rules on the forecast wind, starting from the state at issue time
  persistence_acc: number; // state at issue time carried forward
  model_brier: number;
  rule_brier: number;
  persistence_brier: number;
  model_change_acc?: number; // accuracy on the hours where the OD changed within the lead window
  rule_change_acc?: number;
  persistence_change_acc?: number;
  change_n?: number;
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

// web/public/data/quality.json, written by ml/quality.py (schema documented in ml/README.md).
// Only the fields the UI reads are typed here.
export interface ReliabilityBin {
  lower: number;
  upper: number;
  n: number;
  mean_predicted: number | null;
  observed_frequency: number | null;
}

export interface QualityResult {
  schema_version: number;
  evaluation: string; // "expanding monthly walk-forward"
  r18_label_type: string; // "inferred"
  folds: { month: string; train_n: number; test_n: number }[];
  in_sample: { od: SkillAtLead[]; r18: SkillAtLead[] };
  out_of_sample: { od: SkillAtLead[]; r18: SkillAtLead[] };
  reliability: { od: ReliabilityBin[]; r18?: ReliabilityBin[] };
  next_change: {
    within_1h: number | null; within_3h: number | null; false_alarm_rate: number | null;
    n_actual_change_windows: number; n_no_change_windows?: number; excluded_incomplete_windows?: number;
  };
  od_change_events?: {
    n_actual_events: number; n_matched_events: number; event_recall: number | null;
    n_false_alarm_clusters: number; false_alarms_per_exposure_day: number | null;
    median_warning_lead_h: number | null; tolerance_h: number;
  };
  r18_events?: {
    horizon_h: number; n_issues: number; n_positive_issue_windows: number | null; excluded_issues: number;
    model: { hits: number; misses: number; false_alarms: number; recall: number | null };
  }[];
  rule_label_comparison: { n: number; agreement: number };
  data_sources: { name: string; url: string; file?: string }[];
  limitations: string[];
}
