import type { ReactNode } from "react";

export function cx(...parts: (string | false | null | undefined)[]) {
  return parts.filter(Boolean).join(" ");
}

type Tone = "neutral" | "red" | "green" | "amber" | "blue" | "sun";

const TONES: Record<Tone, string> = {
  neutral: "bg-surface-2 text-ink-2 ring-line",
  red: "bg-red-soft text-red ring-red/20",
  green: "bg-green-soft text-green ring-green/20",
  amber: "bg-amber-soft text-amber ring-amber/20",
  blue: "bg-blue-soft text-blue ring-blue/20",
  sun: "bg-sun-soft text-sun-ink ring-sun/40",
};

export function Badge({ tone = "neutral", children }: { tone?: Tone; children: ReactNode }) {
  return (
    <span
      className={cx(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold ring-1 ring-inset whitespace-nowrap",
        TONES[tone],
      )}
    >
      {children}
    </span>
  );
}

export function Card({
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
    <section className={cx("rounded-xl border border-line bg-surface p-4", className)}>
      {(title || aside) && (
        <header className="mb-3 flex items-center justify-between gap-3">
          {title && (
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted">{title}</h3>
          )}
          {aside}
        </header>
      )}
      {children}
    </section>
  );
}

// Times arrive as local ISO without zone ("2026-10-30T11:40"); read them as written.
export function hhmm(iso: string) {
  return iso.slice(11, 16);
}

const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export function dayLabel(isoDate: string) {
  const [y, m, d] = isoDate.slice(0, 10).split("-").map(Number);
  const wd = new Date(Date.UTC(y, m - 1, d)).getUTCDay();
  return `${WEEKDAYS[wd]} ${d} ${MONTHS[m - 1]}`;
}

export function eur(n: number) {
  return new Intl.NumberFormat("de-DE", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(n);
}

export function minutes(min: number) {
  if (min <= 0) return "on time";
  const h = Math.floor(min / 60);
  const m = min % 60;
  return h ? `+${h}h${m ? ` ${String(m).padStart(2, "0")}m` : ""}` : `+${m}m`;
}

export function seconds(ms: number) {
  return ms < 1000 ? `${Math.max(1, Math.round(ms))} ms` : `${(ms / 1000).toFixed(1)} s`;
}
