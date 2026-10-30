# FRA · 3D asset brief

Build an editable Blender asset library for explaining the FraAlliance forecast.
Visual language: restrained map architecture, realistic proportions, smooth
aircraft silhouettes, ivory metal, slate glazing, muted sage landscape, soft
daylight. Detail comes from form and construction, not noisy photo textures.

- Assets: generic narrowbody and widebody twins, four runway variants, a
  Frankfurt-inspired control tower, and a compact airport demonstration scene.
- Expert focus: readable silhouettes at map distance, consistent origins,
  named movable parts, shared materials and reusable exported geometry.
- Primary inputs: `frankfurt-airport-operating-direction-forecast.md`,
  `ml/rules.json`, `web/src/lib/forecast-types.ts`; Fraport's runway diagram and
  dimensions; DFS photographs of its Frankfurt tower.
- Method: procedural mesh modelling in Blender, bevelled architectural edges,
  solid PBR materials, GLB export and re-import, independent geometry and route
  checks, close-up and overview renders.
- Acceptance: two recognizable aircraft types; tower with glazed cab and
  external stair; correct runway identifiers; three coordinated 07/25 runways;
  departure-only 18 to the south; example paths for both ODs and 18 closure;
  readable renders and self-contained GLBs.

The airport layout is an illustrative compressed diagram, not surveyed geometry
or an operational taxi clearance. The demonstration paths explain the supplied
forecast; they do not predict individual flight assignments or implement ATC.
No web UI or ML contract changes are part of this asset task.

References (consulted 2026-10-30):

- [Official Fraport runway diagram](https://www.fraport.com/en/sustainability/dialog-with-neighbors/noise-and-air/flight-operations/runway-system-and-operating-hours.html)
- [Fraport airport user regulations, runway dimensions, §1.2](https://sslapps.fraport.de/webportalAVS/pdf/Airport-user-regulations.pdf)
- [DFS Frankfurt tower photograph](https://karriere.dfs.de/Media%20je%20Seite/03-00-Ueber%20%28Arbeitgeber%29/03-05-Standorte/03-05-00-Standorte/DFS-Standort-Frankfurt-01.jpg)

All delivered geometry is authored for this project; reference photographs are
not embedded, traced as textures, or redistributed. Aircraft and architecture
are unbranded interpretations, not manufacturer CAD or exact replicas.
