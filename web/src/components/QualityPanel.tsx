"use client";

import { useEffect, useState } from "react";
import type { QualityResult, ReliabilityBin, SkillAtLead } from "@/lib/forecast-types";
import { Panel, cx } from "./ui";

// Held-out quality from the expanding monthly walk-forward (web/public/data/quality.json).
export function QualityPanel() {
  const [q, setQ] = useState<QualityResult | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "missing">("loading");

  useEffect(() => {
    fetch("/data/quality.json", { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: QualityResult) => {
        setQ(d);
        setState("ready");
      })
      .catch(() => setState("missing"));
  }, []);

  if (state !== "ready" || !q) {
    return (
      <Panel title="Model quality">
        <p className="text-[15px] text-muted">
          {state === "loading" ? "Loading…" : "The walk-forward backtest is still running. Its results appear here when they land."}
        </p>
      </Panel>
    );
  }

  const months = q.folds.map((f) => f.month);
  const bin80 = q.reliability.od.find((b) => b.lower >= 0.8 && b.lower < 0.9 && b.n > 0);

  return (
    <Panel
      title="Model quality · held out, walk-forward"
      aside={<span className="text-[13px] text-muted">{q.evaluation}</span>}
    >
      <div className="grid grid-cols-2 gap-2.5 lg:grid-cols-4">
        <Stat
          value={`${months.length} months`}
          label={`tested one month at a time, never trained on (${months[0]} to ${months[months.length - 1]})`}
        />
        <Stat
          value={`${Math.round(q.rule_label_comparison.agreement * 100)}%`}
          label="of flown hours match the official rules on observed wind. The rules alone are not the truth."
        />
        <Stat
          value={`${Math.round(q.next_change.within_3h * 100)}%`}
          label={`of direction changes timed within ±3 h (${Math.round(q.next_change.within_1h * 100)}% within ±1 h)`}
        />
        <Stat
          value={bin80?.observed_frequency != null ? `${Math.round(bin80.observed_frequency * 100)}%` : "n/a"}
          label={
            bin80?.mean_predicted != null
              ? `of hours forecast at about ${Math.round(bin80.mean_predicted * 100)}% west were flown west. The confidence is calibrated.`
              : "calibration check"
          }
        />
      </div>

      <div className="mt-8 grid gap-8 xl:grid-cols-[3fr_2fr]">
        <SkillTable rows={q.out_of_sample.od} inSample={q.in_sample.od} />
        <Reliability bins={q.reliability.od} />
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
        <p className="mt-2">Runway 18 labels are {q.r18_label_type}: no public record of weather closures exists.</p>
      </details>
    </Panel>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div className="flex flex-col justify-between gap-4 rounded-card bg-panel-2 p-4 sm:p-5">
      <div className="text-[26px] font-light leading-none tracking-[-0.02em] tabular sm:text-[40px]">{value}</div>
      <div className="text-[13px] leading-snug text-ink-2">{label}</div>
    </div>
  );
}

function SkillTable({ rows, inSample }: { rows: SkillAtLead[]; inSample: SkillAtLead[] }) {
  const ins = new Map(inSample.map((r) => [r.lead_h, r]));
  return (
    <div>
      <div className="mb-3 text-[20px] font-light leading-tight">Operating direction: accuracy on unseen months</div>
      <div className="overflow-x-auto">
      <table className="w-full min-w-[520px] text-[15px]">
        <thead>
          <tr className="text-left text-[12px] text-muted">
            <th className="pb-1 font-medium">Lead</th>
            <th className="pb-1 font-medium">Model</th>
            <th className="pb-1 font-medium">Official rules</th>
            <th className="pb-1 font-medium">Keep current</th>
            <th className="pb-1 font-medium">Changes caught</th>
            <th className="pb-1 font-medium text-muted">In-sample</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => {
            const best = Math.max(r.model_acc, r.rule_acc, r.persistence_acc);
            const cell = (v: number) => (
              <td className={cx("py-2 tabular", v === best ? "font-semibold text-ink" : "text-muted")}>{(v * 100).toFixed(1)}%</td>
            );
            return (
              <tr key={r.lead_h} className="border-t border-line">
                <td className="py-2 tabular">{r.lead_h} h</td>
                {cell(r.model_acc)}
                {cell(r.rule_acc)}
                {cell(r.persistence_acc)}
                <td className="py-2 tabular text-ink-2">
                  {r.model_change_acc != null && r.change_n ? `${Math.round(r.model_change_acc * 100)}% of ${r.change_n}` : "–"}
                </td>
                <td className="py-2 tabular text-muted">
                  {ins.get(r.lead_h) ? `${(ins.get(r.lead_h)!.model_acc * 100).toFixed(1)}%` : "–"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      </div>
      <div className="mt-2 text-[12px] text-muted">
        Best per row in bold. &quot;Keep current&quot; is persistence. In-sample is shown only to make overfitting visible.
      </div>
    </div>
  );
}

function Reliability({ bins }: { bins: ReliabilityBin[] }) {
  const pts = bins.filter((b) => b.n > 0 && b.mean_predicted != null && b.observed_frequency != null);
  return (
    <div>
      <div className="mb-3 text-[20px] font-light leading-tight">Is the probability honest?</div>
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
      <div className="text-[12px] text-muted">Dots on the dashed line mean the stated probability matches what happened.</div>
    </div>
  );
}
