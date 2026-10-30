"use client";

import { useEffect, useState } from "react";
import type { BacktestResult, SkillAtLead } from "@/lib/forecast-types";
import { Panel, cx } from "./ui";

// Out-of-sample skill from the walk-forward backtest (web/public/data/backtest.json).
export function QualityPanel() {
  const [bt, setBt] = useState<BacktestResult | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "missing">("loading");

  useEffect(() => {
    fetch("/data/backtest.json", { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: BacktestResult) => {
        setBt(d);
        setState("ready");
      })
      .catch(() => setState("missing"));
  }, []);

  if (state !== "ready" || !bt) {
    return (
      <Panel title="Model quality (held-out, walk-forward)">
        <p className="text-sm text-muted">
          {state === "loading" ? "Loading…" : "The walk-forward backtest is still running. Its results appear here when they land."}
        </p>
      </Panel>
    );
  }

  return (
    <Panel
      title="Model quality (held-out, walk-forward)"
      aside={
        <span className="text-xs text-muted">
          test {bt.test_period.start.slice(0, 10)} → {bt.test_period.end.slice(0, 10)}
        </span>
      }
    >
      <div className="grid gap-5 lg:grid-cols-2">
        <SkillTable title="Operating direction" rows={bt.od} />
        <SkillTable title="Runway 18 usable" rows={bt.r18} />
      </div>
      <div className="mt-4 grid gap-4 border-t border-line pt-4 text-sm sm:grid-cols-3">
        <div>
          <div className="text-xs text-muted">Trained on</div>
          <div className="tabular">
            {bt.train_period.start.slice(0, 10)} → {bt.train_period.end.slice(0, 10)}
          </div>
        </div>
        <div>
          <div className="text-xs text-muted">Labels</div>
          <div>{bt.labels}</div>
        </div>
        <div>
          <div className="text-xs text-muted">Base rates</div>
          <div className="tabular">
            {Math.round(bt.base_rates.od25_share * 100)}% west · {Math.round(bt.base_rates.changes_per_year)} changes/yr ·{" "}
            {(bt.base_rates.r18_closed_share * 100).toFixed(1)}% 18 closed
          </div>
        </div>
      </div>
      {bt.drivers.length > 0 && (
        <div className="mt-4 border-t border-line pt-4">
          <div className="mb-2 text-xs text-muted">What drives the forecast (permutation importance)</div>
          <div className="space-y-1">
            {bt.drivers.slice(0, 6).map((d) => (
              <div key={d.feature} className="grid grid-cols-[180px_1fr] items-center gap-2 text-xs">
                <span className="truncate font-mono text-ink-2">{d.feature}</span>
                <div className="h-2 rounded bg-panel-2">
                  <div
                    className="h-2 rounded bg-ink-2"
                    style={{ width: `${Math.min(100, (d.importance / Math.max(...bt.drivers.map((x) => x.importance))) * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </Panel>
  );
}

function SkillTable({ title, rows }: { title: string; rows: SkillAtLead[] }) {
  return (
    <div>
      <div className="mb-2 text-sm font-semibold">{title}</div>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs text-muted">
            <th className="pb-1 font-medium">Lead</th>
            <th className="pb-1 font-medium">Model</th>
            <th className="pb-1 font-medium">Rules</th>
            <th className="pb-1 font-medium">Persistence</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => {
            const best = Math.max(r.model_acc, r.rule_acc, r.persistence_acc);
            return (
              <tr key={r.lead_h} className="border-t border-line">
                <td className="py-1.5 tabular">{r.lead_h} h</td>
                {[r.model_acc, r.rule_acc, r.persistence_acc].map((v, i) => (
                  <td key={i} className={cx("py-1.5 tabular", v === best ? "font-bold text-ok" : "text-ink-2")}>
                    {(v * 100).toFixed(1)}%
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
      <div className="mt-1 text-[11px] text-muted">Accuracy on hours never used for training. Best per row in green.</div>
    </div>
  );
}
