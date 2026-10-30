# FRA · Blender model kit

Open **`fra-airport.blend`**. The initial scene is **FRA · Airport demonstration**.
Press **Space** to play the 30-second example; timeline markers identify:

| Frames | Example state |
| --- | --- |
| 1–240 | OD 25, Runway 18 open |
| 241–480 | OD 07, Runway 18 open |
| 481–720 | OD 07, Runway 18 closed; its example departure goes to the centre runway |

Each state is a separate example. The cuts between states reset traffic; they
are not a simulation of clearing the airport during a real direction change.
Choose an **Asset · …** scene in Blender's scene selector for full-size models.
The radar and three landing-gear groups are separately parented for animation.

## Files

- `exports/aircraft-narrowbody.glb`: generic 37.6 m twinjet.
- `exports/aircraft-widebody.glb`: generic 64 m twinjet with larger wing and bogie gear.
- `exports/tower.glb`: Frankfurt-inspired tower, glazed cab, exterior stair and radar.
- `exports/runway-*.glb`: four physical runway variants with markings, lights
  and threshold anchors. Lengths: 2,800 m northwest, 4,000 m elsewhere.
- `exports/airport-environment.glb`: compact airport, terminal, parked aircraft,
  four runways and tower.
- `exports/airport-traffic-demo.glb`: four animated aircraft and three state
  overlays. Load alongside the environment at the same origin; play its clips
  together. The environment contains no moving traffic.
- `previews/`: nine rendered overview and detail images.
- `manifest.json`: axes, display scales, runway names, scenario paths and
  forecast-field mapping. Path coordinates use Blender axes.
- `verification.json`: measured export sizes, geometry counts and smoke checks.
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
tower ×0.90; moving aircraft ×0.55–0.70. It is a presentation model, not a
georeferenced airport map. Taxi routes, traffic timing and assignments are
illustrative fixtures. They are not connected to the ML forecast, do not model
separation or clearance, and are not suitable for operational use. Individual
aircraft and the tower are original interpretations rather than exact replicas.

## Rebuild and verify

From the repository root, with Blender 5.2 installed:

```sh
blender --background --threads 6 --python tools/blender/build_airport.py
blender --background --threads 6 --python tools/blender/verify_assets.py
```

On this Mac, replace `blender` with
`/Applications/Blender.app/Contents/MacOS/Blender`.
Append `-- --no-render` to rebuild geometry only, or `-- --preview-only` to
render the saved project. `-- --preview-only --preview-filter tower.png`
renders just that preview. Output stays under `assets/airport/`.

Checks cover native-file opening, all nine GLB reimports, finite geometry,
physical aircraft/runway lengths, ground contact, landing-gear hierarchy,
animation presence, coordinated OD, southbound Runway 18 and the closure
example. Visual review covers rendered shapes and composition. Browser/device
performance and integration with the live forecast remain separate work.
