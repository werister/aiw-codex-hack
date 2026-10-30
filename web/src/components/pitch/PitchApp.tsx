"use client";

import Link from "next/link";
import { BrandLogo } from "../BrandLogo";
import { useEffect, useState } from "react";
import type { ForecastResponse, QualityResult } from "@/lib/forecast-types";
import { firstRecordedOpposite, formatPitchTime, planningEvent, scoreReplay } from "@/lib/pitch-replay";
import { Timeline } from "../Timeline";
import { Panel, cx } from "../ui";
import { WindExample } from "./WindExample";

const STEPS = ["The hidden change", "Reveal the outcome", "Beyond one case"];
const BUTTON = "rounded-lg border border-line px-4 py-2 text-sm font-semibold focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-west disabled:opacity-40";

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
            <span className="text-xs uppercase tracking-widest text-muted">Frankfurt · Runway Outlook</span>
          </div>
          <h1 className="mt-3 text-2xl font-bold tracking-tight sm:text-3xl">Make the next change visible.</h1>
        </div>
        <Link href="/" className={BUTTON}>Open cockpit</Link>
      </header>
      <nav aria-label="Presentation steps" className="grid gap-2 sm:grid-cols-3">
        {STEPS.map((label, i) => (
          <button key={label} onClick={() => setStep(i)} aria-current={step === i ? "step" : undefined}
            className={cx(BUTTON, "text-left", step === i ? "border-west bg-west-soft text-ink" : "bg-panel text-ink-2")}>
            <span className="mr-2 text-muted">0{i + 1}</span>{label}
          </button>
        ))}
      </nav>
      {step === 0 && <WindExample onContinue={() => setStep(1)} />}
      {step === 1 && <ReplayPicker onContinue={() => setStep(2)} />}
      {step === 2 && <PitchQuality />}
      <footer className="border-t border-line pt-4 text-xs leading-relaxed text-muted">
        A planning aid for the ground-handling shift lead. Runway clearance remains an operational decision.
        Times are Europe/Berlin. The illustration and historical evaluation have separate evidence.
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
          <h2 className="text-xl font-semibold">First the forecast. Then the outcome.</h2>
          <p className="mt-1 text-sm text-ink-2">Historical reconstruction. The earliest saved case opens first; choose any available day.</p>
        </div>
        <label className="flex flex-col gap-1 text-xs text-muted">
          Historical case
          <select value={day ?? ""} onChange={(e) => setChoice(e.target.value)} disabled={!days.length}
            className="rounded-lg border border-line bg-panel px-3 py-2 text-sm text-ink">
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
  if (error) return <Unavailable label="This case could not be loaded. Choose another day or reload." />;
  if (!f) return <Loading />;
  if (f.mode !== "hindcast" || !Array.isArray(f.hours) || !f.hours.length) return <Unavailable label="This artifact does not contain a historical forecast." />;

  const scores = scoreReplay(f);
  const firstOpposite = firstRecordedOpposite(f);
  const event = planningEvent(f);
  const minutes = preparation.trim() === "" ? null : Number(preparation);
  const validMinutes = minutes !== null && Number.isFinite(minutes) && minutes >= 0 && minutes <= 1440;
  const reviewAt = event && validMinutes ? new Date(Date.parse(event.time) - minutes * 60_000).toISOString() : null;
  const h = f.hours[Math.min(selected, f.hours.length - 1)];

  return (
    <div className="space-y-4">
      <Panel title="Forecast available to the presenter" aside={<span className="text-xs text-muted">Saved model: {f.model_version}</span>}>
        <div className="grid gap-3 sm:grid-cols-2">
          <Metric label="Reconstructed issue time" value={formatPitchTime(f.issued_at)} />
          <Metric label="First predicted direction change" value={f.next_change ? `${f.next_change.from} → ${f.next_change.to} · ${formatPitchTime(f.next_change.time)}` : "None in this forecast"} />
        </div>
        <p className="mt-3 text-xs leading-relaxed text-muted">Saved historical illustration, not a verified as-of backtest. This replay uses the archived-weather availability proxy recorded below; its version can predate the current evaluation. Exact publication times and the initial direction&apos;s reporting delay are unverified.</p>
        <details className="mt-2 text-xs text-muted"><summary className="cursor-pointer">Forecast provenance</summary><p className="mt-2 break-words">{f.nwp} · rules {f.rules_version}</p></details>
      </Panel>
      <Panel title="The next 48 hours, as forecast">
        <Timeline f={f} selected={selected} onSelect={setSelected} rows={["od", "r18", "wind"]} />
        <p className="mt-3 text-sm text-ink-2">Selected: {formatPitchTime(h.time)} · +{h.lead_h} h · model {h.od}, rule baseline {h.rule_od} · runway 18 weather usability {Math.round(h.p_18_usable * 100)}%.</p>
      </Panel>
      <Panel title={revealed ? "Recorded direction revealed" : "The later outcome is hidden"}>
        <p className="text-sm text-ink-2">Direction labels are DFLD&apos;s public operational proxy, not a certified movement log. Runway 18 labels are weather-rule inference; this replay does not validate actual closures.</p>
        <button className={cx(BUTTON, "mt-4 bg-west-soft text-ink")} disabled={scores.matchedHours === 0}
          onClick={() => setRevealed((value) => !value)} aria-expanded={revealed} aria-controls="replay-outcome">
          {revealed ? "Hide recorded outcome" : "Reveal recorded outcome"}
        </button>
        {scores.matchedHours === 0 && <p className="mt-2 text-sm text-muted">No matched recorded direction labels are available for this case.</p>}
        {revealed && <div id="replay-outcome" className="mt-4 space-y-4" aria-live="polite">
          <p className="text-sm"><strong>{scores.matchedHours}/{scores.totalHours} forecast hours have recorded labels.</strong> Gaps are excluded equally for every method.</p>
          <div className="grid gap-3 sm:grid-cols-3">
            <Metric label="Model · matching direction" value={`${scores.modelCorrect}/${scores.matchedHours}`} />
            <Metric label="Weather rules · matching direction" value={`${scores.ruleCorrect}/${scores.matchedHours}`} />
            <Metric label="Keep current · matching direction" value={`${scores.persistenceCorrect}/${scores.matchedHours}`} />
          </div>
          <p className="text-sm text-ink-2">{firstOpposite ? `First recorded direction different from the issue state: ${firstOpposite.od}, ${formatPitchTime(firstOpposite.time)}.` : "No different direction appears in the available recorded hours."} Missing and hourly bins prevent an exact switch-time claim. These are state matches for one case, not event-detection accuracy.</p>
          <details className="text-sm"><summary className="cursor-pointer text-ink-2">Inspect all forecast and recorded hours</summary><div className="mt-3 overflow-x-auto"><table className="w-full min-w-[520px] text-left text-xs tabular">
            <thead><tr className="text-muted"><th className="p-2">Berlin time</th><th>Model</th><th>Rules</th><th>Keep current</th><th>Recorded OD</th></tr></thead>
            <tbody>{f.hours.map((hour) => {
              const recorded = f.observed?.find((o) => o.time === hour.time)?.od;
              return <tr key={hour.time} className="border-t border-line"><td className="p-2">{formatPitchTime(hour.time)}</td><td>{hour.od}</td><td>{hour.rule_od}</td><td>{f.current_od}</td><td>{recorded ?? "Unknown"}</td></tr>;
            })}</tbody>
          </table></div></details>
        </div>}
      </Panel>
      <Panel title="What could the shift lead prepare?">
        <p className="text-sm text-ink-2">Review an alternative ground-handling allocation before the forecast change. Enter the team&apos;s preparation time; no staffing savings are assumed.</p>
        <label className="mt-3 flex flex-wrap items-center gap-3 text-sm">Preparation time (minutes)
          <input type="number" min="0" max="1440" step="1" value={preparation} onChange={(e) => setPreparation(e.target.value)} placeholder="Enter your team's lead time"
            className="w-64 max-w-full rounded-lg border border-line bg-panel-2 px-3 py-2 text-ink" />
        </label>
        <p className="mt-3 text-sm" aria-live="polite">{!event ? "No upcoming direction change or runway-18 restriction is forecast in this case." : !validMinutes ? "Enter 0–1,440 minutes to calculate a conditional review time." : reviewAt && Date.parse(reviewAt) <= Date.parse(f.issued_at) ? "The required preparation time reaches the issue time or earlier. This forecast offers insufficient lead for that preparation." : `Scenario review time: ${formatPitchTime(reviewAt!)} · before the forecast ${event.kind === "direction" ? "direction change" : "runway-18 restriction"}.`}</p>
        <p className="mt-2 text-xs text-muted">Based on the earliest indicated time in this saved forecast. This is a planning scenario, not a guaranteed deadline or a calibrated event interval.</p>
      </Panel>
      <button className={cx(BUTTON, "bg-west-soft text-ink")} onClick={onContinue}>See the wider evaluation →</button>
    </div>
  );
}

