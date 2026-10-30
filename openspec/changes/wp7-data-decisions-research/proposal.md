# Proposal: How the decision is made, and which data exists

**Work package 7 · Owner:** our agents (worker `hk-research`, branch `jayden/research`).

## Why

To beat the rules we need to know which data points the real decision uses, and whether a public record of the flown direction exists.

## What Changes

- `DATA_AND_DECISIONS.md` covers who decides (DFS tower, Fraport) and how. It lists the data points behind the decision (anemometers, METAR/TAF, DWD forecasts, the rules, noise).
- It covers the systems Jayden asked about (DFS PHOENIX, DFS tower systems, Fraport, UNH and any public Betriebsrichtungsprognose, BTS/FAA ASPM) and a table of usable public sources.
- It lists the sources of flown-OD ground truth, what is not public, and which accounts are needed.

## Capabilities

### New Capabilities
- `docs/data-and-decisions`: the cited research on the decision process and data

### Modified Capabilities

## Impact

Contracts: `ml/rules.json` (rules) and `web/src/lib/forecast-types.ts` (ML and UI JSON). Work on a `<person>/<feature>` branch, rebase onto `main`, land by fast-forward (see `AGENTS.md`).
