import type { ReactNode } from "react";
import type { ForecastResponse } from "@/lib/forecast-types";
import { formatForecastInstant } from "@/lib/forecast-events";
import { Provenance } from "./Provenance";
import { ForecastEvents } from "./ForecastEvents";
import { DirectionBand } from "./DirectionBand";
import { Arrow, OD_LABEL, cx, odText, pct } from "./ui";

export function Hero({
  f,
  scene,
  compact,
  onEvidence,
  onSelectHour,
}: {
  f: ForecastResponse;
  scene: ReactNode;
  compact?: boolean;
  onEvidence?: () => void;
  onSelectHour?: (index: number) => void;
}) {
  const nc = f.next_change;

  return (
    <section className="min-w-0" aria-label="Forecast snapshot">
      <div
        className={cx(
          "grid items-center gap-6",
          compact ? "md:grid-cols-[1fr_1fr]" : "py-4 lg:min-h-[520px] lg:grid-cols-[1fr_1.1fr] lg:gap-10",
        )}
      >
        <div className="min-w-0">
          <Provenance f={f} compact />
          <DirectionBand f={f} compact={compact} />

          <div className="mt-6 border-t border-line pt-4">
            <p className="eyebrow text-muted">Next forecast change</p>
            {nc ? (
              <>
                <p className={cx("mt-2 font-light leading-tight", compact ? "text-[24px]" : "text-[26px] sm:text-[32px]")}>
                  <span className={odText(nc.to)}>{OD_LABEL[nc.to]} {nc.to}</span>
                </p>
                <p className="mt-1 text-[13px] leading-snug text-muted tabular">
                  {formatForecastInstant(nc.time, nc.local)}
                </p>
                <p className="mt-1 text-[13px] font-medium tabular">
                  P(OD {nc.to} at this hour) · {pct(nc.p)}
                </p>
                <p className="mt-1 text-[12px] leading-snug text-muted">
                  Forecast window (Berlin): {formatLocal(nc.window_local[0])}–{formatLocal(nc.window_local[1])}
                </p>
              </>
            ) : (
              <p className="mt-2 text-[14px] leading-snug text-muted">
                No change window in this forecast. See hourly changes below.
              </p>
            )}
          </div>

          {onEvidence && (
            <div className="mt-6 flex flex-wrap gap-2">
              <button type="button" onClick={onEvidence} className="pill-btn bg-accent text-accent-ink [--btn-ring:var(--accent)]">
                View evidence <Arrow />
              </button>
              <a href="#timeline" className="pill-btn border border-line text-ink [--btn-ring:var(--line)]">
                Forecast timeline
              </a>
            </div>
          )}
        </div>

        <div className="min-w-0 overflow-hidden rounded-card bg-panel-2 p-2">
          {scene}
        </div>
      </div>

      <ForecastEvents f={f} compact={compact} onSelectHour={onSelectHour} />
    </section>
  );
}

function formatLocal(local: string) {
  return `${local.slice(0, 10)} ${local.slice(11, 16)}`;
}
