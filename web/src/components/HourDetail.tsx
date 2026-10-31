import type { HourForecast } from "@/lib/forecast-types";
import { utcOffset } from "./Provenance";
import { OD_LABEL, Panel, cx, dayLabel, hhmm, odText, pct } from "./ui";

// Drill-down for one hour: inputs, the official rules, the model, and what the certainty score means.
export function HourDetail({ h }: { h: HourForecast }) {
  const r18 = h.p_18_usable >= 0.5;
  const agree = h.od === h.rule_od && r18 === h.rule_18_usable;
  return (
    <Panel title={`Inspecting ${dayLabel(h.local)} ${hhmm(h.local)} · +${h.lead_h} h`}>
      <p className="-mt-2 mb-5 text-[13px] text-muted tabular">
        Valid {hhmm(h.local)} {utcOffset(h.time, h.local)} · {h.time.slice(11, 16)} UTC · {h.lead_h} h after issue
      </p>

      <div className="grid gap-x-10 lg:grid-cols-[2fr_1fr_1.2fr_1.6fr]">
      <Group title="Inputs · forecast weather">
        <Field k="Wind">
          {h.wind_dir_deg == null ? "Direction unavailable / calm" : `${Math.round(h.wind_dir_deg)}° ${Math.round(h.wind_kt)} kt`}
        </Field>
        <Field k="Gusts">{Math.round(h.gust_kt)} kt</Field>
        <Field k="Along runway 25">
          <Component kt={h.tailwind_25_kt} limit={10} />
        </Field>
        <Field k="Along runway 18">
          <Component kt={h.tailwind_18_kt} limit={15} r18 />
        </Field>
      </Group>

      <Group title="Official rules" narrow>
        <Field k="Direction">
          <span className={cx("font-medium", odText(h.rule_od))}>
            {h.rule_od} {OD_LABEL[h.rule_od]}
          </span>
        </Field>
        <Field k="Runway 18">
          <span className={h.rule_18_usable ? "" : "text-bad"}>{h.rule_18_usable ? "usable" : "closed"}</span>
        </Field>
      </Group>

      <Group title="Forecast scores" narrow>
        <Field k="Direction">
          <span className={cx("font-medium", odText(h.od))}>
            {h.od} {OD_LABEL[h.od]}
          </span>{" "}
          <span className="text-[15px] text-muted">P(25) {pct(h.p_od25)}</span>
        </Field>
        <Field k="Runway 18">
          <span className={r18 ? "" : "text-bad"}>{r18 ? "usable" : "closed"}</span>{" "}
          <span className="text-[15px] text-muted">P(usable) {pct(h.p_18_usable)}</span>
        </Field>
      </Group>

      <div className="mb-5 self-start rounded-[8px] bg-panel-2 p-4">
        <div className="flex items-baseline justify-between gap-3">
          <span className="text-[12px] text-muted">Certainty score</span>
          <span className="text-[20px] tabular">{h.certainty}/100</span>
        </div>
        <p className="mt-2 text-[13px] leading-snug text-ink-2">
          The smaller of the two probability margins: 100 × min(|2·P(25) − 1|, |2·P(18 usable) − 1|). 0 is a coin
          toss, 100 is the largest margin. It is not a calibrated chance that both calls are right. Rules-demo scores
          are uncalibrated; historical fitted-model accuracy is shown separately.
        </p>
      </div>
      </div>

      <p className={cx("text-[13px] leading-snug", agree ? "text-muted" : "rounded-[8px] border-[0.5px] border-ink px-3 py-2 text-ink")}>
        {agree ? "Forecast and rule baseline agree for this hour." : "Forecast and rule baseline disagree here. Review the inputs and method."}
      </p>
    </Panel>
  );
}

function Group({ title, narrow, children }: { title: string; narrow?: boolean; children: React.ReactNode }) {
  return (
    <div className="mb-5">
      <div className="eyebrow mb-3 text-muted">{title}</div>
      <div className={cx("grid grid-cols-2 gap-x-6 gap-y-3 text-[17px] leading-snug", narrow && "lg:grid-cols-1")}>{children}</div>
    </div>
  );
}

// Signed wind component: positive is tailwind, negative is headwind.
function Component({ kt, limit, r18 }: { kt: number; limit: number; r18?: boolean }) {
  const over = kt >= limit;
  return (
    <>
      <span className={cx(over && "font-semibold", over && r18 && "text-bad")}>
        {kt >= 0 ? "tailwind" : "headwind"} {Math.abs(kt).toFixed(1)} kt
      </span>
      <span className="text-[15px] text-muted"> {over ? `over limit ${limit}` : `(tailwind limit ${limit})`}</span>
    </>
  );
}

function Field({ k, children }: { k: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="mb-1 text-[12px] text-muted">{k}</div>
      <div className="tabular">{children}</div>
    </div>
  );
}
