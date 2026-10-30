// One real day: a 48 h hindcast vs what was actually flown. Model chance of west (smooth line),
// official rules (thin step line), recorded direction (strip), and the moment of the switch.
// Data: ./example.data.js (generated from web/public/forecasts/2026-10-28.json and 2026-10-29.json).
// Usage: import { mount } from './viz/example.js'; const v = mount(el, { day: "2026-10-28" }); v.replay();
import { DAYS } from "./example.data.js";

let last = null;
const NS = "http://www.w3.org/2000/svg";

function cssVar(el, names, fallback) {
  const cs = getComputedStyle(el);
  for (const n of names) {
    const v = cs.getPropertyValue(n).trim();
    if (v) return v;
  }
  return fallback;
}
function svg(tag, attrs = {}, parent) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}
const easeInOut = (t) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);
const easeOut = (t) => 1 - Math.pow(1 - t, 3);
const WD = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

// Monotone cubic (Fritsch-Carlson) path through points, no overshoot.
function monotonePath(pts) {
  const n = pts.length;
  if (n < 2) return "";
  const dx = [], dy = [], m = [];
  for (let i = 0; i < n - 1; i++) { dx[i] = pts[i + 1][0] - pts[i][0]; dy[i] = (pts[i + 1][1] - pts[i][1]) / dx[i]; }
  m[0] = dy[0]; m[n - 1] = dy[n - 2];
  for (let i = 1; i < n - 1; i++) m[i] = dy[i - 1] * dy[i] <= 0 ? 0 : (dy[i - 1] + dy[i]) / 2;
  for (let i = 0; i < n - 1; i++) {
    if (dy[i] === 0) { m[i] = 0; m[i + 1] = 0; continue; }
    const a = m[i] / dy[i], b = m[i + 1] / dy[i], h = a * a + b * b;
    if (h > 9) { const t = 3 / Math.sqrt(h); m[i] = t * a * dy[i]; m[i + 1] = t * b * dy[i]; }
  }
  let d = `M${pts[0][0]},${pts[0][1]}`;
  for (let i = 0; i < n - 1; i++) {
    const h = dx[i];
    d += ` C${pts[i][0] + h / 3},${pts[i][1] + (m[i] * h) / 3} ${pts[i + 1][0] - h / 3},${pts[i + 1][1] - (m[i + 1] * h) / 3} ${pts[i + 1][0]},${pts[i + 1][1]}`;
  }
  return d;
}

