"use client";

import Link from "next/link";
import { BrandLogo } from "./BrandLogo";
import { useState } from "react";
import { useForecast } from "./ForecastApp";
import { Hero } from "./Hero";
import { utcOffset } from "./Provenance";
import { RunwayMap } from "./RunwayMap";
import { SceneHero } from "./SceneHero";
import { ThemeToggle } from "./ThemeToggle";
import { Timeline } from "./Timeline";
import { TimeScrubber } from "./TimeScrubber";
import { Arrow, Panel, dayLabel, hhmm } from "./ui";

// iPad widget for ops staff and pilots: now, next, and the 48 h strip.
export function Widget() {
  const { f, loading, error, retry } = useForecast();
  const [sel, setSel] = useState(0);
  const h = f?.hours[Math.min(sel, f.hours.length - 1)];
  return (
    <div className="mx-auto flex min-h-screen w-full max-w-[1180px] flex-col gap-2.5 px-4 pb-5 sm:px-5">
      <header className="flex min-h-[56px] flex-wrap items-center gap-3 py-2">
        <div className="flex min-w-0 items-center gap-3">
          <h1 className="shrink-0"><BrandLogo /><span className="sr-only"> · Runway Outlook</span></h1>
        </div>
        <nav className="ml-auto flex items-center gap-2">
          <ThemeToggle />
          <Link href="/" className="pill-btn bg-accent text-accent-ink [--btn-ring:var(--accent)]">
            Full view <Arrow />
          </Link>
        </nav>
      </header>
      {loading && <p role="status" className="py-8 text-muted">Loading forecast…</p>}
      {error && (
        <div role="alert" className="flex flex-wrap items-center gap-4 py-8">
          <p>This forecast could not be loaded.</p>
          <button type="button" onClick={retry} className="pill-btn bg-accent text-accent-ink">Try again</button>
        </div>
      )}
      {f && !f.hours.length && <p role="status" className="py-8 text-muted">This forecast has no hourly data. Open the full view to choose another day.</p>}
      {f && h && <>
      <Hero
        f={f}
        compact
        onSelectHour={(index) => {
          setSel(index);
          document.getElementById("timeline")?.scrollIntoView({ block: "start" });
        }}
        scene={
          <div>
          <SceneHero
            od={h.od}
            forecastHour={h}
            r18Open={h.p_18_usable >= 0.5}
            wind={h.wind_dir_deg == null ? undefined : { dir: h.wind_dir_deg, kt: h.wind_kt }}
            className="h-[330px]"
            fallback={
              <RunwayMap
                od={h.od}
                r18Open={h.p_18_usable >= 0.5}
                windDir={h.wind_dir_deg}
                windKt={h.wind_kt}
                label={`Selected forecast: ${dayLabel(h.local)} ${hhmm(h.local)} (+${h.lead_h} h)`}
              />
            }
          />
          <p className="px-2 py-2 text-[13px] text-muted">
            Selected forecast · {dayLabel(h.local)} {hhmm(h.local)} {utcOffset(h.time, h.local)} · +{h.lead_h} h
          </p>
          </div>
        }
      />
      <section id="timeline" className="scroll-mt-4">
      <Panel title={`Forecast · ${f.hours.length} hourly entries`}>
        <TimeScrubber f={f} selected={sel} onSelect={setSel} />
        <Timeline f={f} selected={sel} onSelect={setSel} rows={["od", "unsure", "r18", "conf"]} />
      </Panel>
      </section>
      </>}
    </div>
  );
}
