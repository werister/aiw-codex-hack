import { Arrow } from "./ui";

const STEPS = [
  {
    title: "Public weather data",
    line: "Weather forecasts and airport weather reports, free for anyone.",
    icon: (
      <path d="M14 30h20a7 7 0 0 0 0-14 10 10 0 0 0-19-2A8 8 0 0 0 14 30Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
    ),
  },
  {
    title: "Our forecast",
    line: "West or east for every hour of the next 2 days, and how sure we are.",
    icon: (
      <>
        <circle cx="24" cy="24" r="14" stroke="currentColor" strokeWidth="1.5" />
        <path d="m24 13 4 11-4 11-4-11 4-11Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
      </>
    ),
  },
  {
    title: "Your plan",
    line: "Staff, slots and runway changes prepared in time, not in a rush.",
    icon: (
      <>
        <rect x="12" y="10" width="24" height="28" rx="4" stroke="currentColor" strokeWidth="1.5" />
        <path d="m17 20 3 3 6-6M17 30h14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </>
    ),
  },
];

// Three steps, no jargon.
export function HowItWorks() {
  return (
    <section className="border-t border-line py-16 sm:py-20" aria-label="How it works">
      <p className="eyebrow text-muted">How it works</p>
      <ol className="mt-8 grid gap-10 md:grid-cols-[1fr_auto_1fr_auto_1fr] md:items-start md:gap-6">
        {STEPS.map((s, i) => (
          <li key={s.title} className="contents">
            {i > 0 && (
              <span aria-hidden className="hidden pt-6 text-muted md:block">
                <Arrow />
              </span>
            )}
            <div>
              <svg viewBox="0 0 48 48" className="size-14 text-accent" fill="none" aria-hidden>
                {s.icon}
              </svg>
              <h3 className="mt-4 text-[24px] font-light">{s.title}</h3>
              <p className="mt-2 max-w-[32ch] text-[17px] leading-snug text-ink-2">{s.line}</p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
