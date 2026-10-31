import Link from "next/link";
import { Brand } from "@/components/Brand";
import { Panel } from "@/components/ui";

export default function ModelCard() {
  return <main className="mx-auto w-full max-w-[900px] space-y-6 px-5 pb-12">
    <header className="flex flex-wrap items-center justify-between gap-4 py-6"><Brand subtitle="Model card" /><Link href="/" className="pill-btn border border-line">Open forecast</Link></header>
    <Panel title="Purpose"><p className="leading-relaxed">A 48-hour hourly outlook for Frankfurt runway direction and weather-derived runway-18 usability. Intended for software evaluation and research. Independent of Fraport and all airlines; not for operational use.</p></Panel>
    <Panel title="Distribution"><p className="leading-relaxed">The public demo computes the rule baseline from licensed archived weather. Fitted weights and recorded direction labels are withheld pending source permission. Historical model measurements are separate and do not describe the rules demo.</p></Panel>
    <Panel title="Historical model"><p className="leading-relaxed">Gradient-boosted trees combine airport observations, archived weather models, runway wind components and rule state. Persistence blending uses earlier validation data. Monthly expanding walk-forward tests compare the model with rules and persistence.</p></Panel>
    <Panel title="Limits"><ul className="list-disc space-y-3 pl-5 leading-relaxed"><li>Test results informed development, so the final test is not untouched.</li><li>Direction labels are a public proxy with excluded change hours and a suspect feed interval.</li><li>Archived forecast availability is approximate; the publication buffer is assumed.</li><li>Runway 18 uses wind-inferred labels, not verified operational closures; rare-event detection remains weak.</li><li>Certainty and timing windows are heuristic. Hourly state accuracy is not exact change timing.</li><li>There is no certified traffic, capacity, separation or clearance model.</li></ul></Panel>
    <Link href="/quality" className="underline">View historical measured results and source limitations</Link>
    <p className="text-sm text-muted">Technical source documentation: MODEL_CARD.md, docs/EVALUATION.md and docs/DATA_SOURCES.md in the source distribution. Proposed MIT code licence needs approval by all four authors.</p>
  </main>;
}
