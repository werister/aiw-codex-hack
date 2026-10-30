> Archived worker report. Claims and paths below refer to the worker's stated snapshot and time. “Nothing committed” describes that worker's run; this report is now preserved by the coordinator. See [the consolidated timeline](../../experiments/REDTEAM_TIMELINE.md) for reconciled status and independently replayed checks.

# Red-team report: temporal leakage and evaluation selection

Scope: ML evaluation and data code in `ml/`. No app review, no training run, nothing committed, merged or pushed.

## Checkouts

- Checkout: `/Volumes/AthenaSSD/fra-redteam-a`, branch `hugo/redteam-a`.
- HEAD before testing: `403f6dce8fcf8db7bc8c93d078b0b1671a5336da`. Fast-forwarded to `origin/main` = `023e7405c88e0cbd452bc1d7a6369e686f7eff3c`. All tests ran at `023e740`.
- Pinned v4: `44d5abd3363248b1de0a3ed96ff32982aafdd7b3` ("feat: approach page with pipeline, iterations and validation"), an ancestor of `origin/main`. Its `ml/models/metadata.json` says `walk-forward-v4`; main says `walk-forward-v5`.
- `docs/STATUS.md` does not exist.
- Scratch files (untracked): `.redteam_scratch/test_redteam_leakage.py`, `.redteam_scratch/probe_real.py`, `.redteam_scratch/tmp/`.

## v4 versus main

- `suspect_od_runs`, the fold purge and the train/test split are identical in v4 and main.
- `ml/quality.py`: main only adds `r18_events`.
- `ml/train.py`: main adds `archived_inputs` (ECMWF, GFS and ICON runs, pressure boxes), significance tests, `--months` 6 → 12 and the label `walk-forward-v5`.
- `ml/features.py`: main adds `WIND_SCALE`, `add_ensemble` and the multimodel, 80 m and pressure-box columns. They use the same `previous_day1/2/3` selection.
- Result: the leakage surface is the same in both versions. Main has 12 test months (2025-11 to 2026-10); v4 has 6 (2026-05 to 2026-10).

## Findings

### F1. The stuck-feed flag looks ahead in time. Vulnerable; current scores not affected.

- **Where.** `ml/quality.py:12-26` (`suspect_od_runs`) groups each recorded run of one direction with `over.groupby(run).transform("sum") >= 3`. Every hour of a run gets the whole run's flag, including hours after the issue time.
- **Where it is used:**
  - training-row selection: `ml/train.py:59`, `:92-93` (`suspect_target`, `suspect_input`) and `:122-126` (`without_stuck_feed`). `fit(without_stuck_feed(train))` at `:196` also feeds the blend-weight validation at `:143-163`;
  - the stuck-feed-excluded scores: `ml/train.py:215`, `:236`, `:249`, `:267`;
  - midnight-issue scoring: `ml/forecast.py:372-389` (`stuck_input = ... in suspect_times`).
- **Counterexample** (`.redteam_scratch/test_redteam_leakage.py`):
  - Setup: a 07 run starts at 2026-05-31T21Z and crosses the fold boundary at 2026-06-01T00Z. Its 12 kt westerly METAR hours (over the limit) all fall after the boundary.
  - Expected: the 07 hours before the boundary are not flagged, because no over-limit hour was known then.
  - Actual: they are flagged `True`. With the data cut at the boundary, they are `False`.
  - Result: a training row (issue 21Z, target 22Z, label available 23Z) passes the purge `label_available_at < start` (`train.py:191`, assert `:195`). `without_stuck_feed` still sets its `y_od` to NaN because of test-period METAR.
- **Real data** (`.redteam_scratch/probe_real.py`):
  - Exactly one flagged run: 07, 2026-10-08T10:00Z to 2026-10-12T16:00Z, 103 hours, 17 over-limit hours.
  - It crosses no fold boundary: 0 crossings in the 12 v5 folds and 0 in the 6 v4 folds. No training set or blend-validation set is affected.
  - 4 issues in the run are flagged only with hindsight: 2026-10-08 16Z, 10-08 22Z, 10-09 04Z and 10-09 10Z. The third over-limit hour was first observed at 2026-10-09T11Z, after 25 run hours.
  - Those 4 issues remove **0** extra scored rows. All their 48 target hours lie inside the run, so the target flag excludes them anyway.
- **Verdict.**
  - Current fold scores are not affected: neither the headline `od`/`out_of_sample` scores nor `*_stuck_feed_excluded`.
  - The code is vulnerable to future data or a flagged run that crosses a month boundary.
  - Dropping target hours after the fact is label cleaning. It is disclosed (`train.py:292`) and the headline still counts those hours.
  - The final `forecast.joblib` fit also uses the whole-run flag. No score is reported for that fit.

### F2. Features were chosen on the test months. This affects how the reported numbers can be read.

