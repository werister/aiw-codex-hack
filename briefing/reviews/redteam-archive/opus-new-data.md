> Archived worker report. Claims and paths below refer to the worker's stated snapshot and time. “Nothing committed” describes that worker's run; this report is now preserved by the coordinator. See [the consolidated timeline](../../experiments/REDTEAM_TIMELINE.md) for reconciled status and independently replayed checks.

# Round 2 review: data eligibility and leakage (Opus lane)

Assignment from `briefing/reviews/kai-data-round2.md` (commit `39f9b40`): new data eligibility, availability and leakage, and how they relate to the first-round exclusion finding. The NASA and literature review belongs to another lane and is not assessed here.

## Source state

| Item | SHA |
|---|---|
| My checkout HEAD (unchanged, first-round tested state) | `023e7405c88e0cbd452bc1d7a6369e686f7eff3c` |
| `origin/main` after `git fetch` | `46be227856e3753a7de7e2cf8bf926464619bd43` |
| Review snapshot (tested) | `5aed997313b78678d11fa23b808c2a9835a1d91a` |
| Review packet | `39f9b40c4a1158a11165f6e5f828925aca4a5c8c` |
| Availability fix | `5ecf04e3bf71996710f4ace5ed1a9f0628800c45` |

- All four commits are ancestors of `origin/main`.
- `5aed997` → `46be227` changes only `RESULTS.md` and `briefing/reviews/kai-data-round2.md`. No `ml/` or `data/` change.
- I tested `5aed997` from `git archive` output in `.redteam_scratch/snap5aed/` (on the SSD). My checkout was not switched.
- `docs/STATUS.md` does not exist at `5aed997` or at `origin/main`.
- First-round files are kept unchanged: `redteam-report.md`, `.redteam_scratch/test_redteam_leakage.py`, `.redteam_scratch/probe_real.py`.

### Changes from `023e740` (round 1) to `5aed997`

- Training inputs are byte-identical; the git blob SHAs are equal:
  - `data/eddf_metar.parquet` `08a27c4140`
  - `data/openmeteo_previous_runs.parquet` `fba656b887`
  - `data/openmeteo_previous_runs_multimodel.parquet` `6fa6439135`
  - `data/dwd_01420_wind_hourly.parquet` `97c3203070`
  - `data/ground_truth/dfld_hourly.csv` `1c473c6eeb`
- `ml/train.py` is unchanged. `suspect_od_runs` in `ml/quality.py:12-26` is unchanged.
- `ml/quality.py::r18_events` adds a `rule_corrected` baseline built from `rule_18_ens`.
- `ml/features.py:79-83` is the `5ecf04e` filter. `ml/tests/test_no_leakage.py` adds one test.
- All 13 `ml/models/*.joblib` files were refreshed.

## Findings

### R2-1. None of the new ml-support data is connected to training, features or the forecast.

- `git grep` at `5aed997` for `ml-support`, `ml-depth`, `eddf_metar_observations`, `open-meteo-icon-global` and `dwd_01420_hourly_wind_gust_overlap` finds no match in `ml/`.
- The only related hits are unrelated existing code: `ml/fetch.py:305` (DWD parquet writer) and `ml/live.py:202` (live `icon_global` request).
- So the path from source through loader to features does not exist for any new CSV. Current model scores cannot be affected by it.

### R2-2. New versus duplicate content, tested against the training parquets

