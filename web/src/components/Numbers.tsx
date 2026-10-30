"use client";

import { useEffect, useRef, useState } from "react";
import type { QualityResult, ReliabilityBin } from "@/lib/forecast-types";

// quality.json also carries certainty-score reliability; only the fields read here are typed.
type Quality = QualityResult & { certainty_reliability?: ReliabilityBin[] };

// Held-out scores, read from web/public/data/quality.json at runtime and counted up when scrolled into view.
export function Numbers() {
  const [q, setQ] = useState<Quality | null>(null);
  const [missing, setMissing] = useState(false);

  useEffect(() => {
    fetch("/data/quality.json", { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then(setQ)
      .catch(() => setMissing(true));
  }, []);

  if (missing) return <p className="py-10 text-[15px] text-muted">Model scores unavailable.</p>;
  if (!q) return <div className="h-[260px]" />;

  const rows = [6, 24, 48].map((lead) => ({ lead, r: q.out_of_sample.od.find((x) => x.lead_h === lead) }));
  const bins = q.certainty_reliability ?? [];
  const total = bins.reduce((s, b) => s + b.n, 0);
  const top = bins.find((b) => b.lower >= 0.9 && b.n > 0 && b.observed_frequency != null);

  return (
    <section className="py-10 sm:py-14" aria-label="Model scores">
      <p className="eyebrow text-muted">Tested on {q.folds.length} months it never saw</p>
      <h2 className="mt-2 max-w-[24ch] text-[28px] font-light leading-tight sm:text-[36px]">How often the direction call was right</h2>

      <div className="mt-8 grid grid-cols-2 gap-2.5 lg:grid-cols-4">
        {rows.map(({ lead, r }) => (
          <Card key={lead} label={`${lead} h ahead`}>
            {r ? (
              <>
                <Big value={r.model_acc * 100} />
                <Vs k="Rules" v={r.rule_acc} />
                <Vs k="Same as now" v={r.persistence_acc} />
              </>
            ) : (
              <p className="text-[17px] text-muted">unavailable</p>
            )}
          </Card>
        ))}
        <Card label="When certainty ≥ 90">
          {top && total ? (
            <>
              <Big value={(top.observed_frequency as number) * 100} />
              <p className="mt-3 text-[15px] text-ink-2">
                right · <span className="tabular">{Math.round((top.n / total) * 100)}%</span> of hours
              </p>
            </>
          ) : (
            <p className="text-[17px] text-muted">unavailable</p>
          )}
        </Card>
      </div>
    </section>
  );
}

function Card({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="rounded-card bg-panel-2 p-5 sm:p-6">
      <div className="eyebrow text-muted">{label}</div>
      <div className="mt-4">{children}</div>
    </div>
  );
}

function Vs({ k, v }: { k: string; v: number }) {
  return (
    <p className="mt-1 flex justify-between gap-3 text-[15px] text-ink-2 first-of-type:mt-3">
      <span>{k}</span>
      <span className="tabular">{(v * 100).toFixed(1)}%</span>
    </p>
  );
}

// Counts from 0 to value once the number scrolls into view; jumps straight there with reduced motion.
// It starts at the final value, so a page that never animates still shows the right number.
function Big({ value }: { value: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const [shown, setShown] = useState(value);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    let raf = 0;
    let done = 0;
    const run = () => {
      const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      const t0 = performance.now();
      const step = (t: number) => {
        const k = still ? 1 : Math.min(1, (t - t0) / 1200);
        setShown(value * (1 - Math.pow(1 - k, 3)));
        if (k < 1) raf = requestAnimationFrame(step);
      };
      raf = requestAnimationFrame(step);
      done = window.setTimeout(() => {
        cancelAnimationFrame(raf);
        setShown(value);
      }, 1600);
    };
    const io = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          io.disconnect();
          run();
        }
      },
      { threshold: 0.4 },
    );
    io.observe(el);
    return () => {
      io.disconnect();
      cancelAnimationFrame(raf);
      clearTimeout(done);
    };
  }, [value]);

  return (
    <div ref={ref} className="text-[44px] font-light leading-none tracking-[-0.02em] tabular sm:text-[56px]">
      {shown.toFixed(1)}
      <span className="text-[0.5em] text-muted">%</span>
    </div>
  );
}
