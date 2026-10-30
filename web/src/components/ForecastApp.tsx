"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import type { ForecastResponse } from "@/lib/forecast-types";
import { EvidenceChain } from "./EvidenceChain";
import { HourDetail } from "./HourDetail";
import { NowPanel } from "./NowPanel";
import { Provenance } from "./Provenance";
import { QualityPanel } from "./QualityPanel";
import { Recommendation, planFrom } from "./Recommendation";
import { RunwayMap } from "./RunwayMap";
import { Timeline } from "./Timeline";
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
  return [{ label: "Live sample (rules only)", file: "sample.json" }];
}

export function useForecast() {
  const [options, setOptions] = useState<Option[]>([]);
  const [file, setFile] = useState<string | null>(null);
  const [f, setF] = useState<ForecastResponse | null>(null);
  const [error, setError] = useState(false);

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
    fetch(`/forecasts/${file}`, { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: ForecastResponse) => {
        setF(d);
        setError(false);
      })
      .catch(() => setError(true));
  }, [file]);

  return { options, file, setFile, f, error };
}

export function ForecastApp() {
  const { options, file, setFile, f, error } = useForecast();
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

  return (
    <div className="mx-auto flex min-h-screen w-full min-w-0 max-w-[1440px] flex-col gap-2.5 overflow-x-clip px-4 pb-8 sm:px-5">
      <header className="flex h-[72px] items-center gap-3">
        <div className="flex min-w-0 items-baseline gap-3">
          <h1 className="text-[19px] font-medium tracking-tight">Runway Outlook</h1>
          <span className="hidden truncate text-[15px] text-muted sm:inline">FraAlliance · Frankfurt Airport</span>
        </div>
        <nav className="ml-auto flex items-center gap-2">
          <ThemeToggle />
          <Link href="/widget" className="pill-btn bg-accent text-accent-ink [--btn-ring:var(--accent)]">
            iPad widget <Arrow />
          </Link>
        </nav>
      </header>

      <section className="flex flex-wrap items-center justify-between gap-x-8 gap-y-3 pb-3" aria-label="Forecast provenance">
        {f ? <Provenance f={f} /> : <span />}
        <div className="flex flex-wrap items-center gap-2">
          <label className="relative">
            <span className="sr-only">Forecast day</span>
            <select
              value={file ?? ""}
              onChange={(e) => {
                setFile(e.target.value);
                setSel(0);
              }}
              className="appearance-none rounded-[8px] border-[0.5px] border-ink bg-panel py-2 pl-4 pr-10 text-[15px] text-ink"
            >
              {options.map((o) => (
                <option key={o.file} value={o.file}>
                  {o.label}
                </option>
              ))}
            </select>
            <svg viewBox="0 0 12 8" className="pointer-events-none absolute right-4 top-1/2 h-2 w-3 -translate-y-1/2" fill="none" aria-hidden>
              <path d="m1 1.5 5 5 5-5" stroke="currentColor" />
            </svg>
          </label>
        </div>
      </section>

      {error && (
        <p className="rounded-card border border-line bg-panel-2 px-4 py-3 text-[15px]">
          Forecast unavailable: this day&apos;s file could not be loaded. Pick another day or reload the page.
        </p>
      )}

      {f && h && (
        <>
          <Recommendation
            f={f}
            onShowEvidence={() => {
              const i = f.hours.findIndex((x) => x.time === planFrom(f).time);
              setSel(Math.max(0, i));
              setEvidenceOpen(true);
              evidenceRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
            }}
          />

          <NowPanel f={f} />

          <Panel
            title="Next 48 hours"
            aside={
              <span className="text-[13px] text-muted">
                {hits ? `Recorded vs forecast: ${hits.ok} of ${hits.n} recorded hours match · ` : ""}select an hour for details
              </span>
            }
          >
            <Timeline f={f} selected={sel} onSelect={setSel} />
          </Panel>

          <div ref={evidenceRef} className="scroll-mt-4">
            <EvidenceChain f={f} h={h} open={evidenceOpen} onToggle={() => setEvidenceOpen((o) => !o)} />
          </div>

          <div className="grid gap-2.5 lg:grid-cols-[3fr_2fr]">
            <Panel title={`Ops view · simulation · ${dayLabel(h.local)} ${hhmm(h.local)}`}>
              <RunwayMap
                od={h.od}
                r18Open={h.p_18_usable >= 0.5}
                windDir={h.wind_dir_deg}
                windKt={h.wind_kt}
                label={`Forecast for +${h.lead_h} h · certainty score ${h.certainty}/100`}
              />
            </Panel>
            <HourDetail h={h} />
          </div>

          <QualityPanel />

          <footer className="mt-8 grid gap-4 border-t border-line pt-6 text-[13px] leading-relaxed text-muted md:grid-cols-[1fr_2fr]">
            <div className="tabular">
              Model {f.model_version}
              <br />
              Rules {f.rules_version}
              <br />
              Weather {f.nwp}
            </div>
            <p>
              Sources: recorded operating directions from DFLD.de, EDDF METAR from the Iowa Environmental Mesonet, weather-model
              forecasts from Open-Meteo, DWD Open Data. Rules from the FraAlliance challenge brief. The ops view is a schematic
              simulation.
            </p>
          </footer>
        </>
      )}
    </div>
  );
}