type PitchReport = QualityResult & { next_change: QualityResult["next_change"] & { n_no_change_windows?: number; excluded_incomplete_windows?: number } };

function PitchQuality() {
  const { data: q, error } = useArtifact<PitchReport>("/data/quality.json");
  if (error) return <Unavailable label="The aggregate evaluation could not be loaded." />;
  if (!q) return <Loading />;
  if (!q.out_of_sample?.od?.length) return <Unavailable label="No held-out direction evaluation is available yet." />;
  return (
    <div className="space-y-4">
      <div><h2 className="text-xl font-semibold">One case illustrates. Held-out months test.</h2><p className="mt-1 text-sm text-ink-2">{q.folds.length} monthly folds · {q.evaluation}. This is a separate evaluation report; it does not declare a model-version link to the saved replay.</p></div>
      <Panel title="Operating direction · same targets, three methods">
        <div className="overflow-x-auto"><table className="w-full min-w-[560px] text-left text-sm tabular">
          <thead className="text-xs text-muted"><tr><th className="py-2">Lead</th><th>Hours</th><th>Model</th><th>Rules</th><th>Keep current</th><th>Model / rules Brier ↓</th></tr></thead>
          <tbody>{q.out_of_sample.od.map((r) => <tr key={r.lead_h} className="border-t border-line"><td className="py-3">+{r.lead_h} h</td><td>{r.n}</td><td>{(r.model_acc * 100).toFixed(1)}%</td><td>{(r.rule_acc * 100).toFixed(1)}%</td><td>{(r.persistence_acc * 100).toFixed(1)}%</td><td>{r.model_brier.toFixed(3)} / {r.rule_brier.toFixed(3)}</td></tr>)}</tbody>
        </table></div>
        <p className="mt-3 text-xs text-muted">Percentages are hourly direction accuracy at each lead against DFLD records. Brier measures probability error; lower is better. These scores do not measure useful preparation time.</p>
      </Panel>
      <Panel title="Changes and false alarms both matter">
        <div className="grid gap-3 sm:grid-cols-2">
          <Metric label={`First change within ±3 h · ${q.next_change.n_actual_change_windows} change windows`} value={`${(q.next_change.within_3h * 100).toFixed(1)}%`} />
          <Metric label={`False alarms · ${q.next_change.n_no_change_windows ?? "reported"} no-change windows`} value={`${(q.next_change.false_alarm_rate * 100).toFixed(1)}%`} />
        </div>
        <p className="mt-3 text-xs text-muted">These are overlapping forecast issue windows, not independent events. {q.next_change.excluded_incomplete_windows ?? "Unspecified"} incomplete windows were excluded. A direction timing result does not validate runway-18 closures.</p>
      </Panel>
      <Panel title="Runway 18 · the evidence boundary">
        <p className="text-sm text-ink-2">Its labels are {q.r18_label_type} from observed weather and the challenge rules. Actual operational closure history is not supplied with this evaluation. The opening example illustrates the threshold calculation; it does not prove an operational forecasting gain.</p>
      </Panel>
      <details className="rounded-xl border border-line bg-panel p-4 text-sm"><summary className="cursor-pointer">Sources and limitations</summary>
        <ul className="mt-3 list-disc space-y-2 pl-5 text-xs text-ink-2">{q.limitations.map((text) => <li key={text}>{text}</li>)}</ul>
        <ul className="mt-4 space-y-2 text-xs">{q.data_sources.map((source) => <li key={source.name}><a href={source.url} target="_blank" rel="noreferrer" className="underline">{source.name}</a></li>)}</ul>
        <a href="/data/quality.json" className="mt-3 inline-block text-xs underline">Open the evaluation data</a>
      </details>
      <Panel title="The next decision"><p className="text-lg font-semibold">Make time for preparation.</p><p className="mt-2 text-sm text-ink-2">Validate the warning with a ground-handling shift lead: what could they prepare, how much time do they need, and which false alarms are tolerable?</p></Panel>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="rounded-lg bg-panel-2 p-3"><p className="text-xs text-muted">{label}</p><p className="mt-1 text-lg font-semibold tabular">{value}</p></div>;
}
function Loading() { return <p role="status" className="py-8 text-muted">Loading saved data…</p>; }
function Unavailable({ label }: { label: string }) { return <p role="alert" className="rounded-xl border border-line bg-panel p-5 text-ink-2">{label} <Link href="/" className="underline">Return to cockpit</Link></p>; }
