# Proposal: Forecast CLI and jury-day forecasts

**Work package 4 · Owner:** A Codex worker.

## Why

The jury compares our forecasts for their test days with the directions actually flown, so any day must be forecastable from one command.

## What Changes

- `python -m ml.forecast --day YYYY-MM-DD` issues at 00:00 Europe/Berlin and prints a 48-row hourly table: OD, P(OD 25), P(18 usable), certainty, rule OD, rule 18, wind, plus the next likely change.
- Past days run as a hindcast with archived forecasts. Today and future days use the live forecast and the latest METAR. `--now` issues at the current hour.
- `--json` emits `ForecastResponse` (`web/src/lib/forecast-types.ts`); `--out` writes it to `web/public/forecasts/`.

## Capabilities

### New Capabilities
- `forecast/cli`: the command that forecasts any given day

### Modified Capabilities

## Impact

Contracts: `ml/rules.json` (rules) and `web/src/lib/forecast-types.ts` (ML and UI JSON). Work on a `<person>/<feature>` branch, rebase onto `main`, land by fast-forward (see `AGENTS.md`).
