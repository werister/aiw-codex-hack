// Liftoff wordmark: a runway line that lifts off, then the name.
export function Brand({ subtitle }: { subtitle?: string }) {
  return (
    <div className="flex min-w-0 items-center gap-2.5">
      <svg viewBox="0 0 32 32" className="size-7 shrink-0 text-accent" aria-hidden="true">
        <rect width="32" height="32" rx="8" fill="currentColor" />
        <path d="M6 22 H15 L26 9" fill="none" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M21 9 H26 V14" fill="none" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      <div className="flex min-w-0 items-baseline gap-3">
        <h1 className="text-[20px] font-semibold tracking-tight">Liftoff</h1>
        {subtitle && <span className="hidden truncate text-[15px] text-muted sm:inline">{subtitle}</span>}
      </div>
    </div>
  );
}
