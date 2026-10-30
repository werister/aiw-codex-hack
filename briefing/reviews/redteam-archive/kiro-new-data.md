> Archived worker report. Claims and paths below refer to the worker's stated snapshot and time. “Nothing committed” describes that worker's run; this report is now preserved by the coordinator. See [the consolidated timeline](../../experiments/REDTEAM_TIMELINE.md) for reconciled status and independently replayed checks.

# Round-2 review — Kiro: package integrity and executable integration

Assignment (from `briefing/reviews/kai-data-round2.md`, commit `39f9b40`): run the
supplied verification/QA scripts where safe, verify manifests and row counts, compare
new CSV schemas with the current parquet loaders, and run focused tests of the new
availability filtering (`5ecf04e`). Distinguish byte integrity from training eligibility.
No merges, no production edits, no training, no downloads, no credential reads.

## Provenance and HEADs

- First-round artifacts preserved: `redteam-report.md` (8617 B) and `.scratch/test_trace_contract.py` untouched.
- `git fetch origin` run. **My working-tree HEAD is unchanged at `a601b77e43e3d78e3209d201077c7469d8b6271a`** (round-1 tested checkout, deliberately preserved).
- `origin/main` is now `46be227856e3753a7de7e2cf8bf926464619bd43` (`docs: economic value at FRA scale…`), **65+ commits** ahead of the review baseline `403f6dc`.
- `a601b77` is a linear ancestor of `origin/main`; **no divergence**.
- Referenced commits resolved:
  - review packet `39f9b40` (`docs: prepare new-data and literature review packet`)
  - source snapshot `5aed997` (`docs: add verified trace contract check results`) — an ancestor of `39f9b40`/`46be227`
  - availability fix `5ecf04e` (`fix: archived inputs honour explicit availability metadata`) — **present at `origin/main`, absent from my `a601b77`**
- **No `docs/STATUS.md`** exists at `origin/main` (only unrelated `weather database/europe/ARCHIVE_STATUS.md`). `AGENTS.md` unchanged between `a601b77` and `origin/main`.
- Env: reused the round-1 SSD venv (`.scratch/venv`, CPython 3.13.5, scikit-learn 1.7.2). The two QA scripts are stdlib-only (no pandas). All reads/writes/caches on AthenaSSD. No installs this round. Internal disk untouched by me.
- Non-destructive method: extracted trees with `git archive <sha> | tar -x` into `.scratch/round2/` — the versioned working tree stayed at `a601b77`. The QA script that writes `qa/source-comparison.json` was run inside the scratch copy only, so no versioned QA output was modified.

## Ran and saw — commands, SHAs, counts

### 1. Package byte integrity (`verify_package.py`) — source `39f9b40`
```
# extracted: git archive 39f9b40 resources/ml-support | tar -x -C .scratch/round2/pkg
cd .scratch/round2/pkg/resources/ml-support && python verify_package.py
-> {"files_checked": 133, "integrity_pass": true, "problems": []}   exit 0
```
All 133 manifest files match bytes + sha256; every `.json` parses; every `csv_rows` count matches. Manifest `created_at_utc=2026-10-30T11:15:54Z`. **Integrity: PASS.**

Claimed headline counts, verified from the manifest `csv_rows` the script enforces:
- `observations/eddf_metar_observations.csv`: **32,156 rows** (6,402,745 B) ✓
- `forecast/normalized/open-meteo-icon-global.csv`: **16,008 rows** (2,045,531 B) ✓
- `observations/dwd_01420_hourly_wind_gust_overlap.csv`: **13,090 rows** ✓
- 46 IEM raw monthly CSVs (type3 routine + type4 special) row counts all matched.

### 2. Source comparison QA (`compare_weather_sources.py`) — source `39f9b40`
```
cd .scratch/round2/pkg/.../qa && python compare_weather_sources.py   -> exit 0
diff committed qa/source-comparison.json  vs  my fresh run  -> IDENTICAL (byte-for-byte)
```
- `forecast_hours=16008`, `paired_hours=16008`, `excluded={}` (ICON archive fully overlaps the METAR series within the ≤60-min pairing rule).
- `inputs_sha256`: ICON `63ff96be…` (matches manifest); METAR `55b0b03c…`.
- ICON−METAR 10 m speed bias ≈ **−3.32 kn** (day1), MAE 3.44, RMSE 4.22; day2/day3 similar (−3.32/−3.34). Wind-vector mean distance 4.53/4.67/4.85 kn over 13,854 pairs.
- **This is a source-data diagnostic, not eligibility**: the script itself states the pairs are "never issue-time predictor features." The ~−3.3 kn underread is consistent with the production `WIND_SCALE` bias correction (best_match 1.684×) and does **not** by itself qualify ICON as a model input.

### 3. Focused availability-filtering tests (`5ecf04e`) — source `46be227` (origin/main)
```
# extracted origin/main via git archive into .scratch/round2/main
PYTHONPATH=.scratch/round2/main python -m pytest ml/tests/test_no_leakage.py::test_archived_rows_with_late_metadata_are_rejected -q
-> 1 passed

PYTHONPATH=.scratch/round2/main python -m pytest ml/tests/test_no_leakage.py ml/tests/test_forecast_cli.py -q
-> 30 passed, 12 warnings        (29 at a601b77 + 1 new test from 5ecf04e)
```

