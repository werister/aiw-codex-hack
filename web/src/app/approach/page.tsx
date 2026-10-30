import type { Metadata } from "next";
import Link from "next/link";
import { Brand } from "@/components/Brand";
import { Arrow, Panel, cx } from "@/components/ui";

export const metadata: Metadata = { title: "Lift-off · How we built it" };

// Experiment results in chronological order. Accuracy values are for recorded operating direction.
const STEPS: { id: string; title: string; did: string; result: string; tone: "win" | "lesson" | "honest" }[] = [
  {
    id: "E1",
    title: "Compare rules with recorded directions",
    did: "Applied FraAlliance's rules to measured airport wind and compared the result with DFLD direction records.",
    result: "The rules matched 89.2% of recorded hours.",
    tone: "lesson",
  },
  {
    id: "E2",
    title: "First model",
    did: "Trees on the direction at issue time, measured wind, forecast wind as issued, and the rules run forward.",
    result: "At 1 h, accuracy was 93.8%, below persistence at 96.9%.",
    tone: "lesson",
  },
  {
    id: "E3",
    title: "Add persistence at short leads",
    did: "Per lead time, mix the model with persistence. Weights are picked on past data only.",
    result: "1 h accuracy rose to 96.9%; other leads were unchanged.",
    tone: "win",
  },
  {
    id: "E4",
    title: "Apply the publication delay",
    did: "Used each forecast run only after its six-hour publication delay: day 1 through 18 h, then days 2 and 3.",
    result: "48 h accuracy fell from 89.8% to 84.1%.",
    tone: "honest",
  },
  {
    id: "E5",
    title: "Compare forecast and training paths",
    did: "Compared the command the jury runs with the training pipeline, hour by hour.",
    result: "Features and probabilities matched on all 144 tested lead rows.",
    tone: "honest",
  },
  {
    id: "E6",
    title: "Test October midnight forecasts",
    did: "Issued forecasts at local midnight for each October day and compared them with DFLD records.",
    result: "The model beat the rules. Persistence scored higher at 1–6 h on calm nights.",
    tone: "lesson",
  },
  {
    id: "E7",
    title: "Extend history to 2018",
    did: "Added recorded directions and METAR data, for 76,588 labelled hours.",
    result: "The dataset contains about three times as many direction changes.",
    tone: "win",
  },
  {
    id: "E8",
    title: "Reject a non-weather label",
    did: "Tested DFLD's runway-18 'not in use' row as a weather-closure label.",
    result: "Only 1 of 2,251 hours had a 15 kt tailwind. The label reflects operations, so it was not used as weather ground truth.",
    tone: "honest",
  },
  {
    id: "E9",
    title: "Blend by time and wind regime",
    did: "Selected blend weights by lead and regime using earlier validation data.",
    result: "At midnight, 1–6 h accuracy was 95.9% vs 94.6% for persistence, excluding the stuck feed.",
    tone: "win",
  },
  {
    id: "E10",
    title: "Add separate weather models",
    did: "Added ECMWF, GFS and ICON forecasts, runway-specific tailwinds, model spread and pressure differences around Frankfurt. Wind speeds were scaled to the airport sensor.",
    result: "Across the same 12 test months, 48 h accuracy rose from 84.9% to 88.6%; Brier score fell from 0.108 to 0.084.",
    tone: "win",
  },
  {
    id: "E11",
    title: "Test alternative models",
    did: "Tested deeper trees, monotonic constraints, one model per lead and extra observations.",
    result: "None improved the scores, so they were not used.",
    tone: "lesson",
  },
  {
    id: "E12",
    title: "Find a stuck direction feed",
    did: "Found 103 h of recorded OD 07 during steady 8–17 kt westerlies, 8–12 Oct. DWD station data confirms the wind.",
    result: "Scores are reported with and without these hours.",
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

      <Panel title="Data and method">
        <p className="max-w-3xl text-[17px] leading-relaxed">
          The model uses recorded directions and archived weather forecasts. Results are compared with FraAlliance&apos;s rules and persistence on held-out months.
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

      <Panel title="Experiments">
        <ol className="space-y-2">
          {STEPS.map((s) => (
            <li key={s.id} className="grid gap-x-4 gap-y-1 rounded-xl border border-line p-3 sm:grid-cols-[56px_1fr_1fr]">
              <span
                className={cx(
                  "h-fit w-fit rounded-full px-2 py-0.5 text-xs font-semibold",
                  s.tone === "win" && "bg-select text-ink",
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
            model changes
          </span>
          <span>
            <span className="mr-1 inline-block size-2 rounded-full bg-accent" />
            comparisons
          </span>
          <span>
            <span className="mr-1 inline-block size-2 rounded-full bg-east" />
            data and validation checks
          </span>
        </div>
      </Panel>

      <Panel title="Validation">
        <div className="grid gap-5 lg:grid-cols-[3fr_2fr]">
          <div>
            <div className="mb-2 text-sm font-semibold">Walk-forward · 12 months, Nov 2025–Oct 2026</div>
            <p className="text-sm text-ink-2">
              Each test month uses a model trained on earlier data. Training expands as time advances.
              Observations begin in 2018; archived forecasts begin in 2024.
            </p>
          </div>
          <ul className="space-y-2 text-sm">
            <li>
              Forecasts enter after the six-hour publication delay; labels enter after the hour ends.
            </li>
            <li>
              Training and test data are split in time order.
            </li>
            <li>
              Baselines: FraAlliance&apos;s rules and persistence.
            </li>
            <li>
              Confidence intervals resample whole days (95%). Accuracy uses McNemar&apos;s test; Brier scores use Diebold–Mariano.
            </li>
            <li>
              Reliability compares stated probabilities with observed frequencies.
            </li>
            <li>
              The jury command matched the training path in the 144-row check above.
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
