# Proposal: Model and held-out backtest

**Work package 3 · Owner:** Kai Detmers, with our agents.

## Why

FraAlliance wants a machine-learning model that beats the rule baseline, evaluated honestly at 1, 6 and 24 hours ahead.

## What Changes

- Gradient boosting (scikit-learn) predicts P(OD 25) and P(runway 18 usable) for every lead from 1 to 48 h.
- Features use only what was known at issue time: the observed state, forecasts from runs issued before it, the rule baseline, hour and season.
- A walk-forward backtest (expanding window, folds by month) on held-out months reports accuracy and Brier score at 1, 6, 24 and 48 h against persistence and the rule baseline. It writes `web/public/data/backtest.json` and the top drivers.

## Capabilities

### New Capabilities
- `forecast/model`: the trained model and its honest evaluation

### Modified Capabilities

## Impact

Contracts: `ml/rules.json` (rules) and `web/src/lib/forecast-types.ts` (ML and UI JSON). Work on a `<person>/<feature>` branch, rebase onto `main`, land by fast-forward (see `AGENTS.md`).
