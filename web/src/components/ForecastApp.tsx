"use client";

import Link from "next/link";
import { Brand } from "./Brand";
import { useEffect, useMemo, useRef, useState } from "react";
import type { ForecastResponse } from "@/lib/forecast-types";
import { EvidenceChain } from "./EvidenceChain";
import { HourDetail } from "./HourDetail";
import { ForecastAssistant } from "./ForecastAssistant";
import { Hero } from "./Hero";
import { Numbers } from "./Numbers";
import { QualityPanel } from "./QualityPanel";
import { planFrom } from "./Recommendation";
import { RunwayMap } from "./RunwayMap";
import { SceneHero } from "./SceneHero";
import { Timeline } from "./Timeline";
import { TimeScrubber } from "./TimeScrubber";
import { ThemeToggle } from "./ThemeToggle";
import { Arrow, Panel, dayLabel, hhmm } from "./ui";

type Option = { label: string; file: string };

// Forecast files come from the CLI: `python -m ml.forecast --day ... --json --out web/public/forecasts/<day>.json`.
export async function loadOptions(): Promise<Option[]> {
  try {
    const r = await fetch("/forecasts/index.json", { cache: "no-store" });
    if (!r.ok) throw new Error();
    const idx: { latest?: string; days?: string[] } = await r.json();
    const opts: Option[] = [];
    if (idx.latest) opts.push({ label: "Live · next 48 h", file: idx.latest });
    for (const d of idx.days ?? []) opts.push({ label: `${dayLabel(d + "T00:00")} (hindcast)`, file: `${d}.json` });
    if (opts.length) return opts;
  } catch {}
  return [{ label: "Sample forecast", file: "sample.json" }];
}

export function useForecast() {
  const [options, setOptions] = useState<Option[]>([]);
  const [file, setFile] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [result, setResult] = useState<{ key: string; forecast?: ForecastResponse; error?: true } | null>(null);
  const requestKey = `${file}:${attempt}`;

  useEffect(() => {
    loadOptions().then((opts) => {
      // ?day=YYYY-MM-DD opens that forecast file even if it isn't in the index yet.
      const want = new URLSearchParams(window.location.search).get("day");
      const hit = want ? opts.find((o) => o.file.startsWith(want)) : undefined;
      if (want && !hit) opts = [...opts, { label: want, file: `${want}.json` }];
      setOptions(opts);
      setFile(hit?.file ?? (want ? `${want}.json` : opts[0].file));
    });
  }, []);

  useEffect(() => {
    if (!file) return;
    const controller = new AbortController();
    fetch(`/forecasts/${file}`, { cache: "no-store", signal: controller.signal })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: ForecastResponse) => {
        if (!Array.isArray(d.hours)) throw new Error("Missing forecast hours");
        if (!controller.signal.aborted) setResult({ key: requestKey, forecast: d });
      })
      .catch(() => {
        if (!controller.signal.aborted) setResult({ key: requestKey, error: true });
      });
    return () => controller.abort();
  }, [file, requestKey]);

  const current = result?.key === requestKey ? result : null;
  return {
    options, file, setFile,
    f: current?.forecast ?? null,
    error: current?.error ?? false,
    loading: current === null,
    retry: () => setAttempt((value) => value + 1),
  };
}

