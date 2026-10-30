# Proposal: Forecast-selected 3D airport scene

**Work package 9 · Owner:** web and Blender contributors

## Why

A selected forecast hour should be legible to a non-aviation audience in seconds. A scene that follows the forecast timeline makes the operating direction and runway-18 decision concrete (team brainstorm, `briefing/brainstorm-268.md`).

## What Changes

- Import the Blender-authored Frankfurt Airport model into a client-side Three.js scene.
- Use a high-fidelity but simplified map style, taking Apple Maps 3D as the quality reference: recognizable airport landmarks, restrained materials, smooth surfaces, and no comic look.
- Drive the scene from the currently selected forecast hour: model operating direction, runway-18 usable probability, and forecast wind.
- Show the selected local time, lead time, model probability, certainty, and the 50% threshold used for the binary runway-18 depiction.
- Add accessible play, pause, and replay controls, with a static initial state for reduced-motion users.
- Show a loading state and fall back to the existing runway map if the 3D scene cannot load.

## Capabilities

### New Capabilities
- `demo/3d-scene`: an optional 3D illustration controlled by the selected forecast hour

### Modified Capabilities

## Impact

Touches the forecast UI adapter, browser scene, and Blender-authored assets. It does not change the ML forecast contract. Aircraft motion is illustrative and does not claim to represent live operations or individual aircraft assignments; the existing forecast/map experience remains available if 3D loading fails.
