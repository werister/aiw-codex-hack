# Tasks

## 1. Features

- [x] 1.1 Issue-time features: state, tailwinds, trend, minutes since change
- [x] 1.2 Forecast features by lead (day 1 run for 1-24 h, day 2 for 25-48 h)
- [x] 1.3 Rule baseline as a feature

## 2. Train and evaluate

- [x] 2.1 Walk-forward evaluation (expanding window, monthly folds), never random cross-validation on a time series; train two classifiers
- [x] 2.1b Report in-sample vs out-of-sample skill side by side
- [x] 2.2 Skill table at 1/6/24/48 h vs rules and persistence
- [x] 2.3 Permutation importance gives the drivers
- [x] 2.4 `web/public/data/backtest.json`
