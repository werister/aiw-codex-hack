// How often we are right: held-out accuracy at 6 / 24 / 48 h for our model vs official rules vs same as now.
// Data: ./accuracy.data.js (generated from web/public/data/quality.json, out_of_sample.od + significance.od).
// Usage: import { mount } from './viz/accuracy.js'; const v = mount(el); v.replay();
import { DATA } from "./accuracy.data.js";

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
const pct = (v) => (100 * v).toFixed(1) + "%";

export function mount(el, opts = {}) {
  const leads = opts.leads ?? [6, 24, 48];
  el.innerHTML = "";
  const fg = cssVar(el, ["--fg", "--ink"], "#1b1b1f");
  const muted = cssVar(el, ["--muted"], "#6b6b78");
  const line = cssVar(el, ["--line"], "#dcdce4");
  const accent = cssVar(el, ["--accent", "--west"], "#2f6fdb");
  const greyA = opts.rulesColor ?? "#9a9aae";
  const greyB = opts.sameColor ?? "#cfcfdc";

  const rows = leads.map((L) => DATA.rows.find((r) => r.lead_h === L)).filter(Boolean);
  const W = 1640, H = 760;
  const top = 110, bottom = 90, left = 20, right = 20;
  const ph = H - top - bottom;
  const s = svg("svg", { viewBox: `0 0 ${W} ${H}`, width: "100%", height: "100%", preserveAspectRatio: "xMidYMid meet" });
  s.style.cssText = `display:block;overflow:visible;font-family:inherit;font-variant-numeric:tabular-nums;`;
  el.appendChild(s);

  // legend
  const series = [
    { key: "model", label: "our model", color: accent },
    { key: "rules", label: "official rules", color: greyA },
    { key: "same", label: "same as now", color: greyB },
  ];
  let lx = left;
  for (const se of series) {
    svg("rect", { x: lx, y: 18, width: 30, height: 30, rx: 6, fill: se.color }, s);
    const t = svg("text", { x: lx + 44, y: 43, "font-size": 30, "font-weight": se.key === "model" ? 700 : 500, fill: se.key === "model" ? fg : muted }, s);
    t.textContent = se.label;
    let tw = se.label.length * 15;
    try { tw = t.getComputedTextLength() || tw; } catch (e) {}
    lx += 44 + tw + 56;
  }

  const y = (v) => top + ph * (1 - v);
  // baseline + 50% guide
  svg("line", { x1: left, x2: W - right, y1: y(0), y2: y(0), stroke: fg, "stroke-width": 2 }, s);

  const groupW = (W - left - right) / rows.length;
  const barW = Math.min(150, groupW / 4.2), gap = 18;
  const anims = [];
  rows.forEach((r, gi) => {
    const gx = left + gi * groupW + groupW / 2;
    const x0 = gx - (3 * barW + 2 * gap) / 2;
    const lab = svg("text", { x: gx, y: H - bottom + 54, "text-anchor": "middle", "font-size": 34, "font-weight": 600, fill: fg }, s);
    lab.textContent = `${r.lead_h} h ahead`;
    series.forEach((se, si) => {
      const v = r[se.key];
      const x = x0 + si * (barW + gap);
      const rect = svg("rect", { x, y: y(0), width: barW, height: 0, rx: 6, fill: se.color }, s);
      const isModel = se.key === "model";
      const txt = svg("text", { x: x + barW / 2, y: y(0) - 14, "text-anchor": "middle", "font-size": isModel ? 40 : 28, "font-weight": isModel ? 800 : 600, fill: isModel ? fg : muted, opacity: 0 }, s);
      txt.textContent = pct(v);
      let whisk = null;
      if (isModel && r.model_ci) {
        whisk = svg("g", { opacity: 0 }, s);
        const cx = x + barW / 2;
        const [lo, hi] = r.model_ci;
        svg("line", { x1: cx, x2: cx, y1: y(lo), y2: y(hi), stroke: fg, "stroke-width": 3 }, whisk);
        svg("line", { x1: cx - 16, x2: cx + 16, y1: y(lo), y2: y(lo), stroke: fg, "stroke-width": 3 }, whisk);
        svg("line", { x1: cx - 16, x2: cx + 16, y1: y(hi), y2: y(hi), stroke: fg, "stroke-width": 3 }, whisk);
      }
      anims.push({ rect, txt, whisk, v, ci: isModel ? r.model_ci : null, delay: gi * 260 + si * 110, isModel });
    });
  });
  const note = svg("text", { x: W - right, y: 43, "text-anchor": "end", "font-size": 24, fill: muted }, s);
  note.textContent = "12 months the model never saw · whisker = 95% range";

  let raf = 0, t0 = 0;
  const dur = 1100;
  function frame(now) {
    if (!t0) t0 = now;
    const el_ = now - t0;
    let done = true;
    for (const a of anims) {
      const t = Math.max(0, Math.min(1, (el_ - a.delay) / dur));
      if (t < 1) done = false;
      const e = easeOut(t);
      const v = a.v * e;
      a.rect.setAttribute("y", y(v));
      a.rect.setAttribute("height", y(0) - y(v));
      const labelTop = a.ci ? y(v + (a.ci[1] - a.v) * e) : y(v);
      a.txt.setAttribute("y", labelTop - 16);
      a.txt.setAttribute("opacity", Math.min(1, t * 2));
      a.txt.textContent = pct(v);
      if (a.whisk) a.whisk.setAttribute("opacity", Math.max(0, (t - 0.75) / 0.25));
    }
    if (!done) raf = requestAnimationFrame(frame);
    else for (const a of anims) a.txt.textContent = pct(a.v);
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
