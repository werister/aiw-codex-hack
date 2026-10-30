import type { OD } from "./forecast-types.ts";

export type FlightRole = "arrive_north" | "arrive_south" | "depart_center" | "depart_flex";
export type Point = readonly [number, number, number];

export interface AirportRunwayMetadata {
  center: readonly [number, number];
  heading: number;
  length: number;
  width?: number;
}

export interface AirportFlightTiming {
  start: number;
  finish: number;
}

export interface AirportManifestPhase {
  od: OD;
  runway_18_usable: boolean;
  timing: Partial<Record<FlightRole, AirportFlightTiming>>;
}

export interface AirportManifestMinimal {
  runways: Record<"north" | "center" | "south" | "west", AirportRunwayMetadata>;
  demonstration_phases: readonly AirportManifestPhase[];
}

export interface AirportSceneState {
  od: OD;
  r18Open: boolean;
  wind?: { dir: number; kt: number };
}

export interface AirportTrafficPlan {
  routes: Record<FlightRole, Point[]>;
  timing: Record<FlightRole, AirportFlightTiming>;
}

export interface FlightSample {
  position: Point;
  tangent: Point;
  progress: number;
}

interface Vec3 {
  x: number;
  y: number;
  z: number;
}

interface ArcSample {
  distance: number;
  position: Point;
  tangent: Point;
}

interface RouteArc {
  samples: ArcSample[];
  length: number;
}

const FLIGHT_ROLES: readonly FlightRole[] = [
  "arrive_north",
  "arrive_south",
  "depart_center",
  "depart_flex",
];
const CORNER_STEPS = 24;
const RAMP = 0.08;
const routeArcs = new WeakMap<AirportTrafficPlan, Record<FlightRole, RouteArc>>();

function point(x: number, y: number, z: number): Point {
  return [x, y, z];
}

function add(a: Vec3, b: Vec3): Vec3 {
  return { x: a.x + b.x, y: a.y + b.y, z: a.z + b.z };
}

function subtract(a: Vec3, b: Vec3): Vec3 {
  return { x: a.x - b.x, y: a.y - b.y, z: a.z - b.z };
}

function scale(v: Vec3, n: number): Vec3 {
  return { x: v.x * n, y: v.y * n, z: v.z * n };
}

function magnitude(v: Vec3): number {
  return Math.hypot(v.x, v.y, v.z);
}

function normalize(v: Vec3): Vec3 {
  const length = magnitude(v);
  if (length < 1e-12) return { x: 0, y: 0, z: 0 };
  return scale(v, 1 / length);
}

function vector(p: Point): Vec3 {
  return { x: p[0], y: p[1], z: p[2] };
}

function tuple(v: Vec3): Point {
  return [v.x, v.y, v.z];
}

function interpolate(a: Vec3, b: Vec3, t: number): Vec3 {
  return add(a, scale(subtract(b, a), t));
}

function dotXY(a: readonly [number, number], b: Vec3): number {
  return a[0] * b.x + a[1] * b.y;
}

function runwayPoint(runway: AirportRunwayMetadata, along: number, height = 1.85): Point {
  const heading = (runway.heading * Math.PI) / 180;
  return point(
    runway.center[0] + Math.sin(heading) * along,
    runway.center[1] + Math.cos(heading) * along,
    height,
  );
}

function basis(manifest: AirportManifestMinimal) {
  const heading = (manifest.runways.center.heading * Math.PI) / 180;
  const along: readonly [number, number] = [Math.sin(heading), Math.cos(heading)];
  const across: readonly [number, number] = [-along[1], along[0]];
  return { along, across };
}

function airportPoint(along: number, across: number, height: number, axes: ReturnType<typeof basis>): Point {
  return point(
    axes.along[0] * along + axes.across[0] * across,
    axes.along[1] * along + axes.across[1] * across,
    height,
  );
}

