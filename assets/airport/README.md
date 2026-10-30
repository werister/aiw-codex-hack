# FRA · Blender model kit

Open **`fra-airport.blend`**. The initial scene is **FRA · Airport demonstration**.
Press **Space** to play the 60-second example; timeline markers identify:

| Frames | Example state |
| --- | --- |
| 1–480 | OD 25, Runway 18 open |
| 481–960 | OD 07, Runway 18 open |
| 961–1440 | OD 07, Runway 18 closed; its example departure goes to the centre runway |

Each state is a separate example. The cuts between states reset traffic; they
are not a simulation of clearing the airport during a real direction change.
Choose an **Asset · …** scene in Blender's scene selector for full-size models.
The radar and three landing-gear groups are separately parented for animation.
The three example winds are 250°/12 kt, 070°/12 kt and 020°/20 kt.
In the last example, Runway 18 has 18.79 kt tailwind, so its departure waits
and then completes its route via 07C. These are fixed explanatory examples.
Each phase takes 20 seconds; jump to frame 1, 481 or 961 to choose a state.

## Files

- `exports/aircraft-narrowbody.glb`: generic 37.6 m twinjet.
- `exports/aircraft-widebody.glb`: generic 64 m twinjet with larger wing and bogie gear.
- `exports/tower.glb`: Frankfurt-inspired tower, glazed cab, exterior stair and radar.
- `exports/runway-*.glb`: four physical runway variants with markings, lights
  and threshold anchors. Lengths: 2,800 m northwest, 4,000 m elsewhere.
- `exports/airport-environment.glb`: compact airport, terminal, parked aircraft,
  four runways, a detailed three-hall terminal and tower.
- `exports/airport-traffic-demo.glb`: four animated aircraft and three state
  overlays. Load alongside the environment at the same origin; play its clips
  together. The environment contains no moving traffic.
- `previews/`: nine rendered overview and detail images.
- `manifest.json`: axes, display scales, runway names, scenario paths and
  forecast-field mapping. Path coordinates use Blender axes.
- `verification.json`: measured export sizes, geometry counts, spatial clearance, surface and full-timeline checks.
- `BRIEF.md`: visual brief, scope and reference sources.

## Integration

GLB is self-contained; no image textures, web packages or external URLs are
required. Materials are standard metallic/roughness PBR. Shared geometry is
instanced within the environment; duplicate loaded aircraft rather than loading
one GLB per flight.

| Convention | Blender | GLB / Three.js |
| --- | --- | --- |
| Up | +Z | +Y |
| North / aircraft nose | +Y | −Z |
| East | +X | +X |
| Position conversion | `[x, y, z]` | `[x, z, -y]` |

Standalone models use metres and ground-level roots. In Blender set heading
with `rotation_euler.z = -radians(heading)`; in Three.js use
`rotation.y = -heading * Math.PI / 180`. The runway asset's local nose/forward
axis is +Y before export, −Z afterwards. The manifest's runway heading describes
its intended geographic placement, not an already-applied standalone rotation.

Use **one shared `HourForecast.od`** for the three parallel runways. Runway 18
always departs south and is independent of OD. Display `p_18_usable` as a
probability; choosing a threshold for an open/closed illustration is a product
decision, not an extra model prediction. Certainty describes the forecast, not
individual aircraft assignments. Retain the existing forecast contract.

The airport is deliberately compressed: runway length ×0.12, width ×0.30;
tower ×0.70; moving aircraft ×0.42–0.60. It is a presentation model, not a
georeferenced airport map. Taxi routes, traffic timing and assignments are
illustrative fixtures. They are not connected to the ML forecast, use a checked illustrative layout and timing, and are not an operational
separation or clearance model. Individual
aircraft and the tower are original interpretations rather than exact replicas.

## Rebuild and verify

From the repository root, with Blender 5.2 and Python 3.14 installed.
One isolated authoring dependency constructs valid planar unions and
triangulates the taxiways; the delivered models need no Python dependencies:

```sh
python3 -m venv tools/blender/.venv
tools/blender/.venv/bin/python -m pip install -r tools/blender/requirements.txt
blender --background --threads 6 --python tools/blender/build_airport.py
blender --background --threads 2 --python-exit-code 1 --python tools/blender/verify_assets.py
```

On this Mac, replace `blender` with
`/Applications/Blender.app/Contents/MacOS/Blender`.
The exporter scopes selection to the active scene and omits unused UV data.
`-- --export-only` re-exports the saved scene without changing its geometry.
Append `-- --no-render` to rebuild geometry only, or `-- --preview-only` to
render the saved project. `-- --preview-only --preview-filter tower.png`
renders just that preview. Output stays under `assets/airport/`.

Checks include all nine GLB reimports, dimensions and finite geometry;
all 1,440 native animation frames; actual obstacle footprints outside runway
clearance bands; aircraft/obstacle convex-envelope separation; complete phase
endpoints; nonoverlapping runway/apron top triangles; and raycasts verifying
that every ground-route sample lies on the generated movement surface.
`verification.json` records the measurements and model hashes. Read the result
field; an earlier export-only check is not evidence of spatial correctness.

Preview images are rendered in Cycles. The optional playback MP4 is a separate
motion review; use `tools/blender/render_demo.py` through Blender to regenerate
it. Browser/device performance and live forecast integration remain separate.
