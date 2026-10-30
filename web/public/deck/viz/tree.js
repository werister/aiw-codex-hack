// Inside the model: the first tree of the real operating-direction model, top 3 levels, drawn node by node.
// Data: ./tree.data.js (extracted from ml/models/forecast.joblib, boosting iteration 1).
// Usage: import { mount } from './viz/tree.js'; const v = mount(el); v.replay();
import { TREE } from "./tree.data.js";

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
const f1 = (v) => (Math.abs(v) < 0.05 ? "0" : v.toFixed(1)).replace("-", "−");

// Plain-word questions. Left branch = "no" (value <= threshold), right = "yes".
function question(n) {
  const t = n.threshold;
  switch (n.feature) {
    case "ens_tailwind_25_mean": return [`Tailwind west > ${f1(t)} kt?`, "forecast, avg of 3 models"];
    case "rule_od25_ens": return ["Official rules say west?", "on forecast wind"];
    case "geo_tailwind_25": return [`Pressure tailwind > ${f1(t)}?`, "hPa, pressure 200 km around"];
    case "geo_tailwind_18": return [`Pressure tailwind 18 > ${f1(t)} hPa?`, "pressure 200 km around"];
    case "ens_votes_25": return ["All forecasts say west?", `share > ${t.toFixed(2)}`];
    case "dp_ns": return [`Pressure north−south > ${f1(t)}?`, "hPa, 200 km apart"];
    case "dp_ew": return [`Pressure east−west > ${f1(t)}?`, "hPa, 200 km apart"];
    case "od_at_issue": return ["Flying west now?", ""];
    case "season_cos": case "season_sin": return ["Time of year", ""];
    case "hour_cos": case "hour_sin": return ["Time of day", ""];
    case "lead_h": return [`More than ${Math.round(t)} h ahead?`, ""];
    case "ecmwf_ifs025_tailwind_25": return ["European model tailwind", ""];
    case "gfs_seamless_tailwind_25": return ["US model tailwind", ""];
    case "icon_seamless_tailwind_25": return ["German model tailwind", ""];
    case "obs_tailwind_25": return [`Measured tailwind > ${f1(t)} kt?`, "airport report"];
    case "hours_since_change": return [`Last switch > ${Math.round(t)} h ago?`, ""];
    default: return [n.feature.replace(/_/g, " "), ""];
  }
}

const SHORT = {
  od_at_issue: "Flying west now", season_cos: "Time of year", season_sin: "Time of year",
  hour_cos: "Time of day", hour_sin: "Time of day", geo_tailwind_25: "Pressure tailwind",
  geo_tailwind_18: "Pressure tailwind", dp_ns: "Pressure N−S", dp_ew: "Pressure E−W",
  ecmwf_ifs025_tailwind_25: "European model", gfs_seamless_tailwind_25: "US model",
  icon_seamless_tailwind_25: "German model", ens_tailwind_25_mean: "Tailwind west",
  rule_od25_ens: "Official rules", ens_votes_25: "Forecast votes", lead_h: "Hours ahead",
  obs_tailwind_25: "Measured tailwind", hours_since_change: "Last switch",
};
const shortName = (n) => SHORT[n.feature] || n.feature.replace(/_/g, " ");