export function mount(el, opts = {}) {
  const day = DAYS[opts.day] ? opts.day : "2026-10-28";
  const D = DAYS[day];
  el.innerHTML = "";
  const fg = cssVar(el, ["--fg", "--ink"], "#1b1b1f");
  const muted = cssVar(el, ["--muted"], "#6b6b78");
  const line = cssVar(el, ["--line"], "#dcdce4");
  const west = cssVar(el, ["--west"], "#2f6fdb");
  const east = cssVar(el, ["--east"], "#e39b2d");
  const accent = cssVar(el, ["--accent", "--west"], west);
  const rulesCol = opts.rulesColor ?? "#8e8ea3";

  const hrs = D.hours;
  const N = hrs.length;
  const W = 1640, H = 760;
  const L = 130, R = 30, T = 96, PH = 440;
  const stripY = T + PH + 34, stripH = 56;
  const pw = W - L - R;
  const xAt = (i) => L + (pw * (i + 0.5)) / N; // centre of hour i
  const xEdge = (i) => L + (pw * i) / N;
  const yAt = (p) => T + PH * (1 - p);

  const s = svg("svg", { viewBox: `0 0 ${W} ${H}`, width: "100%", height: "100%", preserveAspectRatio: "xMidYMid meet" });
  s.style.cssText = "display:block;overflow:visible;font-family:inherit;font-variant-numeric:tabular-nums;";
  el.appendChild(s);

  // legend
  const leg = svg("g", {}, s);
  svg("line", { x1: 0, x2: 44, y1: 30, y2: 30, stroke: accent, "stroke-width": 7, "stroke-linecap": "round" }, leg);
  svg("text", { x: 58, y: 40, "font-size": 30, "font-weight": 700, fill: fg }, leg).textContent = "our model: how sure of west";
  svg("line", { x1: 520, x2: 564, y1: 30, y2: 30, stroke: rulesCol, "stroke-width": 3 }, leg);
  svg("text", { x: 578, y: 40, "font-size": 30, "font-weight": 500, fill: muted }, leg).textContent = "official rules";
  svg("rect", { x: 820, y: 14, width: 18, height: 32, rx: 3, fill: west }, leg);
  svg("rect", { x: 840, y: 14, width: 18, height: 32, rx: 3, fill: east }, leg);
  svg("text", { x: 872, y: 40, "font-size": 30, "font-weight": 500, fill: muted }, leg).textContent = "actually flown";

  // frame: west/east labels and 50/50 guide
  svg("line", { x1: L, x2: L, y1: T, y2: T + PH, stroke: line, "stroke-width": 2 }, s);
  svg("line", { x1: L, x2: L + pw, y1: yAt(0.5), y2: yAt(0.5), stroke: line, "stroke-width": 2, "stroke-dasharray": "6 8" }, s);
  const yl = (txt, y, col, wgt) => { const t = svg("text", { x: L - 18, y, "text-anchor": "end", "font-size": 28, "font-weight": wgt, fill: col }, s); t.textContent = txt; };
  yl("west", yAt(1) + 22, west, 700);
  yl("50/50", yAt(0.5) + 9, muted, 500);
  yl("east", yAt(0) - 6, east, 700);

  // x axis: day boundaries and noon ticks (local time)
  const gx = svg("g", {}, s);
  hrs.forEach((h, i) => {
    const hh = +h.local.slice(11, 13);
    if (hh === 0 || hh === 12) {
      const x = xEdge(i);
      svg("line", { x1: x, x2: x, y1: T, y2: stripY + stripH, stroke: line, "stroke-width": hh === 0 ? 2 : 1 }, gx);
      const d = new Date(h.local.slice(0, 10) + "T00:00:00Z");
      const t = svg("text", { x, y: stripY + stripH + 40, "text-anchor": "middle", "font-size": 24, "font-weight": hh === 0 ? 700 : 500, fill: hh === 0 ? fg : muted }, gx);
      t.textContent = hh === 0 ? `${WD[d.getUTCDay()]} ${d.getUTCDate()} Oct` : "12:00";
    }
  });
  const first = new Date(hrs[0].local.slice(0, 10) + "T00:00:00Z");
  const t0l = svg("text", { x: L, y: stripY + stripH + 40, "text-anchor": "start", "font-size": 24, "font-weight": 700, fill: fg }, gx);
  t0l.textContent = `${WD[first.getUTCDay()]} ${first.getUTCDate()} Oct`;
  if (+hrs[0].local.slice(11, 13) <= 1) t0l.setAttribute("x", L);

  // official rules: thin step line
  let rd = "";
  hrs.forEach((h, i) => {
    const y = yAt(h.rules === "25" ? 1 : 0);
    rd += (i === 0 ? `M${xEdge(i)},${y}` : ` L${xEdge(i)},${y}`) + ` L${xEdge(i + 1)},${y}`;
  });
  const rulesPath = svg("path", { d: rd, fill: "none", stroke: rulesCol, "stroke-width": 3, "stroke-linejoin": "round" }, s);

  // model: smooth line of chance of west
  const pts = hrs.map((h, i) => [xAt(i), yAt(h.p_west)]);
  const modelPath = svg("path", { d: monotonePath(pts), fill: "none", stroke: accent, "stroke-width": 7, "stroke-linecap": "round", "stroke-linejoin": "round" }, s);

  // actual strip
  const strip = svg("g", {}, s);
  svg("text", { x: L - 18, y: stripY + stripH / 2 + 9, "text-anchor": "end", "font-size": 24, "font-weight": 600, fill: muted }, s).textContent = "flown";
  const cells = hrs.map((h, i) => svg("rect", {
    x: xEdge(i) + 0.5, y: stripY, width: pw / N - 1, height: stripH,
    fill: h.actual === "25" ? west : h.actual === "07" ? east : line, opacity: 0,
  }, strip));

  // the switch: first hour whose recorded direction differs from the start
  const startOd = hrs.find((h) => h.actual)?.actual;
  const sw = hrs.findIndex((h) => h.actual && h.actual !== startOd);
  let mark = null;
  if (sw > 0) {
    mark = svg("g", { opacity: 0 }, s);
    const x = xEdge(sw);
    svg("line", { x1: x, x2: x, y1: T - 8, y2: stripY + stripH + 8, stroke: fg, "stroke-width": 3 }, mark);
    const tx = svg("text", { x: x + 14, y: T + 34, "font-size": 30, "font-weight": 800, fill: fg }, mark);
    tx.textContent = `switch ${hrs[sw].local.slice(11, 16)}`;
    const sub = svg("text", { x: x + 14, y: T + 66, "font-size": 24, "font-weight": 500, fill: muted }, mark);
    sub.textContent = `${startOd === "25" ? "west" : "east"} → ${hrs[sw].actual === "25" ? "west" : "east"}`;
  }
  const note = svg("text", { x: W - R, y: H - 4, "text-anchor": "end", "font-size": 22, fill: muted }, s);
  note.textContent = `forecast made ${first.getUTCDate()} Oct 00:00 · grey = no record`;

  const lenM = modelPath.getTotalLength ? modelPath.getTotalLength() || 3000 : 3000;
  const lenR = rulesPath.getTotalLength ? rulesPath.getTotalLength() || 3000 : 3000;
  const DRAW = 2600, STRIP0 = 2700, STRIP = 1200, MARK0 = 4000;

  let raf = 0, t0 = 0;
  function frame(now) {
    if (!t0) t0 = now;
    const el_ = now - t0;
    const p = easeInOut(Math.min(1, el_ / DRAW));
    modelPath.setAttribute("stroke-dasharray", `${lenM} ${lenM}`);
    modelPath.setAttribute("stroke-dashoffset", lenM * (1 - p));
    rulesPath.setAttribute("stroke-dasharray", `${lenR} ${lenR}`);
    rulesPath.setAttribute("stroke-dashoffset", lenR * (1 - p));
    const sp = Math.max(0, Math.min(1, (el_ - STRIP0) / STRIP));
    cells.forEach((c, i) => c.setAttribute("opacity", Math.max(0, Math.min(1, sp * N - i))));
    if (mark) mark.setAttribute("opacity", easeOut(Math.max(0, Math.min(1, (el_ - MARK0) / 500))));
    if (el_ < MARK0 + 600) raf = requestAnimationFrame(frame);
  }
  function replay() {
    cancelAnimationFrame(raf);
    t0 = 0;
    raf = requestAnimationFrame(frame);
  }
  replay();
  const api = { replay, destroy() { cancelAnimationFrame(raf); el.innerHTML = ""; } };
  last = api;
  return api;
}

export function replay() { if (last) last.replay(); }