export function ForecastApp() {
  const { options, file, setFile, f, error, loading, retry } = useForecast();
  const [sel, setSel] = useState(0);
  const [evidenceOpen, setEvidenceOpen] = useState(false);
  const evidenceRef = useRef<HTMLDivElement>(null);
  const h = f?.hours[Math.min(sel, (f?.hours.length ?? 1) - 1)];
  const hits = useMemo(() => {
    if (!f?.observed?.length) return null;
    const byTime = new Map(f.hours.map((x) => [x.time, x.od]));
    const scored = f.observed.filter((o) => byTime.has(o.time));
    const ok = scored.filter((o) => byTime.get(o.time) === o.od).length;
    return scored.length ? { ok, n: scored.length } : null;
  }, [f]);

  const toPlanHour = () => {
    if (!f) return;
    const i = f.hours.findIndex((x) => x.time === planFrom(f).time);
    setSel(Math.max(0, i));
  };

  return (
    <div className="mx-auto flex min-h-screen w-full min-w-0 max-w-[1440px] flex-col overflow-x-clip px-4 pb-8 sm:px-6">
      <header className="flex flex-wrap items-center gap-3 py-4">
        <Brand subtitle="Frankfurt runway direction" />
        <nav className="ml-auto flex flex-wrap items-center gap-2">
          <label className="relative">
            <span className="sr-only">Forecast day</span>
            <select
              value={file ?? ""}
              onChange={(e) => {
                setFile(e.target.value);
                setSel(0);
              }}
              className="appearance-none rounded-full border border-line bg-panel py-2 pl-4 pr-9 text-[15px] text-ink"
            >
              {options.map((o) => (
                <option key={o.file} value={o.file}>
                  {o.label}
                </option>
              ))}
            </select>
            <svg viewBox="0 0 12 8" className="pointer-events-none absolute right-3.5 top-1/2 h-2 w-3 -translate-y-1/2" fill="none" aria-hidden>
              <path d="m1 1.5 5 5 5-5" stroke="currentColor" />
            </svg>
          </label>
          <ThemeToggle />
          <Link href="/pitch" className="pill-btn border border-line">
            Pitch mode
          </Link>
          <Link href="/approach" className="pill-btn hidden border border-line text-ink [--btn-ring:var(--line)] md:inline-flex">
            How we built it
          </Link>
          <Link href="/widget" className="pill-btn hidden bg-accent text-accent-ink [--btn-ring:var(--accent)] sm:inline-flex">
            iPad <Arrow />
          </Link>
        </nav>
      </header>

      {loading && <p role="status" className="py-8 text-[15px] text-muted">Loading forecast…</p>}
      {error && (
        <div role="alert" className="flex flex-wrap items-center gap-4 rounded-card border border-line bg-panel-2 px-4 py-3 text-[15px]">
          <p>This forecast could not be loaded. Try again or choose another day.</p>
          <button type="button" onClick={retry} className="pill-btn bg-accent text-accent-ink">Try again</button>
        </div>
      )}
      {f && !h && <p role="status" className="py-8 text-[15px] text-muted">This forecast has no hourly data. Choose another day.</p>}

      {f && h && (
        <>
          <Hero
            f={f}
            scene={
              <SceneHero
                od={f.hours[0].od}
                r18Open={f.hours[0].p_18_usable >= 0.5}
                wind={f.hours[0].wind_dir_deg == null ? undefined : { dir: f.hours[0].wind_dir_deg, kt: f.hours[0].wind_kt }}
                className="h-[340px] sm:h-[460px]"
                fallback={
                  <RunwayMap
                    od={f.hours[0].od}
                    r18Open={f.hours[0].p_18_usable >= 0.5}
                    windDir={f.hours[0].wind_dir_deg}
                    windKt={f.hours[0].wind_kt}
                    label={`Forecast for ${hhmm(f.hours[0].local)} (+1 h)`}
                  />
                }
              />
            }
            onEvidence={() => {
              toPlanHour();
              setEvidenceOpen(true);
              evidenceRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
            }}
          />

          <Numbers />

          <div className="flex flex-col gap-2.5">
            <section id="timeline" className="scroll-mt-4">
              <Panel
                title="Next 48 hours"
                aside={
                  <span className="text-[13px] text-muted">
                    {hits ? `${hits.ok} of ${hits.n} recorded hours match · ` : ""}tap an hour
                  </span>
                }
              >
                <TimeScrubber f={f} selected={sel} onSelect={setSel} />
                <Timeline f={f} selected={sel} onSelect={setSel} />
              </Panel>
            </section>

            <HourDetail h={h} />

            <div ref={evidenceRef} className="scroll-mt-4">
              <EvidenceChain
                f={f}
                h={h}
                open={evidenceOpen}
                onToggle={() => setEvidenceOpen((o) => !o)}
                onReturn={toPlanHour}
              />
            </div>

            <ForecastAssistant key={`${file}:${f.issued_at}:${h.time}`} f={f} h={h} />
            <QualityPanel />
          </div>

          <footer className="mt-10 grid gap-4 border-t border-line pt-6 text-[13px] leading-relaxed text-muted md:grid-cols-[1fr_2fr]">
            <div className="tabular">
              Model {f.model_version}
              <br />
              Rules {f.rules_version}
              {f.evidence && (
                <>
                  <br />
                  Run {f.evidence.run_id}
                </>
              )}
            </div>
            <p>
              Data: recorded operating directions from DFLD.de, EDDF METAR from the Iowa Environmental Mesonet, weather-model
              forecasts from Open-Meteo, DWD Open Data. Rules from the FraAlliance challenge brief. The runway view is a
              schematic simulation.
            </p>
          </footer>
        </>
      )}
    </div>
  );
}
