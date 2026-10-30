"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import type { ForecastResponse } from "@/lib/forecast-types";
import { HourDetail } from "./HourDetail";
import { NowPanel } from "./NowPanel";
import { QualityPanel } from "./QualityPanel";
import { RunwayMap } from "./RunwayMap";
import { Timeline } from "./Timeline";
import { Panel, cx, dayLabel, hhmm } from "./ui";

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
  const h = f?.hours[Math.min(sel, (f?.hours.length ?? 1) - 1)];
  const hits = useMemo(() => {
    if (!f?.observed?.length) return null;
    const byTime = new Map(f.hours.map((x) => [x.time, x.od]));
    const scored = f.observed.filter((o) => byTime.has(o.time));
    const ok = scored.filter((o) => byTime.get(o.time) === o.od).length;
    return scored.length ? { ok, n: scored.length } : null;
  }, [f]);

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-[1400px] flex-col gap-4 px-4 py-4 sm:px-6">
      <header className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <div>
          <h1 className="text-lg font-bold tracking-tight">Runway Outlook · Frankfurt</h1>
          <div className="text-xs text-muted">Operating direction and runway 18, hour by hour, 48 h ahead</div>
        </div>
        <div className="ml-auto flex flex-wrap items-center gap-2 text-xs">
          {f && (
            <span
              className={cx(
                "rounded-full px-2.5 py-1 font-semibold",
                f.mode === "live" ? "bg-ok-soft text-ok" : "bg-panel-2 text-ink-2",
              )}
            >
              {f.mode === "live" ? "LIVE" : "HINDCAST"} · issued {dayLabel(f.issued_local)} {hhmm(f.issued_local)}
            </span>
          )}
          <select
            value={file ?? ""}
            onChange={(e) => {
              setFile(e.target.value);
              setSel(0);
            }}
            className="rounded-lg border border-line bg-panel px-2 py-1.5 text-ink"
            aria-label="Forecast day"
          >
            {options.map((o) => (
              <option key={o.file} value={o.file}>
                {o.label}
              </option>
            ))}
          </select>
          <Link href="/pitch" className="rounded-lg border border-line px-2.5 py-1.5 text-ink-2 hover:text-ink">
            Pitch mode
          </Link>
          <Link href="/widget" className="rounded-lg border border-line px-2.5 py-1.5 text-ink-2 hover:text-ink">
            iPad widget
          </Link>
        </div>
      </header>

      {error && <p className="rounded-lg bg-bad-soft px-3 py-2 text-sm text-bad">This forecast file could not be loaded.</p>}

      {f && h && (
        <>
          <NowPanel f={f} />

          <Panel
            title="Next 48 hours"
            aside={
              <span className="text-xs text-muted">
                {hits ? `Flown vs forecast: ${hits.ok}/${hits.n} hours right · ` : ""}click an hour for details
              </span>
            }
          >
            <Timeline f={f} selected={sel} onSelect={setSel} />
          </Panel>

          <div className="grid gap-4 lg:grid-cols-[3fr_2fr]">
            <Panel title={`Ops view at ${dayLabel(h.local)} ${hhmm(h.local)}`}>
              <RunwayMap
                od={h.od}
                r18Open={h.p_18_usable >= 0.5}
                windDir={h.wind_dir_deg}
                windKt={h.wind_kt}
                label={`Forecast for +${h.lead_h} h · confidence ${h.certainty}%`}
              />
            </Panel>
            <HourDetail h={h} />
          </div>

          <QualityPanel />

          <footer className="pb-4 text-[11px] leading-relaxed text-muted">
            Model {f.model_version} · rules {f.rules_version} · weather {f.nwp}. Sources: recorded operating directions from
            DFLD.de, EDDF METAR from the Iowa Environmental Mesonet, weather-model forecasts from Open-Meteo, DWD Open Data.
            Rules from the FraAlliance challenge brief. The ops view is a schematic simulation.
          </footer>
        </>
      )}
    </div>
  );
}
