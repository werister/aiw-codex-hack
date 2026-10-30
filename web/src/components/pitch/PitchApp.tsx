"use client";

import Link from "next/link";
import { BrandLogo } from "../BrandLogo";
import { useEffect, useState } from "react";
import type { ForecastResponse, QualityResult } from "@/lib/forecast-types";
import {
  firstRecordedOpposite,
  formatPitchTimeWithOffset,
  planningEvent,
  preparationTimingStatus,
  scoreReplay,
  type PreparationTimingStatus,
} from "@/lib/pitch-replay";
import { Timeline } from "../Timeline";
import { Panel, cx } from "../ui";

const STEPS = ["Historical forecast", "Evaluation"];
const BUTTON = "rounded-full border border-line px-5 py-2.5 text-[15px] transition-colors duration-300 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-west disabled:opacity-40";

// Each requested URL lives in a keyed component, so a new case starts with no old result.
function useArtifact<T>(url: string) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    fetch(url, { signal: controller.signal, cache: "no-store" })
      .then((r) => { if (!r.ok) throw new Error("Unavailable artifact"); return r.json(); })
      .then((value: T) => { if (!controller.signal.aborted) setData(value); })
      .catch(() => { if (!controller.signal.aborted) setError(true); });
    return () => controller.abort();
  }, [url]);
  return { data, error };
}

export function PitchApp() {
  const [step, setStep] = useState(0);
  return (
    <main className="mx-auto w-full max-w-[1200px] space-y-6 px-4 py-6 sm:px-8">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
            <BrandLogo />
            <span className="text-[15px] text-muted">Frankfurt Airport</span>
          </div>
          <h1 className="mt-6 text-[36px] font-light leading-[1.05] tracking-[-0.02em] sm:text-[56px]">Runway forecast for Frankfurt</h1>
        </div>
        <Link href="/" className={BUTTON}>Open cockpit</Link>
      </header>
      <nav aria-label="Presentation steps" className="grid gap-2 sm:grid-cols-2">
        {STEPS.map((label, i) => (
          <button key={label} onClick={() => setStep(i)} aria-current={step === i ? "step" : undefined}
            className={cx(BUTTON, "text-left", step === i ? "border-accent bg-accent text-accent-ink" : "bg-panel text-ink-2")}>
            <span className="mr-2 text-muted">0{i + 1}</span>{label}
          </button>
        ))}
      </nav>
      {step === 0 && <ReplayPicker onContinue={() => setStep(1)} />}
      {step === 1 && <PitchQuality />}
      <footer className="border-t border-line pt-4 text-xs leading-relaxed text-muted">
        For ground-handling planning only. Runway clearance remains an operational decision. Times use Europe/Berlin.
      </footer>
    </main>
  );
}

function ReplayPicker({ onContinue }: { onContinue: () => void }) {
  const { data: index, error } = useArtifact<{ days?: string[] }>("/forecasts/index.json");
  const [choice, setChoice] = useState<string | null>(null);
  const days = [...(index?.days ?? [])].filter((day) => /^\d{4}-\d{2}-\d{2}$/.test(day)).sort();
  const day = choice ?? days[0];
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="text-[28px] font-light leading-tight">Historical forecast</h2>
          <p className="mt-1 text-sm text-ink-2">Choose a published date. The earliest available date opens first.</p>
        </div>
        <label className="flex flex-col gap-1 text-xs text-muted">
          Forecast date
          <select value={day ?? ""} onChange={(e) => setChoice(e.target.value)} disabled={!days.length}
            className="rounded-full border border-line bg-panel px-4 py-2 text-[15px] text-ink">
            {days.map((d) => <option key={d} value={d}>{d}</option>)}
          </select>
        </label>
      </div>
      {error ? <Unavailable label="The list of historical cases could not be loaded." /> : !index ? <Loading /> : !day ? <Unavailable label="No historical cases have been published yet." /> : <HistoricalReplay key={day} day={day} onContinue={onContinue} />}
    </div>
  );
}

