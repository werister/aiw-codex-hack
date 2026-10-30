"use client";

import Link from "next/link";
import { BrandLogo } from "./BrandLogo";
import { useState } from "react";
import { useForecast } from "./ForecastApp";
import { PlainHero } from "./PlainHero";
import { ThemeToggle } from "./ThemeToggle";
import { Arrow } from "./ui";

// iPad widget: the plain first screen with hour selection.
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
      {f && h && <PlainHero f={f} compact selected={sel} onSelectHour={setSel} />}
    </div>
  );
}
