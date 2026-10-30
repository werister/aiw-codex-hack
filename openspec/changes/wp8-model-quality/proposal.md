# Proposal: Model quality numbers for the dashboard

**Work package 8 · Owner:** a Codex worker (Astra). The UI panel itself is WP5.

## Why

The team and the jury want to see how good the model is and on what it was trained: in-sample vs out-of-sample, the walk-forward folds, skill at 1, 6 and 24 h, and a confidence score that means something (team brainstorm, `briefing/brainstorm-268.md`).

## What Changes

- `web/src/data/quality.json` holds the training and test periods, the data used, and the walk-forward folds. It also has per-lead accuracy and Brier score for the model, the rules and persistence, in-sample vs out-of-sample.
- A reliability (calibration) table, so the confidence score can be checked: when we say 80%, are we right about 80% of the time?
- How often the next-change time lands within ±1 h and ±3 h.

## Capabilities

### New Capabilities
- `evaluation/model-quality`: the numbers behind the model quality panel

### Modified Capabilities

## Impact

Reads the WP3 models and the WP2 labels; feeds the WP5 panel and the WP6 model card. Contract: add a `QualityResult` type to `web/src/lib/forecast-types.ts` together with the UI owner.
