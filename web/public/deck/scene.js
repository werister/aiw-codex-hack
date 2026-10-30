// Shared FRA runway scene, used by the pitch deck and the dashboard hero.
//
//   import { mount } from "/deck/scene.js";
//   const fra = mount(element, { od: "25", r18Open: true });
//   fra.setState({ od: "07", r18Open: false, wind: { dir: 20, kt: 18 } });
//
// Options: od "25" | "07", r18Open, wind { dir, kt } (optional, derived from od/r18 when left out),
// story (true: keyframed 12 s loop 25 -> 07 -> 25, ignores setState), intro (tiles settle into runways),
// labels, view (name in VIEWS or { position: [x,y,z], target: [x,y,z] }), aircraftScale, pixelRatio (number or function),
// theme "light" | "tower" (the app's dark mode), onChange({ od, r18Open, wind }).
// fog: a CSS colour (the host background) to fade the far field; leave it out on a transparent hero.
// The canvas is transparent, so the host page owns the background. Three.js loads from ./vendor,
// aircraft and runway models (exported from the team's Blender kit) from ./models; primitives stand in until they load.
import * as THREE from "./vendor/three.module.min.js";
import { GLTFLoader } from "./vendor/addons/GLTFLoader.js";
import { RoomEnvironment } from "./vendor/addons/RoomEnvironment.js";

const MODELS = new URL("./models/", import.meta.url).href;
let gltfCache = null;
function loadModels() {
  if (!gltfCache) {
    const loader = new GLTFLoader();
    const get = (name) => loader.loadAsync(MODELS + name + ".glb").then((g) => g.scene, () => null);
    gltfCache = Promise.all([
      get("aircraft-narrowbody"), get("runway-07L-25R"), get("runway-07C-25C"), get("runway-07R-25L"), get("runway-18"),
    ]).then(([aircraft, nw, c, s, r18]) => ({ aircraft, runways: { NW: nw, C: c, S: s, R18: r18 } }));
  }
  return gltfCache;
}

const T = THREE;
const rad = (d) => (d * Math.PI) / 180;
const clamp01 = (x) => Math.max(0, Math.min(1, x));
const lerp = (a, b, k) => a + (b - a) * k;
const easeInOut = (k) => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2);
const easeOut = (k) => 1 - Math.pow(1 - k, 3);

// FraAlliance tokens (web/DESIGN.md, web/src/app/globals.css). west = OD 25, east = OD 07.
const PALETTE = {
  light: { west: "#3c36da", east: "#9d2f7f", ink: "#1d1a78", tile: "#e3e4fd", grey: "#d3d4e2", label: "#5d5b94", shadow: 0.1 },
  tower: { west: "#7a75ff", east: "#c24fae", ink: "#d9dafd", tile: "#2a2790", grey: "#2e2b8a", label: "#adb0f9", shadow: 0.35 },
};
const TAIL = "#1d1a78";

// Runway frame: heading 070, x east, z south, 1 unit = 100 m. Positions are schematic, not surveyed.
const D = new T.Vector3(Math.sin(rad(70)), 0, -Math.cos(rad(70)));
const L = new T.Vector3(-Math.cos(rad(70)), 0, -Math.sin(rad(70)));
const SOUTH = new T.Vector3(0, 0, 1);
const P = (along, left) => D.clone().multiplyScalar(along).add(L.clone().multiplyScalar(left));
const R18_NORTH = P(-20, 0).add(new T.Vector3(-6.1, 0, -2));

const RUNWAYS = [
  { id: "NW", center: P(-10, 12), dir: D, len: 28, names: ["07L", "25R"] },
  { id: "C", center: P(0, 0), dir: D, len: 40, names: ["07C", "25C"] },
  { id: "S", center: P(0, -5.2), dir: D, len: 40, names: ["07R", "25L"] },
  { id: "R18", center: R18_NORTH.clone().add(new T.Vector3(0, 0, 20)), dir: SOUTH, len: 40, names: ["18", null] },
];
for (const r of RUNWAYS) {
  const half = r.dir.clone().multiplyScalar(r.len / 2);
  r.a = r.center.clone().sub(half); // west end, or north end for 18
  r.b = r.center.clone().add(half);
}
const RW = Object.fromEntries(RUNWAYS.map((r) => [r.id, r]));