function HistoricalReplay({ day, onContinue }: { day: string; onContinue: () => void }) {
  const { data: f, error } = useArtifact<ForecastResponse>(`/forecasts/${day}.json`);
  const [revealed, setRevealed] = useState(false);
  const [selected, setSelected] = useState(0);
  const [preparation, setPreparation] = useState("");
  if (error) return <Unavailable label="Forecast unavailable. Choose another date or reload." />;
  if (!f) return <Loading />;
  if (f.mode !== "hindcast" || !Array.isArray(f.hours) || !f.hours.length) return <Unavailable label="This file is not a historical forecast." />;

  const scores = scoreReplay(f);
  const firstOpposite = firstRecordedOpposite(f);
  const event = planningEvent(f);
  const minutes = preparation.trim() === "" ? null : Number(preparation);
  const validMinutes = minutes !== null && Number.isInteger(minutes) && minutes >= 0 && minutes <= 1440;
  const reviewAt = event && validMinutes ? new Date(Date.parse(event.time) - minutes * 60_000).toISOString() : null;
  const h = f.hours[Math.min(selected, f.hours.length - 1)];

  return (
    <div className="space-y-4">
      <Panel title="Historical forecast" aside={<span className="text-xs text-muted">Model: {f.model_version}</span>}>
        <div className="grid gap-3 sm:grid-cols-2">
          <Metric label="Issue time" value={formatPitchTimeWithOffset(f.issued_at)} />
          <Metric label="First forecast direction change" value={f.next_change ? `${f.next_change.from} → ${f.next_change.to} · ${formatPitchTimeWithOffset(f.next_change.time)}` : "None in this forecast"} />
        </div>
        <p className="mt-3 text-xs leading-relaxed text-muted">This saved replay is not an as-of backtest. Its archived-weather availability proxy may predate the current evaluation. Exact publication times and the initial direction reporting delay are unknown.</p>
        <details className="mt-2 text-xs text-muted"><summary className="cursor-pointer">Forecast provenance</summary><p className="mt-2 break-words">{f.nwp} · rules {f.rules_version}</p></details>
      </Panel>
      <Panel title={`Forecast · ${f.hours.length} hours`}>
        <Timeline f={f} selected={selected} onSelect={setSelected} rows={["od", "r18", "wind"]} />
        <p className="mt-3 text-sm text-ink-2">Selected: {formatPitchTimeWithOffset(h.time)} · lead +{h.lead_h} h · model OD {h.od}, rules {h.rule_od} · Runway 18 usability probability {Math.round(h.p_18_usable * 100)}%.</p>
      </Panel>
      <Panel title={revealed ? "Recorded direction revealed" : "The later outcome is hidden"}>
        <p className="text-sm text-ink-2">DFLD directions are operational proxies, not certified movement records. Runway 18 labels come from weather rules and do not establish actual closures.</p>
        <button className={cx(BUTTON, "mt-4 bg-west-soft text-ink")} disabled={scores.matchedHours === 0}
          onClick={() => setRevealed((value) => !value)} aria-expanded={revealed} aria-controls="replay-outcome">
          {revealed ? "Hide recorded outcome" : "Reveal recorded outcome"}
        </button>
        {scores.matchedHours === 0 && <p className="mt-2 text-sm text-muted">No recorded direction labels match this forecast.</p>}
        {revealed && <div id="replay-outcome" className="mt-4 space-y-4" aria-live="polite">
          <p className="text-sm"><strong>{scores.matchedHours}/{scores.totalHours} forecast hours have recorded labels.</strong> Every method uses the same hours.</p>
          <div className="grid gap-3 sm:grid-cols-3">
            <Metric label="Model · matching direction" value={`${scores.modelCorrect}/${scores.matchedHours}`} />
            <Metric label="Weather rules · matching direction" value={`${scores.ruleCorrect}/${scores.matchedHours}`} />
            <Metric label="Keep current · matching direction" value={`${scores.persistenceCorrect}/${scores.matchedHours}`} />
          </div>
          <p className="text-sm text-ink-2">{firstOpposite ? `First different recorded direction: ${firstOpposite.od} at ${formatPitchTimeWithOffset(firstOpposite.time)}.` : "No different direction appears in the saved hourly records."} These scores count matching hourly states; they do not measure change-event detection or exact switch timing.</p>
          {firstOpposite?.previousMatchingTime && <p className="text-sm text-ink-2">Recorded direction last matched at {formatPitchTimeWithOffset(firstOpposite.previousMatchingTime)} and first differed at {formatPitchTimeWithOffset(firstOpposite.time)}. Hourly records do not show when it changed and may miss temporary changes.</p>}
          <details className="text-sm"><summary className="cursor-pointer text-ink-2">Inspect all forecast and recorded hours</summary><div className="mt-3 overflow-x-auto"><table className="w-full min-w-[520px] text-left text-xs tabular">
            <thead><tr className="text-muted"><th className="p-2">Berlin time</th><th>Model</th><th>Rules</th><th>Keep current</th><th>Recorded OD</th></tr></thead>
            <tbody>{f.hours.map((hour) => {
              const recorded = f.observed?.find((o) => o.time === hour.time)?.od;
              return <tr key={hour.time} className="border-t border-line"><td className="p-2">{formatPitchTimeWithOffset(hour.time)}</td><td>{hour.od}</td><td>{hour.rule_od}</td><td>{f.current_od}</td><td>{recorded ?? "Unknown"}</td></tr>;
            })}</tbody>
          </table></div></details>
        </div>}
      </Panel>
      <Panel title="Preparation time">
        <p className="text-sm text-ink-2">Enter how many minutes an alternative ground-handling allocation would take. The result is a hypothetical scenario; no team procedure or staffing benefit is assumed.</p>
        <label className="mt-3 flex flex-wrap items-center gap-3 text-sm">Preparation time (minutes)
          <input type="number" min="0" max="1440" step="1" value={preparation} onChange={(e) => setPreparation(e.target.value)} placeholder="Minutes"
            className="w-64 max-w-full rounded-card border border-line bg-panel-2 px-3 py-2 text-ink" />
        </label>
        <p className="mt-3 text-sm" aria-live="polite">{!event ? "No direction change or Runway 18 restriction is forecast in this case." : !validMinutes ? "Enter 0–1,440 whole minutes to calculate the review time." : reviewAt && Date.parse(reviewAt) < Date.parse(f.issued_at) ? "This duration places review before issue time; no review time is available." : reviewAt && Date.parse(reviewAt) === Date.parse(f.issued_at) ? `Review time: ${formatPitchTimeWithOffset(reviewAt)} (forecast issue time; no lead time).` : `Scenario review time: ${formatPitchTimeWithOffset(reviewAt!)} · before the forecast ${event.kind === "direction" ? "direction change" : "Runway 18 restriction"}.`}</p>
        <p className="mt-2 text-xs text-muted">This uses the first forecast event. The result is hypothetical, not an operational deadline or a calibrated event interval. Compare it with recorded evidence after revealing the outcome.</p>
        {revealed && <p className="mt-2 rounded-card border border-line bg-panel-2 p-3 text-sm text-ink-2">{historicalPreparationEvidence({ eventKind: event?.kind ?? null, reviewAt, status: reviewAt ? preparationTimingStatus(f.issued_at, reviewAt, firstOpposite) : null, firstOpposite })}</p>}
      </Panel>
      <button className={cx(BUTTON, "bg-west-soft text-ink")} onClick={onContinue}>View evaluation →</button>
    </div>
  );
}

