# FRA · 3D asset brief

Build an editable Blender asset library for explaining the FraAlliance forecast.
Visual language: restrained map architecture, realistic proportions, smooth
aircraft silhouettes, ivory metal, slate glazing, muted sage landscape, soft
daylight. Detail comes from form and construction, not noisy photo textures.

- Assets: generic narrowbody and widebody twins, four runway variants, a
  Frankfurt-inspired control tower, and a compact airport demonstration scene.
- Expert focus: model the movement corridors and architecture together; keep
  entire building/tree footprints clear of runways and aircraft paths. Preserve
  readable silhouettes, consistent origins and reusable exported geometry.
- Quality reference: Apple Maps Detailed City Experience — individually shaped
  landmark architecture, articulated roofs and glazing, restrained material
  contrasts, readable ground markings and soft daylight. Use the actual Apple
  reference images for comparison, not a generic low-poly interpretation.
- Primary inputs: `frankfurt-airport-operating-direction-forecast.md`,
  `ml/rules.json`, `web/src/lib/forecast-types.ts`; Fraport's runway diagram and
  dimensions; DFS photographs of its Frankfurt tower.
- Method: procedural mesh modelling in Blender, bevelled architectural edges,
  solid PBR materials, 2D union and constrained triangulation of movement
  pavement, GLB export/re-import, evaluated-geometry clearance and surface
  checks, and inspection of full playback plus close-up/overview renders.
- Acceptance: two recognizable aircraft types; tower with glazed cab and
  external stair; correct runway identifiers; three coordinated 07/25 runways;
  departure-only 18 to the south; example paths for both ODs and 18 closure;
  readable renders and self-contained GLBs; no building on a runway or taxi
  route; no competing coplanar pavement faces; clear OD25/OD07/18-closed labels;
  the rerouted departure must reach the end of its centre-runway departure;
  smooth curved surfaces, anti-aliased renders and 60 fps animation with gentle
  starts/stops. The MP4 must contain 3,600 individually rendered frames.

The airport layout is an illustrative compressed diagram, not surveyed geometry
or an operational taxi clearance. The demonstration paths explain the supplied
forecast; they do not predict individual flight assignments or implement ATC.
No web UI or ML contract changes are part of this asset task.

References (consulted 2026-10-30):

- [Apple Maps: official 3D city and landmark reference images](https://www.apple.com/newsroom/2021/09/apple-maps-introduces-new-ways-to-explore-major-cities-in-3d/)
- [Shapely constrained triangulation](https://shapely.readthedocs.io/en/2.1.2/reference/shapely.constrained_delaunay_triangles.html) preserves polygon boundaries, including runway cutouts.

- [Official Fraport runway diagram](https://www.fraport.com/en/sustainability/dialog-with-neighbors/noise-and-air/flight-operations/runway-system-and-operating-hours.html)
- [Fraport airport user regulations, runway dimensions, §1.2](https://sslapps.fraport.de/webportalAVS/pdf/Airport-user-regulations.pdf)
- [DFS Frankfurt tower photograph](https://karriere.dfs.de/Media%20je%20Seite/03-00-Ueber%20%28Arbeitgeber%29/03-05-Standorte/03-05-00-Standorte/DFS-Standort-Frankfurt-01.jpg)

All delivered geometry is authored for this project; reference photographs are
not embedded, traced as textures, or redistributed. Aircraft and architecture
are unbranded interpretations, not manufacturer CAD or exact replicas.