| New file | Overlap with existing data (tested) | Truly additional | Causal use |
|---|---|---|---|
| `observations/eddf_metar_observations.csv`: 32,156 rows, 2024-12-29T00:20Z to 2026-10-29T23:50Z | **Complete duplicate of times and values.** All 32,156 timestamps are in `data/eddf_metar.parquet`; the parquet has 0 extra times in that window. Speed equals `sknt` 32,156/32,156; direction equals `drct` 27,791/27,791; gust equals 460/460. 76 direction NaN mismatches, which equals the 76 `CALM` rows. The parquet reaches back to 2018 (154,718 rows). | Parsed status fields: `wind_direction_status` (DIRECTIONAL 18,009, VARIABLE_RANGE 9,782, VARIABLE_VRB 4,289, CALM 76), `variable_direction_from/to_deg`, `wind_gust_status`, `report_type`, `raw_metar` | Yes. Each field is part of the report at `observation_time_utc`, so it could feed `build_features`. The gain is limited to new handling of variable directions, mainly the label policy for runway 18 (24 cases where a direction range makes the 15 kt limit unclear, per the depth README). |
| `forecast/normalized/open-meteo-icon-global.csv`: 16,008 hours, 2025-01-01 to 2026-10-29 | **Not a duplicate, but highly collinear.** Against `icon_seamless` in the multimodel parquet, the mean absolute speed difference is 0.89 kt for day1 (exactly equal 648/16,008) and 0.36 kt for day2 and day3 (equal 1,533 and 1,581). Against `best_match`, exactly equal 642 / 1,529 / 1,552 of 16,008. | ICON-Global gusts, pressure and temperature as a separate model column. Its grid point is 50.000/8.625. | Partly. It has the same `_previous_dayN` semantics and no `issued_at`/`retrieved_at` column, so it fits the existing 6 h proxy (see R2-4). Coverage: **8,784 of the 24,816 training hours (all of 2024) have no ICON-Global value.** Adding it changes the eligible rows or adds missing values that line up with time. Under decision gate 2, that must be a separate coverage experiment. |
| `observations/dwd_01420_hourly_wind_gust_overlap.csv`: 13,090 hours, 2025-04-28 to 2026-10-29 | **Timestamps duplicate the existing data.** All 13,090 times are in `data/dwd_01420_wind_hourly.parquet` (2023-01 to 2026-10, 32,956 rows). Mean wind `wind_mean_ms` equals parquet `F` at shift 0 for 13,079/13,079, against 909 at ±1 h. Same time convention. | `FX_911` hourly maximum gust. The existing parquet has only `F`, `D` and `QN_3`. | Not shown for live use. DWD CDC "recent" files are delayed and not final-QC'd, and an hourly maximum is only known after its hour ends. Usable as a historical comparison or label-check source, not as an issue-time feature without a dated availability rule. |

### R2-3. Label and forecast-run timing claims: replayed locally and they pass, with limited scope.

- **Label audit.** `resources/ml-depth/labels/audit_labels.py --truth-dir data/ground_truth` gives `passed: true`:
  - 154,752 half-hour rows rebuild to 76,588 hourly rows, matching exactly including order and source;
  - 788 excluded hours, with matching keys;
  - 1,681 direction changes;
  - both raw HTML samples (2025-01 and 2026-10) match exactly.
  - This confirms the conversion, not DFLD publication times.
- **Forecast-run timing.** `resources/ml-depth/temporal/probe.py --verify` (cached responses only, no network) gives 0 mismatches and 0 missing values for `icon_global` day1, day2 and day3 on 2026-10-28.
  - This supports run start ≤ `valid − 24N h`, i.e. a lead of 24–29 h for day1, for **`icon_global` on one day only**.
  - Single Runs are archived only from 2026-04-02, so 2025 is unchecked.
  - Not checked for `best_match`, `ecmwf_ifs025`, `gfs_seamless` or `icon_seamless`, which are the actual feature sources.
  - This partly closes my round-1 not-verified item on `previous_dayN` semantics. It does not close it for the models the estimator uses.
- **Out of date by chronology.** `resources/ml-depth/temporal/audit.md` audited `33a7847`. It says the archived branch ignores `issued_at`/`retrieved_at`. Since `5ecf04e` that is no longer true.

### R2-4. The `5ecf04e` availability filter is correct but does nothing on current data, and it cannot express per-offset vintages.

