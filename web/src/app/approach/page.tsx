import type { Metadata } from "next";
import Link from "next/link";
import { Brand } from "@/components/Brand";
import { Arrow, Panel, cx } from "@/components/ui";

export const metadata: Metadata = { title: "Lift-off · How we built it" };

// The iteration log, newest last. Mirrors EXPERIMENTS.md; numbers are held-out operating-direction accuracy.
const STEPS: { id: string; title: string; did: string; result: string; tone: "win" | "lesson" | "honest" }[] = [
  {
    id: "E1",
    title: "Check the rules against reality",
    did: "Ran FraAlliance's official rules on the measured airport wind and compared them with the directions actually flown (DFLD records).",
    result: "They agree in only 89.2% of hours. The rules are a baseline, not the truth, so we learn from what was flown.",
    tone: "lesson",
  },
  {
    id: "E2",
    title: "First gradient-boosted model",
    did: "Trees on the direction at issue time, measured wind, forecast wind as issued, and the rules run forward.",
    result: "Strong at 6 to 48 h, but it lost at 1 h (93.8% vs 96.9% for keep-current).",
    tone: "lesson",
  },
  {
    id: "E3",
    title: "Blend with keep-current at short leads",
    did: "Per lead time, mix the model with persistence. Weights are picked on past data only.",
    result: "1 h fixed: 97.0%.",
    tone: "win",
  },
  {
    id: "E4",
    title: "Close a leak",
    did: "Forecast runs only count as known 6 h after they start. That uses day-1 forecasts up to 18 h, then day 2 and day 3.",
    result: "48 h dropped from 89.8% to 84.1%. The lower number is the honest one.",
    tone: "honest",
  },
  {
    id: "E5",
    title: "Same path as the jury",
    did: "Compared the command the jury runs with the training pipeline, hour by hour.",
    result: "144 of 144 lead rows identical: features and probabilities.",
    tone: "honest",
  },
  {
    id: "E6",
    title: "Forecast like the jury days",
    did: "Issued every October day at local midnight and scored against what was flown.",
    result: "Beat the rules at every lead, but lost to keep-current at 1 to 6 h on calm nights.",
    tone: "lesson",
  },
  {
    id: "E7",
    title: "Three times more history",
    did: "Extended recorded directions and METAR back to 2018 (76,588 labelled hours).",
    result: "About three times as many direction changes to learn from.",
    tone: "win",
  },
  {
    id: "E8",
    title: "Reject a tempting label",
    did: "Tested DFLD's runway-18 'not in use' row as a weather-closure label.",
    result: "Only 1 of 2,251 such hours had a 15 kt tailwind. It reflects operations, not weather, so it was rejected.",
    tone: "honest",
  },
  {
    id: "E9",
    title: "Night and calm regimes",
    did: "Blend weights per lead and regime (night, calm, active), chosen on inner validation data.",
    result: "Midnight issues at 1 to 6 h: 95.9% vs 94.6% keep-current (stuck feed excluded).",
    tone: "win",
  },
  {
    id: "E10",
    title: "Stronger weather inputs",
    did: "ECMWF, GFS and ICON separately, wind corrected to the airport sensor, per-runway tailwinds, model spread, pressure differences about 200 km around FRA.",
    result: "On 12 test months, 48 h rose from 84.9% to 89.2%, and the Brier score improved by 24%.",
    tone: "win",
  },
  {
    id: "E11",
    title: "Tried, no gain",
    did: "Deeper trees, monotonic constraints, one model per lead, extra observation features.",
    result: "No improvement, so they were dropped. Kept simple.",
    tone: "lesson",
  },
  {
    id: "E12",
    title: "Data quality catch",
    did: "Spotted 103 h of recorded 07 against steady 8 to 17 kt westerlies (8 to 12 Oct). DWD station data confirms the wind.",
    result: "A stuck feed. Scores are reported with and without it.",
    tone: "honest",
  },
];

const PIPELINE = [
  ["Sources", "Recorded directions (DFLD), airport METAR, three weather models as issued"],
  ["Labels", "What was flown; runway 18 inferred from the official 15 kt rule"],
  ["Features", "Only what was known at issue time, plus the rules as a state machine"],
  ["Model", "Gradient-boosted trees, one for the direction, one for runway 18"],
  ["Blend", "Keep-current at short leads by regime, weights from past data"],
  ["Forecast", "48 hourly probabilities, certainty, next change"],
];

// 12 monthly walk-forward folds: train on everything before the month, test on the month.
const FOLDS = ["Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct"];

