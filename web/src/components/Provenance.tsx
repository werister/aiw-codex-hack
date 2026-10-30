"use client";

import { useSyncExternalStore } from "react";
import type { ForecastResponse } from "@/lib/forecast-types";
import { cx, dayLabel, hhmm } from "./ui";

// Wall clock in whole minutes; null on the server so the first render matches.
function subscribeMinute(cb: () => void) {
  const t = setInterval(cb, 30_000);
  return () => clearInterval(t);
}
const minuteNow = () => Math.floor(Date.now() / 60_000);

export function useNowMs() {
  const m = useSyncExternalStore(subscribeMinute, minuteNow, () => null);
  return m == null ? null : m * 60_000;
}

const utcMs = (iso: string) => Date.parse(iso.endsWith("Z") ? iso : iso + "Z");

// Berlin offset from the pair of stamps the producer writes, e.g. "UTC+1".
export function utcOffset(utcIso: string, local: string) {
  const h = Math.round((Date.parse(local + "Z") - utcMs(utcIso)) / 3_600_000);
  return `UTC${h >= 0 ? "+" : "−"}${Math.abs(h)}`;
}

function ago(ms: number) {
  const min = Math.max(0, Math.round(ms / 60_000));
  if (min < 60) return `${min} min ago`;
  const h = Math.floor(min / 60);
  if (h < 48) return `${h} h ${min % 60} min ago`;
  return `${Math.floor(h / 24)} days ago`;
}

// Where this forecast comes from, above everything it says.
export function Provenance({ f, compact }: { f: ForecastResponse; compact?: boolean }) {
  const now = useNowMs();
  const issued = utcMs(f.issued_at);
  const last = f.hours[f.hours.length - 1];
  const elapsed = now != null && now >= utcMs(last.time) + 3_600_000;
  const fallback = f.model_version === "rules-fallback";

  const items: [string, string][] = [
    ["Issued", `${dayLabel(f.issued_local)} ${hhmm(f.issued_local)} ${utcOffset(f.issued_at, f.issued_local)}`],
    ["Age", now == null ? "–" : ago(now - issued)],
    ["Horizon", elapsed ? "Elapsed" : `to ${dayLabel(last.local)} ${hhmm(last.local)}`],
    ["Rules", f.rules_version],
  ];
  if (!fallback) items.splice(3, 0, ["Model", f.model_version]);

  return (
    <div className={cx("flex flex-wrap items-center gap-x-5 gap-y-2 text-[13px]", compact && "text-[12px]")}>
      <span
        className="eyebrow inline-flex items-center gap-2 rounded-full border border-ink px-3 py-2"
        title={f.mode === "live" ? "Issued from the latest inputs. Not a live ATC or DFS feed." : "A past day, forecast with archived inputs only."}
      >
        <span className={cx("size-2 rounded-full", f.mode === "live" ? "bg-accent" : "border border-ink")} />
        {f.mode === "live" ? "Live forecast" : "Historical forecast"}
      </span>
      {fallback && (
        <span className="eyebrow rounded-full bg-ink px-3 py-2 text-bg">Rules fallback · not the trained model</span>
      )}
      {items.map(([k, v]) => (
        <span key={k} className={cx("tabular", k === "Horizon" && elapsed && "font-semibold")}>
          <span className="text-muted">{k} </span>
          {v}
        </span>
      ))}
    </div>
  );
}
