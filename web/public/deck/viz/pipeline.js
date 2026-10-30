// How it works: public weather + airport reports + flown history -> signals -> model (trees) -> 48 h forecast + how sure.
// Data: ./pipeline.data.js (ml/models/metadata.json), ./tree.data.js (tree count), ./example.data.js (sample output strip).
// Usage: import { mount } from './viz/pipeline.js'; const v = mount(el); v.replay();
import { META } from "./pipeline.data.js";
import { TREE } from "./tree.data.js";
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
const easeOut = (t) => 1 - Math.pow(1 - t, 3);
const fmt = (n) => n.toLocaleString("en-US");

export function mount(el, opts = {}) {
  el.innerHTML = "";
  const fg = cssVar(el, ["--fg", "--ink"], "#1b1b1f");
  const muted = cssVar(el, ["--muted"], "#6b6b78");
  const bg = cssVar(el, ["--bg", "--scene"], "#ffffff");
  const line = cssVar(el, ["--line"], "#dcdce4");
  const west = cssVar(el, ["--west"], "#2f6fdb");
  const east = cssVar(el, ["--east"], "#e39b2d");
  const accent = cssVar(el, ["--accent", "--west"], west);

  const W = 1640, H = 640;
  const s = svg("svg", { viewBox: `0 0 ${W} ${H}`, width: "100%", height: "100%", preserveAspectRatio: "xMidYMid meet" });
  s.style.cssText = "display:block;overflow:visible;font-family:inherit;font-variant-numeric:tabular-nums;";
  el.appendChild(s);
  const gWires = svg("g", {}, s), gDots = svg("g", {}, s), gBoxes = svg("g", {}, s);

  const steps = []; // {g, start}
  const wires = []; // {path, len, start}

  function box(x, y, w, h, title, sub, opt = {}) {
    const g = svg("g", { opacity: 0 }, gBoxes);
    svg("rect", { x, y, width: w, height: h, rx: 22, fill: opt.fill || bg, stroke: opt.stroke || line, "stroke-width": opt.sw || 2.5 }, g);
    const t = svg("text", { x: x + w / 2, y: y + (sub ? h / 2 - 4 : h / 2 + 12), "text-anchor": "middle", "font-size": opt.size || 32, "font-weight": 700, fill: opt.color || fg }, g);
    t.textContent = title;
    if (sub) {
      const st = svg("text", { x: x + w / 2, y: y + h / 2 + 34, "text-anchor": "middle", "font-size": 24, "font-weight": 500, fill: opt.subColor || muted }, g);
      st.textContent = sub;
    }
    return { g, x, y, w, h, cx: x + w / 2, cy: y + h / 2 };
  }
  function wire(a, b, start) {
    const x1 = a.x + a.w, y1 = a.cy, x2 = b.x, y2 = b.cy, mx = (x1 + x2) / 2;
    const p = svg("path", { d: `M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}`, fill: "none", stroke: line, "stroke-width": 4, "stroke-linecap": "round" }, gWires);
    const dot = svg("circle", { r: 8, fill: accent, opacity: 0 }, gDots);
    wires.push({ path: p, dot, start, len: 0 });
  }

  // column 1: three inputs
  const c1x = 0, c1w = 330, ih = 120, gap = 34;
  const inY = (H - (3 * ih + 2 * gap)) / 2;
  const inputs = [
    box(c1x, inY, c1w, ih, "Public weather", "3 weather models"),
    box(c1x, inY + ih + gap, c1w, ih, "Airport reports", "measured wind"),
    box(c1x, inY + 2 * (ih + gap), c1w, ih, "Flown history", "recorded directions"),
  ];
  inputs.forEach((b, i) => steps.push({ g: b.g, start: i * 160 }));

  // column 2: signals
  const sig = box(470, H / 2 - 100, 300, 200, `${META.n_features} signals`, "tailwind, pressure, now", { size: 38 });
  steps.push({ g: sig.g, start: 900 });
  inputs.forEach((b, i) => wire(b, sig, 650 + i * 80));

  // column 3: model, with a small forest glyph
  const mod = box(910, H / 2 - 100, 300, 200, `${TREE.n_trees} trees`, "add up their answers", { size: 38, stroke: accent, sw: 4 });
  const forest = svg("g", {}, mod.g);
  for (let i = 0; i < 5; i++) {
    const fx = mod.x + 70 + i * 40, fy = mod.y + 26;
    svg("path", { d: `M${fx},${fy + 28} L${fx},${fy + 8} M${fx},${fy + 8} L${fx - 12},${fy + 28} M${fx},${fy + 8} L${fx + 12},${fy + 28}`, stroke: accent, "stroke-width": 3, fill: "none", "stroke-linecap": "round" }, forest);
    svg("circle", { cx: fx, cy: fy + 8, r: 5, fill: accent }, forest);
  }
  steps.push({ g: mod.g, start: 1500 });
  wire(sig, mod, 1250);

  // column 4: output strip
  const ox = 1350, ow = 290, oh = 220, oy = H / 2 - oh / 2;
  const out = svg("g", { opacity: 0 }, gBoxes);
  svg("rect", { x: ox, y: oy, width: ow, height: oh, rx: 22, fill: bg, stroke: line, "stroke-width": 2.5 }, out);
  svg("text", { x: ox + ow / 2, y: oy + 50, "text-anchor": "middle", "font-size": 32, "font-weight": 700, fill: fg }, out).textContent = "Next 48 h";
  const hrs = (DAYS["2026-10-28"] || Object.values(DAYS)[0]).hours;
  const cw = (ow - 40) / hrs.length;
  hrs.forEach((h, i) => {
    const sure = Math.abs(h.p_west - 0.5) * 2; // 0 = 50/50, 1 = certain
    svg("rect", { x: ox + 20 + i * cw, y: oy + 76, width: cw + 0.3, height: 64, fill: h.p_west >= 0.5 ? west : east, opacity: 0.25 + 0.75 * sure }, out);
  });
  svg("text", { x: ox + ow / 2, y: oy + 182, "text-anchor": "middle", "font-size": 24, "font-weight": 500, fill: muted }, out).textContent = "west / east + how sure";
  const outBox = { x: ox, y: oy, w: ow, h: oh, cy: oy + oh / 2 };
  steps.push({ g: out, start: 2100 });
  wire(mod, outBox, 1850);

  const foot = svg("text", { x: 0, y: H - 2, "font-size": 22, fill: muted, opacity: 0 }, s);
  foot.textContent = `trained on ${fmt(META.n_rows)} forecast hours`;
  steps.push({ g: foot, start: 2500 });

  for (const w of wires) w.len = w.path.getTotalLength ? w.path.getTotalLength() || 300 : 300;

  let raf = 0, t0 = 0;
  function frame(now) {
    if (!t0) t0 = now;
    const el_ = now - t0;
    for (const st of steps) {
      const t = Math.max(0, Math.min(1, (el_ - st.start) / 450));
      st.g.setAttribute("opacity", easeOut(t));
    }
    for (const w of wires) {
      const t = Math.max(0, Math.min(1, (el_ - w.start) / 400));
      w.path.setAttribute("stroke-dasharray", `${w.len} ${w.len}`);
      w.path.setAttribute("stroke-dashoffset", w.len * (1 - easeOut(t)));
      // after drawing, a dot keeps flowing along each wire
      if (el_ > w.start + 400 && w.path.getPointAtLength) {
        const ph = (((el_ - w.start - 400) / 1400) % 1 + 1) % 1;
        const pt = w.path.getPointAtLength(ph * w.len);
        w.dot.setAttribute("cx", pt.x);
        w.dot.setAttribute("cy", pt.y);
        w.dot.setAttribute("opacity", Math.sin(Math.PI * ph));
      }
    }
    raf = requestAnimationFrame(frame);
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
