# Spec Delta

## Purpose

Show how the selected Frankfurt Airport forecast hour maps to operating direction and runway-18 availability, using a clearly labelled illustrative 3D scene.

## ADDED Requirements

### Requirement: Crafted map-like 3D presentation

The scene SHALL present recognizable Frankfurt Airport landmarks and aircraft in a high-fidelity, simplified map style, with restrained materials and smoothly rendered forms. It SHALL use antialiasing and SHALL not use comic styling.

#### Scenario: Airport scene renders in the browser

- **WHEN** the airport model and scene are ready
- **THEN** terminal, tower, runways, and aircraft silhouettes are smooth at the displayed size, with no jagged edges or visible geometry gaps

### Requirement: Selected forecast hour drives the scene

The scene SHALL render the model OD, the runway-18 state derived from the selected hour's `p_18_usable` at the 50% threshold, and that hour's forecast wind. When a selected hour is supplied, the scene SHALL identify its Berlin local time and lead, show the model's runway-18 probability and certainty, and state that the binary display uses the 50% threshold. Traffic SHALL be labelled illustrative.

#### Scenario: User selects an hour

- **WHEN** the selected forecast hour changes
- **THEN** the scene updates to that hour's model OD, runway-18 threshold result, and wind, and the caption identifies its local time, lead, probability, certainty, and display threshold

#### Scenario: Existing widget omits forecast metadata

- **WHEN** the scene is rendered without the optional forecast-hour metadata
- **THEN** it still renders from OD, runway-18 state, and wind without failing

### Requirement: Show all supported runway states

The scene SHALL support all four combinations of model OD 25 or 07 and runway 18 open or closed. Parallel-runway flow SHALL follow the selected OD. When runway 18 is open, illustrative departures may use it; when closed, no illustrative traffic SHALL use runway 18 and any depicted departures SHALL use the parallel runway system. These flows are explanatory visuals, not aircraft assignments.

#### Scenario: Runway 18 open

- **WHEN** `p_18_usable >= 0.5` for the selected hour
- **THEN** the scene shows runway 18 as open and allows illustrative southbound departure traffic on it

#### Scenario: Runway 18 closed

- **WHEN** `p_18_usable < 0.5` for the selected hour
- **THEN** the scene shows runway 18 as closed, routes no illustrative traffic on it, and keeps parallel-runway traffic consistent with the selected OD

### Requirement: Reset traffic at forecast-hour boundaries

The scene SHALL start a new illustrative traffic flow when the selected forecast hour changes. It SHALL NOT animate an aircraft through a 180-degree turn on a runway to represent a direction change.

#### Scenario: Consecutive hours use different operating directions

- **WHEN** the user selects a new hour whose model OD differs from the prior hour
- **THEN** the prior flow clears and a new flow begins from the selected hour's OD without an on-runway U-turn

### Requirement: Accessible motion controls and reduced-motion behavior

The scene SHALL provide keyboard-operable pause and replay controls with accessible names. It SHALL begin paused when `prefers-reduced-motion: reduce` is active; users can explicitly start motion.

#### Scenario: User pauses or replays

- **WHEN** the user activates a motion control
- **THEN** the scene pauses, resumes, or restarts traffic for the currently selected forecast hour

#### Scenario: Reduced motion is requested

- **WHEN** reduced motion is active at load or becomes active during playback
- **THEN** the scene remains or becomes paused until the user explicitly starts it

### Requirement: Loading and failure fallback

The UI SHALL expose a loading state until the 3D scene is ready. If the module, WebGL renderer, or required asset fails, it SHALL show the existing schematic runway map as a fallback.

#### Scenario: 3D scene cannot load

- **WHEN** scene import or initialization reports an error
- **THEN** the 3D host is removed and the runway-map fallback is shown
