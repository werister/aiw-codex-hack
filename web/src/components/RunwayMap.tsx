import type { OD } from "@/lib/forecast-types";

// Schematic FRA runway system, north up, not to scale. Traffic is simulated.
// Parallel runways lie on 070/250; runway 18 (Startbahn West) runs north to south.
const AX = { x: Math.sin((70 * Math.PI) / 180), y: -Math.cos((70 * Math.PI) / 180) };

type Rwy = { id: string; name: string; west: [number, number]; len: number; role: "land" | "dep" };
const PARALLELS: Rwy[] = [
  { id: "nw", name: "07L / 25R", west: [150, 150], len: 300, role: "land" },
  { id: "c", name: "07C / 25C", west: [220, 262], len: 400, role: "dep" },
  { id: "s", name: "07R / 25L", west: [240, 318], len: 400, role: "land" },
];
const R18 = { x: 95, top: 170, bottom: 380 };

function pt(r: Rwy, t: number): [number, number] {
  return [r.west[0] + AX.x * r.len * t, r.west[1] + AX.y * r.len * t];
}

function path(a: [number, number], b: [number, number]) {
  return `M${a[0].toFixed(1)},${a[1].toFixed(1)} L${b[0].toFixed(1)},${b[1].toFixed(1)}`;
}

export function RunwayMap({
  od,
  r18Open,
  windDir,
  windKt,
  label,
}: {
  od: OD;
  r18Open: boolean;
  windDir: number | null;
  windKt: number;
  label: string;
}) {
  const west = od === "25";
  const color = west ? "var(--west)" : "var(--east)";
  // t along the runway from its west end; flow goes east->west for 25, west->east for 07.
  const flows = PARALLELS.map((r) => {
    const from = r.role === "land" ? (west ? 1.35 : -0.35) : west ? 0.98 : 0.02;
    const to = r.role === "land" ? (west ? 0.3 : 0.7) : west ? -0.4 : 1.4;
    return { r, d: path(pt(r, from), pt(r, to)) };
  });
  const depCount = r18Open ? 2 : 4;

  return (
    <div className="relative">
      <svg viewBox="0 0 680 420" className="w-full" role="img" aria-label={`Schematic runway map, operating direction ${od}`}>
        <defs>
          <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
            <path d="M0,0 L10,5 L0,10 z" fill={color} />
          </marker>
        </defs>

        {PARALLELS.map((r) => {
          const [x1, y1] = pt(r, 0);
          const [x2, y2] = pt(r, 1);
          const lbl = pt(r, 0.5);
          return (
            <g key={r.id}>
              <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="var(--line)" strokeWidth="14" strokeLinecap="round" />
              <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="var(--panel-2)" strokeWidth="1.5" strokeDasharray="8 8" />
              <text x={lbl[0]} y={lbl[1] + 26} textAnchor="middle" fontSize="11" fill="var(--ink-2)" transform={`rotate(-20 ${lbl[0]} ${lbl[1] + 26})`}>
                {r.name} · {r.role === "land" ? "landings" : "departures"}
              </text>
            </g>
          );
        })}

        {/* runway 18 */}
        <line x1={R18.x} y1={R18.top} x2={R18.x} y2={R18.bottom} stroke={r18Open ? "var(--line)" : "var(--bad)"} strokeWidth="14" strokeLinecap="round" opacity={r18Open ? 1 : 0.7} />
        <text x={R18.x - 16} y={(R18.top + R18.bottom) / 2} textAnchor="middle" fontSize="11" fill="var(--ink-2)" transform={`rotate(-90 ${R18.x - 16} ${(R18.top + R18.bottom) / 2})`}>
          18 · departures south
        </text>
        {!r18Open && (
          <g>
            <rect x={R18.x + 14} y={R18.top + 70} width="74" height="24" rx="4" fill="var(--bad)" />
            <text x={R18.x + 51} y={R18.top + 86} textAnchor="middle" fontSize="12" fontWeight="700" fill="var(--bg)">CLOSED</text>
          </g>
        )}

        {/* simulated traffic */}
        <g key={od + String(r18Open)}>
          {flows.map(({ r, d }) =>
            Array.from({ length: r.role === "dep" ? depCount : 3 }, (_, k) => (
              <circle key={r.id + k} r="4.5" fill={color}>
                <animateMotion dur={r.role === "dep" ? "6s" : "7s"} begin={`${(k * (r.role === "dep" ? 6 / depCount : 7 / 3)).toFixed(2)}s`} repeatCount="indefinite" path={d} />
              </circle>
            )),
          )}
          {r18Open &&
            [0, 1].map((k) => (
              <circle key={"r18" + k} r="4.5" fill="var(--ok)">
                <animateMotion dur="6s" begin={`${k * 3}s`} repeatCount="indefinite" path={`M${R18.x},${R18.top + 4} L${R18.x},${R18.bottom + 40}`} />
              </circle>
            ))}
          {/* direction arrow on the centre runway */}
          <path d={path(pt(PARALLELS[1], west ? 0.7 : 0.3), pt(PARALLELS[1], west ? 0.45 : 0.55))} stroke={color} strokeWidth="4" markerEnd="url(#arrow)" />
        </g>

        {/* wind */}
        <g transform="translate(600 360)">
          <circle r="34" fill="var(--panel-2)" stroke="var(--line)" />
          {windDir != null && (
            <path d="M0,-24 L8,10 L0,4 L-8,10 Z" fill="var(--ink)" transform={`rotate(${windDir + 180})`} />
          )}
          <text y="52" textAnchor="middle" fontSize="11" fill="var(--ink-2)">
            {windDir == null ? "calm" : `${Math.round(windDir)}° ${Math.round(windKt)} kt`}
          </text>
        </g>

        <text x="12" y="20" fontSize="13" fontWeight="700" fill={color}>
          OD {od} · {west ? "toward 250° (west)" : "toward 070° (east)"}
        </text>
        <text x="12" y="38" fontSize="11" fill="var(--muted)">{label}</text>
      </svg>
      <div className="absolute bottom-1 left-2 text-[10px] text-muted">Simulated traffic · schematic, not to scale</div>
    </div>
  );
}
