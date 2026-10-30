# FRA · Blender model kit

Open **`fra-airport.blend`**. The initial scene is **FRA · Airport demonstration**.
Press **Space** to play the 60-second example; timeline markers identify:

| Frames | Example state |
| --- | --- |
| 1–1200 | OD 25, Runway 18 open |
| 1201–2400 | OD 07, Runway 18 open |
| 2401–3600 | OD 07, Runway 18 closed; its example departure goes to the centre runway |

Each state is a separate example. The cuts between states reset traffic; they
are not a simulation of clearing the airport during a real direction change.
Choose an **Asset · …** scene in Blender's scene selector for full-size models.
The radar and three landing-gear groups are separately parented for animation.
The three example winds are 250°/12 kt, 070°/12 kt and 020°/20 kt.
In the last example, Runway 18 has 18.79 kt tailwind, so its departure waits
and then completes its route via 07C. These are fixed explanatory examples.
Native playback uses 60 fps. Each phase takes 20 seconds; jump to frame 1, 1201 or 2401 to choose a state.

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
- `verification.json`: native export hashes, dimensions, geometry, runway and
  scene checks. Its `result` must be `passed` before publishing.
- `runtime-verification.json`: sampled browser traffic checked against actual
  Blender runway/apron surfaces. The current report passes 19,200 samples
  across four states and four roles; all 12,097 ground samples hit pavement,
  with no recorded obstacle or aircraft-hull collisions. This validates the
  illustrative geometry, not operational clearance.
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

## Web demonstration

The cockpit and widget load the Blender environment and aircraft as GLBs. The
currently selected `HourForecast` drives the scene: its single `od` selects the
direction for all three parallel runways, and `p_18_usable >= 0.5` selects the
illustrated open/closed state for Runway 18. The caption also shows the exact
probability and forecast certainty. The 50% cutoff is a display policy; it is
not an operational clearance or a second model output. Certainty describes the
forecast, not an aircraft assignment.

All four combinations (OD 25/07 × Runway 18 open/closed) are supported. Runway
18 traffic, when shown, departs south; when closed, the flexible example
departure uses the selected parallel-runway direction. Selecting a different
forecast hour resets the illustrative flow. The web scene displays forecast
wind when available, but its route and timing fixtures do not infer ATC or
individual aircraft assignments from the weather.

The airport is deliberately compressed: runway length ×0.12, width ×0.30;
tower ×0.70; moving aircraft ×0.42–0.60. It is a presentation model, not a
georeferenced airport map. The native `.blend` playback remains three fixed
examples; it is not driven by ML. Neither version is an operational taxi,
separation or clearance model. Individual aircraft and the tower are original
interpretations rather than exact replicas.

Publish the three browser GLBs and matching manifest from the repository root:

```sh
python3 tools/blender/publish_web_assets.py --dry-run
python3 tools/blender/publish_web_assets.py
python3 tools/blender/publish_web_assets.py --check
```

The publisher checks each GLB against its SHA-256 and byte count in
`verification.json`, stages all four files, then atomically replaces each web
copy. `--dry-run` verifies sources without writing; `--check` also verifies the
published copies. The native report does not contain a manifest hash, so the
publisher copies the manifest byte-for-byte and checks it against the source
when verifying the web package.

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
all 3,600 native animation frames; actual obstacle footprints outside runway
clearance bands; aircraft/obstacle convex-envelope separation; complete phase
endpoints; nonoverlapping runway/apron top triangles; and raycasts verifying
that every ground-route sample lies on the generated movement surface.
`verification.json` records the measurements and model hashes. Read the result
field; an earlier export-only check is not evidence of spatial correctness.

Preview images use Cycles at 2,400 × 1,650 pixels, 128 samples, denoising
and a 1.5 px Blackman–Harris filter. EEVEE viewport sampling is set to 64.
Curved roofs use smooth normals with crisp fascia edges. Ground motion has
short acceleration/deceleration ramps and 60 Hz animation samples.
Anti-aliasing belongs to the renderer; a GLB viewer must also enable it.

The native Blender scene is authored at 60 fps for 60 seconds (3,600 frames).
The final EEVEE MP4 is verified at 1280 × 880, 60 fps and 3,600 frames, with
32 temporal anti-aliasing samples. The encoded video is H.264 and runs for
60 seconds. Its file size and SHA-256, plus the still-image and model hashes,
are recorded in `media-verification.json`. Regenerate it with:

```sh
blender --background --threads 2 --python-exit-code 1 --python tools/blender/render_demo.py
```

Native viewport and browser frame rates depend on the device and shading mode.
The web 3D scene is connected to the selected forecast hour; it illustrates
the resulting state and does not make operational decisions.
