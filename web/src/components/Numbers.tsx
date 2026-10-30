"use client";

import { useEffect, useState } from "react";
import type { QualityResult } from "@/lib/forecast-types";

// Held-out scores, read from web/public/data/quality.json at runtime.
export function Numbers() {
  const [q, setQ] = useState<QualityResult | null>(null);
  const [missing, setMissing] = useState(false);

  useEffect(() => {
    fetch("/data/quality.json", { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then(setQ)
      .catch(() => setMissing(true));
  }, []);

  const two = q?.out_of_sample.od.find((x) => x.lead_h === 48);
  const modelScore = measuredPercentage(two?.model_acc, two?.n);
  const ruleScore = measuredPercentage(two?.rule_acc, two?.n);

  return (
    <section className="py-16 sm:py-24" aria-label="Held-out forecast accuracy">
      <div className="grid gap-12 md:grid-cols-2 md:gap-8">
        <Item
          big={modelScore == null ? null : <>{modelScore}%</>}
          line="Model accuracy, 48 hours ahead"
          missing={missing || (!!q && modelScore == null)}
        />
        <Item
          big={ruleScore == null ? null : <>{ruleScore}%</>}
          line="Official rules accuracy, 48 hours ahead"
          missing={missing || (!!q && ruleScore == null)}
        />
      </div>
      {q && <p className="mt-10 text-[13px] text-muted">Measured on {q.folds.length} held-out months.</p>}
    </section>
  );
}

function measuredPercentage(value: number | null | undefined, n: number | null | undefined) {
  if (!Number.isInteger(n) || n! <= 0 || typeof value !== "number" || !Number.isFinite(value) || value < 0 || value > 1) return null;
  return (value * 100).toFixed(1);
}

function Item({ big, line, missing }: { big: React.ReactNode; line: string; missing?: boolean }) {
  return (
    <div>
      <div className="text-[56px] font-light leading-none tracking-[-0.03em] tabular sm:text-[72px]">
        {big ?? <span className="text-muted">{missing ? "unavailable" : "…"}</span>}
      </div>
      <p className="mt-4 max-w-[28ch] text-[20px] leading-snug">{line}</p>
    </div>
  );
}