function routesFor(
  manifest: AirportManifestMinimal,
  state: AirportSceneState,
): Record<FlightRole, Point[]> {
  const direction = state.od === "07" ? 1 : -1;
  const axes = basis(manifest);
  const routes = {} as Record<FlightRole, Point[]>;

  for (const key of ["north", "south"] as const) {
    const runway = manifest.runways[key];
    const half = runway.length / 2;
    routes[key === "north" ? "arrive_north" : "arrive_south"] = [
      runwayPoint(runway, -direction * (half + 85), 32),
      runwayPoint(runway, -direction * (half - 28)),
      runwayPoint(runway, direction * (half - 60)),
    ];
  }

  const center = manifest.runways.center;
  const half = center.length / 2;
  const entry = runwayPoint(center, -direction * (half - 18));
  const centerAcross = dotXY(center.center, {
    x: axes.across[0],
    y: axes.across[1],
    z: 0,
  });
  const lane = add(vector(entry), {
    x: axes.across[0] * 40,
    y: axes.across[1] * 40,
    z: 0,
  });
  routes.depart_center = [
    airportPoint(65, 55, 1.85, axes),
    airportPoint(65, 40 + centerAcross, 1.85, axes),
    tuple(lane),
    entry,
    runwayPoint(center, direction * 110),
    runwayPoint(center, direction * (half + 150), 58),
  ];

  if (state.r18Open) {
    const west = manifest.runways.west;
    const westHalf = west.length / 2;
    const start = airportPoint(-150, 70, 1.85, axes);
    routes.depart_flex = [
      start,
      point(-230, start[1], 1.85),
      point(-285, 60, 1.85),
      runwayPoint(west, -westHalf + 17),
      runwayPoint(west, 110),
      runwayPoint(west, westHalf + 75, 40),
    ];
  } else {
    routes.depart_flex = [
      airportPoint(-150, 70, 1.85, axes),
      airportPoint(-150, 40 + centerAcross, 1.85, axes),
      tuple(lane),
      entry,
      runwayPoint(center, direction * 110),
      runwayPoint(center, direction * (half + 105), 38),
    ];
  }

  return routes;
}

function fillet(points: readonly Point[]): Vec3[] {
  const result: Vec3[] = [vector(points[0])];
  for (let i = 1; i < points.length - 1; i += 1) {
    const a = vector(points[i - 1]);
    const b = vector(points[i]);
    const c = vector(points[i + 1]);
    const ab = subtract(a, b);
    const cb = subtract(c, b);
    const distance = Math.min(18, magnitude(ab) * 0.25, magnitude(cb) * 0.25);
    const entry = add(b, scale(normalize(ab), distance));
    const exit = add(b, scale(normalize(cb), distance));
    result.push(entry);
    for (let step = 1; step <= CORNER_STEPS; step += 1) {
      const t = step / CORNER_STEPS;
      const oneMinusT = 1 - t;
      result.push(add(
        add(scale(entry, oneMinusT * oneMinusT), scale(b, 2 * oneMinusT * t)),
        scale(exit, t * t),
      ));
    }
  }
  result.push(vector(points[points.length - 1]));
  return result;
}

function buildArc(points: readonly Point[]): RouteArc {
  const control = fillet(points);
  const directions = control.slice(1).map((next, index) =>
    normalize(subtract(next, control[index])));
  const samples: ArcSample[] = [];
  let distance = 0;
  for (let index = 0; index < control.length; index += 1) {
    let tangent: Vec3;
    if (index === 0) tangent = directions[0];
    else if (index === control.length - 1) tangent = directions[directions.length - 1];
    else {
      tangent = normalize(add(directions[index - 1], directions[index]));
      if (magnitude(tangent) < 1e-12) tangent = directions[index];
    }
    if (index > 0) distance += magnitude(subtract(control[index], control[index - 1]));
    samples.push({ distance, position: tuple(control[index]), tangent: tuple(tangent) });
  }
  return { samples, length: distance };
}

function smoothProgress(t: number): number {
  if (t <= 0) return 0;
  if (t >= 1) return 1;
  if (t < RAMP) return (t * t) / (2 * RAMP * (1 - RAMP));
  if (t > 1 - RAMP) return 1 - ((1 - t) ** 2) / (2 * RAMP * (1 - RAMP));
  return (t - RAMP / 2) / (1 - RAMP);
}

function findTimingPhase(
  manifest: AirportManifestMinimal,
  state: AirportSceneState,
): AirportManifestPhase | undefined {
  return manifest.demonstration_phases.find((phase) =>
    phase.od === state.od && phase.runway_18_usable === state.r18Open)
    ?? manifest.demonstration_phases.find((phase) => phase.runway_18_usable === state.r18Open);
}

