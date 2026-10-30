// 8 years of recorded directions: one column per day, one row per local hour, west vs east.
// Data: ./barcode.data.js (generated from data/ground_truth/dfld_hourly.csv).
// Usage: import { mount } from './viz/barcode.js'; const v = mount(el); v.replay();
import { META, BITS } from "./barcode.data.js";

let last = null;

function cssVar(el, names, fallback) {
  const cs = getComputedStyle(el);
  for (const n of names) {
    const v = cs.getPropertyValue(n).trim();
    if (v) return v;
  }
  return fallback;
}

function toRGB(color) {
  const c = document.createElement("canvas").getContext("2d");
  c.fillStyle = "#000";
  c.fillStyle = color;
  const s = c.fillStyle;
  if (s[0] === "#") return [1, 3, 5].map((i) => parseInt(s.slice(i, i + 2), 16));
  const m = s.match(/[\d.]+/g) || [0, 0, 0];
  return m.slice(0, 3).map(Number);
}

function decode() {
  const bin = atob(BITS);
  const days = META.days;
  const grid = new Uint8Array(days * 24); // 0 none, 1 west, 2 east
  for (let d = 0; d < days; d++) {
    let lo = 0, hi = 0;
    for (let b = 0; b < 3; b++) lo |= bin.charCodeAt(d * 6 + b) << (8 * b);
    for (let b = 0; b < 3; b++) hi |= bin.charCodeAt(d * 6 + 3 + b) << (8 * b);
    for (let h = 0; h < 12; h++) grid[d * 24 + h] = (lo >> (2 * h)) & 3;
    for (let h = 0; h < 12; h++) grid[d * 24 + 12 + h] = (hi >> (2 * h)) & 3;
  }
  return grid;
}

const fmt = (n) => n.toLocaleString("en-US");