### 4. Negative control — does `5ecf04e` actually close a gap? (`.scratch/round2/neg_control_5ecf04e.py`)
Pre-fix `select_nwp` (`5ecf04e~1`) vs post-fix (`origin/main`), same scenario = archived day1/2/3 coverage + `issued_at` **two hours after** issue:
```
pre_clean_rows: 48   post_clean_rows: 48                      (both accept clean coverage)
pre_late:  USED 48 rows (NO rejection) -> pre-fix would leak
post_late: ValueError: Incomplete 48-hour archived wind coverage -> post-fix rejects
VERDICT: PASS (fix changes behaviour, closes the gap)        exit 0
```
Before the fix, archived rows carrying a **post-issue** publication stamp were silently used; after it, they are dropped and coverage fails. The guard is real, not cosmetic.

**Scope of this guarantee (corrected after Opus's review — the earlier wording was too broad).**
The negative control proves only that archived rows **carrying an explicit `issued_at`/`retrieved_at` after the issue** are now rejected. It does **not** prove the archives are leakage-free in general. Opus verified the current archives contain **no actual issue/publication metadata**: the production path relies on `nwp_offset_days` + a **6-hour `PUBLICATION_LAG_H` proxy** and the per-offset day1/day2/day3 "vintages", both of which remain **unverified assumptions**, not confirmed publication times. So the correct, narrow claim is: *`5ecf04e` closes the explicit-late-metadata leak, and my round-1 trace checks confirm the explicit-input cutoffs hold; the no-future-input property beyond that rests on the offset/lag proxy and has not been independently verified.*

### 5. CSV-to-parquet schema compatibility (bounded integration probe)
Production loaders: `ml.live.normalize_metar` (renames `valid,drct,sknt,gust`) and `ml.features.select_nwp` (expects unsuffixed `wind_{speed,direction,gusts}_10m_previous_dayN`, `time`).

| New CSV | Columns | Matches a production loader as-is? |
|---|---|---|
| `eddf_metar_observations.csv` | `observation_time_utc, wind_direction_deg, wind_speed_kt, wind_gust_kt, …status…, raw_*` (21) | **No** — loader wants `valid/drct/sknt/gust`. Richer status fields; not drop-in. |
| `open-meteo-icon-global.csv` | `time_utc, …, wind_speed_10m_previous_dayN_kn, …_deg, …_hpa, …_c` (21) | **No** — unit-suffixed names + `time_utc`; no 80 m, no pressure boxes, no multimodel. |
| `dwd_01420_hourly_wind_gust_overlap.csv` | `timestamp_utc, wind_mean_kt, wind_gust_hourly_max_kt, …qn…` (10) | **No** — separate station product; not wired to any loader. |

Executed adapter probe on ICON (source `46be227` loader):
```
RAW ICON csv -> select_nwp raises ValueError "Non-offset forecasts need issued_at or retrieved_at"  (NOT loadable)
RENAMED (3 wind fields x 3 days; units already kn/deg) -> select_nwp OK, 48 rows, wind_kt 1.0–6.5
  pressure_msl populated: False   wind_speed_80m all-NaN: True
```
So even after a rename adapter, ICON feeds only a **reduced** v5 vector (no 80 m, synoptic, or multimodel columns) — not parity with `data/openmeteo_previous_runs.parquet` (29 cols incl. 80 m + pressure offsets).

## Inferred

- Integrity vs eligibility are cleanly separable here. **Byte integrity: fully verified** (133/133 files, reproducible QA output). **Training eligibility: not established by this package** — the CSVs are a comparison/diagnostic export, not loader-compatible inputs, and the deeper handoff explicitly preserves the existing best_match training cache. This matches the packet's own framing and the NASA-paper caveat (US next-15-min config task ≠ FRA 48 h labels/transfer).
- The ~−3.3 kn ICON underread is a *source property*, already compensated in-model; it is not evidence to switch sources.
- `5ecf04e` closes the specific archived-input leak where an **explicit** post-issue `issued_at`/`retrieved_at` would have been used. It does **not** establish general leakage-freedom: the current archives carry **no actual publication metadata** (Opus-verified), so ordering rests on the `nwp_offset_days` + 6 h `PUBLICATION_LAG_H` proxy and the per-offset vintages — unverified assumptions. My round-1 trace checks confirm the **explicit** issue-time input cutoffs; they do not validate the offset/lag proxy.

## Not verified

- I did **not** run a full/live/hindcast CLI forecast, any model fit, or any of the 12/13 joblib artifacts this round (no training per instructions). Model-eligibility of the ICON data was probed only at the `select_nwp` adapter boundary, not end-to-end through `predict_48h`.
- DWD and the `kaggle/`, `reference/`, `ground-truth/` package subtrees were integrity-checked by `verify_package.py` but not individually schema-mapped to loaders.
- I did not independently re-derive the 32,156 / 16,008 counts from the raw monthly files beyond the manifest `csv_rows` the script enforces (counts cross-checked against the README prose, not re-parsed from `raw/`).
- Claims about any snapshot later than `origin/main=46be227`; other reviewers' branches/worktrees.

## Smallest actionable next step

If ICON is ever to be a *candidate input* (not just a diagnostic), add an explicit normalized-CSV adapter that (a) renames the `_kn/_deg/_hpa/_c` offset columns to the production names incl. `pressure_msl_previous_dayN`, and (b) declares the missing 80 m / synoptic / multimodel columns as absent so `select_nwp` leaves them NaN — then gate it behind the same `issued_at <= issue` filter `5ecf04e` added. Until then, keep ICON as a comparison source only; do not join it into the estimator.
