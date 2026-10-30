> Archived worker report. Claims and paths below refer to the worker's stated snapshot and time. “Nothing committed” describes that worker's run; this report is now preserved by the coordinator. See [the consolidated timeline](../../experiments/REDTEAM_TIMELINE.md) for reconciled status and independently replayed checks.

# Round 3: review of the ICON-Global supplemental ablation protocol

The protocol under review comes from the user message: a standalone Colab v5 notebook pinned to `5aed997`. Its two arms are the base features versus base + ICON-Global wind, gust and tailwind features. Both arms keep the `best_match` sources and use identical 2025+ training and scoring rows. Training uses labels before 1 October; October is the exploratory test month. Learner and chronological blending are the same in both arms. Nothing is promoted.

- Muse's notebook was not available. `origin/main` = `26f531a` has no ablation file. This reviews the stated protocol against `5aed997` code.
- Checkout HEAD is unchanged at `023e740`. Tests ran in `.redteam_scratch/snap5aed` (a `git archive` extract of `5aed997`).
- `round2-review.md` and `redteam-report.md` are kept unchanged.

## Blocker (one)

**The feature cache key ignores ICON inputs, so both arms can silently get identical features.**

- **Where.** `ml/train.py:104-119` (`cached_dataset`) builds its key from stride plus the size and mtime of 5 fixed data files, `train.py` and `features.py`. The ICON CSV is not part of the key.
- **Failure.** If the notebook adds ICON by patching `train.archived_inputs` or `features.MULTIMODELS` and then calls `cached_dataset`, the second arm loads the first arm's cache.
- **Test.** `test_feature_cache_key_ignores_icon_inputs` passes, which confirms the collision. It printed "Using cached issue-time features"; `dataset` was called once for two arms, and both arms returned `("base-arm",)`.
- **Fix, either of:**
  - call `train.dataset(stride)` directly for each arm and cache per arm under a key that includes the SHA-256 of the ICON CSV and the arm name; or
  - include those in the key.
- **Accept when** the arms differ in their feature column list and `frame[icon_cols].notna().mean() > 0.99` on matched rows.

## Required safeguards

1. **Per-offset join on valid time.**
   - Rename each CSV column `*_previous_dayN_kn/_deg` to `icon_global__<var>_previous_dayN`.
   - Merge on target/valid `time` (UTC, tz-aware) with `validate="one_to_one"`.
   - Then select through the same `nwp_offset_days` as `best_match`: day1 for leads 1–18, day2 for 19–42, day3 for 43–48 (`ml/features.py:58-60`, `pick` at `:90-94`).
   - Never join on issue time, and never apply day1 to all leads.
   - Test: offsets are [18, 24, 6] and values are finite for the issue 2025-06-01T22Z.
2. **Alignment check before training.**
   - ICON day1 speed against METAR at the same valid hour: correlation r = 0.786 at shift 0, against 0.362 at −24 h and 0.385 at +24 h.
   - Keep this assert in the notebook.
   - A merge on string times against tz-aware parquet times gives all-NaN ICON columns silently (test `test_tz_naive_or_string_join_silently_gives_all_nan`). `nanmean` in `add_ensemble` would hide it.
3. **Keep ICON out of `MULTIMODELS` for a supplemental arm.**
   - Patching `features.MULTIMODELS` raises `KeyError` on `WIND_SCALE['icon_global']`.
   - Once a scale exists, it **changes the base features** `ens_tailwind_25_mean`, `ens_*`, `rule_od25_ens` and `rule_18_ens`.
   - Meanwhile `FEATURES`, built at import, does not list `icon_global_tailwind_*`. Both are shown in a test.
   - Add the ICON columns as an explicit extra feature list. Assert that the base columns in the base+ICON arm are byte-equal to the base arm on matched rows.
4. **Scaling or bias correction fitted only on training data.**
   - Do not reuse the package's −3.32 kt mean bias (`resources/ml-support/qa/findings.md:9-11`). It was computed over all 16,008 hours, including October.
   - Fit any ratio or offset on rows with target `time` before `2026-10-01` (and before `validation_start` if it feeds blend selection), or leave ICON unscaled.
   - The `WIND_SCALE` "2024-only" convention is impossible here, because ICON starts 2025-01-01.
