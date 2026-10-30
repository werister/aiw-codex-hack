> Archived worker report. Claims and paths below refer to the worker's stated snapshot and time. “Nothing committed” describes that worker's run; this report is now preserved by the coordinator. See [the consolidated timeline](../../experiments/REDTEAM_TIMELINE.md) for reconciled status and independently replayed checks.

# Red-team report — v5 trace / evidence / replay contract

Independent stress-test of the Frankfurt runway forecast's trace-proof and replay
contract. Scope: trace/evidence contract only (model hashes, source-snapshot
identity, feature-order binding, CLI/predict parity, missing/mismatched-input
handling). No model training. No production files modified. No merges, no PRs.

## Environment & provenance

- **Checkout:** dedicated worktree `/Volumes/AthenaSSD/fra-redteam-c` on branch `hugo/redteam-c` (on SSD).
- **Fetched** `origin`; rebased my branch onto `origin/main`.
- **HEAD recorded before testing:** `a601b77e43e3d78e3209d201077c7469d8b6271a`
  (`a601b77 style: one name for persistence`). All tests ran at this HEAD.
- **Version distinction (as requested):**
  - Pinned **v4** `44d5abd3363248b1de0a3ed96ff32982aafdd7b3` (`feat: approach page…`, 2026-10-30 13:41).
    v4 metadata: `version=walk-forward-v4`, **25 features** (base only), `n=194352`, `trained_through=2026-10-29T18:00Z`.
  - **Current main** `a601b77`. metadata: `version=walk-forward-v5`, **45 features**
    (base + ensemble + synoptic), same `n` and `trained_through`.
  - `git merge-base --is-ancestor` confirms **v4 is a linear ancestor of current main** (not divergent).
    Between them, `ml/` gained `synoptic.py` (+101), `significance.py` (+90), ensemble/hash
    logic in `predict.py` (+42), `evidence()`/`run_id` in `forecast.py` (+71), and **all 13 model
    joblibs were retrained** (~152 KB → ~214 KB; v5).
