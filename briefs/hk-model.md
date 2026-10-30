# hk-model · rules, model, walk-forward backtest, quality numbers (WP2 code, WP3, WP8)

Worktree `C:\olawt\aiw-wt-ml`, branch `jayden/model`. The head lane merges and talks to you through this terminal. You may use heavy subagents for parallel parts (features, evaluation, tests). Other workers: `hk-data3` (branch `jayden/data`: METAR, TAF, Open-Meteo and DWD into `data/`), `hk-research` (branch `jayden/research`: ground truth in `data/ground_truth/`), `hk-cli` (branch `jayden/cli`: the forecast CLI, it calls your `ml/predict.py`). Kai Detmers (human) co-leads the ML work and reviews.

Read first: `AGENTS.md`, `frankfurt-airport-operating-direction-forecast.md` (official brief: wins), `ml/rules.json`, `ml/README.md`, `web/src/lib/forecast-types.ts`, and `openspec/changes/wp2-*`, `wp3-*`, `wp8-*` (tick tasks off as you finish them).

## PUSH IS PAUSED
origin/main's history is being rewritten. **Commit locally only, and don't push** until the head lane says PUSH OK. Then: `git fetch && git rebase --onto origin/main <OLD_SHA>` (the head gives you the SHA) and `git push -u origin jayden/model`.

## Data you build on (all in this repo)
- **Target for OD = recorded flown directions:** `data/ground_truth/dfld_hourly.csv` on `origin/jayden/research` (DFLD, 24,546 hourly rows 2024-01 to 2026-10-29, `od` as string "25"/"07"). Read `data/ground_truth/README.md` first. Get it with `git checkout origin/jayden/research -- data/ground_truth` (don't commit that folder; it lands from its own branch).
- **METAR, TAF, Open-Meteo previous runs and historical forecast, DWD:** branch `jayden/data` (local in this repo, may still be growing). Copy what you need with `git checkout jayden/data -- data/ ml/fetch.py ml/__init__.py` and don't commit those files. If a file you need isn't there yet, ask the head lane instead of downloading it yourself.
- **Runway 18 target:** no recorded weather-closure history exists, so it's **INFERRED** from METAR with the official rule (tailwind on 180 of 15 kt or more, or crosswind including gusts over 40 kt). Say "inferred" in every output.

## You own (create only these)
`ml/rules.py`, `ml/tests/test_rules.py`, `ml/features.py`, `ml/train.py`, `ml/predict.py`, `ml/quality.py`, `ml/models/`, `ml/tests/test_no_leakage.py`, `web/src/data/backtest.json`, `web/src/data/quality.json`, and `ml/requirements.txt` additions (tzdata, pytest, joblib).

1. **`ml/rules.py` + tests (WP2 code; Kai reviews):** pure functions reading `ml/rules.json`. `tailwind(speed, dir, heading)` = speed × cos(dir − heading − 180°). Also `crosswind`, `r18_usable`, and `od_state_machine` over time-ordered (time, dir|None, speed, gust):
   - ≥ 10 kt tailwind on the current OD → switch now;
   - 0 < tailwind < 10 kt for more than 30 min → switch to the headwind direction;
   - calm or variable → hold.
   Test with the brief's examples (090°/20 kt → OD 07; 330°/20 kt → 18 closed; 30° and 45° off at 20 kt give 17.3 and 14.1) and the hysteresis cases.
2. **Features (`ml/features.py`), only what was known at issue time T:**
   - the recorded OD at T and hours since the last change (DFLD up to T);
   - observed METAR wind and tailwinds at T and their 3 h trend;
   - weather-model values for the target hour from runs issued before T (`_previous_day1` for leads 1–24 h, `_previous_day2` for 25–48 h);
   - forecast tailwinds on 25, 07 and 18;
   - the rule baseline (state machine run forward from the OD at T over the forecast wind);
   - hour of day (local, Europe/Berlin via zoneinfo + tzdata), season, and the lead h.
3. **Model and walk-forward (`ml/train.py`):** `HistGradientBoostingClassifier` for P(OD 25) and P(18 usable). Walk-forward with expanding windows and monthly folds over the last 6+ months: each fold trains only on data before the fold. Report out-of-sample per lead (1, 6, 24, 48 h) for model, rules and persistence: accuracy, Brier, and accuracy on hours where the OD changed within the lead window (the hard cases). Also report in-sample next to it. Save the final model trained on everything to `ml/models/`.
4. **`ml/predict.py`, the interface `hk-cli` calls:** `predict_48h(issue_time_utc, obs: DataFrame, nwp: DataFrame, od_at_issue: str) -> DataFrame`. It has 48 rows with `time`, `lead_h`, `wind_dir_deg`, `wind_kt`, `gust_kt`, `tailwind_25_kt`, `tailwind_18_kt`, `rule_od`, `rule_18_usable`, `p_od25`, `p_18_usable`. Document the expected `obs` and `nwp` columns in its docstring.
5. **Outputs:** `web/src/data/backtest.json` (`BacktestResult` in `web/src/lib/forecast-types.ts`) and `web/src/data/quality.json`:
   - walk-forward folds (train and test periods, sizes)
   - in- vs out-of-sample per lead
   - a reliability table (predicted-probability bins vs observed frequency)
   - next-change timing hit rate within ±1 h and ±3 h
   - top drivers (permutation importance)
   - the data sources
   Write the `quality.json` shape into `ml/README.md`; the head lane adds the TypeScript type.
6. **`ml/tests/test_no_leakage.py`:** for a few issue times, assert that no feature uses data after T and that the weather-model offset matches the lead.

## Rules
- No AI assistant, model or vendor names in commit messages, trailers or files (say "head agent" or "our agents"). Plain messages like `feat: add walk-forward backtest`.
- Never read, print or write API keys or `.env*`.
- About 4 GB of RAM is free: no deep learning, no huge grids, and process the data in chunks.
- Report in one line at each milestone: rules plus tests green, first walk-forward table, `predict.py` ready for `hk-cli`, outputs written. **First out-of-sample table by 13:45.**
