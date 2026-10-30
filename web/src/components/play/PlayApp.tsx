"use client";

import Link from "next/link";
import { useEffect, useRef, useState, type PointerEvent, type KeyboardEvent } from "react";
import type { OD, QualityResult } from "@/lib/forecast-types";
import { LANDING_CHANGE_NOW_KT, LANDING_TOLERANCE_MINUTES, R18_TAILWIND_LIMIT_KT, playWind } from "@/lib/play-wind";
import { BrandLogo } from "../BrandLogo";
import { Arrow, cx } from "../ui";

type Scene = { setState: (s: { od: OD; r18Open: boolean; wind?: { dir: number; kt: number } }) => void; destroy: () => void };
type Quality = QualityResult & {
  coverage?: { observed_base_rates?: { od25_share?: number; changes_per_year?: number } };
};

// The shared FRA scene from the finals deck; loaded at runtime so the app builds without it.
const SCENE_URL = "/deck/scene.js";
const WAY: Record<OD, string> = { "25": "west", "07": "east" };
const PRESETS = [
  { label: "Calm", dir: 250, kt: 0 },
  { label: "West wind", dir: 250, kt: 15 },
  { label: "East wind", dir: 70, kt: 15 },
  { label: "North wind", dir: 0, kt: 18 },
];

// Audience page: set the wind, see the official rules turn Frankfurt around.
export function PlayApp() {
  const [dir, setDir] = useState(250);
  const [kt, setKt] = useState(8);
  const [od, setOd] = useState<OD>("25");
  const [flipNote, setFlipNote] = useState<string | null>(null);
  const r = playWind(od, dir, kt);

  // Apply the rules on every wind change; the direction is kept between changes, as at the airport.
  const setWind = (nextDir: number, nextKt: number) => {
    const step = playWind(od, nextDir, nextKt);
    setDir(nextDir);
    setKt(nextKt);
    if (step.flipped) {
      setOd(step.od);
      setFlipNote(`Tailwind reached ${LANDING_CHANGE_NOW_KT} kt, so planes turned around.`);
    } else setFlipNote(null);
  };

  return (
    <main className="mx-auto flex w-full max-w-[640px] flex-col gap-10 px-4 pb-16 pt-6">
      <header>
        <p className="text-[15px] text-muted">Frankfurt Airport</p>
        <h1 className="mt-2 text-[36px] font-light leading-[1.05] tracking-[-0.02em]">Play the wind</h1>
        <p className="mt-3 text-[17px] leading-snug text-ink-2">
          Turn the wind and watch which way planes land. The official rules decide.
        </p>
      </header>

      <section aria-label="Airport and result" className="flex flex-col gap-4">
        <SceneBox od={r.od} r18Open={r.r18Open} dir={dir} kt={kt} />
        <div aria-live="polite">
          <p className="text-[28px] font-light leading-tight">
            Planes land toward the <span className={r.od === "25" ? "text-west" : "text-east"}>{WAY[r.od]}</span>.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <span className={cx("rounded-full px-4 py-2 text-[15px]", r.r18Open ? "bg-panel-2 text-ink" : "bg-bad text-on-signal")}>
              Runway 18 {r.r18Open ? "open" : "closed"}
            </span>
          </div>
          <p className="mt-3 text-[15px] leading-snug text-ink-2">
            {flipNote ??
              (kt === 0
                ? "No wind: planes keep their direction."
                : r.tolerated
                  ? `Light tailwind of ${r.tailwindKt.toFixed(0)} kt: allowed for up to ${LANDING_TOLERANCE_MINUTES} minutes, then planes turn around.`
                  : "Headwind: planes keep this direction.")}
            {!r.r18Open &&
              (r.r18Reason === "tailwind"
                ? ` Runway 18 closes at ${R18_TAILWIND_LIMIT_KT} kt tailwind; it has ${r.r18TailwindKt.toFixed(0)} kt.`
                : " Runway 18 closes in very strong crosswind.")}
          </p>
        </div>
      </section>

      <section aria-label="Wind controls" className="flex flex-col gap-6">
        <Dial dir={dir} onChange={(d) => setWind(d, kt)} />
        <div>
          <label htmlFor="wind-speed" className="flex items-baseline justify-between text-[17px]">
            <span>Wind speed</span>
            <span className="tabular">{kt} kt</span>
          </label>
          <div className="mt-3 flex items-center gap-3">
            <StepButton label="Less wind" onClick={() => setWind(dir, Math.max(0, kt - 1))}>−</StepButton>
            <input
              id="wind-speed"
              type="range"
              min={0}
              max={40}
              step={1}
              value={kt}
              onChange={(e) => setWind(dir, Number(e.target.value))}
              className="h-11 w-full cursor-pointer accent-[var(--accent)]"
            />
            <StepButton label="More wind" onClick={() => setWind(dir, Math.min(40, kt + 1))}>+</StepButton>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {PRESETS.map((p) => (
            <button
              key={p.label}
              type="button"
              onClick={() => setWind(p.dir, p.kt)}
              className="min-h-11 rounded-full border border-line px-4 text-[15px] text-ink active:bg-select"
            >
              {p.label}
            </button>
          ))}
        </div>
        <p className="text-[13px] text-muted">
          Rules from the FraAlliance challenge: turn around at {LANDING_CHANGE_NOW_KT} kt tailwind, runway 18 closes at{" "}
          {R18_TAILWIND_LIMIT_KT} kt tailwind.
        </p>
      </section>

      <Facts />

      <section className="flex flex-col items-start gap-5 rounded-card bg-panel-2 p-6" aria-label="Lift-off">
        <BrandLogo />
        <p className="text-[20px] font-light leading-snug">A 2-day runway forecast for Frankfurt Airport, built on public data.</p>
        <Link href="/" className="pill-btn bg-accent text-accent-ink [--btn-ring:var(--accent)]">
          See the forecast <Arrow />
        </Link>
      </section>
    </main>
  );
}