export function mount(el, opts = {}) {
  const duration = opts.duration ?? 2600;
  el.innerHTML = "";
  const fg = cssVar(el, ["--fg", "--ink"], "#1b1b1f");
  const muted = cssVar(el, ["--muted"], "#6b6b78");
  const west = cssVar(el, ["--west"], "#2f6fdb");
  const east = cssVar(el, ["--east"], "#e39b2d");
  const none = cssVar(el, ["--line"], "#dcdce4");
  const accent = cssVar(el, ["--accent"], west);

  const root = document.createElement("div");
  root.style.cssText = `position:relative;width:100%;height:100%;display:flex;flex-direction:column;gap:18px;color:${fg};font-family:inherit;`;
  const plot = document.createElement("div");
  plot.style.cssText = "position:relative;flex:1 1 auto;min-height:0;";
  const canvas = document.createElement("canvas");
  canvas.style.cssText = "position:absolute;display:block;";
  plot.appendChild(canvas);
  const caption = document.createElement("div");
  caption.style.cssText = `display:flex;align-items:baseline;gap:40px;flex-wrap:wrap;font-size:30px;font-weight:600;letter-spacing:-0.01em;opacity:0;transition:opacity .6s ease;`;
  const westShare = Math.round((100 * META.west_hours) / META.hours);
  caption.innerHTML =
    `<span>${fmt(META.hours)} hours</span>` +
    `<span style="display:inline-flex;align-items:center;gap:12px"><i style="width:22px;height:22px;border-radius:4px;background:${west};display:inline-block"></i>west ${westShare}%</span>` +
    `<span style="display:inline-flex;align-items:center;gap:12px"><i style="width:22px;height:22px;border-radius:4px;background:${east};display:inline-block"></i>east ${100 - westShare}%</span>`;
  root.appendChild(plot);
  root.appendChild(caption);
  el.appendChild(root);

  const grid = decode();
  const days = META.days;
  const start = new Date(META.start + "T00:00:00Z");
  const W_RGB = toRGB(west), E_RGB = toRGB(east), N_RGB = toRGB(none);

  const padL = 92, padB = 46, padT = 16, padR = 8;
  let img = null, cw = 0, ch = 0, dpr = 1, raf = 0, t0 = 0;

  function layout() {
    // Layout uses the unscaled stage dimensions; the deck applies its own transform.
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    cw = Math.max(200, plot.clientWidth);
    ch = Math.max(120, plot.clientHeight);
    canvas.style.left = "0px";
    canvas.style.top = "0px";
    canvas.style.width = cw + "px";
    canvas.style.height = ch + "px";
    canvas.width = Math.round(cw * dpr);
    canvas.height = Math.round(ch * dpr);
    // Aggregate days into device-pixel columns; colour = share of west in that column/hour.
    const pw = Math.round((cw - padL - padR) * dpr);
    const off = document.createElement("canvas");
    off.width = pw;
    off.height = 24;
    const octx = off.getContext("2d");
    const id = octx.createImageData(pw, 24);
    for (let x = 0; x < pw; x++) {
      const d0 = Math.floor((x * days) / pw), d1 = Math.max(d0 + 1, Math.floor(((x + 1) * days) / pw));
      for (let h = 0; h < 24; h++) {
        let w = 0, e = 0;
        for (let d = d0; d < d1; d++) {
          const v = grid[d * 24 + h];
          if (v === 1) w++;
          else if (v === 2) e++;
        }
        const k = (h * pw + x) * 4;
        let c;
        if (w + e === 0) c = N_RGB;
        else {
          const f = w / (w + e);
          c = [0, 1, 2].map((i) => Math.round(E_RGB[i] + (W_RGB[i] - E_RGB[i]) * f));
        }
        id.data[k] = c[0]; id.data[k + 1] = c[1]; id.data[k + 2] = c[2]; id.data[k + 3] = 255;
      }
    }
    octx.putImageData(id, 0, 0);
    img = off;
  }

  function draw(p) {
    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, cw, ch);
    const pw = cw - padL - padR, ph = ch - padT - padB;
    const xr = pw * p;
    if (xr > 0) {
      ctx.save();
      ctx.beginPath();
      ctx.rect(padL, padT, xr, ph);
      ctx.clip();
      ctx.imageSmoothingEnabled = false;
      ctx.drawImage(img, padL, padT, pw, ph);
      ctx.restore();
    }
    // y axis: local hour
    ctx.fillStyle = muted;
    ctx.font = `500 22px ${getComputedStyle(root).fontFamily}`;
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    for (const h of [0, 6, 12, 18, 24]) {
      const y = padT + (ph * h) / 24;
      ctx.fillText(String(h).padStart(2, "0") + ":00", padL - 14, y);
    }
    // x axis: years
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    const y0 = new Date(start).getUTCFullYear();
    for (let y = y0; y <= y0 + 9; y++) {
      const t = Date.UTC(y, 0, 1);
      const d = (t - start.getTime()) / 864e5;
      if (d < 0 || d > days) continue;
      const x = padL + (pw * d) / days;
      ctx.fillStyle = muted;
      ctx.fillRect(x, padT + ph + 4, 1.5, 10);
      const nx = padL + (pw * Math.min(days, d + 182)) / days;
      ctx.fillStyle = fg;
      ctx.fillText(String(y), nx, padT + ph + 14);
    }
    // playhead
    if (p > 0 && p < 1) {
      ctx.fillStyle = accent;
      ctx.fillRect(padL + xr - 1.5, padT - 4, 3, ph + 8);
    }
  }

  function frame(now) {
    if (!t0) t0 = now;
    const raw = Math.min(1, (now - t0) / duration);
    const p = raw < 0.5 ? 2 * raw * raw : 1 - Math.pow(-2 * raw + 2, 2) / 2;
    draw(p);
    if (raw < 1) raf = requestAnimationFrame(frame);
    else caption.style.opacity = "1";
  }

  function replay() {
    cancelAnimationFrame(raf);
    caption.style.transition = "none";
    caption.style.opacity = "0";
    void caption.offsetWidth;
    caption.style.transition = "opacity .6s ease";
    layout();
    t0 = 0;
    raf = requestAnimationFrame(frame);
  }

  const ro = typeof ResizeObserver !== "undefined" ? new ResizeObserver(() => { layout(); draw(1); }) : null;
  replay();
  if (ro) setTimeout(() => ro.observe(plot), duration + 50);

  const api = {
    replay,
    destroy() { cancelAnimationFrame(raf); if (ro) ro.disconnect(); el.innerHTML = ""; },
  };
  last = api;
  return api;
}

export function replay() { if (last) last.replay(); }