export const VIEWS = {
  hero: { position: [-4, 60, 74], target: [-4, 0, 6] },
  wide: { position: [-4, 80, 96], target: [-4, 0, 8] },
  top: { position: [-4, 104, 30], target: [-4, 0, 8] },
  low: { position: [-62, 20, 52], target: [-18, 0, 6] },
  intro: { position: [30, 110, 150], target: [-4, 4, 6] },
};

const STORY = [
  { od: "25", r18Open: true, wind: { dir: 250, kt: 12 } },
  { od: "07", r18Open: false, wind: { dir: 20, kt: 18 } },
];

function defaultWind(od, r18Open) {
  if (od === "07") return r18Open ? { dir: 70, kt: 10 } : { dir: 20, kt: 18 };
  return r18Open ? { dir: 250, kt: 12 } : { dir: 340, kt: 18 };
}

// Timing of one "half": one landing and one departure, 6 s.
const HALF = 6;
const TURN_AT = 4.6, TURN_DUR = 1.4, COLOR_AT = 5.1, COLOR_DUR = 0.7;
const INTRO = 2.8;

// Arrival: straight approach, flare, touchdown, rollout.
const APP = 26, TA = 3.4, VA = APP / TA, TR = 1.8, VEND = 1.2, DEC = (VA - VEND) / TR;
const SR = VA * TR - 0.5 * DEC * TR * TR, ARR_LIFE = 5.6, GLIDE = Math.tan(rad(7));
// Departure: short hold, take-off roll, rotate, climb.
const HOLD = 0.4, ACC = 2.0, VR = 7, VMAX = 9, SLO = 0.5 * ACC * (VR / ACC) ** 2;
const TMAX = VMAX / ACC, SMAX = 0.5 * ACC * TMAX * TMAX, DEP_LIFE = 5.9, CLIMB = Math.tan(rad(10));
const Y0 = 0.2;

function arrivalS(u) {
  if (u < TA) return -APP + VA * u;
  const t = u - TA;
  return t < TR ? VA * t - 0.5 * DEC * t * t : SR + VEND * (t - TR);
}
function arrivalH(s) {
  if (s >= 0) return 0;
  if (s > -4) { const x = -s / 4; return GLIDE * 4 * (2 * x * x - x * x * x); }
  return GLIDE * -s;
}
function departureS(u) {
  if (u < HOLD) return 0;
  const t = u - HOLD;
  return t < TMAX ? 0.5 * ACC * t * t : SMAX + VMAX * (t - TMAX);
}
function departureH(s) {
  const d = s - SLO;
  if (d <= 0) return 0;
  return d < 3 ? (CLIMB * d * d) / 6 : CLIMB * (d - 1.5);
}

function roundedRect(w, l, r) {
  r = Math.min(r, w / 2 - 1e-3, l / 2 - 1e-3);
  const s = new T.Shape();
  const x = -w / 2, y = -l / 2;
  s.moveTo(x + r, y);
  s.lineTo(x + w - r, y);
  s.quadraticCurveTo(x + w, y, x + w, y + r);
  s.lineTo(x + w, y + l - r);
  s.quadraticCurveTo(x + w, y + l, x + w - r, y + l);
  s.lineTo(x + r, y + l);
  s.quadraticCurveTo(x, y + l, x, y + l - r);
  s.lineTo(x, y + r);
  s.quadraticCurveTo(x, y, x + r, y);
  return s;
}
function slabGeometry(w, l, r, depth) {
  const g = new T.ExtrudeGeometry(roundedRect(w, l, r), { depth, bevelEnabled: false, curveSegments: 6 });
  g.rotateX(-Math.PI / 2); // lie flat, thickness up, shape y -> -z
  return g;
}

