// What matters most: held-out permutation importance of the direction model (increase in Brier score
// when a feature is shuffled, final held-out month), in plain words. Bars are relative; no numbers shown.
// Data: ./drivers.data.js (generated from web/public/data/quality.json drivers).
// Usage: import { mount } from './viz/drivers.js'; const v = mount(el); v.replay();
import { DRIVERS } from "./drivers.data.js";

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

const NAMES = {
  ens_tailwind_25_mean: "Forecast tailwind, west runway",
  dp_ns: "Pressure north vs south",
  od_at_issue: "Direction right now",
  ecmwf_ifs025_tailwind_25: "European model tailwind",
  rule_od25_ens: "Official rules on forecast",
  geo_tailwind_25: "Pressure-driven tailwind",
  lead_h: "Hours ahead",
  obs_tailwind_25: "Measured tailwind now",
  hour_cos: "Time of day",
  hour_sin: "Time of day",
  ecmwf_ifs025_tailwind_18: "European model, runway 18",
  dp_ew: "Pressure east vs west",
  hours_since_change: "Hours since last switch",
};

export function mount(el, opts = {}) {
  const top = opts.top ?? 8;
  el.innerHTML = "";
  const fg = cssVar(el, ["--fg", "--ink"], "#1b1b1f");
  const muted = cssVar(el, ["--muted"], "#6b6b78");
  const accent = cssVar(el, ["--accent", "--west"], "#2f6fdb");
  const line = cssVar(el, ["--line"], "#dcdce4");

  const rows = DRIVERS.slice(0, top);
  const max = Math.max(...rows.map((r) => r.importance));
  const W = 1640, rowH = 78, T = 20, H = T + rows.length * rowH + 60;
  const labelW = 560, barX = labelW + 30, barMax = W - barX - 40;
  const s = svg("svg", { viewBox: `0 0 ${W} ${H}`, width: "100%", height: "100%", preserveAspectRatio: "xMidYMid meet" });
  s.style.cssText = "display:block;overflow:visible;font-family:inherit;font-variant-numeric:tabular-nums;";
  el.appendChild(s);

  const anims = rows.map((r, i) => {
    const y = T + i * rowH;
    const name = svg("text", { x: labelW, y: y + 44, "text-anchor": "end", "font-size": 32, "font-weight": i === 0 ? 800 : 600, fill: fg }, s);
    name.textContent = NAMES[r.feature] || r.feature.replace(/_/g, " ");
    svg("rect", { x: barX, y: y + 14, width: barMax, height: 44, rx: 8, fill: line, opacity: 0.45 }, s);
    const bar = svg("rect", { x: barX, y: y + 14, width: 0, height: 44, rx: 8, fill: accent, opacity: i === 0 ? 1 : 0.55 + 0.45 * (r.importance / max) }, s);
    return { bar, w: (barMax * r.importance) / max, v: r.importance, delay: i * 120 };
  });
  const note = svg("text", { x: barX, y: H - 10, "font-size": 24, fill: muted }, s);
  note.textContent = "how much worse the forecast gets without it";

  let raf = 0, t0 = 0;
  const dur = 1000;
  function frame(now) {
    if (!t0) t0 = now;
    const el_ = now - t0;
    let done = true;
    for (const a of anims) {
      const t = Math.max(0, Math.min(1, (el_ - a.delay) / dur));
      if (t < 1) done = false;
      const e = easeOut(t);
      a.bar.setAttribute("width", a.w * e);
    }
    if (!done) raf = requestAnimationFrame(frame);
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