function StepButton({ label, onClick, children }: { label: string; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      type="button"
      aria-label={label}
      onClick={onClick}
      className="flex size-11 shrink-0 items-center justify-center rounded-full border border-line text-[22px] text-ink active:bg-select"
    >
      {children}
    </button>
  );
}

// Wind-from dial: drag the handle round the ring, or use the arrow keys.
function Dial({ dir, onChange }: { dir: number; onChange: (deg: number) => void }) {
  const ref = useRef<SVGSVGElement>(null);
  const dragging = useRef(false);
  const fromPointer = (e: PointerEvent<SVGSVGElement>) => {
    const box = ref.current?.getBoundingClientRect();
    if (!box) return;
    const dx = e.clientX - (box.left + box.width / 2);
    const dy = e.clientY - (box.top + box.height / 2);
    const deg = Math.round(((Math.atan2(dx, -dy) * 180) / Math.PI + 360) % 360 / 5) * 5;
    onChange(deg % 360);
  };
  const onKey = (e: KeyboardEvent<SVGSVGElement>) => {
    if (e.key === "ArrowRight" || e.key === "ArrowUp") onChange((dir + 5) % 360);
    else if (e.key === "ArrowLeft" || e.key === "ArrowDown") onChange((dir + 355) % 360);
    else return;
    e.preventDefault();
  };
  const rad = (dir * Math.PI) / 180;
  const hx = 100 + 78 * Math.sin(rad);
  const hy = 100 - 78 * Math.cos(rad);

  return (
    <div className="flex items-center gap-5">
      <svg
        ref={ref}
        viewBox="0 0 200 200"
        className="size-[200px] shrink-0 touch-none select-none rounded-full outline-offset-4"
        role="slider"
        tabIndex={0}
        aria-label="Wind direction, where the wind comes from"
        aria-valuemin={0}
        aria-valuemax={359}
        aria-valuenow={dir}
        aria-valuetext={`from ${dir} degrees`}
        onKeyDown={onKey}
        onPointerDown={(e) => {
          dragging.current = true;
          e.currentTarget.setPointerCapture(e.pointerId);
          fromPointer(e);
        }}
        onPointerMove={(e) => dragging.current && fromPointer(e)}
        onPointerUp={() => (dragging.current = false)}
        onPointerCancel={() => (dragging.current = false)}
      >
        <circle cx="100" cy="100" r="78" fill="var(--panel-2)" stroke="var(--line)" strokeWidth="2" />
        {[
          ["N", 100, 36],
          ["E", 166, 104],
          ["S", 100, 172],
          ["W", 34, 104],
        ].map(([t, x, y]) => (
          <text key={t as string} x={x as number} y={y as number} textAnchor="middle" fontSize="14" fill="var(--muted)">
            {t}
          </text>
        ))}
        {/* Arrow shows where the wind blows to. */}
        <g transform={`rotate(${dir + 180} 100 100)`}>
          <path d="M100 52 L100 140" stroke="var(--ink)" strokeWidth="4" strokeLinecap="round" />
          <path d="M88 126 L100 148 L112 126 Z" fill="var(--ink)" />
        </g>
        <circle cx={hx} cy={hy} r="16" fill="var(--accent)" stroke="var(--bg)" strokeWidth="4" />
      </svg>
      <div>
        <p className="text-[17px]">Wind from</p>
        <p className="text-[36px] font-light leading-none tabular">{dir}°</p>
        <p className="mt-2 text-[13px] text-muted">Drag the dot round the circle.</p>
      </div>
    </div>
  );
}

