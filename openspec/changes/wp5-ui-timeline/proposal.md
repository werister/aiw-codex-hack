# Proposal: UI: 48 h timeline and iPad widget

**Work package 5 · Owner:** Jayden (head agent).

## Why

Ops staff need to see in seconds what will change, when, and how sure we are.

## What Changes

- A Next.js page in `web/` reads `ForecastResponse` JSON and shows 48 hourly cells: OD 25/07, P(18 usable), certainty, and the next change with its window.
- An iPad-sized widget view for ops or pilots.
- A backtest panel with skill at 1/6/24 h vs rules and persistence, and a day picker for the jury days.
- Deployed on Vercel from this repo's `main`.

## Capabilities

### New Capabilities
- `ui/timeline`: the ops timeline and widget

### Modified Capabilities

## Impact

Contracts: `ml/rules.json` (rules) and `web/src/lib/forecast-types.ts` (ML and UI JSON). Work on a `<person>/<feature>` branch, rebase onto `main`, land by fast-forward (see `AGENTS.md`).
