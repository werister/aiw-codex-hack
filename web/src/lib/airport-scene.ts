import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { mergeGeometries } from "three/addons/utils/BufferGeometryUtils.js";
import { buildTrafficPlan, sampleFlight, type AirportSceneState, type FlightRole } from "./airport-traffic";
import type { HourForecast } from "./forecast-types";

type State = AirportSceneState & {
  forecastHour?: Pick<HourForecast, "time" | "local" | "lead_h" | "p_18_usable" | "certainty">;
};
type Options = State & { theme?: "light" | "tower"; paused?: boolean; onReady?: () => void; onError?: (error: unknown) => void };
const MODEL_ROOT = "/models/airport/";
const ROLES: FlightRole[] = ["arrive_north", "arrive_south", "depart_center", "depart_flex"];
const CYCLE_SECONDS = 20;

// Blender +Z up/+Y north becomes glTF +Y up/-Z north.
function world(point: readonly number[]) { return new THREE.Vector3(point[0], point[2], -point[1]); }
function heading(degrees: number) {
  const a = THREE.MathUtils.degToRad(degrees);
  return new THREE.Vector3(Math.sin(a), 0, -Math.cos(a));
}
function release(roots: THREE.Object3D[]) {
  const geometry = new Set<THREE.BufferGeometry>();
  const materials = new Set<THREE.Material>();
  roots.forEach((root) => root.traverse((object) => {
    const mesh = object as THREE.Mesh;
    if (mesh.geometry) geometry.add(mesh.geometry);
    if (mesh.material) (Array.isArray(mesh.material) ? mesh.material : [mesh.material]).forEach((m) => materials.add(m));
  }));
  geometry.forEach((g) => g.dispose());
  materials.forEach((m) => m.dispose());
}

// Blender keeps every window and marking editable. Batch static parts by
// material at load time so that this detail does not cost thousands of draws.
function batchModel(root: THREE.Object3D) {
  root.updateMatrixWorld(true);
  const batches = new Map<string, { material: THREE.Material; cast: boolean; receive: boolean; parts: THREE.BufferGeometry[] }>();
  const originals = new Set<THREE.BufferGeometry>();
  root.traverse((object) => {
    if (!(object instanceof THREE.Mesh) || Array.isArray(object.material)) return;
    const key = `${object.material.uuid}:${object.castShadow}:${object.receiveShadow}`;
    let batch = batches.get(key);
    if (!batch) {
      batch = { material: object.material, cast: object.castShadow, receive: object.receiveShadow, parts: [] };
      batches.set(key, batch);
    }
    const geometry = object.geometry.index ? object.geometry.toNonIndexed() : object.geometry.clone();
    geometry.applyMatrix4(object.matrixWorld);
    batch.parts.push(geometry);
    originals.add(object.geometry);
  });
  const result = new THREE.Group();
  for (const batch of batches.values()) {
    const geometry = mergeGeometries(batch.parts);
    if (!geometry) throw new Error("Airport geometry could not be batched");
    const mesh = new THREE.Mesh(geometry, batch.material);
    mesh.castShadow = batch.cast;
    mesh.receiveShadow = batch.receive;
    result.add(mesh);
    batch.parts.forEach((part) => part.dispose());
  }
  originals.forEach((geometry) => geometry.dispose());
  return result;
}

