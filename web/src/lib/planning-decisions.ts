import type { ForecastResponse } from "./forecast-types";

export const PLANNING_ROLES = ["ground_operations", "forecast_review"] as const;
export type PlanningRole = (typeof PLANNING_ROLES)[number];
export interface PlanningCandidate {
  id: string;
  kind: "direction" | "runway18" | "disagreement" | "provenance" | "monitor";
  action: "prepare" | "review" | "monitor";
  title: string;
  detail: string;
  time: string;
  hour_indices: number[];
}
export interface PlanningReview {
  schema_version: 1;
  policy_version: "planning-priorities-v1";
  generated_at: string;
  forecast_basis: ReturnType<typeof planningBasis>;
  candidates: PlanningCandidate[];
  selections: Record<PlanningRole, { candidate_id: string; selection_confidence?: number }>;
  status: "decisions" | "fallback";
  status_reason: string | null;
}

// Matches the producer's pre-outcome basis. A later truth overlay is never part of a review.
export function planningBasis(f: ForecastResponse) {
  return {
    issued_at: f.issued_at,
    current_od: f.current_od,
    model_version: f.model_version,
    rules_version: f.rules_version,
    nwp: f.nwp,
    hours: f.hours.map(({ time, lead_h, od, p_od25, p_18_usable, rule_od, rule_18_usable }) =>
      ({ time, lead_h, od, p_od25, p_18_usable, rule_od, rule_18_usable })),
    next_change: f.next_change ?? null,
    closures_18: f.closures_18,
    evidence: f.evidence ?? null,
  };
}

function stable(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.entries(value).sort(([a], [b]) => a.localeCompare(b))
      .map(([key, item]) => `${JSON.stringify(key)}:${stable(item)}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

export function planningReviewFor(value: unknown, forecast: ForecastResponse): PlanningReview | null {
  if (!value || typeof value !== "object") return null;
  const r = value as PlanningReview;
  if (r.schema_version !== 1 || r.policy_version !== "planning-priorities-v1" ||
      !["decisions", "fallback"].includes(r.status) || !Number.isFinite(Date.parse(r.generated_at)) ||
      stable(r.forecast_basis) !== stable(planningBasis(forecast)) ||
      !Array.isArray(r.candidates) || !r.candidates.length || r.candidates.length > 200) return null;
  const ids = new Set<string>();
  for (const c of r.candidates) {
    if (!c || typeof c.id !== "string" || ids.has(c.id) ||
        !["direction", "runway18", "disagreement", "provenance", "monitor"].includes(c.kind) ||
        !["prepare", "review", "monitor"].includes(c.action) ||
        typeof c.title !== "string" || c.title.length > 200 || typeof c.detail !== "string" || c.detail.length > 1000 ||
        !Array.isArray(c.hour_indices) || !c.hour_indices.length ||
        c.hour_indices.some((i, n) => !Number.isInteger(i) || i < 0 || i >= forecast.hours.length ||
          (n > 0 && i <= c.hour_indices[n - 1])) ||
        forecast.hours[c.hour_indices[0]].time !== c.time) return null;
    ids.add(c.id);
  }
  for (const role of PLANNING_ROLES) {
    const selection = r.selections?.[role];
    if (!selection || !ids.has(selection.candidate_id)) return null;
    if (r.status === "decisions" && (typeof selection.selection_confidence !== "number" ||
        !Number.isFinite(selection.selection_confidence) || selection.selection_confidence < 0 ||
        selection.selection_confidence > 1)) return null;
  }
  return r;
}

export function planningAssetPath(file: string | null) {
  return file && /^(?:latest|sample|\d{4}-\d{2}-\d{2})\.json$/.test(file) ? `/decisions/${file}` : null;
}

export function preparationTime(eventTime: string, minutes: string, issueTime: string) {
  if (!/^\d{1,4}$/.test(minutes) || Number(minutes) > 1440) return null;
  const time = Date.parse(eventTime) - Number(minutes) * 60_000;
  if (!Number.isFinite(time)) return null;
  return { time: new Date(time).toISOString(), enoughLead: time > Date.parse(issueTime) };
}
