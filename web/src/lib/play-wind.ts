import type { OD } from "./forecast-types.ts";

// Official limits from ml/rules.json (fraalliance-brief-2026-10-30); formulas as in ml/rules.py.
export const LANDING_HEADING_DEG: Record<OD, number> = { "25": 250, "07": 70 };
export const LANDING_CHANGE_NOW_KT = 10;
export const LANDING_TOLERANCE_MINUTES = 30;
export const R18_HEADING_DEG = 180;
export const R18_TAILWIND_LIMIT_KT = 15;
export const R18_CROSSWIND_LIMIT_KT = 40;

// Signed knots, positive behind the aircraft.
export function tailwind(speedKt: number, windFromDeg: number, headingDeg: number) {
  return speedKt * Math.cos(((windFromDeg - headingDeg - 180) * Math.PI) / 180);
}

export function crosswind(speedKt: number, windFromDeg: number, headingDeg: number) {
  return Math.abs(speedKt * Math.sin(((windFromDeg - headingDeg) * Math.PI) / 180));
}

export interface PlayWindResult {
  od: OD;
  flipped: boolean;
  // Tailwind on the landing direction that stays in use, after any flip.
  tailwindKt: number;
  // 0 < tailwind < 10 kt: the rules tolerate it for up to 30 minutes, then the direction changes.
  tolerated: boolean;
  r18Open: boolean;
  r18Reason: "tailwind" | "crosswind" | null;
  r18TailwindKt: number;
}

// One step of the official rules for a wind the user sets now. No gust control, so gusts equal the mean wind.
export function playWind(current: OD, windFromDeg: number, windKt: number): PlayWindResult {
  const calm = windKt <= 0;
  const flipped = !calm && tailwind(windKt, windFromDeg, LANDING_HEADING_DEG[current]) >= LANDING_CHANGE_NOW_KT;
  const od: OD = flipped ? (current === "25" ? "07" : "25") : current;
  const tailwindKt = calm ? 0 : tailwind(windKt, windFromDeg, LANDING_HEADING_DEG[od]);
  const r18TailwindKt = tailwind(windKt, windFromDeg, R18_HEADING_DEG);
  const r18Reason =
    r18TailwindKt >= R18_TAILWIND_LIMIT_KT
      ? "tailwind"
      : crosswind(windKt, windFromDeg, R18_HEADING_DEG) > R18_CROSSWIND_LIMIT_KT
        ? "crosswind"
        : null;
  return {
    od,
    flipped,
    tailwindKt,
    tolerated: !calm && tailwindKt > 1e-9 && tailwindKt < LANDING_CHANGE_NOW_KT,
    r18Open: r18Reason === null,
    r18Reason,
    r18TailwindKt,
  };
}
