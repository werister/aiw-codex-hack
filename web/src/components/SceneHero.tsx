"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import type { HourForecast, OD } from "@/lib/forecast-types";

type SelectedHour = Pick<HourForecast, "time" | "local" | "lead_h" | "p_18_usable" | "certainty">;
type Theme = "light" | "tower";
type SceneState = {
  od: OD;
  r18Open: boolean;
  wind?: { dir: number; kt: number };
  forecastHour?: SelectedHour;
};
type SceneController = {
  setState: (state: SceneState) => void;
  reset: () => void;
  setPaused: (paused: boolean) => void;
  destroy: () => void;
};

export function SceneHero({
  od,
  r18Open,
  wind,
  forecastHour,
  fallback,
  className,
  theme = "light",
}: SceneState & { fallback: ReactNode; className?: string; theme?: Theme }) {
  const box = useRef<HTMLDivElement>(null);
  const scene = useRef<SceneController | null>(null);
  const latestState = useRef<SceneState>({ od, r18Open, wind, forecastHour });
  const paused = useRef(true);
  const [sceneStatus, setSceneStatus] = useState<{ theme: Theme; phase: "loading" | "ready" | "failed" }>({ theme, phase: "loading" });
  const [isPaused, setIsPaused] = useState(true);
  const phase = sceneStatus.theme === theme ? sceneStatus.phase : "loading";

  const windDir = wind?.dir;
  const windKt = wind?.kt;
  const forecastTime = forecastHour?.time;
  const forecastLocal = forecastHour?.local;
  const forecastLead = forecastHour?.lead_h;
  const forecastR18 = forecastHour?.p_18_usable;
  const forecastCertainty = forecastHour?.certainty;

  useEffect(() => {
    const selectedForecast =
      forecastTime == null || forecastLocal == null || forecastLead == null || forecastR18 == null || forecastCertainty == null
        ? undefined
        : { time: forecastTime, local: forecastLocal, lead_h: forecastLead, p_18_usable: forecastR18, certainty: forecastCertainty };
    const selectedWind = windDir == null || windKt == null ? undefined : { dir: windDir, kt: windKt };
    const nextState = { od, r18Open, wind: selectedWind, forecastHour: selectedForecast };
    latestState.current = nextState;

    const current = scene.current;
    if (!current) return;
    // The renderer resets on a changed hour, OD, or runway-18 state.
    current.setState(nextState);
    current.setPaused(paused.current);
  }, [od, r18Open, windDir, windKt, forecastTime, forecastLocal, forecastLead, forecastR18, forecastCertainty]);

  useEffect(() => {
    const preference = window.matchMedia("(prefers-reduced-motion: reduce)");
    const pauseForReducedMotion = () => {
      if (preference.matches) setPlaybackPaused(true);
    };

    if (preference.matches) pauseForReducedMotion();
    else setPlaybackPaused(false);
    preference.addEventListener("change", pauseForReducedMotion);
    return () => preference.removeEventListener("change", pauseForReducedMotion);
  }, []);

  useEffect(() => {
    let alive = true;
    let failedDuringMount = false;
    let mounted: SceneController | null = null;

    const fail = () => {
      if (!alive) return;
      failedDuringMount = true;
      mounted?.destroy();
      if (scene.current === mounted) scene.current = null;
      setSceneStatus({ theme, phase: "failed" });
    };

    import("@/lib/airport-scene")
      .then((module) => {
        if (!alive || !box.current) return;
        const options = {
          od: latestState.current.od,
          r18Open: latestState.current.r18Open,
          wind: latestState.current.wind,
          forecastHour: latestState.current.forecastHour,
          theme,
          paused: paused.current,
          onReady: () => {
            if (alive && !failedDuringMount) setSceneStatus({ theme, phase: "ready" });
          },
          onError: fail,
        };
        mounted = module.mount(box.current, options);

        if (!alive || failedDuringMount) {
          mounted.destroy();
          return;
        }

        scene.current = mounted;
        mounted.setState(latestState.current);
        mounted.setPaused(paused.current);
      })
      .catch(fail);

    return () => {
      alive = false;
      scene.current?.destroy();
      scene.current = null;
    };
  }, [theme]);

  function setPlaybackPaused(nextPaused: boolean) {
    paused.current = nextPaused;
    setIsPaused(nextPaused);
    scene.current?.setPaused(nextPaused);
  }

  const replay = () => {
    const current = scene.current;
    if (!current) return;
    current.reset();
    current.setState(latestState.current);
    setPlaybackPaused(false);
  };

  const r18Probability = forecastHour ? Math.round(forecastHour.p_18_usable * 100) : null;
  const forecastLabel = forecastHour
    ? `Berlin ${forecastHour.local.replace("T", " ")} (+${forecastHour.lead_h} h)`
    : "Current forecast";
  const accessibleCaption = forecastHour
    ? `${forecastLabel}; model OD ${od}; runway 18 probability ${r18Probability}% usable, shown ${r18Open ? "open" : "closed"} at the 50% threshold; model certainty ${forecastHour.certainty}%; traffic is illustrative, not an aircraft assignment.`
    : `${forecastLabel}; model OD ${od}; runway 18 is shown ${r18Open ? "open" : "closed"} at the 50% threshold; traffic is illustrative, not an aircraft assignment.`;

  if (phase === "failed") {
    return (
      <div className={className} data-theme={theme}>
        {fallback}
        <p className="sr-only" role="status">3D preview unavailable; showing the runway map.</p>
      </div>
    );
  }

  return (
    <section className={`w-full overflow-hidden ${className ?? ""}`} data-theme={theme} role="group" aria-label="Forecast-controlled Frankfurt Airport 3D illustration">
      <div className="relative h-full w-full">
        <div ref={box} role="img" aria-label={`3D Frankfurt Airport illustration. ${accessibleCaption}`} className="absolute inset-0 h-full w-full" />

        {phase === "loading" && (
          <p role="status" className="absolute left-3 top-3 rounded-full bg-panel/90 px-3 py-2 text-xs text-ink">
            Loading 3D airport scene…
          </p>
        )}

        <p aria-live="polite" className="absolute bottom-2 left-3 right-3 rounded-lg bg-panel/95 px-3 py-2 text-xs leading-5 text-ink">
          <span className="block">{forecastLabel} · model OD {od}</span>
          <span className="block">
            {forecastHour ? `R18 ${r18Probability}% usable` : "R18"} · {r18Open ? "open" : "closed"} at 50% · traffic illustrative
          </span>
        </p>

        {phase === "ready" && (
          <div className="absolute right-3 top-3 flex gap-2">
            <button
              type="button"
              className="rounded-full border border-line bg-panel/95 px-3 py-2 text-[15px] text-ink focus-visible:outline-2 focus-visible:outline-accent"
              aria-label={isPaused ? "Play illustrative aircraft traffic" : "Pause illustrative aircraft traffic"}
              onClick={() => setPlaybackPaused(!isPaused)}
            >
              {isPaused ? "Play" : "Pause"}
            </button>
            <button
              type="button"
              className="rounded-full border border-line bg-panel/95 px-3 py-2 text-[15px] text-ink focus-visible:outline-2 focus-visible:outline-accent"
              aria-label="Replay illustrative aircraft traffic for the selected hour"
              onClick={replay}
            >
              Replay
            </button>
          </div>
        )}
      </div>
    </section>
  );
}