/** The forecast owns state. Only the illustrative motion loops; it never picks an OD. */
export function mount(host: HTMLElement, options: Options) {
  let state: State = options;
  let disposed = false;
  let ready = false;
  let visible = true;
  let paused = options.paused ?? window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let elapsed = 0;
  let previousTime = 0;
  let animationId = 0;
  let dirty = true;
  let frameCount = 0;
  let lastStatsAt = 0;
  let statsFrames = 0;
  const abort = new AbortController();
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: "high-performance" });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.AgXToneMapping;
  renderer.toneMappingExposure = 1.25;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  const canvas = renderer.domElement;
  canvas.style.cssText = "display:block;width:100%;height:100%;touch-action:pan-y";
  canvas.setAttribute("aria-hidden", "true");
  canvas.dataset.antialias = String(renderer.getContext().getContextAttributes()?.antialias ?? false);
  host.appendChild(canvas);

  const scene = new THREE.Scene();
  const towerTheme = options.theme === "tower";
  const background = towerTheme ? 0x16144d : 0xedf0ef;
  scene.background = new THREE.Color(background);
  const camera = new THREE.OrthographicCamera(-650, 650, 470, -470, 1, 6000);
  camera.position.set(660, 1550, 1000);
  camera.zoom = 1.12;
  const controls = new OrbitControls(camera, canvas);
  canvas.style.touchAction = "pan-y";
  controls.target.set(0, 0, 55);
  controls.enableDamping = true;
  controls.dampingFactor = 0.09;
  controls.minZoom = 0.8;
  controls.maxZoom = 3.5;
  controls.minPolarAngle = 0.15;
  controls.maxPolarAngle = Math.PI * 0.47;
  controls.enablePan = false;
  controls.update();
  scene.add(new THREE.HemisphereLight(0xe4efff, 0x718172, towerTheme ? 1.1 : 2.1));
  const sun = new THREE.DirectionalLight(0xfff4df, towerTheme ? 1.8 : 3.2);
  sun.position.set(-500, 1000, 350);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  Object.assign(sun.shadow.camera, { left: -720, right: 720, top: 720, bottom: -720, near: 1, far: 2200 });
  sun.shadow.normalBias = 0.3;
  sun.shadow.bias = -0.00015;
  scene.add(sun);
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(5000, 5000), new THREE.MeshStandardMaterial({ color: background, roughness: 1 }));
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = -3.2;
  floor.receiveShadow = true;
  scene.add(floor);

  const indicators = new THREE.Group();
  scene.add(indicators);
  const arrows: THREE.ArrowHelper[] = [];
  const closure = new THREE.Group();
  for (const angle of [-Math.PI / 4, Math.PI / 4]) {
    const bar = new THREE.Mesh(new THREE.BoxGeometry(32, 0.5, 3.5), new THREE.MeshStandardMaterial({ color: 0xd9381e, roughness: 1 }));
    bar.rotation.y = angle;
    closure.add(bar);
  }
  indicators.add(closure);
  const windArrow = new THREE.ArrowHelper(heading(180), new THREE.Vector3(345, 4, -170), 65, 0x334a63, 18, 12);
  indicators.add(windArrow);
  const labelLayer = document.createElement("div");
  labelLayer.style.cssText = "position:absolute;inset:0;pointer-events:none;overflow:hidden";
  labelLayer.setAttribute("aria-hidden", "true");
  host.appendChild(labelLayer);
  const labels: { element: HTMLSpanElement; position: THREE.Vector3 }[] = [];
  function label(text: string, position: THREE.Vector3) {
    const element = document.createElement("span");
    element.textContent = text;
    element.style.cssText = "position:absolute;transform:translate(-50%,-50%);white-space:nowrap;font-size:10px;font-weight:500;letter-spacing:.02em;color:#273a4a;background:rgba(248,250,248,.88);padding:2px 5px;border-radius:4px";
    labelLayer.appendChild(element);
    labels.push({ element, position });
    return element;
  }
  const windLabel = label("Wind", new THREE.Vector3(345, 4, -120));
  let bounds: THREE.Box3 | null = null;
  let manifest: Parameters<typeof buildTrafficPlan>[0] | null = null;
  let plan: ReturnType<typeof buildTrafficPlan> | null = null;
  const planes = new Map<FlightRole, THREE.Object3D>();
  let routeLine: THREE.Line | null = null;

  function resize() {
    const width = Math.max(1, host.clientWidth);
    const height = Math.max(1, host.clientHeight);
    renderer.setSize(width, height, false);
    const aspect = width / height;
    let halfHeight = 470;
    if (bounds) {
      camera.updateMatrixWorld();
      let x = 0, y = 0;
      for (const bx of [bounds.min.x, bounds.max.x]) for (const by of [bounds.min.y, bounds.max.y]) for (const bz of [bounds.min.z, bounds.max.z]) {
        const p = new THREE.Vector3(bx, by, bz).applyMatrix4(camera.matrixWorldInverse);
        x = Math.max(x, Math.abs(p.x)); y = Math.max(y, Math.abs(p.y));
      }
      halfHeight = Math.max(y, x / aspect) * 1.025;
    }
    camera.left = -halfHeight * aspect; camera.right = halfHeight * aspect;
    camera.top = halfHeight; camera.bottom = -halfHeight;
    camera.updateProjectionMatrix();
    dirty = true;
  }
  const resizeObserver = new ResizeObserver(resize);
  resizeObserver.observe(host);
  const visibilityObserver = new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; previousTime = 0; dirty = true; });
  visibilityObserver.observe(host);

  function applyState() {
    canvas.dataset.od = state.od;
    canvas.dataset.r18Open = String(state.r18Open);
    canvas.dataset.centerRunway = state.od + "C";
    canvas.dataset.flexRunway = state.r18Open ? "18" : state.od + "C";
    canvas.dataset.forecastTime = state.forecastHour?.time ?? "";
    canvas.dataset.paused = String(paused);
    if (!manifest) return;
    plan = buildTrafficPlan(manifest, state);
    const activeHeading = state.od === "25" ? 250 : 70;
    arrows.forEach((arrow, index) => {
      arrow.setDirection(heading(index === 3 ? 180 : activeHeading));
      arrow.setColor(index === 3 ? 0x15803d : state.od === "25" ? 0x3c36da : 0x9d2f7f);
      arrow.visible = index !== 3 || state.r18Open;
    });
    closure.visible = !state.r18Open;
    const wind = state.wind;
    windArrow.visible = !!wind && wind.kt > 0;
    if (wind) windArrow.setDirection(heading(wind.dir + 180));
    windLabel.textContent = wind ? `Wind from ${Math.round(wind.dir)}° · ${Math.round(wind.kt)} kt` : "Calm / variable wind";
    if (routeLine) { scene.remove(routeLine); release([routeLine]); }
    // The path is the actual generated taxi route; omit its airborne takeoff end.
    const taxi = plan.routes.depart_flex.slice(0, -2).map((p) => world([p[0], p[1], 2.15]));
    routeLine = new THREE.Line(new THREE.BufferGeometry().setFromPoints(taxi), new THREE.LineBasicMaterial({ color: state.r18Open ? 0x15803d : 0xd9381e }));
    scene.add(routeLine);
    dirty = true;
  }

  function updateTraffic() {
    if (!plan) return;
    const t = (elapsed % CYCLE_SECONDS) / CYCLE_SECONDS;
    ROLES.forEach((role) => {
      const plane = planes.get(role);
      if (!plane) return;
      const sample = sampleFlight(plan!, role, t);
      plane.position.copy(world(sample.position));
      const [dx, dy, dz] = sample.tangent;
      const yaw = Math.atan2(-dx, dy);
      const pitch = Math.atan2(dz, Math.hypot(dx, dy)) * THREE.MathUtils.clamp((sample.position[2] - 1.85) / 12, 0, 1);
      plane.rotation.set(pitch, yaw, 0, "YXZ");
    });
  }
  function animate(now: number) {
    if (disposed) return;
    animationId = requestAnimationFrame(animate);
    if (!ready || !visible || document.hidden) { previousTime = 0; return; }
    const delta = previousTime ? Math.min((now - previousTime) / 1000, 0.05) : 0;
    previousTime = now;
    if (!paused) { elapsed += delta; updateTraffic(); }
    const cameraMoved = controls.update();
    if (paused && !dirty && !cameraMoved) return;
    labels.forEach(({ element, position }) => {
      const p = position.clone().project(camera);
      element.style.left = `${(p.x * 0.5 + 0.5) * host.clientWidth}px`;
      element.style.top = `${(-p.y * 0.5 + 0.5) * host.clientHeight}px`;
    });
    renderer.render(scene, camera);
    dirty = false; frameCount++; statsFrames++;
    if (now - lastStatsAt >= 1000) {
      canvas.dataset.renderedFrames = String(frameCount);
      canvas.dataset.fps = lastStatsAt ? String(Math.round(statsFrames * 1000 / (now - lastStatsAt))) : "warming";
      canvas.dataset.drawCalls = String(renderer.info.render.calls);
      lastStatsAt = now; statsFrames = 0;
    }
  }
  function contextLost(event: Event) { event.preventDefault(); options.onError?.(new Error("3D graphics context unavailable")); }
  canvas.addEventListener("webglcontextlost", contextLost);
  applyState(); resize(); animationId = requestAnimationFrame(animate);

  async function loadModels() {
    const loader = new GLTFLoader();
    async function model(name: string) {
      const response = await fetch(MODEL_ROOT + name, { signal: abort.signal });
      if (!response.ok) throw new Error(`Airport model unavailable: ${name}`);
      return (await loader.parseAsync(await response.arrayBuffer(), MODEL_ROOT)).scene;
    }
    const [environment, narrowbody, widebody, layout] = await Promise.all([
      model("airport-environment.glb"), model("aircraft-narrowbody.glb"), model("aircraft-widebody.glb"),
      fetch(MODEL_ROOT + "manifest.json", { signal: abort.signal }).then((r) => {
        if (!r.ok) throw new Error("Airport layout unavailable");
        return r.json();
      }),
    ]);
    if (disposed) { release([environment, narrowbody, widebody]); return; }
    manifest = layout;
    environment.traverse((o) => {
      if (o instanceof THREE.Mesh) {
        const materials = Array.isArray(o.material) ? o.material : [o.material];
        // Ground layers receive aircraft/building shadows, but must not shadow
        // themselves: their centimetre offsets are below shadow-map precision.
        o.castShadow = !materials.every((m) => /^(Diorama|Landscape|Marking|Runway|Shoulder|Apron|Flow) ·/.test(m.name));
        o.receiveShadow = true;
      }
    });
    const airport = batchModel(environment);
    const narrow = batchModel(narrowbody);
    const wide = batchModel(widebody);
    scene.add(airport);
    bounds = new THREE.Box3().setFromObject(airport);
    ROLES.forEach((role) => {
      const aircraft = (role === "arrive_south" ? wide : narrow).clone(true);
      aircraft.scale.setScalar(role === "arrive_south" ? 0.42 : 0.6);
      aircraft.traverse((o) => { if (o instanceof THREE.Mesh) o.castShadow = true; });
      planes.set(role, aircraft); scene.add(aircraft);
    });
    ["north", "center", "south", "west"].forEach((key, index) => {
      const runway = layout.runways[key];
      const [x, y] = runway.center;
      const offset = index === 3 ? new THREE.Vector3(28, 0, 0) : new THREE.Vector3(-Math.cos(70 * Math.PI / 180) * 27, 0, -Math.sin(70 * Math.PI / 180) * 27);
      const position = world([x, y, 2.3]).add(offset);
      const arrow = new THREE.ArrowHelper(heading(index === 3 ? 180 : 250), position, 65, 0x3c36da, 17, 10);
      arrows.push(arrow); indicators.add(arrow);
      label(index === 3 ? "18 · departures" : ["07L / 25R · arrivals", "07C / 25C · departures", "07R / 25L · arrivals"][index], world([x, y, 3]).add(new THREE.Vector3(0, 0, 24)));
      if (index === 3) closure.position.copy(position);
    });
    applyState(); updateTraffic(); resize(); ready = true;
    canvas.dataset.ready = "true";
    options.onReady?.();
  }
  loadModels().catch((error) => { if (!disposed && !abort.signal.aborted) options.onError?.(error); });

  return {
    setState(next: State) {
      const reset = next.od !== state.od || next.r18Open !== state.r18Open || next.forecastHour?.time !== state.forecastHour?.time;
      state = next;
      if (reset) elapsed = 0;
      applyState(); updateTraffic(); dirty = true;
    },
    setPaused(value: boolean) { paused = value; previousTime = 0; canvas.dataset.paused = String(paused); dirty = true; },
    reset() { elapsed = 0; updateTraffic(); dirty = true; },
    destroy() {
      if (disposed) return;
      disposed = true; abort.abort(); cancelAnimationFrame(animationId);
      resizeObserver.disconnect(); visibilityObserver.disconnect(); controls.dispose();
      canvas.removeEventListener("webglcontextlost", contextLost);
      release([scene]); renderer.dispose(); canvas.remove(); labelLayer.remove();
    },
  };
}
