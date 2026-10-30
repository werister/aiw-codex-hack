"use client";

import Link from "next/link";
import { useState } from "react";
import { useForecast } from "./ForecastApp";
import { NowPanel } from "./NowPanel";
import { Timeline } from "./Timeline";
import { dayLabel, hhmm } from "./ui";

// iPad widget for ops staff and pilots: the three answers and a two-row timeline.
export function Widget() {
  const { f } = useForecast();
  const [sel, setSel] = useState(0);
  if (!f) return null;
  return (
    <div className="mx-auto flex min-h-screen max-w-[1180px] flex-col gap-4 p-5">
      <div className="flex items-baseline justify-between">
        <h1 className="text-xl font-bold">FRA Runway Outlook</h1>
        <span className="text-sm text-muted">
          issued {dayLabel(f.issued_local)} {hhmm(f.issued_local)} ·{" "}
          <Link href="/" className="underline">
            full view
          </Link>
        </span>
      </div>
      <NowPanel f={f} compact />
      <div className="rounded-xl border border-line bg-panel p-4">
        <Timeline f={f} selected={sel} onSelect={setSel} rows={["od", "r18", "conf"]} />
      </div>
    </div>
  );
}
