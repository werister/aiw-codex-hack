"use client";

import Link from "next/link";
import { useState } from "react";
import { useForecast } from "./ForecastApp";
import { NowPanel } from "./NowPanel";
import { ThemeToggle } from "./ThemeToggle";
import { Timeline } from "./Timeline";
import { Arrow, Panel, dayLabel, hhmm } from "./ui";

// iPad widget for ops staff and pilots: the three answers and a two-row timeline.
export function Widget() {
  const { f } = useForecast();
  const [sel, setSel] = useState(0);
  if (!f) return null;
  return (
    <div className="mx-auto flex min-h-screen w-full max-w-[1180px] flex-col gap-2.5 px-4 pb-5 sm:px-5">
      <header className="flex h-[64px] items-center gap-3">
        <div className="flex min-w-0 items-baseline gap-3">
          <h1 className="text-[19px] font-medium tracking-tight">Runway Outlook</h1>
          <span className="truncate text-[15px] text-muted tabular">
            issued {dayLabel(f.issued_local)} {hhmm(f.issued_local)}
          </span>
        </div>
        <nav className="ml-auto flex items-center gap-2">
          <ThemeToggle />
          <Link href="/" className="pill-btn bg-accent text-accent-ink [--btn-ring:var(--accent)]">
            Full view <Arrow />
          </Link>
        </nav>
      </header>
      <NowPanel f={f} compact />
      <Panel title="Next 48 hours">
        <Timeline f={f} selected={sel} onSelect={setSel} rows={["od", "r18", "conf"]} />
      </Panel>
    </div>
  );
}