function buildAircraft() {
  const wing = (rootF, rootB, tipF, tipB, span, thick) => {
    const s = new T.Shape();
    s.moveTo(0, rootF); s.lineTo(span, tipF); s.lineTo(span, tipB); s.lineTo(0, rootB); s.closePath();
    const g = new T.ExtrudeGeometry(s, { depth: thick, bevelEnabled: false });
    g.rotateX(Math.PI / 2);
    return g;
  };
  const fin = new T.Shape();
  fin.moveTo(-0.5, 0); fin.lineTo(-0.9, 0.44); fin.lineTo(-1.05, 0.44); fin.lineTo(-0.95, 0); fin.closePath();
  const finGeo = new T.ExtrudeGeometry(fin, { depth: 0.024, bevelEnabled: false });
  finGeo.rotateY(-Math.PI / 2);
  finGeo.translate(0.012, 0.06, 0);
  return {
    body: new T.CylinderGeometry(0.115, 0.115, 1.25, 16).rotateX(Math.PI / 2),
    nose: new T.SphereGeometry(0.115, 16, 10).scale(1, 1, 2.2),
    tail: new T.ConeGeometry(0.115, 0.44, 16).rotateX(-Math.PI / 2),
    wing: wing(0.24, -0.16, -0.24, -0.4, 0.9, 0.028),
    stab: wing(-0.62, -0.84, -0.8, -0.93, 0.36, 0.022),
    fin: finGeo,
    engine: new T.CylinderGeometry(0.06, 0.054, 0.3, 14).rotateX(Math.PI / 2),
  };
}

function labelSprite(text) {
  const cv = document.createElement("canvas");
  cv.width = 256; cv.height = 128;
  const g = cv.getContext("2d");
  g.font = '500 72px "Inter Tight", system-ui, sans-serif';
  g.textAlign = "center"; g.textBaseline = "middle";
  g.fillStyle = "#ffffff"; // tinted per theme through the sprite colour
  g.fillText(text, 128, 66);
  const tex = new T.CanvasTexture(cv);
  tex.colorSpace = T.SRGBColorSpace;
  const sp = new T.Sprite(new T.SpriteMaterial({ map: tex, transparent: true, depthWrite: false, opacity: 0 }));
  sp.scale.set(2.4, 1.2, 1);
  return sp;
}