5. **Identical rows in both arms.**
   - Common rows: `issue_time >= 2025-01-01T00Z`, all 48 ICON wind, direction and gust values present, and all base requirements met.
   - Apply one row mask to both arms before `fit`, blend validation and scoring.
   - ICON wind has 0 missing values over 16,008 contiguous hours (2025-01-01T00Z to 2026-10-29T23Z). The 77 missing temperature and pressure values are irrelevant if only wind and gust are used.
   - Report n for each lead and arm; it must be equal.
6. **Training exclusions and blending.**
   - Use the same `without_stuck_feed` on training rows in both arms.
   - The only flagged run (2026-10-08T10Z to 10-12T16Z) is in the October test month, so training is unaffected. The 60-day blend validation (`train.py:143-145`) falls inside the training months for both arms.
   - Report October both with all recorded hours and with the stuck feed excluded.
   - The excluded score uses the whole-run flag (round-1 F1). The 4 issues flagged only with hindsight add 0 rows, so the exclusion is equal for both arms. Label it as hindsight-cleaned.
7. **Lag sensitivity, feasible now.**
   - Patching `features.PUBLICATION_LAG_H` to 9 or 12 gives offsets [15, 24, 9] or [12, 24, 12]. ICON keeps full day3 coverage and the availability proxy stays ≤ issue time (tested).
   - Run base and base+ICON at lag 6 and at lag 12.
   - Lag applies to `best_match` too, so compare arms only within the same lag.
   - Label all runs as proxy-lag exploratory; this does not prove historical publication times.
8. **Reporting.**
   - Report Brier at 6, 24 and 48 h (primary), accuracy, and 1 h non-degradation, on matched rows.
   - Include rules and persistence on the same rows.
   - Use one October only, with no fold or feature selection on October.
   - Freeze source SHA `5aed997`, data hashes, feature order and the environment (pinned sklearn 1.7.2).

## Ran and saw

```
git fetch origin -> origin/main 26f531aea162a69bf0a6162bdb6e7b136361fd4c (no ablation notebook in tree)
git rev-parse HEAD -> 023e7405c88e0cbd452bc1d7a6369e686f7eff3c (unchanged)
cd .redteam_scratch/snap5aed   # git archive of 5aed997
TMPDIR=/Volumes/AthenaSSD/fra-redteam-a/.redteam_scratch/tmp PYTHONDONTWRITEBYTECODE=1 \
  /usr/bin/python3 -m pytest -q -p no:cacheprovider --rootdir=. -s test_round3_icon_protocol.py
  -> 9 passed, 0 failed; printed corr by shift {-24: 0.3615, 0: 0.7862, 24: 0.3846}; "Using cached issue-time features"
/usr/bin/python3 -m pytest -q -p no:cacheprovider --rootdir=. ml/tests/test_no_leakage.py ml/tests/test_rules.py \
  test_redteam_leakage.py test_round2_availability.py test_round3_icon_protocol.py
  -> 28 passed, 0 failed (10 + 4 existing, 2 round 1, 3 round 2, 9 round 3)
```

Python 3.9.6, pandas 2.3.3, sklearn 1.6.1 (`/usr/bin/python3`), no installs, everything on the SSD. Scratch source: `.redteam_scratch/test_round3_icon_protocol.py`. Several tests assert a failure mode (cache collision, all-NaN join, ensemble rewrite, `KeyError`), so passing confirms the hazard exists.

## Inferred

- If any one of the blocker, safeguard 1 or safeguard 3 is missed, the comparison is either a null result by construction or not supplemental.
- The ICON day1 mapping (run start ≤ valid − 24 h − (hour mod 6)) is verified for `icon_global` only. That makes ICON the cleanest of the model columns under the 6 h proxy.

## Not verified

- Muse's actual notebook code, outputs and environment.
- Any model fit or score. No training was run.
- Colab temp-folder behaviour; it is assumed to be session-local, which does not prevent the collision within one session.
- ICON-Global publication times for 2025.
