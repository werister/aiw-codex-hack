"use client";

import Link from "next/link";
import { Brand } from "./Brand";
import { useState } from "react";
import { useForecast } from "./ForecastApp";
import { NowPanel } from "./NowPanel";
import { Provenance } from "./Provenance";
import { Recommendation } from "./Recommendation";
import { ThemeToggle } from "./ThemeToggle";
import { Timeline } from "./Timeline";
import { Arrow, Panel } from "./ui";

// iPad widget for ops staff and pilots: the three answers and a two-row timeline.
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
      <Provenance f={f} compact />
      <Recommendation f={f} compact />
      <NowPanel f={f} compact />
      <Panel title="Next 48 hours">
        <Timeline f={f} selected={sel} onSelect={setSel} rows={["od", "r18", "conf"]} />
      </Panel>
    </div>
  );
}