export function mount(container, options = {}) {
  const opts = { od: "25", r18Open: true, story: false, intro: true, labels: true, view: "hero", aircraftScale: 1.5, theme: "light", ...options };
  let pal = PALETTE[opts.theme] || PALETTE.light;
  if (opts.story) Object.assign(opts, STORY[0]);

  const renderer = new T.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
  renderer.setClearColor(0x000000, 0);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = T.PCFSoftShadowMap;
  const canvas = renderer.domElement;
  canvas.style.cssText = "position:absolute;inset:0;width:100%;height:100%;display:block";
  if (getComputedStyle(container).position === "static") container.style.position = "relative";
  container.appendChild(canvas);

  const scene = new T.Scene();
  const camera = new T.PerspectiveCamera(30, 16 / 9, 0.5, 600);
  if (opts.fog) scene.fog = new T.Fog(opts.fog, 110, 240);
  const pmrem = new T.PMREMGenerator(renderer);
  const envTex = pmrem.fromScene(new RoomEnvironment(renderer), 0.04).texture;
  scene.environment = envTex;

  scene.add(new T.HemisphereLight(0xffffff, 0xd9dafd, 2.1));
  const sun = new T.DirectionalLight(0xffffff, 1.9);
  sun.position.set(-34, 64, 30);
  sun.target.position.set(-6, 0, 8);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  Object.assign(sun.shadow.camera, { left: -70, right: 70, top: 70, bottom: -70, near: 10, far: 180 });
  sun.shadow.bias = -0.0004;
  sun.shadow.radius = 4;
  scene.add(sun, sun.target);

  const catcher = new T.Mesh(new T.PlaneGeometry(500, 500), new T.ShadowMaterial({ opacity: pal.shadow }));
  catcher.rotation.x = -Math.PI / 2;
  catcher.receiveShadow = true;
  scene.add(catcher);

  // ---- state ----
  const initWind = opts.wind || defaultWind(opts.od, opts.r18Open);
  const state = { od: opts.od, r18Open: opts.r18Open, wind: { dir: initWind.dir, kt: initWind.kt } };
  let target = { od: state.od, r18Open: state.r18Open, wind: { ...state.wind } };
  let t = 0;
  let windTween = null;
  const colorNow = { par: new T.Color(odColor(state.od)), r18: new T.Color(r18Color(state.r18Open)) };
  let colorTween = null;

  function odColor(od) { return od === "07" ? pal.east : pal.west; }
  function r18Color(open) { return open ? pal.ink : pal.grey; }

  // ---- runways: FraAlliance tiles that settle into the layout ----
  const DEPTH = 0.08;
  const TILE_START = [
    { p: [-16, 15, -2], r: [-0.9, 0.785, 0.35], s: 7.5 },
    { p: [-3, 19, 4], r: [-1.1, 0.6, -0.2], s: 9 },
    { p: [9, 14, -4], r: [-0.7, 0.95, 0.15], s: 6.5 },
    { p: [-8, 11, 16], r: [-1.25, 0.7, 0.4], s: 8 },
  ];
  const slabs = RUNWAYS.map((rw, i) => {
    const st = TILE_START[i];
    const mat = new T.MeshLambertMaterial({ color: pal.tile, transparent: true, opacity: 0.94 });
    const mesh = new T.Mesh(slabGeometry(1, 1, 0.2, DEPTH), mat);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    scene.add(mesh);
    const endQ = new T.Quaternion().setFromEuler(new T.Euler(0, Math.atan2(rw.dir.x, rw.dir.z), 0));
    const startQ = new T.Quaternion().setFromEuler(new T.Euler(st.r[0], st.r[1], st.r[2]));
    const centre = new T.Mesh(new T.PlaneGeometry(0.07, rw.len - 3).rotateX(-Math.PI / 2),
      new T.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0, depthWrite: false }));
    centre.position.copy(rw.center).setY(DEPTH + 0.01);
    centre.rotation.y = Math.atan2(rw.dir.x, rw.dir.z);
    scene.add(centre);
    return { rw, mesh, mat, centre, startQ, endQ, startP: new T.Vector3(...st.p), size: st.s, delay: i * 0.16, geoKey: "" };
  });

  let slabW = 0.9;
  function placeSlab(sl, k) {
    const e = easeInOut(clamp01(k));
    const w = lerp(sl.size, slabW, e), l = lerp(sl.size, sl.rw.len + (slabW > 0.9 ? 0.6 : 0), e), r = lerp(sl.size * 0.24, 0.25, e);
    const key = w.toFixed(3) + l.toFixed(3);
    if (key !== sl.geoKey) {
      sl.mesh.geometry.dispose();
      sl.mesh.geometry = slabGeometry(w, l, r, DEPTH);
      sl.geoKey = key;
    }
    sl.mesh.position.lerpVectors(sl.startP, sl.rw.center, e);
    sl.mesh.quaternion.slerpQuaternions(sl.startQ, sl.endQ, e);
    return e;
  }

  // ---- approach guides: rectangles on the approach side of the landing runways ----
  const guideGeo = slabGeometry(0.9, 1.3, 0.25, 0.02);
  const guides = [];
  for (const od of ["25", "07"]) {
    for (const rw of [RW.NW, RW.S]) {
      const u = od === "07" ? rw.dir.clone() : rw.dir.clone().negate();
      const thr = od === "07" ? rw.a : rw.b;
      for (let k = 0; k < 6; k++) {
        const mat = new T.MeshBasicMaterial({ color: odColor(od), transparent: true, opacity: 0, depthWrite: false });
        const m = new T.Mesh(guideGeo, mat);
        m.rotation.y = Math.atan2(rw.dir.x, rw.dir.z);
        scene.add(m);
        guides.push({ od, mesh: m, mat, k, u, thr });
      }
    }
  }

  // ---- runway labels ----
  const labels = [];
  if (opts.labels) {
    const add = () => {
      for (const rw of RUNWAYS) {
        rw.names.forEach((name, i) => {
          if (!name) return;
          const sp = labelSprite(name);
          sp.material.color.set(pal.label);
          const out = rw.dir.clone().multiplyScalar(i === 0 ? -2.4 : 2.4);
          sp.position.copy(i === 0 ? rw.a : rw.b).add(out).setY(0.8);
          scene.add(sp);
          labels.push(sp);
        });
      }
    };
    const ready = document.fonts && document.fonts.load ? document.fonts.load('500 72px "Inter Tight"') : Promise.resolve();
    ready.then(add, add);
  }

  // ---- wind arrow ----
  const arrowShape = new T.Shape();
  arrowShape.moveTo(-0.28, -3.2); arrowShape.lineTo(0.28, -3.2); arrowShape.lineTo(0.28, 1.2); arrowShape.lineTo(1.05, 1.2);
  arrowShape.lineTo(0, 3.2); arrowShape.lineTo(-1.05, 1.2); arrowShape.lineTo(-0.28, 1.2); arrowShape.closePath();
  const arrowGeo = new T.ExtrudeGeometry(arrowShape, { depth: 0.16, bevelEnabled: true, bevelThickness: 0.04, bevelSize: 0.04, bevelSegments: 2 });
  arrowGeo.rotateX(Math.PI / 2);
  const arrowMat = new T.MeshLambertMaterial({ color: pal.ink, transparent: true, opacity: 0 });
  const arrow = new T.Mesh(arrowGeo, arrowMat);
  arrow.castShadow = true;
  const ARROW_AT = P(-4, 21).setY(6);
  arrow.position.copy(ARROW_AT);
  scene.add(arrow);

  // ---- aircraft ----
  const GEO = buildAircraft();
  function makeAircraft() {
    const g = new T.Group();
    const body = new T.MeshStandardMaterial({ color: 0xffffff, roughness: 0.5, metalness: 0.05, transparent: true });
    const tail = new T.MeshStandardMaterial({ color: TAIL, roughness: 0.6, transparent: true });
    const parts = [
      [GEO.body, body], [GEO.nose, body, [0, 0, 0.62]], [GEO.tail, body, [0, 0.03, -0.84]],
      [GEO.wing, body, [0, -0.03, 0]], [GEO.wing, body, [0, -0.03, 0], -1],
      [GEO.stab, body, [0, 0.03, 0]], [GEO.stab, body, [0, 0.03, 0], -1],
      [GEO.fin, tail], [GEO.engine, tail, [0.33, -0.1, 0.12]], [GEO.engine, tail, [-0.33, -0.1, 0.12]],
    ];
    for (const [geo, mat, pos, flip] of parts) {
      const m = new T.Mesh(geo, mat);
      if (pos) m.position.set(...pos);
      if (flip) m.scale.x = -1;
      m.castShadow = true;
      g.add(m);
    }
    g.scale.setScalar(opts.aircraftScale);
    g.visible = false;
    scene.add(g);
    return { obj: g, mats: [body, tail], busy: false };
  }
  const pool = [makeAircraft(), makeAircraft(), makeAircraft(), makeAircraft()];
  const flights = [];
  let groundY = Y0;

  // Team Blender kit: real aircraft and runway models replace the primitives once loaded.
  const runwayModels = [];
  let alive = true;
  loadModels().then(({ aircraft, runways }) => {
    if (!alive) return;
    if (aircraft) {
      const box = new T.Box3().setFromObject(aircraft);
      const k = 1.75 / (box.max.z - box.min.z);
      groundY = DEPTH + 0.03;
      for (const ac of pool) {
        const model = aircraft.clone(true);
        const mats = [];
        model.traverse((m) => {
          if (!m.isMesh) return;
          m.material = m.material.clone();
          const name = m.material.name || "";
          if (name.startsWith("Livery")) m.material.color.set(TAIL);
          if (name.startsWith("Flow")) m.material.color.set("#3c36da");
          m.material.transparent = true;
          m.material.envMapIntensity = 0.7;
          m.castShadow = true;
          mats.push(m.material);
        });
        model.scale.setScalar(k);
        model.rotation.y = Math.PI; // GLB faces -Z, ours +Z
        ac.obj.clear();
        ac.obj.add(model);
        ac.mats = mats;
      }
    }
    for (const rw of RUNWAYS) {
      const src = runways[rw.id];
      if (!src) continue;
      const model = src.clone(true);
      const box = new T.Box3().setFromObject(model);
      const mats = [];
      model.traverse((m) => {
        if (!m.isMesh) return;
        m.material = m.material.clone();
        if (/^(Runway|Shoulder)/.test(m.material.name || "")) m.material.color.multiplyScalar(0.62);
        m.material.envMapIntensity = 0.5;
        m.material.transparent = true;
        m.material.opacity = 0;
        m.receiveShadow = true;
        mats.push(m.material);
      });
      const holder = new T.Group();
      holder.add(model);
      model.scale.set(0.95 / (box.max.x - box.min.x), 0.01, rw.len / (box.max.z - box.min.z));
      holder.position.copy(rw.center).setY(DEPTH + 0.005);
      holder.rotation.y = Math.atan2(rw.dir.x, rw.dir.z);
      scene.add(holder);
      runwayModels.push({ rw, mats });
    }
    if (runwayModels.length === RUNWAYS.length) {
      slabW = 1.35;
      for (const sl of slabs) sl.centre.visible = false;
    }
  });

  function spawn(kind, rw, od, startAge = 0) {
    const ac = pool.find((a) => !a.busy);
    if (!ac) return;
    ac.busy = true;
    let u, origin;
    if (kind === "arr") {
      u = od === "07" ? rw.dir.clone() : rw.dir.clone().negate();
      origin = (od === "07" ? rw.a : rw.b).clone().add(u.clone().multiplyScalar(3)); // touchdown point
    } else {
      u = rw === RW.R18 ? SOUTH.clone() : od === "07" ? rw.dir.clone() : rw.dir.clone().negate();
      origin = (rw === RW.R18 || od === "07" ? rw.a : rw.b).clone().add(u.clone().multiplyScalar(1));
    }
    flights.push({ ac, kind, rw, u, origin, age: startAge, fade: null });
  }

  const pA = new T.Vector3(), pB = new T.Vector3();
  function flightPos(f, age, out) {
    const s = f.kind === "arr" ? arrivalS(age) : departureS(age);
    const h = f.kind === "arr" ? arrivalH(s) : departureH(s);
    return out.copy(f.u).multiplyScalar(s).add(f.origin).setY(groundY + h);
  }
  function updateFlights(dt) {
    for (let i = flights.length - 1; i >= 0; i--) {
      const f = flights[i];
      f.age += dt;
      const life = f.kind === "arr" ? ARR_LIFE : DEP_LIFE;
      let op = f.kind === "arr"
        ? Math.min(clamp01(f.age / 0.5), clamp01((life - f.age) / 0.6))
        : Math.min(clamp01(f.age / 0.4), clamp01((life - f.age) / 0.7));
      if (f.fade !== null) { f.fade += dt; op = Math.min(op, 1 - clamp01(f.fade / 0.6)); }
      if (f.age >= life || (f.fade !== null && f.fade >= 0.6)) {
        f.ac.busy = false; f.ac.obj.visible = false; flights.splice(i, 1); continue;
      }
      const o = f.ac.obj;
      o.visible = true;
      flightPos(f, f.age, pA);
      flightPos(f, f.age + 0.12, pB);
      if (pB.distanceToSquared(pA) < 1e-6) pB.copy(pA).add(f.u);
      o.position.copy(pA);
      o.lookAt(pB);
      if (f.kind === "arr") {
        const s = arrivalS(f.age);
        const flare = s < 0 && s > -4 ? 1 - -s / 4 : s >= 0 ? clamp01(1 - (s / 3)) : 0;
        o.rotateX(-0.05 - 0.07 * flare);
      } else {
        o.rotateX(-0.06 * clamp01((departureS(f.age) - SLO + 1) / 2));
      }
      const easeOp = easeInOut(clamp01(op));
      for (const m of f.ac.mats) { m.opacity = easeOp; m.depthWrite = easeOp > 0.98; }
      o.traverse((m) => { m.castShadow = easeOp > 0.4; });
    }
  }

  // ---- halves: one landing, one departure ----
  let halfStart = null, halfIndex = 0, turned = false;
  function halfState(n) { return opts.story ? STORY[n % 2] : target; }
  function startHalf() {
    const s = halfState(halfIndex);
    spawn("arr", RW.S, s.od);
    spawn("dep", s.r18Open ? RW.R18 : RW.C, s.od);
    turned = false;
  }

  function beginTransition(next) {
    const from = { ...state.wind };
    windTween = { from, to: { ...next.wind }, t0: t, dur: TURN_DUR };
    if (next.od !== state.od || next.r18Open !== state.r18Open) {
      colorTween = {
        fromPar: colorNow.par.clone(), toPar: new T.Color(odColor(next.od)),
        fromR18: colorNow.r18.clone(), toR18: new T.Color(r18Color(next.r18Open)),
        t0: t + (COLOR_AT - TURN_AT), dur: COLOR_DUR, next,
      };
    }
  }

  // ---- camera ----
  const toView = (v) => {
    const view = typeof v === "string" ? VIEWS[v] || VIEWS.hero : v;
    return { position: new T.Vector3(...view.position), target: new T.Vector3(...view.target) };
  };
  let cam = toView(opts.intro ? "intro" : opts.view);
  let camTween = null;
  const camPos = cam.position.clone(), camTgt = cam.target.clone();
  function setCamera(view, seconds = 1.6) {
    const to = toView(view);
    camTween = { fromP: camPos.clone(), fromT: camTgt.clone(), to, t0: t, dur: seconds };
    cam = to;
  }

  // ---- sizing ----
  function resize() {
    const w = container.clientWidth || 1, h = container.clientHeight || 1;
    const pr = typeof opts.pixelRatio === "function" ? opts.pixelRatio() : opts.pixelRatio || window.devicePixelRatio || 1;
    renderer.setPixelRatio(Math.min(2, pr));
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  const ro = typeof ResizeObserver !== "undefined" ? new ResizeObserver(resize) : null;
  if (ro) ro.observe(container);
  resize();

  // ---- change events ----
  let lastKey = "";
  function emit() {
    if (!opts.onChange) return;
    const w = { dir: Math.round(state.wind.dir) % 360, kt: Math.round(state.wind.kt) };
    const key = state.od + state.r18Open + Math.round(w.dir / 5) + w.kt;
    if (key === lastKey) return;
    lastKey = key;
    opts.onChange({ od: state.od, r18Open: state.r18Open, wind: w });
  }

  // ---- loop ----
  let introStart = opts.intro ? 0 : -INTRO;
  if (opts.intro) setCamera(opts.view, INTRO);
  let raf = 0, last = performance.now(), visible = true;
  const io = typeof IntersectionObserver !== "undefined"
    ? new IntersectionObserver((e) => { visible = e[0].isIntersecting; })
    : null;
  if (io) io.observe(container);

  function frame(now) {
    raf = requestAnimationFrame(frame);
    const dt = Math.min(0.05, (now - last) / 1000);
    last = now;
    if (!visible) return;
    t += dt;

    // Intro: tiles settle, then guides, labels and arrow fade in.
    const ki = (t - introStart) / INTRO;
    for (const sl of slabs) {
      const k = clamp01((t - introStart - sl.delay) / (INTRO - 0.5));
      const e = placeSlab(sl, k);
      const base = sl.rw.id === "R18" ? colorNow.r18 : colorNow.par;
      sl.mat.color.set(pal.tile).lerp(base, e);
      sl.mat.opacity = lerp(0.9, 1, e);
      sl.centre.material.opacity = 0.75 * clamp01((ki - 0.85) / 0.25) * (sl.rw.id === "R18" && !state.r18Open ? 0.4 : 1);
    }
    const settled = clamp01((ki - 0.8) / 0.3);
    for (const rm of runwayModels) {
      const target = settled * (rm.rw.id === "R18" && !state.r18Open ? 0.35 : 1);
      for (const m of rm.mats) m.opacity = lerp(m.opacity, target, Math.min(1, dt * 4));
    }
    arrowMat.opacity = 0.9 * settled;
    arrow.castShadow = settled > 0.5;
    for (const sp of labels) sp.material.opacity = settled;

    // Halves start once the tiles have settled.
    if (halfStart === null && ki >= 0.9) { halfStart = t; halfIndex = 0; startHalf(); }
    if (halfStart !== null) {
      const u = t - halfStart;
      if (opts.story && !turned && u >= TURN_AT) { turned = true; beginTransition(STORY[(halfIndex + 1) % 2]); }
      if (u >= HALF) { halfStart += HALF; halfIndex++; startHalf(); }
    }

    // Wind turn.
    if (windTween) {
      const k = easeInOut(clamp01((t - windTween.t0) / windTween.dur));
      const delta = ((windTween.to.dir - windTween.from.dir + 540) % 360) - 180;
      state.wind.dir = (windTween.from.dir + delta * k + 360) % 360;
      state.wind.kt = lerp(windTween.from.kt, windTween.to.kt, k);
      if (k >= 1) windTween = null;
    }
    const vx = -Math.sin(rad(state.wind.dir)), vz = Math.cos(rad(state.wind.dir));
    arrow.rotation.y = Math.atan2(vx, vz);
    arrow.position.y = ARROW_AT.y + Math.sin(t * 0.9) * 0.12;

    // Runway colours.
    if (colorTween && t >= colorTween.t0) {
      const k = easeInOut(clamp01((t - colorTween.t0) / colorTween.dur));
      colorNow.par.copy(colorTween.fromPar).lerp(colorTween.toPar, k);
      colorNow.r18.copy(colorTween.fromR18).lerp(colorTween.toR18, k);
      if (k > 0.5) { state.od = colorTween.next.od; state.r18Open = colorTween.next.r18Open; }
      if (k >= 1) colorTween = null;
    }

    // Approach guides drift toward the threshold of the active direction.
    for (const g of guides) {
      const on = g.od === state.od ? 1 : 0;
      const phase = ((t * 0.8) % 1);
      const dist = 3 + (g.k + 1 - phase) * 3.2;
      g.mesh.position.copy(g.thr).add(g.u.clone().multiplyScalar(-dist)).setY(0.01);
      const x = g.k + 1 - phase; // 0 at the threshold, 6 far out
      const shade = clamp01(x / 0.8) * clamp01((6 - x) / 1.2) * (1 - x / 8);
      g.mat.opacity = lerp(g.mat.opacity, on * settled * 0.6 * shade, Math.min(1, dt * 6));
      g.mesh.visible = g.mat.opacity > 0.01;
    }

    updateFlights(dt);

    if (camTween) {
      const k = easeInOut(clamp01((t - camTween.t0) / camTween.dur));
      camPos.lerpVectors(camTween.fromP, camTween.to.position, k);
      camTgt.lerpVectors(camTween.fromT, camTween.to.target, k);
      if (k >= 1) camTween = null;
    }
    camera.position.copy(camPos);
    camera.lookAt(camTgt);

    renderer.render(scene, camera);
    emit();
  }
  raf = requestAnimationFrame(frame);

  if (opts.debug) opts.debug({ slabs, colorNow, state });
  return {
    VIEWS,
    // Drive from outside, e.g. the hour shown on the dashboard. Ignored while story is on.
    setState(next = {}) {
      const od = next.od === "07" || next.od === "25" ? next.od : target.od;
      const r18Open = typeof next.r18Open === "boolean" ? next.r18Open : target.r18Open;
      const wind = next.wind || defaultWind(od, r18Open);
      const changed = od !== target.od || r18Open !== target.r18Open;
      target = { od, r18Open, wind: { dir: wind.dir, kt: wind.kt } };
      if (opts.story) return;
      beginTransition(target);
      if (colorTween) colorTween.t0 = t; // apply now, not on the story beat
      if (changed && halfStart !== null) {
        for (const f of flights) {
          const dirBound = f.kind === "arr" || f.rw === RW.C;
          if (od !== state.od && dirBound) f.fade = 0;
          if (!r18Open && f.rw === RW.R18 && departureS(f.age) < SLO) f.fade = 0;
        }
        halfStart = t + TURN_DUR - HALF; // next half right after the turn
      }
    },
    setStory(on) {
      opts.story = !!on;
      if (!on) beginTransition(target);
    },
    setCamera,
    setTheme(name) {
      pal = PALETTE[name] || PALETTE.light;
      colorTween = null;
      colorNow.par.set(odColor(state.od));
      colorNow.r18.set(r18Color(state.r18Open));
      for (const g of guides) g.mat.color.set(odColor(g.od));
      for (const sp of labels) sp.material.color.set(pal.label);
      arrowMat.color.set(pal.ink);
      catcher.material.opacity = pal.shadow;
    },
    replayIntro() { introStart = t; halfStart = null; for (const f of flights) f.fade = 0; },
    getState: () => ({ od: state.od, r18Open: state.r18Open, wind: { ...state.wind } }),
    resize,
    destroy() {
      alive = false;
      cancelAnimationFrame(raf);
      envTex.dispose();
      pmrem.dispose();
      if (ro) ro.disconnect();
      if (io) io.disconnect();
      renderer.dispose();
      canvas.remove();
    },
  };
}
