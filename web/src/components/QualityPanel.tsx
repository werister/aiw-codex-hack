"use client";

import { useEffect, useState } from "react";
import type { QualityResult, ReliabilityBin, SkillAtLead } from "@/lib/forecast-types";
import { Panel, cx } from "./ui";

type Quality = QualityResult & {
  next_change: QualityResult["next_change"] & { n_no_change_windows?: number };
};

// Held-out quality from the expanding monthly walk-forward (web/public/data/quality.json).
export function QualityPanel() {
  const [q, setQ] = useState<Quality | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "missing">("loading");

  useEffect(() => {
    fetch("/data/quality.json", { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: Quality) => {
        setQ(d);
        setState("ready");
      })
      .catch(() => setState("missing"));
  }, []);

  if (state !== "ready" || !q) {
    return (
      <Panel title="Model quality">
        <p className="text-[15px] text-muted">
          {state === "loading" ? "Loading…" : "Evaluation data unavailable."}
        </p>
      </Panel>
    );
  }

  const months = q.folds.map((f) => f.month);

  return (
    <Panel
      title="Model quality · held out, walk-forward"
      aside={<span className="text-[13px] text-muted">{q.evaluation}</span>}
    >
      <p className="-mt-1 max-w-[90ch] text-[15px] leading-snug text-ink-2">
        Each test month was excluded from its fit, but results informed development. Direction uses a public DFLD proxy, excluding change hours.
        Runway 18 uses {q.r18_label_type} labels.
      </p>
      <dl className="mt-5 flex flex-wrap gap-x-10 gap-y-3 text-[15px]">
        <Fact k="Held-out months" v={months.length ? `${months.length} · ${months[0]} to ${months[months.length - 1]}` : "Unavailable"} />
        <Fact k="Changes timed within ±3 h" v={`${measuredRate(q.next_change.within_3h, q.next_change.n_actual_change_windows)} (±1 h: ${measuredRate(q.next_change.within_1h, q.next_change.n_actual_change_windows)})`} />
        <Fact k="False alarms in no-change windows" v={measuredRate(q.next_change.false_alarm_rate, q.next_change.n_no_change_windows)} />
        <Fact k="Recorded hours matching the rules" v={measuredRate(q.rule_label_comparison.agreement, q.rule_label_comparison.n)} />
      </dl>

      <div className="mt-8 grid gap-8 xl:grid-cols-[3fr_2fr]">
        <SkillTable rows={q.out_of_sample?.od ?? []} inSample={q.in_sample?.od ?? []} />
        <Reliability bins={q.reliability?.od ?? []} />
      </div>

      <details className="mt-6 border-t border-line pt-4 text-[13px] leading-relaxed text-muted">
        <summary className="cursor-pointer text-[15px] text-ink">Data sources and limitations</summary>
        <ul className="mt-2 space-y-1">
          {q.data_sources.map((s) => (
            <li key={s.name}>
              {s.name}:{" "}
              <a href={s.url} className="underline" target="_blank" rel="noreferrer">
                {s.url}
              </a>
            </li>
          ))}
        </ul>
        <ul className="mt-2 list-disc space-y-1 pl-4">
          {q.limitations.map((l) => (
            <li key={l}>{l}</li>
          ))}
        </ul>
        <p className="mt-2">Runway 18 labels are {q.r18_label_type}. Recorded operational closures are unavailable.</p>
      </details>
    </Panel>
  );
}

function measuredRate(value: number | null | undefined, n: number | null | undefined) {
  return hasMeasuredRate(value, n) ? `${Math.round(value * 100)}%` : "Unavailable";
}

function hasMeasuredRate(value: number | null | undefined, n: number | null | undefined): value is number {
  return Number.isInteger(n) && n! > 0 && typeof value === "number" && Number.isFinite(value) && value >= 0 && value <= 1;
}

function Fact({ k, v }: { k: string; v: string }) {
  return (
    <div>
      <dt className="text-[12px] text-muted">{k}</dt>
      <dd className="tabular">{v}</dd>
    </div>
  );
}

