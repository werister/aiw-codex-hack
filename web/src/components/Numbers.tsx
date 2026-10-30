"use client";

import { useEffect, useRef, useState } from "react";
import type { QualityResult, ReliabilityBin, SkillAtLead } from "@/lib/forecast-types";
import { cx } from "./ui";

// RESULTS.md money line (12363f8), word for word. An estimate, not a number from quality.json.
const MONEY_LINE =
  "Estimated value: about €0.4M a year at Frankfurt (range €0.13M to €3.2M), plus a similar amount in passengers' time. Based on EUROCONTROL delay costs and published studies of runway direction changes.";

// quality.json also carries certainty-score reliability; only the fields read here are typed.
type Quality = QualityResult & { certainty_reliability?: ReliabilityBin[] };

// The scores in plain words, then what they are worth. Read from web/public/data/quality.json at runtime.
export function Numbers() {
  const [q, setQ] = useState<Quality | null>(null);
  const [missing, setMissing] = useState(false);

  useEffect(() => {
    fetch("/data/quality.json", { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then(setQ)
      .catch(() => setMissing(true));
  }, []);

  // Only rows with samples and scores in range count (guard from the quality review).
  const valid = (r?: SkillAtLead) => (r && r.n > 0 && [r.model_acc, r.rule_acc].every((v) => Number.isFinite(v) && v >= 0 && v <= 1) ? r : undefined);
  const two = valid(q?.out_of_sample.od.find((x) => x.lead_h === 48));
  const day = valid(q?.out_of_sample.od.find((x) => x.lead_h === 24));
  const inTen = two ? Math.round(two.model_acc * 10) : null;
  // Share of the rulebook's wrong hours that the forecast gets right, two days ahead.
  const fewer = two && two.rule_acc < 1 ? Math.round((1 - (1 - two.model_acc) / (1 - two.rule_acc)) * 100) : null;
  const sure = q?.certainty_reliability?.find((b) => b.lower >= 0.9 && b.observed_frequency != null);
  // Hour-level: of the hours whose direction differs 24 h later, the share where the new direction is forecast.
  const caught = day?.model_change_acc;
  // Fewer wrong-direction hours a year, 24 h ahead, rounded to 50.
  const perYear = (a: number, b: number) => Math.round(((a - b) * 8760) / 50) * 50;
  const vsNow = day ? perYear(day.model_acc, day.persistence_acc) : null;
  const vsRules = day ? perYear(day.model_acc, day.rule_acc) : null;

  return (
    <>
      <section className="py-16 sm:py-24" aria-label="How good it is">
        <div className="grid gap-12 md:grid-cols-3 md:gap-8">
          <Item big={inTen == null ? null : <><Count to={inTen} /> in 10</>} line="hours called right, 2 days ahead" missing={missing} />
          <Item
            big={fewer == null ? null : <><Count to={fewer} />%</>}
            line="fewer mistakes than the official rulebook, 2 days ahead"
            missing={missing}
          />
          <Item
            big={sure ? <><Count to={Math.round((sure.observed_frequency as number) * 100)} /> in 100</> : null}
            line="right when it says it is very sure"
            missing={missing}
          />
        </div>
        {day && <Mistakes model={day.model_acc} rules={day.rule_acc} now={day.persistence_acc} />}
        <p className="mt-10 text-[13px] text-muted">
          Measured on {q ? `${q.folds.length} months` : "past months"} the forecast had never seen.
        </p>
      </section>

      <section className="border-t border-line py-16 sm:py-20" aria-label="What it is worth">
        <h2 className="text-[28px] font-light sm:text-[36px]">What it means for the people doing the work</h2>
        <div className="mt-10 grid gap-2.5 md:grid-cols-3">
          <Tile icon={ICON.bell} big={caught == null ? null : <><Count to={Math.round(caught * 100)} />%</>} missing={missing}>
            When the direction will be different 24 h later, the model predicts the new direction in{" "}
            {caught == null ? "most" : `${Math.round(caught * 100)}%`} of those hours
          </Tile>
          <Tile icon={ICON.clock} big={vsNow == null ? null : <>about <Count to={vsNow} /> h</>} missing={missing}>
            About {vsNow == null ? "…" : vsNow.toLocaleString("en-GB")} fewer hours a year planned for the wrong direction than{" "}
            &lsquo;same as now&rsquo; (about {vsRules ?? "…"} fewer than the official rules)
          </Tile>
          <Tile icon={ICON.euro} big={<>~€0.4M</>}>
            {MONEY_LINE}
          </Tile>
        </div>
      </section>
    </>
  );
}

// Wrong hours per 100, 24 h ahead, bars from zero so the gap is not exaggerated.
function Mistakes({ model, rules, now }: { model: number; rules: number; now: number }) {
  const rows = [
    { k: "Our forecast", v: (1 - model) * 100, cls: "bg-accent" },
    { k: "Official rulebook", v: (1 - rules) * 100, cls: "bg-ink/40" },
    { k: "Same as now", v: (1 - now) * 100, cls: "bg-ink/20" },
  ];
  const max = Math.max(...rows.map((r) => r.v), 1);
  return (
    <figure className="mt-14 max-w-[720px]">
      <figcaption className="text-[20px] font-light">Wrong hours per 100, one day ahead</figcaption>
      <div className="mt-5 space-y-3">
        {rows.map((r) => (
          <div key={r.k} className="grid grid-cols-[150px_1fr_52px] items-center gap-3 text-[15px]">
            <span>{r.k}</span>
            <span className="h-4 rounded-full bg-panel-2">
              <span className={cx("block h-full rounded-full", r.cls)} style={{ width: `${(r.v / max) * 100}%` }} />
            </span>
            <span className="text-right tabular">{r.v.toFixed(1)}</span>
          </div>
        ))}
      </div>
    </figure>
  );
}

const ICON = {
  bell: <path d="M24 10a9 9 0 0 0-9 9v7l-3 5h24l-3-5v-7a9 9 0 0 0-9-9ZM21 35a3 3 0 0 0 6 0" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />,
  clock: (
    <>
      <circle cx="24" cy="24" r="13" stroke="currentColor" strokeWidth="1.5" />
      <path d="M24 16v8l5 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </>
  ),
  euro: <path d="M31 15a10 10 0 1 0 0 18M14 21h12M14 27h12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />,
};

function Tile({
  icon,
  big,
  note,
  missing,
  children,
}: {
  icon: React.ReactNode;
  big: React.ReactNode;
  note?: string;
  missing?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-card bg-panel-2 p-6 sm:p-7">
      <svg viewBox="0 0 48 48" className="size-11 text-accent" fill="none" aria-hidden>
        {icon}
      </svg>
      <div className="mt-5 text-[40px] font-light leading-none tracking-[-0.02em] tabular sm:text-[48px]">
        {big ?? <span className="text-muted">{missing ? "unavailable" : "…"}</span>}
      </div>
      <p className="mt-3 text-[17px] leading-snug">{children}</p>
      {note && <p className="mt-3 text-[12px] leading-snug text-muted">{note}</p>}
    </div>
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

  return <span ref={ref}>{shown.toLocaleString("en-GB")}</span>;
}