type PitchReport = QualityResult & { next_change: QualityResult["next_change"] & { n_no_change_windows?: number; excluded_incomplete_windows?: number } };

function historicalPreparationEvidence({
  eventKind,
  reviewAt,
  status,
  firstOpposite,
}: {
  eventKind: "direction" | "runway18" | null;
  reviewAt: string | null;
  status: PreparationTimingStatus | null;
  firstOpposite: ReturnType<typeof firstRecordedOpposite>;
}) {
  if (!reviewAt) return "Enter a duration to compare the hypothetical review time with recorded evidence.";
  if (eventKind === "runway18") return "Runway 18 timing cannot be compared: this replay has weather-rule labels but no recorded closure history.";
  if (eventKind !== "direction") return "No forecast event is available to compare with the review time.";
  if (!firstOpposite) return "No different recorded direction is available for comparison.";

  const firstDifferent = formatPitchTimeWithOffset(firstOpposite.time);
  if (status === "insufficient-lead") return "The review time is before forecast issuance; no forecast lead remains for this scenario.";
  if (status === "late") return `Late: review is at or after the first different recorded direction (${firstDifferent}). The hourly record does not show the exact transition time or prove an operational action was missed.`;
  if (status === "before-recorded-change-interval" && firstOpposite.previousMatchingTime) {
    return `Before the recorded change: the last matching sample was ${formatPitchTimeWithOffset(firstOpposite.previousMatchingTime)} and the first different sample was ${firstDifferent}. Hourly records may miss temporary changes.`;
  }
  if (firstOpposite.previousMatchingTime) {
    return `The review falls between the last matching sample (${formatPitchTimeWithOffset(firstOpposite.previousMatchingTime)}) and the first different sample (${firstDifferent}). The exact transition time is unknown within this gap.`;
  }
  return `The first different recorded direction is ${firstDifferent}, but no earlier post-issue sample is available to bound the change time.`;
}

function formatRate(value: number | null | undefined, denominator: number | null | undefined) {
  if (typeof denominator !== "number" || !Number.isFinite(denominator) || denominator <= 0) return "Unavailable";
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0 || value > 1) return "Unavailable";
  return `${(value * 100).toFixed(1)}%`;
}

