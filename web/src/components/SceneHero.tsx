"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import type { OD } from "@/lib/forecast-types";

type SceneState = { od: OD; r18Open: boolean; wind?: { dir: number; kt: number } };
type Scene = { setState: (s: SceneState) => void; destroy: () => void };

// The shared FRA 3D scene lives at /deck/scene.js (also used by the finals deck).
// Loaded at runtime so the app builds without it; until it is there, or without WebGL, the fallback shows.
const SCENE_URL = "/deck/scene.js";

export function SceneHero({
  od,
  r18Open,
  wind,
  fallback,
  className,
}: SceneState & { fallback: ReactNode; className?: string }) {
  const box = useRef<HTMLDivElement>(null);
  const scene = useRef<Scene | null>(null);
  const [failed, setFailed] = useState(false);
  // Latest forecast state, so a scene that finishes loading late still starts on it.
  const state = useRef<SceneState>({ od, r18Open, wind });

  useEffect(() => {
    let alive = true;
    import(/* webpackIgnore: true */ /* turbopackIgnore: true */ SCENE_URL)
      .then((m: { mount: (el: HTMLElement, o: object) => Scene }) => {
        if (!alive || !box.current) return;
        scene.current = m.mount(box.current, { ...state.current, intro: true, labels: true });
      })
      .catch(() => alive && setFailed(true));
    return () => {
      alive = false;
      scene.current?.destroy();
      scene.current = null;
    };
  }, []);

  // Drive the scene from the forecast, not from a demo loop.
  useEffect(() => {
    state.current = { od, r18Open, wind };
    scene.current?.setState(state.current);
  }, [od, r18Open, wind?.dir, wind?.kt]); // eslint-disable-line react-hooks/exhaustive-deps

  if (failed) return <>{fallback}</>;
  return (
    <div
      ref={box}
      role="img"
      aria-label={`3D view of Frankfurt runways, operating direction ${od}, runway 18 ${r18Open ? "open" : "closed"}`}
      className={className}
    />
  );
}