- `EXPERIMENTS.md` E10, E13, E14 and E16 choose features and hyperparameters on "the same 12 test months" or "on the same folds". Examples: multimodel features, pressure boxes, deeper trees, monotonic constraints.
- The E12 table reports bootstrap CIs, McNemar and Diebold-Mariano p-values on those months (`ml/significance.py` via `train.py:236`). They do not correct for this selection.
- So the 12 out-of-sample months are no longer a clean held-out set. I did not measure the size of the bias; E14 reports alternatives within ±0.6 points.
- The stuck-run rule (`min_hours=3`) was also written after the October run had been seen. The headline score is protected because it counts those hours anyway.

### F3. Forecast-run timing (vintage join) is correct under its own assumption, with zero margin at 18 h.

- `ml/features.py:58-112`: `nwp_offset_days = (lead_h + 6 + 23) // 24` maps leads 1-18 to day1, 19-42 to day2 and 43-48 to day3.
- The archived branch reads only `_previous_dayN` columns. `data/openmeteo_previous_runs.parquet` also has unsuffixed latest-forecast (day-0) columns, and they are never read.
- At lead 18, `nwp_available_proxy` equals the issue time exactly.
- The hindcast CLI uses the same suffix rule (`ml/forecast.py:58-66`, `ml/live.py:89`, `:119`) and an availability assert (`ml/forecast.py:323-324`).
- Correctness depends on Open-Meteo `previous_dayN` coming from a run started at least 24·N hours before the target hour. Not verified.

### F4. Purge and fold boundaries hold.

- `ml/train.py:191-195`: train uses `label_available_at < start`; test uses `issue_time` within the month and `label_available_at < end`.
- In main's `web/public/data/quality.json`, 12/12 folds satisfy `train_target_end < test_start`, `od_blend_validation_period.end < test_start` and test end before the next month. In v4's `quality.json`, 6/6 folds satisfy the same checks. 0 violations.
- Minor, not leakage: the local-midnight issue on the 1st of each month (22Z or 23Z on the last day, UTC) falls in the previous fold, and `train.py:192` drops most of its leads.

### F5. Wind-speed scaling factors (`WIND_SCALE`) cannot be traced to a fit.

- `ml/features.py:16-18`: the constants are said to be fitted on 2024 only.
- The fitting script is not in the repo. `git log -S"1.684"` shows only `2300db6`.
- 2024 comes before every test month (the earliest is 2025-11). If the claim holds, there is no leak.

## Ran and saw

```
git rev-parse HEAD                                   -> 403f6dce8fcf8db7bc8c93d078b0b1671a5336da
git fetch origin; git merge --ff-only origin/main    -> 023e7405c88e0cbd452bc1d7a6369e686f7eff3c
git merge-base --is-ancestor 44d5abd origin/main     -> true
git diff 44d5abd origin/main -- ml/train.py ml/features.py ml/quality.py ml/predict.py ml/tests/test_no_leakage.py
/Users/hugohader/.venv/bin/python -c "import pandas"  -> ModuleNotFoundError: No module named 'pandas'
/usr/bin/python3 -> Python 3.9.6, pandas 2.3.3, sklearn 1.6.1 (no venv created, nothing installed)
export TMPDIR=$PWD/.redteam_scratch/tmp PYTHONDONTWRITEBYTECODE=1
/usr/bin/python3 -m pytest -q -p no:cacheprovider ml/tests/test_no_leakage.py ml/tests/test_rules.py
    -> 13 passed, 0 failed
/usr/bin/python3 -m pytest -q -p no:cacheprovider --rootdir=. .redteam_scratch/test_redteam_leakage.py
    -> 2 passed, 0 failed
/usr/bin/python3 -m pytest -q -p no:cacheprovider --rootdir=. ml/tests/test_no_leakage.py ml/tests/test_rules.py .redteam_scratch/test_redteam_leakage.py
    -> 15 passed, 0 failed
PYTHONPATH=$PWD /usr/bin/python3 .redteam_scratch/probe_real.py
    -> 1 flagged run (2026-10-08T10Z..2026-10-12T16Z, 103 h, 17 over-limit hours)
    -> v5 and v4: 0 flagged runs crossing a fold boundary
    -> 4 issues flagged only with hindsight; 0 extra rows removed
    -> quality.json (main): 12 folds, 0 invariant violations
git show 44d5abd:web/public/data/quality.json -> 6 folds (2026-05..2026-10), 0 violations, stuck_feed_hours 103
```

The 2 scratch tests assert the leak behaviour, so passing confirms that the leak path exists.

## Inferred

- Fold scores, blend weights and the walk-forward fold fits are not contaminated by the whole-run flag on current data. They would be if a flagged run ever crossed a month boundary, for example after new data arrives.
- Reported out-of-sample margins over rules and persistence are probably slightly optimistic because of F2. The direction and size are unknown.
- v4 and v5 share F1, F3 and F4. F2 affects v5 more, because E10 to E16 happened after v4.

## Not verified

- No retraining and no loaded model. `ml.train` writes to `web/public/data` and `ml/models` and caches in the system temp folder. The local sklearn is 1.6.1; the repo pins 1.7.2.
- The exact run times and publication delay of Open-Meteo `previous_dayN`.
- The DFLD upstream publication delay.
- How `WIND_SCALE` was fitted.
- Behaviour on Python 3.13; I tested on 3.9.6.
- The effect of F2 on scores.