function formatDecimal(value: number | null | undefined) {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(3) : "Unavailable";
}

function PitchQuality() {
  const { data: q, error } = useArtifact<PitchReport>("/data/quality.json");
  if (error) return <Unavailable label="The aggregate evaluation could not be loaded." />;
  if (!q) return <Loading />;
  const outOfSampleByLead = new Map((q.out_of_sample?.od ?? []).map((row) => [row.lead_h, row]));
  return (
    <div className="space-y-4">
      <div><h2 className="text-[28px] font-light leading-tight">Evaluation</h2><p className="mt-1 text-sm text-ink-2">{q.folds.length} monthly folds · {q.evaluation}. These results are separate from the selected historical forecast and are not tied to its model version.</p></div>
      <Panel title="Operating direction">
        <div className="overflow-x-auto"><table className="w-full min-w-[560px] text-left text-sm tabular">
          <thead className="text-xs text-muted"><tr><th className="py-2">Lead</th><th>Hours</th><th>Model</th><th>Rules</th><th>Keep current</th><th>Model / rules Brier ↓</th></tr></thead>
          <tbody>{([1, 6, 24] as const).map((lead) => {
            const r = outOfSampleByLead.get(lead);
            return <tr key={lead} className="border-t border-line"><td className="py-3">+{lead} h</td><td>{r && r.n > 0 ? r.n : "Unavailable"}</td><td>{formatRate(r?.model_acc, r?.n)}</td><td>{formatRate(r?.rule_acc, r?.n)}</td><td>{formatRate(r?.persistence_acc, r?.n)}</td><td>{r && r.n > 0 ? `${formatDecimal(r.model_brier)} / ${formatDecimal(r.rule_brier)}` : "Unavailable"}</td></tr>;
          })}</tbody>
        </table></div>
        <p className="mt-3 text-xs text-muted">Percentages are hourly direction accuracy against DFLD records. Brier measures probability error; lower is better. These scores do not show whether the lead time is sufficient for an operational task.</p>
      </Panel>
      <Panel title="Change timing and false alarms">
        <div className="grid gap-3 sm:grid-cols-3">
          <Metric label={`First change within ±1 h · ${q.next_change.n_actual_change_windows} change windows`} value={formatRate(q.next_change.within_1h, q.next_change.n_actual_change_windows)} />
          <Metric label={`First change within ±3 h · ${q.next_change.n_actual_change_windows} change windows`} value={formatRate(q.next_change.within_3h, q.next_change.n_actual_change_windows)} />
          <Metric label={`False alarms · ${q.next_change.n_no_change_windows ?? "unknown"} no-change windows`} value={formatRate(q.next_change.false_alarm_rate, q.next_change.n_no_change_windows)} />
        </div>
        <p className="mt-3 text-xs text-muted">These are overlapping forecast issue windows, not independent events. {q.next_change.excluded_incomplete_windows ?? "Unspecified"} incomplete windows were excluded. Direction timing does not validate runway-18 closures.</p>
      </Panel>
      <Panel title="Runway 18 labels">
        <p className="text-sm text-ink-2">Its labels are {q.r18_label_type} from observed weather and the challenge rules. Actual operational closure history is not supplied with this evaluation.</p>
      </Panel>
      <details className="rounded-card border border-line bg-panel p-5 text-sm"><summary className="cursor-pointer">Sources and limitations</summary>
        <ul className="mt-3 list-disc space-y-2 pl-5 text-xs text-ink-2">{q.limitations.map((text) => <li key={text}>{text}</li>)}</ul>
        <ul className="mt-4 space-y-2 text-xs">{q.data_sources.map((source) => <li key={source.name}><a href={source.url} target="_blank" rel="noreferrer" className="underline">{source.name}</a></li>)}</ul>
        <a href="/data/quality.json" className="mt-3 inline-block text-xs underline">Open the evaluation data</a>
      </details>
      <Panel title="Next validation"><p className="mt-2 text-sm text-ink-2">Ask a ground-handling shift lead what staff could prepare, how much lead time they need, and which false-alarm rate they can accept.</p></Panel>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="rounded-card bg-panel-2 p-4"><p className="text-[13px] text-muted">{label}</p><p className="mt-2 text-[26px] font-light leading-tight tabular">{value}</p></div>;
}
function Loading() { return <p role="status" className="py-8 text-muted">Loading saved data…</p>; }
function Unavailable({ label }: { label: string }) { return <p role="alert" className="rounded-card border border-line bg-panel p-5 text-ink-2">{label} <Link href="/" className="underline">Return to cockpit</Link></p>; }
