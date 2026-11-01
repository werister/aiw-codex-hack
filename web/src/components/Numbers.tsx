"use client";

import { useEffect, useState } from "react";
import type { QualityResult } from "@/lib/forecast-types";

export function Numbers() {
  const [quality, setQuality] = useState<QualityResult | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    fetch("/data/quality.json").then((r) => r.ok ? r.json() : Promise.reject()).then(setQuality).catch(() => setFailed(true));
  }, []);
  return <section aria-label="Historical direction accuracy" className="grid gap-6 py-5 sm:grid-cols-3">
    {[1, 6, 24].map((lead) => {
      const row = quality?.out_of_sample.od.find((r) => r.lead_h === lead && r.n > 0);
      return <div key={lead} className="rounded-card border border-line p-6">
        <p className="text-[15px] text-muted">Direction accuracy · {lead} h ahead</p>
        <p className="mt-3 text-[48px] font-light tabular">{row ? `${(row.model_acc * 100).toFixed(1)}%` : failed ? "Unavailable" : "…"}</p>
        <p className="mt-3 text-[15px] text-muted">{row ? `Rules ${(row.rule_acc * 100).toFixed(1)}% · persistence ${(row.persistence_acc * 100).toFixed(1)}%` : "Measured values only"}</p>
      </div>;
    })}
  </section>;
}