function SceneBox({ od, r18Open, dir, kt }: { od: OD; r18Open: boolean; dir: number; kt: number }) {
  const box = useRef<HTMLDivElement>(null);
  const scene = useRef<Scene | null>(null);
  const latest = useRef({ od, r18Open, wind: { dir, kt } });
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let alive = true;
    import(/* webpackIgnore: true */ /* turbopackIgnore: true */ SCENE_URL)
      .then((m: { mount: (el: HTMLElement, o: object) => Scene }) => {
        if (!alive || !box.current) return;
        scene.current = m.mount(box.current, { ...latest.current, intro: true, labels: false, drift: 0 });
      })
      .catch(() => alive && setFailed(true));
    return () => {
      alive = false;
      scene.current?.destroy();
      scene.current = null;
    };
  }, []);

  useEffect(() => {
    latest.current = { od, r18Open, wind: { dir, kt } };
    scene.current?.setState(latest.current);
  }, [od, r18Open, dir, kt]);

  return (
    <div className="relative h-[44svh] max-h-[420px] min-h-[260px] overflow-hidden rounded-card bg-panel-2">
      {failed ? (
        <p className="absolute inset-0 flex items-center justify-center p-6 text-center text-[15px] text-muted">
          The 3D airport could not load on this device. The rules below still work.
        </p>
      ) : (
        <div ref={box} role="img" aria-label={`3D Frankfurt Airport, planes landing toward the ${WAY[od]}`} className="absolute inset-0" />
      )}
    </div>
  );
}

// Three plain facts, read from the published evaluation file.
function Facts() {
  const [q, setQ] = useState<Quality | null>(null);
  useEffect(() => {
    fetch("/data/quality.json", { cache: "no-store" })
      .then((res) => (res.ok ? res.json() : Promise.reject()))
      .then(setQ)
      .catch(() => setQ(null));
  }, []);

  const rates = q?.coverage?.observed_base_rates;
  const day = q?.out_of_sample.od.find((x) => x.lead_h === 24);
  const facts = [
    rates?.changes_per_year != null && `Frankfurt changes direction about ${Math.round(rates.changes_per_year / 10) * 10} times a year.`,
    rates?.od25_share != null && `Planes land toward the west ${Math.round(rates.od25_share * 100)}% of the time.`,
    day && day.n > 0 && `A day ahead, our forecast gets ${Math.round(day.model_acc * 100)} of 100 hours right.`,
  ].filter(Boolean) as string[];

  if (!facts.length) return null;
  return (
    <section aria-label="Facts" className="flex flex-col gap-2.5">
      {facts.map((t) => (
        <p key={t} className="rounded-card border border-line p-5 text-[17px] leading-snug">
          {t}
        </p>
      ))}
    </section>
  );
}
