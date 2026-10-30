# Red-team test evidence

Read [the experiment timeline](../REDTEAM_TIMELINE.md) for model scores and decisions. These files preserve executable checks from the independent review lanes; they do not represent additional trained models.

| File | What it checks | Recorded execution |
|---|---|---|
| `check_evidence.py` | Recompute v4 accuracy/Brier and validate masks, blend arithmetic, split and provenance from exported traces | 29 checks passed; 72/72 metric rows matched; coordinator replayed |
| `test_redteam_leakage.py` | Construct future-METAR effects on earlier whole-run exclusion flags | 2 counterexample tests passed, within a 15-test focused run |
| `test_trace_contract.py` | v5 model hash, feature order, required wind, future METAR and evidence IDs on synthetic inputs with real fitted artifacts | 7 scratch checks, within a 27-test CLI/contract run at `a601b77` |
| `test_icon_supplement.py` | Units, offset boundaries, missingness, explicit availability and determinism | 13 passed |
| `test_icon_protocol.py` and `icon_protocol.py` | Supplemental experiment safeguard helpers | 14 passed; together with adapter tests, coordinator replay: 27 passed in 2.90 s |

Important interpretation:
- The leakage tests **assert the problematic behavior**. Passing demonstrates the counterexample, not a fixed causal preprocessing pipeline.
- The protocol cache test uses a simplified signature demonstration; source inspection found the real omitted supplemental input. It is not a full end-to-end cache integration test.
- The direct model feature-permutation negative control deliberately strips column names. Production prediction uses ordered named DataFrames, and a misordered named DataFrame is rejected. This does not establish an existing production permutation bug.
- Contract tests are not a live UI/CLI process replay or proof that every identity/availability field is complete.
- The experiment uses safeguard assertions inline; it does not import the separate protocol helper. Tests of the helper alone cannot prove the whole experiment script runs.
- Tests are not model-performance experiments. Several reported suite totals include existing tests and must not be added into a unique-test count.

## Reproduce in Colab

Use a checked-out/extracted source tree with `ml/`, data and v5 model artifacts, plus this evidence directory and `../v5-icon/icon_supplement.py`. Install the pinned source requirements in Colab. From the repository root:

```sh
PYTHONPATH=.:briefing/experiments/v5-icon:briefing/experiments/redteam python -m pytest briefing/experiments/redteam/test_icon_supplement.py briefing/experiments/redteam/test_icon_protocol.py -q
PYTHONPATH=. python -m pytest briefing/experiments/redteam/test_redteam_leakage.py -q
PYTHONPATH=. python -m pytest briefing/experiments/redteam/test_trace_contract.py ml/tests/test_forecast_cli.py -q
python briefing/experiments/redteam/check_evidence.py /content/fra-red-team-results
```

The evidence audit requires the completed v4 `metrics.csv`, `per_row_traces.parquet` and `manifest.json`; it never loads `models.joblib`. ICON tests require `resources/ml-support/forecast/normalized/open-meteo-icon-global.csv`; verify the real-data test is not skipped. For original-run reproduction, use the source snapshots identified in the reviews rather than assuming today's main is identical.

**Packaging status:** test bodies are preserved; repository-relative data/model paths replace scratch-machine paths, and the evidence audit accepts a directory argument. The recorded passes were obtained **before this path-only packaging change**. The relocated files have not yet been rerun in Colab. Further model runs are Colab-only at the owner's request.

## Archived reviews and reconciled findings

- [Opus: leakage and selection](../../reviews/redteam-archive/opus-round1.md)
- [Opus: new-data eligibility](../../reviews/redteam-archive/opus-new-data.md)
- [Opus: ICON blocker and eight safeguards](../../reviews/redteam-archive/opus-icon-protocol.md)
- [Kiro: v5 contract review](../../reviews/redteam-archive/kiro-contract-review.md)
- [Kiro: package/integration review](../../reviews/redteam-archive/kiro-new-data.md)
- [Kiro: delay-data eligibility](../../reviews/redteam-archive/kiro-delay-eligibility.md)

Original worker reports retain their historical wording and local paths. The consolidated timeline is the reconciled account: explicit availability rejection is conditional on metadata being supplied; archived weather publication times remain unverified. The BTS file cannot validate FRA/hourly/flight-level claims; this does not rule out a separately designed monthly US forecasting study with additional temporal/availability controls.
