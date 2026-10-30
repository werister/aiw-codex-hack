## Context

`ForecastApp` already selects one `HourForecast` row and passes its model OD, runway-18 threshold result, and wind to `SceneHero`. The current scene loader targets a missing `/pitch/scene.js`; the existing `RunwayMap` is the fallback. The ML/UI forecast contract is owned by `web/src/lib/forecast-types.ts` and remains unchanged.

## Goals / Non-Goals

**Goals:**
- Make the selected forecast hour the source of the browser scene state.
- Keep the Blender-authored airport model reusable while rendering traffic in the browser.
- Preserve a crafted, high-fidelity map look with simplified recognizable landmarks, smooth forms, restrained materials, and antialiasing.
- Make loading, failure, motion, and the runway-18 probability threshold understandable to users.

**Non-Goals:**
- Simulate individual flight plans, aircraft assignments, air-traffic control, or live airport operations.
- Change model outputs, forecast-hour selection, or the serialized ML/UI contract.
- Claim that the 3D illustration improves forecast accuracy or represents measured aircraft activity.

## Decisions

1. **Use Blender for airport geometry and Three.js for interactive rendering.** A static Blender render cannot respond to any of the 48 selected forecast hours. The browser scene can reuse the authored airport model and change its illustrative flow without changing the forecast data. A single Blender animation remains useful as a visual reference, but is not the runtime. The user-supplied Apple Maps 3D reference sets a quality bar for simplified, recognizable forms; it does not call for copied assets or comic styling.

2. **Keep `SceneHero` as the adapter.** It dynamically imports `@/lib/airport-scene` on the client and passes `{ od, r18Open, wind?, forecastHour?, theme, paused, onReady, onError }` to `mount(host, options)`. The returned controller exposes `setState(state)`, `reset()`, `setPaused(boolean)`, and `destroy()`. State contains `{ od, r18Open, wind?, forecastHour? }`; `forecastHour` is the selected row's `time`, `local`, `lead_h`, `p_18_usable`, and `certainty` only. `Widget` remains valid when it omits `forecastHour`.

3. **Preserve the probability and threshold in the UI.** The scene receives the model OD and the `p_18_usable >= 0.5` binary depiction. The caption shows the selected local time, lead, exact runway-18 probability, model certainty, and the 50% display threshold. This describes the model output without implying a deterministic operational decision.

4. **Restart illustrative traffic at a selected-hour boundary.** `forecastHour.time` is the scene reset key. Updating the selected hour clears and starts a new illustrative flow under that hour's state; it does not interpolate a runway U-turn. Same-hour state changes can explicitly reset the controller. Traffic remains labelled illustrative.

5. **Fail back to the existing map and respect reduced motion.** The scene shows a loading status until `onReady`; import, WebGL, or asset errors restore the schematic runway map. Normal users see traffic motion with pause and replay controls. When `prefers-reduced-motion` is active, motion stays paused until the user explicitly starts it; if that preference becomes active during playback, playback pauses.

## Risks / Trade-offs

- **3D assets or WebGL fail to load** → Keep the existing `RunwayMap` as the visible fallback and expose a loading/error status.
- **Users mistake probability for an operational guarantee** → Show the numeric probability, threshold, and illustrative-traffic caption together.
- **Motion becomes distracting or inaccessible** → Provide keyboard-operable controls and honor reduced-motion changes.

## Migration Plan

No forecast artifact or API migration is required. Add the optional `forecastHour` prop at the `SceneHero` call sites; call sites without it continue to render. If the browser scene fails, the adapter restores the existing map.