function SkillTable({ rows, inSample }: { rows: SkillAtLead[]; inSample: SkillAtLead[] }) {
  const ins = new Map(inSample.map((r) => [r.lead_h, r]));
  return (
    <div>
      <div className="mb-3 text-[20px] font-light leading-tight">Operating direction: chronological test accuracy</div>
      <div className="overflow-x-auto">
      <table className="w-full min-w-[520px] text-[15px]">
        <thead>
          <tr className="text-left text-[12px] text-muted">
            <th className="pb-1 font-medium">Lead</th>
            <th className="pb-1 font-medium">Model</th>
            <th className="pb-1 font-medium">Official rules</th>
            <th className="pb-1 font-medium">Same as now</th>
            <th className="pb-1 font-medium">Right in hours that change · model / rules</th>
            <th className="pb-1 font-medium text-muted">In-sample</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 && <tr><td colSpan={6} className="py-2 text-muted">Unavailable</td></tr>}
          {rows.map((r) => {
            const scores = [r.model_acc, r.rule_acc, r.persistence_acc].filter((value) => hasMeasuredRate(value, r.n));
            const best = scores.length ? Math.max(...scores) : null;
            const cell = (v: number) => {
              const available = hasMeasuredRate(v, r.n);
              return (
                <td className={cx("py-2 tabular", available && v === best ? "font-semibold text-ink" : "text-muted")}>
                  {available ? `${(v * 100).toFixed(1)}%` : "Unavailable"}
                </td>
              );
            };
            const changeN = Number.isInteger(r.change_n) && r.change_n! > 0 ? r.change_n : null;
            const inSampleRow = ins.get(r.lead_h);
            return (
              <tr key={r.lead_h} className="border-t border-line">
                <td className="py-2 tabular">{r.lead_h} h</td>
                {cell(r.model_acc)}
                {cell(r.rule_acc)}
                {cell(r.persistence_acc)}
                <td className="py-2 tabular text-ink-2">
                  {changeN
                    ? `${measuredRate(r.model_change_acc, changeN)} / ${measuredRate(r.rule_change_acc, changeN)} of ${changeN}`
                    : "Unavailable"}
                </td>
                <td className="py-2 tabular text-muted">
                  {inSampleRow && hasMeasuredRate(inSampleRow.model_acc, inSampleRow.n)
                    ? `${(inSampleRow.model_acc * 100).toFixed(1)}%`
                    : "Unavailable"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      </div>
      <div className="mt-2 text-[12px] text-muted">
        Best result per row in bold. Persistence keeps the direction at issue time. In-sample scores use training data.
      </div>
    </div>
  );
}

function Reliability({ bins }: { bins: ReliabilityBin[] }) {
  const pts = bins.filter((b) =>
    Number.isInteger(b.n) && b.n > 0 &&
    hasProbability(b.mean_predicted) && hasProbability(b.observed_frequency),
  );
  return (
    <div>
      <div className="mb-3 text-[20px] font-light leading-tight">Predicted and observed probabilities</div>
      {pts.length === 0 ? (
        <p className="text-[12px] text-muted">Unavailable</p>
      ) : (
        <>
      <svg viewBox="0 0 220 180" className="w-full max-w-[300px]">
        <rect x="30" y="10" width="180" height="140" fill="var(--panel-2)" />
        <line x1="30" y1="150" x2="210" y2="10" stroke="var(--muted)" strokeDasharray="4 4" />
        {pts.map((b) => (
          <circle
            key={b.lower}
            cx={30 + 180 * (b.mean_predicted as number)}
            cy={150 - 140 * (b.observed_frequency as number)}
            r={Math.max(2.5, Math.min(7, Math.sqrt(b.n) / 12))}
            fill="var(--west)"
          />
        ))}
        <text x="120" y="170" textAnchor="middle" fontSize="9" fill="var(--muted)">predicted P(OD 25)</text>
        <text x="12" y="80" textAnchor="middle" fontSize="9" fill="var(--muted)" transform="rotate(-90 12 80)">observed share 25</text>
      </svg>
      <div className="text-[12px] text-muted">On the dashed line, predicted probability equals observed frequency.</div>
        </>
      )}
    </div>
  );
}

function hasProbability(value: number | null | undefined): value is number {
  return typeof value === "number" && Number.isFinite(value) && value >= 0 && value <= 1;
}