`ml/features.py:79-83` drops archived rows whose `issued_at` or `retrieved_at` is after the issue time. Scratch test file: `.redteam_scratch/test_round2_availability.py`.

- **Does nothing today.** None of the archived training parquets or the new ICON CSV has either column (checked by column listing). Fold features and scores cannot change through this filter. The refreshed joblibs come from `6de474f`, not from this filter. Not verified by retraining.
- **One stamp cannot describe three vintages.** A row holds day1, day2 and day3 values from three different runs.
  - Counterexample: a row stamped with the oldest (day3) run time passes the filter.
  - Expected: day1 values are blocked until the day1 run is available.
  - Actual: `wind_kt` = day1 value for leads 1–18, and `nwp_available_proxy.max()` still equals the issue time.
  - The filter therefore never tightens the 6 h proxy; it only removes whole rows.
- **Download time as `retrieved_at` blocks all history.** Attaching the package download time (2026-10-30) as `retrieved_at` makes historical issues raise `Incomplete 48-hour archived wind coverage`. That is the correct fail-closed behaviour. It means new archives must not carry download time as an availability stamp, and an archive cannot be made causal by removing that stamp.
- **Missing stamp.** A row with `issued_at` = NaT is dropped, so coverage fails. Correct.

### R2-5. Remaining availability risk at the 18 h boundary for non-ICON models (inferred).

- Under the confirmed mapping, the day1 run starts at `valid − 24 h − (valid_hour mod 6)`.
- For valid hours at 00, 06, 12 and 18 UTC at lead 18, the run starts exactly 6 h before issue. The proxy assumes it is published within 6 h.
- If ECMWF IFS or GFS via Open-Meteo take more than 6 h, those rows used values that were not yet published at issue time.
- The audit cites 4–6 h as typical for global models. No per-run record exists.
- **Question for the owner (Kai or Jayden):** what publication delay applies to `ecmwf_ifs025` and `gfs_seamless` previous runs? If it is over 6 h, day1 must stop at lead 17 (or 12) for those columns, and the 6/24/48 h scores of E10 and E12 need a rerun.

### R2-6. Reconciling with the round-1 whole-history exclusion finding

- **Two different mechanisms; do not conflate them.**
  - Round-1 F1 concerns **label and row selection**: `suspect_od_runs` uses the whole recorded run, including hours after the issue time, to drop targets and issue states (`ml/train.py:59`, `92-93`, `122-126`, `196`; `ml/forecast.py:372-389`).
  - `5ecf04e` concerns **input availability**: which forecast values a feature may read.
  - `5ecf04e` does not touch `quality.py` or `train.py`, so F1 is neither fixed nor made worse.
- **F1 at `5aed997`.** The code and data are identical to round 1, and the 12 fold boundaries are unchanged. So the round-1 result holds:
  - one flagged run, 2026-10-08T10Z to 2026-10-12T16Z, 103 h;
  - 0 crossings of a fold boundary;
  - 4 issues flagged only with hindsight, removing 0 extra scored rows.
  - Vulnerable, not affected.
  - Not re-run against the refreshed joblibs, because labels, data and fold boundaries are unchanged.
- **New relevance.** F21 proposes live forecasts from 30 October onward as the untouched evaluation.
  - Any stuck-feed exclusion there must use only METAR known at issue time, or must be fixed before any labels are observed.
  - Otherwise the whole-run flag would decide after the fact which live rows count.

## Smallest actionable next step

Before any coverage experiment with ICON-Global or DWD gusts:
1. Write down per-source availability: lag per model for `_previous_dayN`, and the DWD CDC release delay.
2. Freeze a causal stuck-feed rule for the live evaluation. Count over-limit METAR hours with time ≤ issue only. It is a one-line change in a copy of `suspect_od_runs`; this review made no production edit.

## Ran and saw

