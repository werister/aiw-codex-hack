"use client";

import Link from "next/link";
import { BrandLogo } from "./BrandLogo";
import { useState } from "react";
import { useForecast } from "./ForecastApp";
import { Hero } from "./Hero";
import { RunwayMap } from "./RunwayMap";
import { SceneHero } from "./SceneHero";
import { ThemeToggle } from "./ThemeToggle";
import { Timeline } from "./Timeline";
import { TimeScrubber } from "./TimeScrubber";
import { Arrow, Panel, hhmm } from "./ui";

// iPad widget for ops staff and pilots: now, next, and the 48 h strip.
export function Widget() {
  const { f, loading, error, retry } = useForecast();
  const [sel, setSel] = useState(0);
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
      {f && f.hours.length > 0 && <>
      <Hero
        f={f}
        compact
        scene={
          <SceneHero
            od={f.hours[0].od}
            r18Open={f.hours[0].p_18_usable >= 0.5}
            wind={f.hours[0].wind_dir_deg == null ? undefined : { dir: f.hours[0].wind_dir_deg, kt: f.hours[0].wind_kt }}
            className="h-[330px]"
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
      />
      <Panel title="Next 48 hours">
        <TimeScrubber f={f} selected={sel} onSelect={setSel} />
        <Timeline f={f} selected={sel} onSelect={setSel} rows={["od", "unsure", "r18", "conf"]} />
      </Panel>
      </>}
    </div>
  );
}
