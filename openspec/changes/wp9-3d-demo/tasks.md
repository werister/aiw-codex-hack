# Tasks

## 1. Forecast-selected airport scene

- [x] 1.1 Choose Blender-authored airport geometry with a client-side Three.js renderer; a fixed Blender animation is not the runtime.
- [x] 1.2 Finalize and import the Blender airport assets in the browser scene, including all four runways and the airport landmark models.
- [x] 1.3 Implement antialiased illustrative traffic for OD 25/07 and runway 18 open/closed, with selected-hour reset behavior and no on-runway U-turn.
- [x] 1.4 Connect `SceneHero` to the selected forecast hour, preserve callers without forecast metadata, and add accessible play/pause/replay behavior.
- [ ] 1.5 Verify reduced-motion behavior and asynchronous import, asset, and WebGL-error fallbacks in the browser. Completed state, transition, control, and antialiasing evidence is recorded in `assets/airport/browser-verification.md`.
