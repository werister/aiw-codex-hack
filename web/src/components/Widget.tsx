"use client";

import Link from "next/link";
import { Brand } from "./Brand";
import { useState } from "react";
import { useForecast } from "./ForecastApp";
import { Hero } from "./Hero";
import { RunwayMap } from "./RunwayMap";
import { ThemeToggle } from "./ThemeToggle";
import { Timeline } from "./Timeline";
import { Arrow, Panel, hhmm } from "./ui";

// iPad widget for ops staff and pilots: now, next, and the 48 h strip.
export function Widget() {
  const { f } = useForecast();
  const [sel, setSel] = useState(0);
  if (!f) return null;
  return (
    <div className="mx-auto flex min-h-screen w-full max-w-[1180px] flex-col gap-2.5 px-4 pb-5 sm:px-5">
      <header className="flex h-[56px] items-center gap-3">
        <Brand subtitle="Frankfurt" />
        <nav className="ml-auto flex items-center gap-2">
          <ThemeToggle />
          <Link href="/" className="pill-btn bg-accent text-accent-ink [--btn-ring:var(--accent)]">
            Full view <Arrow />
          </Link>
        </nav>
      </header>
      <Hero
        f={f}
        compact
        scene={
          <RunwayMap
            od={f.hours[0].od}
            r18Open={f.hours[0].p_18_usable >= 0.5}
            windDir={f.hours[0].wind_dir_deg}
            windKt={f.hours[0].wind_kt}
            label={`Forecast for ${hhmm(f.hours[0].local)} (+1 h)`}
          />
        }
      />
      <Panel title="Next 48 hours">
        <Timeline f={f} selected={sel} onSelect={setSel} rows={["od", "unsure", "r18", "conf"]} />
      </Panel>
    </div>
  );
}
