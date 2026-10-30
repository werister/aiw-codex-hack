# Proposal: Data sources and download

**Work package 1 · Owner:** our agents (worker `hk-data`, branch `jayden/data`). Data check: Luca.

## Why

Every later package needs the same public data, downloaded once, with every source cited, as the brief requires.

## What Changes

- `python -m ml.fetch` downloads and caches at least 2 years of EDDF data into `data/`: METAR, TAF, Open-Meteo previous runs (forecasts issued 1 and 2 days ahead), Open-Meteo historical forecast, DWD station 01420 wind, and a live snapshot.
- `data/README.md` lists every file with source URL, period, rows, units, licence and retrieval time.
- Sources that need an account are listed with a sign-up URL. Agents never sign up.

## Capabilities

### New Capabilities
- `data/sources`: downloading and documenting the public input data

### Modified Capabilities

## Impact

Contracts: `ml/rules.json` (rules) and `web/src/lib/forecast-types.ts` (ML and UI JSON). Work on a `<person>/<feature>` branch, rebase onto `main`, land by fast-forward (see `AGENTS.md`).
