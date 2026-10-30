"use client";

import { useEffect, useState } from "react";
import type { ForecastResponse } from "@/lib/forecast-types";
import { planningAssetPath, planningReviewFor, preparationTime, type PlanningRole } from "@/lib/planning-decisions";
import { Panel } from "./ui";

const local = (time: string) => new Intl.DateTimeFormat("en-GB", {
  timeZone: "Europe/Berlin", day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit", timeZoneName: "short",
}).format(new Date(time));

export function PlanningPriorities({ f, file, onSelectHour }: {
  f: ForecastResponse; file: string | null; onSelectHour: (index: number) => void;
}) {
  // Remount on a changed forecast, even when the filename or issuance is reused.
  return <PrioritiesSession key={JSON.stringify([file, f])} f={f} file={file} onSelectHour={onSelectHour} />;
}

function PrioritiesSession({ f, file, onSelectHour }: {
  f: ForecastResponse; file: string | null; onSelectHour: (index: number) => void;
}) {
  const [role, setRole] = useState<PlanningRole>("ground_operations");
  const [result, setResult] = useState<{ data: unknown; failed: boolean } | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [minutes, setMinutes] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    const path = planningAssetPath(file);
    if (!path) return;
    fetch(path, { cache: "no-store", signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error("No saved planning review");
        const data: unknown = await response.json();
        if (!controller.signal.aborted) setResult({ data, failed: false });
      })
      .catch(() => { if (!controller.signal.aborted) setResult({ data: null, failed: true }); });
    return () => controller.abort();
  }, [file, attempt]);

  const review = result && !result.failed ? planningReviewFor(result.data, f) : null;
  const missing = Boolean(result && !review) || !planningAssetPath(file);
  const selection = review?.selections[role];
  const focus = review?.candidates.find((candidate) => candidate.id === selection?.candidate_id);
  const h = focus ? f.hours[focus.hour_indices[0]] : undefined;
  const prep = focus?.action === "prepare" ? preparationTime(focus.time, minutes, f.issued_at) : null;

  return (
    <Panel title="Planning priorities">
      <p className="text-[15px] text-ink-2">Choose a role to review its priorities for this forecast.</p>
      <div className="mt-4 flex flex-wrap gap-2" role="group" aria-label="Planning perspective">
        {([["ground_operations", "Ground operations"], ["forecast_review", "Forecast review"]] as const).map(([value, label]) => (
          <button key={value} type="button" aria-pressed={role === value} onClick={() => { setRole(value); setMinutes(""); }}
            className={`pill-btn min-h-11 border border-line ${role === value ? "bg-select text-ink" : "bg-panel text-muted"}`}>{label}</button>
        ))}
      </div>
      {!review && <div className="mt-4 text-[15px] text-muted" role="status">
        {missing ? "No matching planning review is available. Use the forecast events and source details below." : "Loading the saved planning review…"}
        {missing && planningAssetPath(file) && <button type="button" className="ml-3 min-h-11 underline" onClick={() => { setResult(null); setAttempt((n) => n + 1); }}>Retry review</button>}
      </div>}
      {review && focus && h && <div className="mt-4 space-y-4" aria-live="polite">
        <div className="rounded-card border border-line bg-panel-2 p-4 sm:p-5">
          <div className="flex flex-wrap items-center justify-between gap-2 text-[12px] uppercase tracking-wide text-muted">
            <span>{focus.action === "prepare" ? "Preparation" : focus.action === "review" ? "Review" : "Monitor"}</span>
            <span>{review.status === "decisions" ? "Saved Decisions review" : review.status_reason === "single_candidate" ? "One forecast issue" : "Rule-based fallback"}</span>
          </div>
          <h3 className="mt-2 text-[24px] font-light leading-tight text-ink">{focus.title}</h3>
          <p className="mt-2 max-w-3xl text-[15px] leading-relaxed text-ink-2">{focus.detail}</p>
          <p className="mt-3 text-[13px] tabular text-muted">{local(focus.time)} · +{h.lead_h} h · {focus.hour_indices.length} referenced forecast {focus.hour_indices.length === 1 ? "hour" : "hours"}</p>
          <dl className="mt-4 grid gap-3 text-[15px] sm:grid-cols-2">
            <div><dt className="text-[12px] text-muted">At the first referenced hour</dt><dd>Model OD {h.od} · rule baseline OD {h.rule_od}</dd></div>
            <div><dt className="text-[12px] text-muted">Runway 18 · weather-derived</dt><dd>{Math.round(h.p_18_usable * 100)}% probability of usability</dd></div>
          </dl>
          <button type="button" onClick={() => onSelectHour(focus.hour_indices[0])} className="pill-btn mt-4 min-h-11 bg-accent text-accent-ink">View hour</button>
        </div>
        {focus.action === "prepare" && <div className="text-[15px]">
          <label className="flex flex-wrap items-center gap-3">Your preparation time (minutes)
            <input type="number" min="0" max="1440" step="1" value={minutes} onChange={(event) => setMinutes(event.target.value)}
              placeholder="Enter your team's lead time" className="min-h-11 w-64 max-w-full rounded-lg border border-line bg-panel px-3 text-ink" />
          </label>
          <p className="mt-2 text-muted">{prep ? prep.enoughLead ? `Scenario start: ${local(prep.time)}.` : "This duration would require starting at or before forecast issue time." : "Enter 0–1,440 minutes to calculate a start time."} Calculated from your duration and the forecast; no operational deadline is set.</p>
        </div>}
        <details className="text-[13px] text-muted">
          <summary className="min-h-11 cursor-pointer py-3">Other issues and review source</summary>
          <ul className="space-y-2">{review.candidates.filter((candidate) => candidate.id !== focus.id).map((candidate) => (
            <li key={candidate.id}><button type="button" onClick={() => onSelectHour(candidate.hour_indices[0])} className="min-h-11 text-left underline">{candidate.title} · {local(candidate.time)}</button></li>
          ))}</ul>
          <p className="mt-3">Review created {local(review.generated_at)} from the forecast issued {local(f.issued_at)}. Policy {review.policy_version}.</p>
          <p className="mt-2">Priorities are selected from forecast-derived issues. Flight demand and staffing data are unavailable. {f.mode === "hindcast" ? "This review was created later from the saved forecast." : "The shift lead decides which actions to take."}</p>
        </details>
      </div>}
    </Panel>
  );
}
