# Browser verification · 2026-10-30

Scope: browser rendering of the Blender airport environment, selected-hour state, and illustrative traffic. This is not operational clearance or an aircraft-assignment validation.

The interaction checks below were run against the browser development app; CDP supplied the media and network test overrides. They were not run against a production deployment.

## Verified

- Browser UI selection exercised all four model states: OD 25/07 × Runway 18 open/closed. The renderer reported the matching `data-od`, `data-center-runway` and `data-flex-runway` values; the flexible departure uses Runway 18 when open and the selected centre runway when closed.
- A deliberately conflicting fixture set `rule_od` and `rule_18_usable` opposite to the model. The scene followed the model fields.
- On the real 2026-10-02 forecast, selecting 08:00 changed OD 25 to 07 and updated the selected-time and Runway 18 probability caption.
- The `/widget` view also loaded the same scene at 542 × 330 pixels; its 08:00 event button updated the model direction to 07 and the caption to the selected hour.
- Pause and replay controls worked. WebGL antialiasing reported `true`; the scene rendered at 118 draw calls and about 120 fps without concurrent Blender work. Frame rate was lower while Blender was rendering, so these are device observations, not a general performance guarantee.
- The 1280 × 720 browser capture is [25-closed-test.png](previews/web-verification/25-closed-test.png). Nine anti-aliased native Blender preview images are in [previews](previews/). Offline route checks are recorded in [runtime-verification.json](runtime-verification.json).
- With `prefers-reduced-motion: reduce` enabled before reload, the scene reached `ready` paused and exposed Play; activating Play changed the renderer's paused state to false.
- At 390 × 844, the page had no horizontal overflow and the scene canvas measured 310 × 280 pixels. See [mobile.png](previews/web-verification/mobile.png).
- Blocking only the environment GLB and reloading removed the WebGL canvas, the unavailable-scene status, and the RunwayMap fallback. All four test-fixture forecast-hour controls remained available. A second check on the real 2026-10-02 forecast selected 08:00 during this failure and confirmed that the fallback map changed to OD 07. See [model-load-fallback.png](previews/web-verification/model-load-fallback.png).
- After the overrides, the media preference and viewport were reset and the real forecast restored.

## Remaining qualification

- These checks used CDP media/network overrides in the development app; a production build or physical-device check is not represented here.
- Import-module rejection and WebGL context loss were not injected. The browser-tested network failure covered the environment GLB recovery path.

## Build

- The normal `npm run build` Turbopack path failed in this environment because its CSS/PostCSS worker could not bind a port (`Operation not permitted`), including after an escalated retry from the main process (`/tmp/airport-default-production-build.log`). Panic logs: `/var/folders/pc/tm7c6s3x3_xc0lg1qdsjrp100000gq/T/next-panic-76eabb1cc37ce4220ed37374648e38d3.log` and `/var/folders/pc/tm7c6s3x3_xc0lg1qdsjrp100000gq/T/next-panic-47b82d1e987240c2efca517166991a2a.log`.
- The documented alternate `npx next build --webpack` compiled, type-checked, and generated all 7 pages on Next.js 16.4.3, but it is **not a production pass**: the production browser smoke showed missing Tailwind utilities, leaving the icons and timeline layout unstyled. The current `next.config.ts` configures the Tailwind Turbopack loader only; no config workaround was made. The temporary server on port 3054 has been stopped.

Source and UI checks are scoped to the illustrative demo; they do not validate live aircraft operations.
