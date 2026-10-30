"use client";

import { useEffect, useRef, useState } from "react";
import type { QualityResult } from "@/lib/forecast-types";

// RESULTS.md, pitch line 2, word for word. It is an estimate, not a number from quality.json.
const MONEY_LINE =
  "Using EUROCONTROL's public delay costs and stated assumptions, that is worth an illustrative €0.1M a year against the official rules and €0.6M against no forecast, in central scenarios. This is an estimate, not a measured FRA saving.";

// The scores in plain words, read from web/public/data/quality.json at runtime and counted up on scroll.
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
  const inTen = two ? Math.round(two.model_acc * 10) : null;
  // Share of the rulebook's wrong hours that the forecast gets right, two days ahead.
  const fewer = two && two.rule_acc < 1 ? Math.round((1 - (1 - two.model_acc) / (1 - two.rule_acc)) * 100) : null;

  return (
    <section className="py-16 sm:py-24" aria-label="How good it is">
      <div className="grid gap-12 md:grid-cols-3 md:gap-8">
        <Item
          big={inTen == null ? null : <><Count to={inTen} /> in 10</>}
          line="hours called right, 2 days ahead"
          missing={missing}
        />
        <Item
          big={fewer == null ? null : <><Count to={fewer} />%</>}
          line="fewer mistakes than the official rulebook, 2 days ahead"
          missing={missing}
        />
        <Item big={<>€0.1–0.6M</>} line="a year, estimated" note={`${MONEY_LINE} Source: RESULTS.md.`} />
      </div>
      <p className="mt-10 text-[13px] text-muted">
        Measured on {q ? `${q.folds.length} months` : "past months"} the forecast had never seen.
      </p>
    </section>
  );
}

function Item({ big, line, note, missing }: { big: React.ReactNode; line: string; note?: string; missing?: boolean }) {
  return (
    <div>
      <div className="text-[56px] font-light leading-none tracking-[-0.03em] tabular sm:text-[72px]">
        {big ?? <span className="text-muted">{missing ? "unavailable" : "…"}</span>}
      </div>
      <p className="mt-4 max-w-[28ch] text-[20px] leading-snug">{line}</p>
      {note && <p className="mt-3 max-w-[48ch] text-[13px] leading-snug text-muted">{note}</p>}
    </div>
  );
}

// Counts from 0 to `to` when scrolled into view. Starts on the final value, so a page that never animates is still right.
function Count({ to }: { to: number }) {
  const ref = useRef<HTMLSpanElement>(null);
  const [shown, setShown] = useState(to);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    let raf = 0;
    let done = 0;
    const io = new IntersectionObserver(
      (entries) => {
        if (!entries.some((e) => e.isIntersecting)) return;
        io.disconnect();
        if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
        const t0 = performance.now();
        const step = (t: number) => {
          const k = Math.min(1, (t - t0) / 1200);
          setShown(Math.round(to * (1 - Math.pow(1 - k, 3))));
          if (k < 1) raf = requestAnimationFrame(step);
        };
        raf = requestAnimationFrame(step);
        done = window.setTimeout(() => {
          cancelAnimationFrame(raf);
          setShown(to);
        }, 1600);
      },
      { threshold: 0.5 },
    );
    io.observe(el);
    return () => {
      io.disconnect();
      cancelAnimationFrame(raf);
      clearTimeout(done);
    };
  }, [to]);

  return <span ref={ref}>{shown}</span>;
}