function getTiming(
  manifest: AirportManifestMinimal,
  state: AirportSceneState,
): Record<FlightRole, AirportFlightTiming> {
  const fixture = findTimingPhase(manifest, state);
  if (!fixture) throw new Error("Airport manifest has no " + (state.r18Open ? "open" : "closed") + " runway 18 timing");
  const timing = {} as Record<FlightRole, AirportFlightTiming>;
  for (const role of FLIGHT_ROLES) {
    const value = fixture.timing[role];
    if (!value || !Number.isFinite(value.start) || !Number.isFinite(value.finish)
      || value.start < 0 || value.finish > 1 || value.finish <= value.start) {
      throw new Error("Airport manifest has invalid " + role + " timing");
    }
    timing[role] = { start: value.start, finish: value.finish };
  }
  return timing;
}

function sampleArc(route: RouteArc, progress: number): { position: Point; tangent: Point } {
  if (progress <= 0) return { position: route.samples[0].position, tangent: route.samples[0].tangent };
  if (progress >= 1) {
    const last = route.samples[route.samples.length - 1];
    return { position: last.position, tangent: last.tangent };
  }

  const target = route.length * progress;
  let low = 0;
  let high = route.samples.length - 1;
  while (low < high) {
    const mid = (low + high) >>> 1;
    if (route.samples[mid].distance < target) low = mid + 1;
    else high = mid;
  }
  const right = route.samples[low];
  const left = route.samples[Math.max(0, low - 1)];
  const span = right.distance - left.distance;
  const local = span > 0 ? (target - left.distance) / span : 0;
  const position = tuple(interpolate(vector(left.position), vector(right.position), local));
  const smoothLocal = local * local * (3 - 2 * local);
  const tangent = tuple(normalize(interpolate(vector(left.tangent), vector(right.tangent), smoothLocal)));
  return { position, tangent };
}

/** Build traffic routes in the same Blender display-metre coordinates as the GLBs. */
export function buildTrafficPlan(
  manifest: AirportManifestMinimal,
  state: AirportSceneState,
): AirportTrafficPlan {
  if (state.od !== "25" && state.od !== "07") throw new Error("Operating direction must be 25 or 07");
  for (const key of ["north", "center", "south", "west"] as const) {
    const runway = manifest.runways[key];
    if (!runway || !Number.isFinite(runway.heading) || !Number.isFinite(runway.length) || runway.length <= 0
      || !runway.center.every(Number.isFinite)) {
      throw new Error("Airport manifest has invalid " + key + " runway geometry");
    }
  }
  if (state.wind && (!Number.isFinite(state.wind.dir) || !Number.isFinite(state.wind.kt)
    || state.wind.dir < 0 || state.wind.dir >= 360 || state.wind.kt < 0)) {
    throw new Error("Wind needs a direction in [0, 360) and a nonnegative speed");
  }

  const routes = routesFor(manifest, state);
  const timing = getTiming(manifest, state);
  const plan: AirportTrafficPlan = { routes, timing };
  routeArcs.set(plan, Object.fromEntries(
    FLIGHT_ROLES.map((role) => [role, buildArc(routes[role])]),
  ) as Record<FlightRole, RouteArc>);
  return plan;
}

/** Sample a flight at normalized scene time; 0..1 holds before/after its slot. */
export function sampleFlight(plan: AirportTrafficPlan, role: FlightRole, time: number): FlightSample {
  if (!FLIGHT_ROLES.includes(role)) throw new Error("Unknown airport flight role: " + role);
  if (!Number.isFinite(time)) throw new Error("Flight sample time must be finite");
  const arcs = routeArcs.get(plan);
  const arc = arcs?.[role];
  if (!arc) throw new Error("Traffic plan was not created by buildTrafficPlan");
  const timing = plan.timing[role];
  const elapsed = Math.min(1, Math.max(0, (time - timing.start) / (timing.finish - timing.start)));
  const progress = smoothProgress(elapsed);
  const sample = sampleArc(arc, progress);
  return { ...sample, progress };
}
