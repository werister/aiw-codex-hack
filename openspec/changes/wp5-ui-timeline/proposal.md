# Proposal: UI: 48 h timeline and iPad widget

**Work package 5 · Owner:** Jayden (head agent).

## Why

Ops staff need to see in seconds what will change, when, and how sure we are.

## What Changes

- A tower-staff view first. The people in the tower work under stress, so the screen shows the current OD, runway 18 yes/no and the next change with its confidence in large type, with a click to drill down (team brainstorm, `briefing/brainstorm-268.md`).
- A Next.js page in `web/` reads `ForecastResponse` JSON and shows 48 hourly cells: OD 25/07, P(18 usable), confidence, and the next change with its window.
- A simulated ops screen: a schematic FRA runway map with the active direction and traffic flow, labelled as simulated.
- FraAlliance's look and feel.
- An iPad-sized widget view for ops or pilots.
- A model quality panel (data from WP8) and a day picker for the jury days.
- Deployed on Vercel from this repo's `main`.

- A simple tower-inspired summary and selectable hourly detail, following `briefing/brainstorm-268.md`; visible issue time, timezone, mode, source and versions explain the forecast.
- Field-specific recorded, inferred or unknown provenance: DFLD/UNH OD when established, `INFERRED` for METAR-rule fallback and runway-18 targets. Reconcile the newer CLI brief with stale type comments through a joint metadata change.
- Published-day selection from static JSON, with loading/unavailable/invalid-data states and evaluation provenance. See `design.md` and the CLI brief for the existing producer publication contract and proposed UI behavior.

## Scope

Approved refinement, 30 October: support preparation and handover with simultaneous operating-direction and runway-18 event tracks, a deterministic six-hour briefing, and a historical preparation-time comparison. Reuse the existing hour selector, conversation runtime and pitch replay. Correct marginal-probability labels and remove unsupported operational firmness claims. A separate, visibly synthetic runway-18 weather-rule scenario demonstrates the restriction workflow when saved historical cases contain no restriction; it is excluded from evaluation and published forecasts.

The delivered screen supports planning with forecast data. Live ATC integration, aircraft-position feeds and operational controls are outside WP5. The WP5 schematic traffic animation must be labelled `SIMULATION`; WP9 owns optional 3D and drops it if not ready by 15:00.

## Capabilities

### New Capabilities
- `ui/timeline`: the ops timeline and widget

### Modified Capabilities

## Impact

Contracts: `ml/rules.json` (rules) and `web/src/lib/forecast-types.ts` (ML and UI JSON). Work in the shared `main` checkout with disjoint ownership and serialized Git operations (see `AGENTS.md`).

Coordinate forecast publication with WP4, model evidence with WP3/WP8, and flown-direction provenance with WP7. Use the already documented `/forecasts/index.json`, `/forecasts/latest.json` and dated outputs from the CLI brief. The brief also defines the 0.5 runway-18 threshold and margin-based certainty score; retain those semantics. Resolve closure endpoints beyond the forecast horizon jointly before displaying a reopening time. Preserve WP3's `web/src/data/backtest.json`; WP8's `quality.json` and `QualityResult` remain joint contract dependencies. Browser context and operational-system evidence: `briefing/2026-10-30-ui-atc-context.md`.

The updated CLI brief permits recorded DFLD and published UNH OD references, while existing type comments still call them rule-derived. Per-target provenance and missing-reference handling need producer/type/UI agreement; until then unknown provenance stays explicit. Preserve the documented `rules-fallback` model-version label.
