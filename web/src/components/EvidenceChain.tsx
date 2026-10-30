import { Fragment } from "react";
import type { ForecastResponse, HourForecast } from "@/lib/forecast-types";
import { CERTAINTY_DEF, PLAN_POLICY, planFrom, planHeadline, planWindow, probLabel } from "./Recommendation";
import { Arrow, OD_LABEL, Panel, cx, dayLabel, hhmm, isUnsure, pct, unsureReason } from "./ui";

type Node = { title: string; summary: string; rows: [string, string][] };

const NOT_RECORDED = "not recorded in this forecast file";
const num = (v: number | null | undefined, d = 1, unit = "") => (v == null ? "unavailable" : `${v.toFixed(d)}${unit}`);

// Sources -> Features -> Model + rules -> Forecast -> Planning response, with the selected hour's values.
export function EvidenceChain({
  f,
  h,
  open,
  onToggle,
  onReturn,
}: {
  f: ForecastResponse;
  h: HourForecast;
  open: boolean;
  onToggle: () => void;
  onReturn: () => void;
}) {
  const plan = planFrom(f);
  const planHour = f.hours.find((x) => x.time === plan.time);
  const atPlan = h.time === plan.time;
  const ev = f.evidence;
  const inp = h.inputs;
  const r18 = h.p_18_usable >= 0.5;
  const wind =
    h.wind_dir_deg == null ? "Direction unavailable / calm" : `${Math.round(h.wind_dir_deg)}° ${Math.round(h.wind_kt)} kt`;
  const agree = h.od === h.rule_od && r18 === h.rule_18_usable;

  const nodes: Node[] = [
    {
      title: "Sources",
      summary: `Issued ${dayLabel(f.issued_local)} ${hhmm(f.issued_local)}`,
      rows: [
        ["Mode", f.mode === "live" ? "Live forecast" : "Historical forecast"],
        ["Issued", `${dayLabel(f.issued_local)} ${hhmm(f.issued_local)}`],
        ["Model", f.model_version],
        ["Weather and records, as the file names them", f.nwp],
        ["OD at issue", `${f.current_od} ${OD_LABEL[f.current_od]}${ev ? ` · ${ev.issue_inputs.od_source}` : ""}`],
        ["Run ID", ev?.run_id ?? NOT_RECORDED],
        [
          "Model artifact",
          ev
            ? `${ev.model_artifact.version} · ${ev.model_artifact.file} · sha256 ${ev.model_artifact.sha256.slice(0, 12)} · trained through ${ev.model_artifact.trained_through.slice(0, 10)}`
            : NOT_RECORDED,
        ],
        ["Weather feeds", ev ? ev.sources.map((s) => `${s.name}${s.missing ? " (missing)" : ""}`).join(", ") : NOT_RECORDED],
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
        ["Weather models voting 25", inp?.ens_votes_25 == null ? NOT_RECORDED : pct(inp.ens_votes_25)],
        ["Ensemble direction spread (0 = all agree)", inp ? num(inp.ens_dir_spread, 3) : NOT_RECORDED],
        [
          "Ensemble tailwind on 25",
          inp ? `${num(inp.ens_tailwind_25_mean, 1, " kt")} ± ${num(inp.ens_tailwind_25_std, 1, " kt")}` : NOT_RECORDED,
        ],
        ["Pressure difference N–S / E–W", inp ? `${num(inp.dp_ns_hpa, 1)} / ${num(inp.dp_ew_hpa, 1)} hPa` : NOT_RECORDED],
      ],
    },
    {
      title: "Model + rules",
      summary: `P(25) ${pct(h.p_od25)} · rules ${h.rule_od}`,
      rows: [
        ["Model P(OD 25), published", pct(h.p_od25)],
        ["Model P(OD 25), raw before blending", inp ? pct(inp.p_od25_raw) : NOT_RECORDED],
        ["Blend with current direction", inp ? `${inp.blend_key}, weight ${inp.blend_weight}` : NOT_RECORDED],
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
        ["Certainty score", `${h.certainty}/100`],
        ["Unsure", isUnsure(h) ? `yes, ${unsureReason(h)}` : "no"],
        ["Against rules", agree ? "agrees" : "differs"],
      ],
    },
    {
      title: "Planning response",
      summary: planHeadline(plan),
      rows: [
        ["Window", planWindow(plan)],
        [probLabel(plan), plan.kind === "hold" && !plan.hasHours ? "Unavailable" : pct(plan.p)],
        [plan.kind === "hold" ? "Lowest supplied certainty score" : "Certainty at event hour", `${plan.kind === "hold" && !plan.hasHours ? "Unavailable" : `${plan.certainty}/100`}. ${CERTAINTY_DEF}`],
        ["Traffic", "demand data unavailable"],
        ["Policy", PLAN_POLICY],
      ],
    },
  ];

  return (
    <Panel
      title="Evidence trail"
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
      <div className="mb-4 flex flex-wrap items-center gap-x-6 gap-y-2 text-[15px]">
        <span>
          <span className="text-muted">Recommendation for </span>
          {planHour ? `${dayLabel(planHour.local)} ${hhmm(planHour.local)}` : "the supplied forecast coverage"}
        </span>
        <span className={cx(!atPlan && "font-medium")}>
          <span className="text-muted">Inspecting </span>
          {dayLabel(h.local)} {hhmm(h.local)} · {h.time.slice(11, 16)} UTC · +{h.lead_h} h
        </span>
        {!atPlan && (
          <button type="button" onClick={onReturn} className="pill-btn bg-accent text-accent-ink [--btn-ring:var(--accent)]">
            Return to recommendation evidence
          </button>
        )}
      </div>
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
        Values come from this forecast file. Features, model and rules, and forecast follow the selected hour;
        the planning response summarizes the earliest supplied event or the available coverage.
      </p>
    </Panel>
  );
}
