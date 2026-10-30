# Lift-off | Model card

**Version:** walk-forward-v6 | **Date:** 30 October 2026 | **Challenge:** FraAlliance

## Purpose and model

Hourly forecasts up to 48 h ahead: operating direction 25/07, probability of runway-18 weather usability, certainty and next likely change. Two gradient-boosted classifiers use 45 features and persistence blending. Intended for planning support; actual operating decisions remain with DFS.

## Public data and key drivers

[DFLD](https://www.dfld.de/Mess/StatWetter.php?R=1&D=01.10.2026) supplies half-hour operating-direction records from 2018; [IEM](https://mesonet.agron.iastate.edu/request/download.phtml) supplies EDDF METAR. [Open-Meteo Previous Runs](https://open-meteo.com/en/docs/previous-runs-api) supplies archived ECMWF, GFS and ICON weather forecasts from 2024. The [FraAlliance brief](https://github.com/werister/aiw-codex-hack/blob/main/frankfurt-airport-operating-direction-forecast.md) defines the rule baseline. Runway-18 targets are inferred from METAR, not observed closures.

Top permutation drivers in the final test month: north-south pressure difference, current direction, ensemble tailwind on 25, ECMWF tailwind on 25 and pressure-derived tailwind.

## Evaluation and quality

Twelve expanding monthly folds, November 2025-October 2026; training targets end before each test month. Issues every 6 h; archived forecast availability uses a six-hour publication proxy. Stable-hour accuracy on matched labelled rows:

| Lead | Model | Base-wind rules | Keep-current | Rows |
|---|---:|---:|---:|---:|
| 1 h | 95.7% | 93.1% | 95.9% | 1,416 |
| 6 h | 92.7% | 88.1% | 88.8% | 1,416 |
| 24 h | 91.8% | 87.7% | 75.1% | 1,383 |
| 48 h | 88.9% | 84.0% | 64.2% | 1,338 |

24 h Brier score: model 0.0637; rules 0.1229. At 6/24/48 h, seven-day block-bootstrap 95% intervals for the accuracy advantage over rules are +2.7 to +6.5 / +3.1 to +6.3 / +3.5 to +7.2 percentage points. No accuracy advantage over persistence is established at 1 h.

## Limits

The folds informed feature selection and review; they are not an untouched final test. Exact weather publication times, DFLD publication delays and summer-clock alignment remain unverified. DFLD is a public proxy; transition hours are excluded from the accuracy table. Certainty is a probability-margin score and the change window is heuristic, neither calibrated.

Runway-18 skill is unproven: at 24 h, 0 of 12 positive windows detected, 0 false alarms, 307 complete windows; 1,125 excluded. These are overlapping windows with inferred weather labels, not unique operational closures.

**Evidence and reproduction:** [Technical card](https://github.com/werister/aiw-codex-hack/blob/main/MODEL_CARD.md), [published results](https://github.com/werister/aiw-codex-hack/blob/main/web/public/data/quality.json), [submission and run commands](https://github.com/werister/aiw-codex-hack/blob/main/SUBMISSION.md).
