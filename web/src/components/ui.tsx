import type { ReactNode } from "react";
import type { HourForecast, OD } from "@/lib/forecast-types";

export function cx(...parts: (string | false | null | undefined)[]) {
  return parts.filter(Boolean).join(" ");
}

export const OD_LABEL: Record<OD, string> = { "25": "West", "07": "East" };

export function odText(od: OD) {
  return od === "25" ? "text-west" : "text-east";
}

export function odBg(od: OD) {
  return od === "25" ? "bg-west" : "bg-east";
}

export function odSoft(od: OD) {
  return od === "25" ? "bg-west-soft" : "bg-east-soft";
}

// FraAlliance card: flat, 10 px radius, hairline edge, short title on top.
export function Panel({
  title,
  aside,
  children,
  className,
}: {
  title?: ReactNode;
  aside?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={cx("rounded-card border border-line bg-panel p-5 sm:p-6", className)}>
      {(title || aside) && (
        <header className="mb-4 flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
          {title && <h2 className="eyebrow text-ink">{title}</h2>}
          {aside}
        </header>
      )}
      {children}
    </section>
  );
}

// Thin outline arrow in the style of their link arrows.
export function Arrow({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 17 8" className={cx("h-2 w-[17px] shrink-0", className)} fill="none" aria-hidden>
      <path d="M0 4h16M12.5 0.5 16 4l-3.5 3.5" stroke="currentColor" />
    </svg>
  );
}

// Unsure: the probability behind a call is under 60%, for direction or runway 18.
export function isUnsure(h: HourForecast) {
  return Math.abs(h.p_od25 - 0.5) < 0.1 || Math.abs(h.p_18_usable - 0.5) < 0.1;
}

// Why, from the file only: the weather models split on the rule call, or the hour sits near a limit.
export function unsureReason(h: HourForecast) {
  const v = h.inputs?.ens_votes_25;
  const split = Math.abs(h.p_od25 - 0.5) < 0.1 && v != null && v > 0 && v < 1;
  return split ? "models disagree" : "close to the limit";
}

// Local ISO without zone ("2026-10-31T13:00") is read as written: it is already Europe/Berlin.
export function hhmm(local: string) {
  return local.slice(11, 16);
}

const WD = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MO = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export function dayLabel(local: string) {
  const [y, m, d] = local.slice(0, 10).split("-").map(Number);
  return `${WD[new Date(Date.UTC(y, m - 1, d)).getUTCDay()]} ${d} ${MO[m - 1]}`;
}

export function pct(p: number) {
  return `${Math.round(p * 100)}%`;
}
