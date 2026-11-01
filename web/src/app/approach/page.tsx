import { Brand } from "@/components/Brand";
import { Panel } from "@/components/ui";

export default function Approach() {
  return <main className="mx-auto w-full max-w-[1000px] space-y-6 px-5 pb-12">
    <header className="flex flex-wrap items-center justify-between gap-4 py-6"><Brand subtitle="Data and method" /><a href="/" className="pill-btn border border-line">Open forecast</a></header>
    <Panel title="From weather to a runway outlook"><p className="leading-relaxed">Airport wind reports establish the issue-time state. Archived weather forecasts describe the next 48 hours. A state machine applies wind limits and direction-change hysteresis. The offline demo uses that rule baseline and uncalibrated margin scores.</p></Panel>
    <Panel title="Historical fitted model"><p className="leading-relaxed">Gradient-boosted trees combine weather forecasts, airport observations, runway tailwinds, model disagreement and the current direction. A short-lead blend with persistence is selected on earlier validation data. Direction labels came from a public operating-direction proxy; runway 18 labels were inferred from wind limits, not observed closures. Fitted files are withheld pending source permission.</p></Panel>
    <Panel title="Evaluation"><p className="leading-relaxed">Monthly expanding walk-forward evaluation compares each fit with the rule baseline and persistence. Whole-day bootstrap intervals account for within-day dependence. Test results informed development, archived run availability is approximate, and change hours are excluded from direction labels. Hourly state accuracy is separate from event timing.</p><a href="/quality" className="mt-5 inline-block underline">View measured model quality</a></Panel>
    <Panel title="Interpretation"><p className="leading-relaxed">Certainty measures distance from a probability boundary, not calibrated joint correctness. The next-change probability supports the new direction at an hour, not the probability of an event. Timing windows are heuristic. Illustrative aircraft do not represent traffic, capacity or clearances.</p></Panel>
    <p className="text-sm text-muted">Independent decision-support demo, not for operational use. Not affiliated with Fraport or any airline.</p>
  </main>;
}