export default function Approach() {
  return (
    <div className="mx-auto flex min-h-screen w-full max-w-[1200px] flex-col gap-3 px-4 pb-10 sm:px-5">
      <header className="flex min-h-[72px] flex-wrap items-center gap-3 py-3">
        <Brand subtitle="How we built the forecast" />
        <nav className="ml-auto">
          <Link href="/" className="pill-btn bg-accent text-accent-ink [--btn-ring:var(--accent)]">
            Open the forecast <Arrow />
          </Link>
        </nav>
      </header>

      <Panel title="The idea">
        <p className="max-w-3xl text-[17px] leading-relaxed">
          Learn from the directions Frankfurt <b>actually flew</b>, using only what a forecaster could have known at the time,
          and beat FraAlliance&apos;s own rules. Every step below was tested on months the model never saw.
        </p>
      </Panel>

      <Panel title="Pipeline">
        <ol className="grid gap-2 sm:grid-cols-3 lg:grid-cols-6">
          {PIPELINE.map(([name, text], i) => (
            <li key={name} className="rounded-xl bg-panel-2 p-3">
              <div className="text-xs font-semibold text-muted">{i + 1}</div>
              <div className="text-[15px] font-semibold">{name}</div>
              <div className="mt-1 text-xs leading-snug text-ink-2">{text}</div>
            </li>
          ))}
        </ol>
      </Panel>

      <Panel title="How we iterated">
        <ol className="space-y-2">
          {STEPS.map((s) => (
            <li key={s.id} className="grid gap-x-4 gap-y-1 rounded-xl border border-line p-3 sm:grid-cols-[56px_1fr_1fr]">
              <span
                className={cx(
                  "h-fit w-fit rounded-full px-2 py-0.5 text-xs font-semibold",
                  s.tone === "win" && "bg-ok-soft text-ok",
                  s.tone === "lesson" && "bg-select text-ink",
                  s.tone === "honest" && "bg-east-soft text-east",
                )}
              >
                {s.id}
              </span>
              <div>
                <div className="text-[15px] font-semibold">{s.title}</div>
                <div className="text-sm text-ink-2">{s.did}</div>
              </div>
              <div className="text-sm">{s.result}</div>
            </li>
          ))}
        </ol>
        <div className="mt-3 flex flex-wrap gap-3 text-xs text-muted">
          <span>
            <span className="mr-1 inline-block size-2 rounded-full bg-ok" />
            improved the model
          </span>
          <span>
            <span className="mr-1 inline-block size-2 rounded-full bg-accent" />
            taught us something
          </span>
          <span>
            <span className="mr-1 inline-block size-2 rounded-full bg-east" />
            kept us honest
          </span>
        </div>
      </Panel>

      <Panel title="How we validated">
        <div className="grid gap-5 lg:grid-cols-[3fr_2fr]">
          <div>
            <div className="mb-2 text-sm font-semibold">Walk-forward: 12 monthly folds, Nov 2025 to Oct 2026</div>
            <div className="space-y-1">
              {FOLDS.map((m, i) => (
                <div key={m} className="grid grid-cols-[40px_1fr] items-center gap-2 text-xs">
                  <span className="text-muted">{m}</span>
                  <div className="flex h-3 gap-px">
                    <div className="rounded-l bg-west-soft" style={{ width: `${40 + i * 4.5}%` }} />
                    <div className="rounded-r bg-accent" style={{ width: "4.5%" }} />
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-2 text-xs text-muted">
              Pale: training data before the month (from 2018 for observations, 2024 for archived forecasts). Dark: the
              month being tested.
            </div>
          </div>
          <ul className="space-y-2 text-sm">
            <li>
              <b>No hindsight:</b> forecasts are used as published, 6 h after each run starts, and the labels only once the
              hour is over.
            </li>
            <li>
              <b>No random cross-validation:</b> time only moves forward.
            </li>
            <li>
              <b>Two baselines:</b> FraAlliance&apos;s official rules, and keeping the current direction.
            </li>
            <li>
              <b>Uncertainty:</b> 95% confidence intervals by resampling whole days. McNemar test on accuracy,
              Diebold-Mariano on Brier.
            </li>
            <li>
              <b>Honest probabilities:</b> a reliability check that stated chances match observed frequencies.
            </li>
            <li>
              <b>Same code path:</b> the jury command reproduces the backtest exactly.
            </li>
          </ul>
        </div>
      </Panel>

      <p className="text-xs text-muted">
        Full log with every number: EXPERIMENTS.md · one-page summary: MODEL_CARD.md · live held-out quality: the panel at
        the bottom of the forecast page.
      </p>
    </div>
  );
}
