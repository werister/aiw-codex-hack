import type { ReactNode } from "react";
import type { OD } from "@/lib/forecast-types";

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
    <section className={cx("rounded-xl border border-line bg-panel p-4", className)}>
      {(title || aside) && (
        <header className="mb-3 flex items-center justify-between gap-3">
          {title && <h2 className="text-xs font-semibold uppercase tracking-wider text-muted">{title}</h2>}
          {aside}
        </header>
      )}
      {children}
    </section>
  );
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
