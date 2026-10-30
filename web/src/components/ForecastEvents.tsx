import type { ReactNode } from "react";
import type { ForecastResponse } from "@/lib/forecast-types";
import {
  forecastEvents,
  formatForecastInstant,
  type DirectionEvent,
  type Runway18Event,
} from "@/lib/forecast-events";
import { cx, OD_LABEL, odText, pct } from "./ui";

export function ForecastEvents({
  f,
  compact,
  onSelectHour,
}: {
  f: ForecastResponse;
  compact?: boolean;
  onSelectHour?: (index: number) => void;
}) {
  const events = forecastEvents(f);

  return (
    <section
      className={cx("rounded-card border border-line bg-panel", compact ? "mt-4 p-3" : "mt-6 p-4 sm:p-5")}
      aria-labelledby="forecast-events-title"
    >
      <header className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <h3 id="forecast-events-title" className="eyebrow text-ink">Forecast events</h3>
        <p className="text-[12px] text-muted">Coverage · {events.coverage.label}</p>
      </header>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <Track
          title="Operating direction"
          empty={f.hours.length ? "No direction transition in the supplied hourly calls." : "No direction forecast supplied."}
        >
          {events.direction.map((event) => (
            <DirectionCard key={event.id} event={event} onSelectHour={onSelectHour} />
          ))}
        </Track>

        <Track
          title="Runway 18"
          empty={f.hours.length ? "No closure interval or status change in the supplied forecast." : "No runway 18 forecast supplied."}
        >
          {events.runway18.map((event) => (
            <RunwayCard key={event.id} event={event} f={f} onSelectHour={onSelectHour} />
          ))}
        </Track>
      </div>
    </section>
  );
}

function Track({ title, empty, children }: { title: string; empty: string; children: ReactNode }) {
  const hasEvents = Array.isArray(children) ? children.length > 0 : Boolean(children);
  return (
    <section className="min-w-0 rounded-card border border-line bg-bg p-3" aria-label={title}>
      <h4 className="eyebrow text-muted">{title}</h4>
      {hasEvents ? <ul className="mt-2 space-y-2">{children}</ul> : <p className="mt-2 text-[13px] leading-snug text-muted">{empty}</p>}
    </section>
  );
}

function DirectionCard({ event, onSelectHour }: { event: DirectionEvent; onSelectHour?: (index: number) => void }) {
  const content = (
    <>
      <p className="text-[14px] leading-snug">
        <span className={odText(event.to)}>{OD_LABEL[event.to]} {event.to}</span>
        <span className="text-muted"> from </span>
        <span className={odText(event.from)}>{OD_LABEL[event.from]} {event.from}</span>
      </p>
      <p className="mt-1 text-[12px] leading-snug text-muted">{formatForecastInstant(event.time, event.local)}</p>
      <p className="mt-1 text-[12px] font-medium tabular">{event.probabilityLabel} · {pct(event.probability)}</p>
      <p className="mt-1 text-[11px] leading-snug text-muted">{event.sourceLabel}</p>
      {event.windowLocal && (
        <p className="mt-1 text-[11px] leading-snug text-muted">
          Supplied Europe/Berlin window: {formatLocal(event.windowLocal[0])}–{formatLocal(event.windowLocal[1])}
        </p>
      )}
    </>
  );

  return (
    <li>
      <EventAction
        hourIndex={event.hourIndex}
        onSelectHour={onSelectHour}
        label={`Select forecast hour for OD ${event.to} at ${event.local}`}
      >
        {content}
      </EventAction>
    </li>
  );
}

function RunwayCard({
  event,
  f,
  onSelectHour,
}: {
  event: Runway18Event;
  f: ForecastResponse;
  onSelectHour?: (index: number) => void;
}) {
  const ongoingText = event.kind === "closure" && event.ongoing
    ? `Closure interval reaches the final supplied row (${lastForecastInstant(f)}); reopening is unknown beyond this forecast.`
    : null;

  return (
    <li>
      <EventAction
        hourIndex={event.hourIndex}
        onSelectHour={onSelectHour}
        label={`Select forecast hour for runway 18 event at ${event.local}`}
      >
        {event.kind === "closure" ? (
          <>
            <p className="text-[14px] leading-snug">Runway 18 likely unusable</p>
            <p className="mt-1 text-[12px] leading-snug text-muted">Starts · {formatForecastInstant(event.time, event.local)}</p>
            {event.end && <p className="mt-1 text-[12px] leading-snug text-muted">First usable forecast hour · {formatForecastInstant(event.end.time, event.end.local)}</p>}
            {ongoingText && <p className="mt-1 text-[12px] leading-snug text-muted">{ongoingText}</p>}
          </>
        ) : (
          <>
            <p className="text-[14px] leading-snug">Runway 18 likely unusable in supplied hourly calls</p>
            <p className="mt-1 text-[12px] leading-snug text-muted">
              {event.closedSampleCount} closed sample{event.closedSampleCount === 1 ? "" : "s"} · {formatForecastInstant(event.time, event.local)}
            </p>
            {event.lastClosedCall.time !== event.time && (
              <p className="mt-1 text-[12px] leading-snug text-muted">Last supplied closed call · {formatForecastInstant(event.lastClosedCall.time, event.lastClosedCall.local)}</p>
            )}
            {event.firstUsableCall && (
              <p className="mt-1 text-[12px] leading-snug text-muted">First usable sampled hour · {formatForecastInstant(event.firstUsableCall.time, event.firstUsableCall.local)}</p>
            )}
            {event.ongoing && <p className="mt-1 text-[12px] leading-snug text-muted">Reopening is unknown beyond the supplied calls.</p>}
            {event.gapsPresent && <p className="mt-1 text-[12px] leading-snug text-muted">Timestamp gaps are present; no state is inferred for missing hours.</p>}
          </>
        )}
        <p className="mt-1 text-[12px] font-medium tabular">{event.probabilityLabel} · {pct(event.probability)}</p>
        <p className="mt-1 text-[11px] leading-snug text-muted">{event.sourceLabel}</p>
      </EventAction>
    </li>
  );
}

function EventAction({
  hourIndex,
  onSelectHour,
  label,
  children,
}: {
  hourIndex: number | null;
  onSelectHour?: (index: number) => void;
  label: string;
  children: ReactNode;
}) {
  const className = "block w-full rounded-md p-2 text-left transition-colors hover:bg-panel focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink";
  if (hourIndex !== null && onSelectHour) {
    return <button type="button" className={className} onClick={() => onSelectHour(hourIndex)} aria-label={label}>{children}</button>;
  }
  return <div className={className}>{children}</div>;
}

function formatLocal(local: string) {
  return `${local.slice(0, 10)} ${local.slice(11, 16)}`;
}

function lastForecastInstant(f: ForecastResponse) {
  const last = [...f.hours].sort((a, b) => a.time.localeCompare(b.time)).at(-1);
  return last ? formatForecastInstant(last.time, last.local) : "the final supplied hour";
}
