import type { HourForecast } from "@/lib/forecast-types";
import { OD_LABEL, Panel, cx, dayLabel, hhmm, odText, pct } from "./ui";

// Drill-down for one hour: what the model says, what the official rules say, and why.
export function HourDetail({ h }: { h: HourForecast }) {
  const agree = h.od === h.rule_od && h.p_18_usable >= 0.5 === h.rule_18_usable;
  return (
    <Panel title={`${dayLabel(h.local)} ${hhmm(h.local)} · +${h.lead_h} h`}>
      <div className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
        <Field k="Direction (model)">
          <span className={cx("font-bold", odText(h.od))}>
            {h.od} {OD_LABEL[h.od]}
          </span>{" "}
          <span className="text-muted">P(25) {pct(h.p_od25)}</span>
        </Field>
        <Field k="Direction (rules)">
          <span className={odText(h.rule_od)}>{h.rule_od}</span>
        </Field>
        <Field k="Runway 18 (model)">
          <span className={h.p_18_usable >= 0.5 ? "text-ok" : "text-bad"}>{h.p_18_usable >= 0.5 ? "usable" : "closed"}</span>{" "}
          <span className="text-muted">{pct(h.p_18_usable)}</span>
        </Field>
        <Field k="Runway 18 (rules)">
          <span className={h.rule_18_usable ? "text-ok" : "text-bad"}>{h.rule_18_usable ? "usable" : "closed"}</span>
        </Field>
        <Field k="Wind">
          {h.wind_dir_deg == null ? "calm" : `${Math.round(h.wind_dir_deg)}°`} {Math.round(h.wind_kt)} kt, gusts {Math.round(h.gust_kt)}
        </Field>
        <Field k="Confidence">{h.certainty}%</Field>
        <Field k="Tailwind on 25">
          <span className={h.tailwind_25_kt >= 10 ? "text-bad" : ""}>{h.tailwind_25_kt.toFixed(1)} kt</span>
          <span className="text-muted"> (limit 10)</span>
        </Field>
        <Field k="Tailwind on 18">
          <span className={h.tailwind_18_kt >= 15 ? "text-bad" : ""}>{h.tailwind_18_kt.toFixed(1)} kt</span>
          <span className="text-muted"> (limit 15)</span>
        </Field>
      </div>
      <p className={cx("mt-3 text-xs", agree ? "text-muted" : "text-warn")}>
        {agree ? "Model and official rules agree for this hour." : "Model and official rules disagree here. The model has learned from what was actually flown."}
      </p>
    </Panel>
  );
}

function Field({ k, children }: { k: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="text-xs text-muted">{k}</div>
      <div className="tabular">{children}</div>
    </div>
  );
}