- **Python env:** shared `/Users/hugohader/.venv` lacks pandas/pyarrow/sklearn; no existing
  suitable env found. Built an isolated **CPython 3.13.5** venv at `.scratch/venv` **on the SSD**,
  caches (`UV_CACHE_DIR`, `TMPDIR`) on the SSD. Installed pinned deps incl.
  **scikit-learn==1.7.2** (required to unpickle the models) and joblib==1.5.2. Resolved
  pandas 3.1.0 / numpy 2.5.4 (satisfy the repo's `>=` pins). `openai` deliberately not
  installed (only the optional tower briefing needs it; out of trace scope).
  **No internal-disk installs** — entire 651 MB footprint lives under `.scratch/` on the SSD.

## Ran and saw — exact commands and pass counts

1. Existing focused leakage + CLI contract tests:
   ```
   .scratch/venv/bin/python -m pytest ml/tests/test_no_leakage.py ml/tests/test_forecast_cli.py -p no:cacheprovider -q
   -> 29 passed, 12 warnings in 6.23s
   ```
2. Full `ml/` suite (excluding `test_briefing.py`, which imports `openai`, out of scope):
   ```
   .scratch/venv/bin/python -m pytest ml/tests/ --ignore=ml/tests/test_briefing.py -p no:cacheprovider -q
   -> 43 passed, 12 warnings in 2.03s
   ```
   `test_briefing.py` is **not run** (ModuleNotFoundError: openai) — a scope decision, not a failure.
3. My scratch trace-contract suite (`.scratch/test_trace_contract.py`, 7 tests), driving the
   **real trained walk-forward-v5 artifact** through `ml.predict.predict_48h` and
   `ml.forecast.evidence()`:
   ```
   PYTHONPATH=. .scratch/venv/bin/python -m pytest .scratch/test_trace_contract.py -p no:cacheprovider -q -s
   -> 7 passed, 607 warnings in 6.29s
   [feature-order] numpy-permuted max|delta|=0.702686 (silent); df-permuted -> ValueError (guarded)
   ```

Total: **29 + 43 + 7 passed; 0 failed; 0 unexpected errors.** (The 43 subsumes the 29.)

## What each scratch test proves — and the important distinction

The shipped `ml/tests` exercise the CLI via `fallback_predict`; they **never load the trained
v5 model**, so the real hash/evidence/feature path was previously untested. My scratch tests
close that gap. Two categories, kept distinct as requested:

**A. Production inference-path checks** (go through `predict_48h` / `forecast.evidence`, the code
that actually runs in a forecast):

- `test_model_hash_and_version_binding` — `frame.attrs["model_sha256"]` equals the real sha256
  of the on-disk selected joblib; version is `walk-forward-v5`; `trained_through < issue`
  (hindcast fit-selection honored). **Pass.**
- `test_feature_order_matches_trained_metadata` — `metadata.json["features"]`, the pickled
  `bundle["features"]`, and code `FEATURES` are identical **and in the same order**. This is the
  source-snapshot identity / feature-order binding. **Pass.**
- `test_run_id_is_deterministic_and_input_sensitive` — the documented run_id payload
  (`[issue, model_sha256, issue_inputs, per_hour_inputs]`, `sort_keys`) is reproducible, and
  flips when `od_at_issue` changes or when the model hash changes. **Pass.**
- `test_cli_evidence_run_id_real_pipeline_parity` — calls the real `forecast.evidence()` over
  real `predict_48h` output twice: identical `run_id`; artifact version `walk-forward-v5`;
  recorded sha256 matches `file_sha256` of the named file; every per-hour `inputs` block carries
  the evidence keys; changing `od_at_issue` end-to-end changes the `run_id`. **Pass.**
- `test_missing_required_wind_is_caught_negative_control` — dropping day-2 wind coverage makes
  `predict_48h` raise `ValueError(... coverage ...)` rather than silently filling. **Pass.**
- `test_future_observation_excluded_negative_control` — appending a post-issue METAR with absurd
  wind does **not** change `p_od25` (issue-time cutoff holds in the real path). **Pass.**

**B. Direct `model.predict_proba` probe** (does NOT go through production inference — it calls the
estimator directly to characterize the feature-order contract; treat as a property of sklearn +
the fitted estimator, not a check of shipped code):

- `test_feature_order_is_load_bearing_negative_control` — with the fitted `od` estimator:
  - feeding a **named DataFrame in shuffled column order** → sklearn raises
    `ValueError: Feature names must be in the same order as they were in fit` (**guarded**);
  - feeding a **bare numpy array in shuffled order** (names stripped) → **silently** mispredicts,
    max |Δ P(OD25)| = **0.70**. **Pass** (asserts the silent-corruption magnitude).

## Inferred

- The feature-order binding is **doubly protected in practice**: metadata/pickle/code agree on
  order (test A), and `predict_48h` always passes `frame[FEATURES]` — a *named, correctly ordered*
  DataFrame — so sklearn's name+order check would catch an accidental reorder at runtime. The
  silent-corruption mode (probe B) only triggers if a caller ever passes a bare numpy array in the
  wrong order; **no current code path does that**, so this is a latent risk, not a live defect.
- `run_id` binds issue time, model sha256, issue inputs, and per-hour inputs. It does **not**
  include the rules_version or feature_set strings (those sit beside it in `evidence`, unhashed),
  so two runs that differ only in `rules_version` would share a `run_id`. Low severity for the
  demo; noting for honesty.

## Real gaps / current failures (honest)

- **No live failures.** 0 failed / 0 errored across all scoped runs at HEAD `a601b77`.
- **Gap (pre-existing, now partially covered):** the repo's own test-suite never loads the trained
  model, so before this report the v5 hash/evidence/run_id/feature-binding path had **no shipped
  test coverage**. My scratch tests cover it but live under `.scratch/` and are **not** added to
  `ml/tests` (per instruction not to extend the suite / not to modify production files).
- **Gap (minor):** `run_id` omits `rules_version`/`feature_set` from its hashed payload (see Inferred).
- **Residual risk (latent, not triggered):** positional (numpy, nameless) feature input would be
  silently mispredicted (Δ up to 0.70); guarded today only because the one caller uses a named
  DataFrame.
- **Note:** `test_briefing.py` was not executed (needs `openai`, outside trace scope) — not a pass,
  not a failure; simply out of scope.

## Not verified

- Behavior under the repo's exact pinned pandas/numpy (I resolved pandas 3.1.0 / numpy 2.5.4 vs the
  `>=` pins; sklearn matched exactly at 1.7.2, which is what governs unpickling). Many
  `Pandas4Warning`/NumPy 2.5 deprecation warnings surfaced but did not affect results.
- The optional OpenAI tower-briefing path (`tower_briefing`, `test_briefing.py`) — not installed,
  out of scope.
- End-to-end run against **real** `data/` parquet inputs via the CLI (`python -m ml.forecast`) — I
  drove `predict_48h`/`evidence` with controlled synthetic inputs to isolate the contract; I did
  not execute a full live/hindcast CLI run.
- Cross-fold hash uniqueness and that each `fold-*.joblib` is selected for the correct issue window
  beyond the single issue (`2026-10-30T00:00Z`) tested.
- Any claim about `origin/main` beyond `a601b77`; I did not inspect other branches/worktrees.