export function mount(el, opts = {}) {
  el.innerHTML = "";
  const fg = cssVar(el, ["--fg", "--ink"], "#1b1b1f");
  const muted = cssVar(el, ["--muted"], "#6b6b78");
  const bg = cssVar(el, ["--bg", "--scene"], "#ffffff");
  const west = cssVar(el, ["--west"], "#2f6fdb");
  const east = cssVar(el, ["--east"], "#e39b2d");
  const line = cssVar(el, ["--line"], "#dcdce4");

  const W = 1640, H = 800;
  const levelY = [40, 250, 460, 690];
  const boxW = [440, 400, 396, 196];
  const boxH = [104, 104, 104, 64];
  const s = svg("svg", { viewBox: `0 0 ${W} ${H}`, width: "100%", height: "100%", preserveAspectRatio: "xMidYMid meet" });
  s.style.cssText = "display:block;overflow:visible;font-family:inherit;font-variant-numeric:tabular-nums;";
  el.appendChild(s);
  const gEdges = svg("g", {}, s), gNodes = svg("g", {}, s);

  const total = TREE.root.count;
  const leanMax = 0.25;
  const leanColor = (lean) => (lean >= 0 ? west : east);
  const items = []; // {kind, el, start, len?}
  let order = 0;

  function place(node, depth, idx) {
    const slots = Math.pow(2, depth);
    return { x: ((idx + 0.5) * W) / slots, y: levelY[depth] };
  }

  // breadth-first so the drawing reads top-down
  const queue = [{ node: TREE.root, depth: 0, idx: 0, parent: null, side: null }];
  while (queue.length) {
    const q = queue.shift();
    const { node, depth, idx } = q;
    const p = place(node, depth, idx);
    const w = boxW[depth], h = boxH[depth];
    const start = depth * 650 + (depth === 0 ? 0 : 250) + (idx % Math.pow(2, depth)) * 70;

    if (q.parent) {
      const a = q.parent;
      const x1 = a.x + (q.side === "L" ? -a.w * 0.22 : a.w * 0.22), y1 = a.y + a.h;
      const x2 = p.x, y2 = p.y;
      const my = (y1 + y2) / 2;
      const path = svg("path", {
        d: `M${x1},${y1} C${x1},${my} ${x2},${my} ${x2},${y2}`,
        fill: "none", stroke: leanColor(node.lean), "stroke-opacity": 0.45,
        "stroke-width": 3 + 22 * (node.count / total), "stroke-linecap": "round",
      }, gEdges);
      const lab = svg("text", {
        x: (x1 + x2) / 2 + (q.side === "L" ? -14 : 14), y: my - 6,
        "text-anchor": q.side === "L" ? "end" : "start", "font-size": 24, "font-weight": 600, fill: muted, opacity: 0,
      }, gEdges);
      lab.textContent = q.side === "L" ? "no" : "yes";
      items.push({ kind: "edge", el: path, start: start - 250, dur: 420 });
      items.push({ kind: "fade", el: lab, start: start - 60, dur: 300 });
    }

    const g = svg("g", { opacity: 0 }, gNodes);
    const isQuestion = !node.leaf && depth < 3;
    const k = Math.min(1, Math.abs(node.lean) / leanMax);
    if (isQuestion) {
      svg("rect", { x: p.x - w / 2, y: p.y, width: w, height: h, rx: 18, fill: bg, stroke: depth === 0 ? fg : leanColor(node.lean), "stroke-width": depth === 0 ? 3 : 2 + 3 * k }, g);
      const [main, sub] = question(node);
      const t1 = svg("text", { x: p.x, y: p.y + (sub ? 46 : 60), "text-anchor": "middle", "font-size": depth === 0 ? 34 : depth === 1 ? 30 : 27, "font-weight": 700, fill: fg }, g);
      t1.textContent = main;
      if (sub) {
        const t2 = svg("text", { x: p.x, y: p.y + 82, "text-anchor": "middle", "font-size": 21, fill: muted }, g);
        t2.textContent = sub;
      }
    } else {
      // endpoint: a real leaf, or the start of deeper questions (level 4+), coloured by where it leans
      const col = leanColor(node.lean);
      const ww = node.leaf ? (depth < 3 ? 260 : w) : w;
      const hh = node.leaf ? (depth < 3 ? 80 : h) : h;
      svg("rect", {
        x: p.x - ww / 2, y: p.y, width: ww, height: hh, rx: hh / 2,
        fill: node.leaf ? col : bg, "fill-opacity": node.leaf ? 0.25 + 0.75 * k : 1,
        stroke: col, "stroke-width": 2.5, "stroke-dasharray": node.leaf ? "none" : "7 6",
      }, g);
      const txt = svg("text", { x: p.x, y: p.y + hh / 2 + 9, "text-anchor": "middle", "font-size": node.leaf ? 28 : 21, "font-weight": node.leaf ? 800 : 600, fill: node.leaf ? (k > 0.5 ? "#fff" : fg) : fg }, g);
      txt.textContent = node.leaf ? (node.value >= 0 ? "west" : "east") : shortName(node) + " …";
      if (!node.leaf) {
        const lean = svg("text", { x: p.x, y: p.y + hh + 28, "text-anchor": "middle", "font-size": 20, "font-weight": 600, fill: col }, g);
        lean.textContent = node.lean >= 0 ? "leans west" : "leans east";
      }
    }
    items.push({ kind: "node", el: g, start, dur: 380, cx: p.x, cy: p.y + h / 2 });

    if (isQuestion) {
      const me = { x: p.x, y: p.y, w, h };
      queue.push({ node: node.left, depth: depth + 1, idx: idx * 2, parent: me, side: "L" });
      queue.push({ node: node.right, depth: depth + 1, idx: idx * 2 + 1, parent: me, side: "R" });
    }
    order++;
  }

  const cap = svg("text", { x: 0, y: 30, "font-size": 28, "font-weight": 700, fill: fg, opacity: 0 }, s);
  cap.textContent = `1 of ${TREE.n_trees} trees · first 3 levels`;
  const cap2 = svg("text", { x: 0, y: 66, "font-size": 22, fill: muted, opacity: 0 }, s);
  cap2.textContent = "line width = hours that pass";
  const endT = Math.max(...items.map((i) => i.start + i.dur));
  items.push({ kind: "fade", el: cap, start: 0, dur: 500 });
  items.push({ kind: "fade", el: cap2, start: endT, dur: 500 });

  for (const it of items) if (it.kind === "edge") { it.len = it.el.getTotalLength ? it.el.getTotalLength() || 600 : 600; }

  let raf = 0, t0 = 0;
  function frame(now) {
    if (!t0) t0 = now;
    const el_ = now - t0;
    let done = true;
    for (const it of items) {
      const t = Math.max(0, Math.min(1, (el_ - it.start) / it.dur));
      if (t < 1) done = false;
      const e = easeOut(t);
      if (it.kind === "edge") {
        it.el.setAttribute("stroke-dasharray", `${it.len} ${it.len}`);
        it.el.setAttribute("stroke-dashoffset", String(it.len * (1 - e)));
      } else if (it.kind === "node") {
        it.el.setAttribute("opacity", e);
        const sc = 0.85 + 0.15 * e;
        it.el.setAttribute("transform", `translate(${it.cx * (1 - sc)},${it.cy * (1 - sc)}) scale(${sc})`);
      } else {
        it.el.setAttribute("opacity", e);
      }
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
