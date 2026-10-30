import { Fragment } from "react";
import type { ForecastResponse, HourForecast } from "@/lib/forecast-types";
import { PLAN_POLICY, planFrom, planHeadline, planWindow } from "./Recommendation";
import { Arrow, OD_LABEL, Panel, cx, dayLabel, hhmm, pct } from "./ui";

type Node = { title: string; summary: string; rows: [string, string][] };

// Sources -> Features -> Model + rules -> Forecast -> Planning response, with the selected hour's values.
export function EvidenceChain({
  f,
  h,
  open,
  onToggle,
}: {
  f: ForecastResponse;
  h: HourForecast;
  open: boolean;
  onToggle: () => void;
}) {
  const plan = planFrom(f);
  const r18 = h.p_18_usable >= 0.5;
  const wind = h.wind_dir_deg == null ? "calm" : `${Math.round(h.wind_dir_deg)}° ${Math.round(h.wind_kt)} kt`;
  const agree = h.od === h.rule_od && r18 === h.rule_18_usable;

  const nodes: Node[] = [
    {
      title: "Sources",
      summary: `Issued ${dayLabel(f.issued_local)} ${hhmm(f.issued_local)}`,
      rows: [
        ["Issued", `${dayLabel(f.issued_local)} ${hhmm(f.issued_local)}`],
        ["OD at issue", `${f.current_od} ${OD_LABEL[f.current_od]}`],
        ["Inputs", f.nwp],
        ["Observations", "EDDF METAR, recorded directions from DFLD.de"],
      ],
    },
    {
      title: "Features",
      summary: wind,
      rows: [
        ["Wind", wind],
        ["Gusts", `${Math.round(h.gust_kt)} kt`],
        ["Tailwind on 25", `${h.tailwind_25_kt.toFixed(1)} kt (limit 10)`],
        ["Tailwind on 18", `${h.tailwind_18_kt.toFixed(1)} kt (limit 15)`],
      ],
    },
    {
      title: "Model + rules",
      summary: `P(25) ${pct(h.p_od25)} · rules ${h.rule_od}`,
      rows: [
        ["Model P(OD 25)", pct(h.p_od25)],
        ["Model P(18 usable)", pct(h.p_18_usable)],
        ["Rule call", `${h.rule_od}, runway 18 ${h.rule_18_usable ? "usable" : "closed"}`],
        ["Versions", `${f.model_version} · ${f.rules_version}`],
      ],
    },
    {
      title: "Forecast",
      summary: `${h.od} ${OD_LABEL[h.od]} · 18 ${r18 ? "open" : "closed"}`,
      rows: [
        ["Direction", `${h.od} ${OD_LABEL[h.od]}`],
        ["Runway 18", r18 ? "open" : "closed"],
        ["Confidence", `${h.certainty}%`],
        ["Against rules", agree ? "agrees" : "differs"],
      ],
    },
    {
      title: "Planning response",
      summary: planHeadline(plan),
      rows: [
        ["Window", planWindow(plan)],
        ["Probability", plan.kind === "hold" ? `lowest confidence ${plan.minCertainty}%` : pct(plan.p)],
        ["Traffic", "demand data unavailable"],
        ["Policy", PLAN_POLICY],
      ],
    },
  ];

  return (
    <Panel
      title={`Evidence chain · ${dayLabel(h.local)} ${hhmm(h.local)} · +${h.lead_h} h`}
      aside={
        <button
          type="button"
          onClick={onToggle}
          aria-expanded={open}
          className="pill-btn border border-line text-ink [--btn-ring:var(--line)]"
        >
          {open ? "Hide values" : "Show values"}
          <svg viewBox="0 0 12 8" className={cx("h-2 w-3 transition-transform duration-300", open && "rotate-180")} fill="none" aria-hidden>
            <path d="m1 1.5 5 5 5-5" stroke="currentColor" />
          </svg>
        </button>
      }
    >
      <ol className="flex flex-col gap-2 lg:flex-row lg:items-stretch">
        {nodes.map((n, i) => (
          <Fragment key={n.title}>
            {i > 0 && (
              <li aria-hidden className="flex items-center justify-center text-muted lg:w-5">
                <Arrow className="rotate-90 lg:rotate-0" />
              </li>
            )}
            <li className="min-w-0 flex-1 rounded-card bg-panel-2 p-4">
              <div className="eyebrow text-muted">
                {i + 1} · {n.title}
              </div>
              <div className="mt-2 text-[15px] leading-snug">{n.summary}</div>
              {open && (
                <dl className="mt-3 space-y-2 border-t border-line pt-3 text-[13px] leading-snug">
                  {n.rows.map(([k, v]) => (
                    <div key={k}>
                      <dt className="text-muted">{k}</dt>
                      <dd className="tabular [overflow-wrap:anywhere]">{v}</dd>
                    </div>
                  ))}
                </dl>
              )}
            </li>
          </Fragment>
        ))}
      </ol>
      <p className="mt-4 text-[13px] text-muted">
        Values are the recorded inputs and outputs of this forecast run for the selected hour. Click any hour in the
        timeline to follow it here.
      </p>
    </Panel>
  );
}