```
git rev-parse HEAD                     -> 023e7405c88e0cbd452bc1d7a6369e686f7eff3c (unchanged)
git fetch origin                       -> origin/main 46be227856e3753a7de7e2cf8bf926464619bd43
git merge-base --is-ancestor <39f9b40|5aed997|5ecf04e> origin/main -> all ancestors
git diff --stat 5aed997 origin/main    -> RESULTS.md, briefing/reviews/kai-data-round2.md only
git rev-parse 023e740:<data file> vs 5aed997:<data file> -> identical for all 5 training inputs
git diff 023e740 5aed997 -- ml/quality.py ml/train.py ml/features.py -> select_nwp filter + r18_events rule_corrected only
git archive 5aed997 resources/ml-support resources/ml-depth ml briefing/experiments briefing/forecast-trace-questions.md data | tar -x -C .redteam_scratch/snap5aed
git grep (5aed997) for new package paths in ml/ -> no loader references
export TMPDIR=/Volumes/AthenaSSD/fra-redteam-a/.redteam_scratch/tmp PYTHONDONTWRITEBYTECODE=1   # /usr/bin/python3 3.9.6, pandas 2.3.3, sklearn 1.6.1; no installs
/usr/bin/python3 .redteam_scratch/round2_overlap.py -> METAR 32,156/32,156 duplicate; ICON-Global vs icon_seamless/best_match numbers above; DWD 13,090/13,090 times in parquet
/usr/bin/python3 (inline) DWD shift test -> F equal 13,079/13,079 at shift 0; 909 at -1 h and +1 h
/usr/bin/python3 resources/ml-depth/labels/audit_labels.py --truth-dir data/ground_truth -> passed: true (76,588 / 788 / 1,681; 2 HTML samples exact)
/usr/bin/python3 resources/ml-depth/temporal/probe.py --verify -> 0 mismatches, 0 missing, day1/2/3 icon_global
cd .redteam_scratch/snap5aed; python3 -m pytest -q -p no:cacheprovider --rootdir=. <file>:
  ml/tests/test_no_leakage.py            10 passed, 0 failed
  ml/tests/test_rules.py                  4 passed, 0 failed
  test_redteam_leakage.py (round 1)       2 passed, 0 failed
  test_round2_availability.py (round 2)   3 passed, 0 failed
  combined run                           19 passed, 0 failed
```

The round-1 and round-2 scratch tests assert the vulnerable or limiting behaviour, so passing confirms the mechanism exists. The supplied verifiers ran on scratch copies; any report files they rewrite stay inside `.redteam_scratch/snap5aed`. Network was not used.

## Inferred

- The METAR CSV adds no new observations and no new coverage, only parsed fields. Merging it would not change current features unless the label or feature policy for variable directions changes.
- ICON-Global would mostly add a near-collinear model column. Any gain must be judged in a coverage-matched experiment (2025+ rows only, for both arms), because 2024 has none.
- DWD gusts are not usable as a live feature until their release time is defined.
- R2-5 is a plausible boundary leak for 6-hourly global models at lead 18. Its size is unknown and its occurrence is not shown.
- F1 is still only a vulnerability for walk-forward scores. It becomes material for the proposed live evaluation if it is applied as is.

## Not verified

- Publication delay for `best_match`, `ecmwf_ifs025`, `gfs_seamless` and `icon_seamless` previous runs; the `icon_global` mapping before 2026-04-02 or on other days.
- DWD CDC release time for hourly `FX_911`.
- Whether the refreshed joblibs at `5aed997` reproduce identical fold scores. I did not retrain or load models; the local sklearn is 1.6.1, the repo pins 1.7.2.
- `verify_package.py`, `qa/compare_weather_sources.py` and manifest byte integrity: the integrity lane's job, not run here.
- NASA paper, literature notes and their transfer to FRA: another reviewer's lane, not read.
- `briefing/experiments/v4-colab-october.*` and the F17–F23 answers were extracted but not re-checked; I used only the packet's summary of them.
- Behaviour on Python 3.13; I tested on 3.9.6.
