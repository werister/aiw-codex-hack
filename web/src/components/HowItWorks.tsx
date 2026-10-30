import Link from "next/link";
import { Arrow } from "./ui";

const STEPS = [
  {
    title: "Weather data",
    line: "Weather forecasts and airport reports.",
    icon: (
      <path d="M14 30h20a7 7 0 0 0 0-14 10 10 0 0 0-19-2A8 8 0 0 0 14 30Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
    ),
  },
  {
    title: "Direction forecast",
    line: "A runway direction, runway 18 probability and certainty score for each hour.",
    icon: (
      <>
        <circle cx="24" cy="24" r="14" stroke="currentColor" strokeWidth="1.5" />
        <path d="m24 13 4 11-4 11-4-11 4-11Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
      </>
    ),
  },
  {
    title: "Review",
    line: "Check forecast changes before your shift.",
    icon: (
      <>
        <rect x="12" y="10" width="24" height="28" rx="4" stroke="currentColor" strokeWidth="1.5" />
        <path d="m17 20 3 3 6-6M17 30h14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </>
    ),
  },
];

export function HowItWorks() {
  return (
    <section className="border-t border-line py-16 sm:py-20" aria-label="How it works">
      <h2 className="text-[28px] font-light sm:text-[36px]">How it works</h2>
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
      <Link href="/pitch" className="pill-btn mt-12 bg-accent text-accent-ink [--btn-ring:var(--accent)]">
        View a historical forecast <Arrow />
      </Link>
    </section>
  );
}
