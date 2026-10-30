# Proposal: Model card, business case and pitch

**Work package 6 · Owner:** Hugo Hader and Luca Schultz.

## Why

The submission needs a one-page model card, and the 17:00 pitch needs the business case in numbers.

## What Changes

- `MODEL_CARD.md`, one page: data sources (from WP1/WP7), labels, model, quality at 1/6/24 h vs baselines, key drivers, limits.
- Business case with cited or clearly labelled numbers: staff repositioning, missed connections, capacity when 18 closes.
- Pitch and demo script for Hugo; Luca is the backup presenter and runs a fresh-user dry run.

## Capabilities

### New Capabilities
- `docs/model-card`: the one-page model card and the pitch material

### Modified Capabilities

## Impact

Contracts: `ml/rules.json` (rules) and `web/src/lib/forecast-types.ts` (ML and UI JSON). Work on a `<person>/<feature>` branch, rebase onto `main`, land by fast-forward (see `AGENTS.md`).
