import Link from "next/link";
import { Brand } from "@/components/Brand";
import { Numbers } from "@/components/Numbers";
import { QualityPanel } from "@/components/QualityPanel";

export default function QualityPage() {
  return <main className="mx-auto w-full max-w-[1200px] space-y-6 px-5 pb-12">
    <header className="flex flex-wrap items-center justify-between gap-4 py-6"><Brand subtitle="Historical model evaluation" /><Link className="pill-btn border border-line" href="/">Open forecast</Link></header>
    <p className="rounded-card bg-panel-2 p-5 leading-relaxed">These measurements describe the historical fitted model. The downloadable dashboard runs a separate rules demo: fitted artifacts and direction records are withheld pending source permission. Each test month was excluded from its fit, but test results informed development; this is not an untouched final test.</p>
    <Numbers />
    <QualityPanel />
    <Link className="underline" href="/model-card/">Model card and limitations</Link>
  </main>;
}
