# Proposal: Labels and rule baseline

**Work package 2 · Owner:** Kai Detmers.

## Why

The jury grades against the operating direction actually flown. Our labels and our baseline must follow the official rules exactly, including the 30-minute tolerance.

## What Changes

- `ml/rules.py` implements the official rules from `ml/rules.json` as pure functions with unit tests: the tailwind and crosswind formulas, the OD state machine with the 30-minute hysteresis, and runway 18 usability.
- `python -m ml.labels` turns the half-hourly METARs into hourly labels (OD 25/07, runway 18 usable) and prints the base rates against FraAlliance's numbers (61% west, 156 changes a year).
- The rule baseline applies the same state machine to the forecast wind, starting from the state at issue time.

## Capabilities

### New Capabilities
- `labels/official-rules`: the official FraAlliance rules as tested code, and the labels made from them

### Modified Capabilities

## Impact

Contracts: `ml/rules.json` (rules) and `web/src/lib/forecast-types.ts` (ML and UI JSON). Work on a `<person>/<feature>` branch, rebase onto `main`, land by fast-forward (see `AGENTS.md`).
