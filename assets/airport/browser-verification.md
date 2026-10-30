# Browser verification · 2026-10-30

Scope: browser rendering of the Blender airport environment, selected-hour state, and illustrative traffic. This is not operational clearance or an aircraft-assignment validation.

## Verified

- Browser UI selection exercised all four model states: OD 25/07 × Runway 18 open/closed. The renderer reported the matching `data-od`, `data-center-runway` and `data-flex-runway` values; the flexible departure uses Runway 18 when open and the selected centre runway when closed.
- A deliberately conflicting fixture set `rule_od` and `rule_18` opposite to the model. The scene followed the model fields.
- On the real 2026-10-02 forecast, selecting 08:00 changed OD 25 to 07 and updated the selected-time and Runway 18 probability caption.
- Pause and replay controls worked. WebGL antialiasing reported `true`; the scene rendered at 118 draw calls and about 120 fps without concurrent Blender work. Frame rate was lower while Blender was rendering, so these are device observations, not a general performance guarantee.
- The 1280 × 720 browser capture is [25-closed-test.png](previews/web-verification/25-closed-test.png). Nine anti-aliased native Blender preview images are in [previews](previews/). Offline route checks are recorded in [runtime-verification.json](runtime-verification.json).

## Not yet verified in a browser

- Toggling the operating system's reduced-motion preference.
- Failure recovery for asynchronous scene import, missing GLB assets, or WebGL context loss.

The component and renderer contain reduced-motion and error-fallback paths, but source inspection is not browser evidence. Keep these checks open in the WP9 task list.
