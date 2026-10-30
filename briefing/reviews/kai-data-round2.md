# Review packet: Kai's new data and literature

Requested by Hugo on 30 October 2026. Review baseline: `403f6dce8fcf8db7bc8c93d078b0b1671a5336da`; new snapshot: `5aed997313b78678d11fa23b808c2a9835a1d91a` (65 commits ahead). Record any later snapshot separately. The aim is to identify usable additional inputs and one bounded next Colab experiment, with executed checks.

## Start with the completed work

- [Executed v4 October experiment and independently checked results](../experiments/v4-colab-october.md).
- [Executed Colab notebook](../experiments/v4-colab-october.ipynb).
- [Owner answers F17–F23](../forecast-trace-questions.md#f17--which-learning-approaches-have-not-been-tried-yet-kai--jayden--ml-implementer).
- [Existing experiments](../../EXPERIMENTS.md), [current results](../../RESULTS.md), [model card](../../MODEL_CARD.md).

The October v4 Extra Trees / equal-average comparison did not improve accuracy. Muse recomputed all 72 metric rows; coordinator replayed 29 checks. Opus's constructed exclusion-leak tests plus existing focused tests passed 15/15 (passing proves the vulnerable mechanism); no actual flagged run crossed a current fold boundary. Kiro's synthetic-input trace checks plus forecast CLI unit tests passed 27/27 in the coordinator replay. These findings have different source snapshots and must not be collapsed into a new-model benchmark.

F21 now names Brier at 6/24/48 hours as primary, with accuracy, change/timing metrics, and 1-hour non-degradation. The existing 12 folds informed feature selection. Live forecasts from October 30 onward are proposed as the untouched evaluation; preserve their predictions before observing labels.

## Files to review

### New data package and its provenance

- [Package README](../../resources/ml-support/README.md)
- [METAR observations CSV](../../resources/ml-support/observations/eddf_metar_observations.csv)
- [ICON-Global normalized CSV](../../resources/ml-support/forecast/normalized/open-meteo-icon-global.csv)
- [DWD overlap CSV](../../resources/ml-support/observations/dwd_01420_hourly_wind_gust_overlap.csv)
- [Evaluation handoff](../../resources/ml-support/evaluation-handoff.md)
- [Deeper audit index](../../resources/ml-depth/README.md)
- [Comparability audit](../../resources/ml-depth/comparability/audit.md)
- [Label audit](../../resources/ml-depth/labels/audit.md)
- [Temporal audit](../../resources/ml-depth/temporal/audit.md)
- [Observation audit](../../resources/ml-depth/observations/audit.md)

The package describes 32,156 METAR reports and 16,008 ICON hours. Those are supplied claims to verify, not counts from a new model run. Its deeper handoff explicitly preserves the existing best-match training cache and treats the extra ICON data as a comparison source. Some earlier package prose says historical labels were absent; the deeper audit supersedes that statement with reconstructed DFLD labels. Keep chronology explicit.

### Literature and transfer limits

- [Model literature / NASA and FRA source chains](../../weather%20database/models/NOTES.md)
- [Advisory review framework](../../weather%20database/ADVISORY_BOARD.md)
- [Additional data sources and acquisition status](../../weather%20database/DATA_SOURCES.md)
- [NASA runway configuration paper](../../weather%20database/models/nasa-runway-configurations-2023.pdf)

The supplied review describes NASA's next-15-minute US-airport configuration task and its issue-time available inputs. This does not supply FRA labels or demonstrate 48-hour transfer. Distinguish research papers, methods, downloaded tables, and fields actually joined into the estimator. Do not relabel BTS delay causes as runway outcomes, or copy random splitting into a chronological forecast evaluation.

### Recent producer/test changes

Inspect `ml/features.py`, `ml/forecast.py`, `ml/quality.py`, `ml/requirements.txt`, `ml/tests/test_no_leakage.py`, `ml/tests/test_forecast_cli.py`, and changed model artifacts. In particular, commit `5ecf04e` claims archived-input filtering on explicit availability metadata; `6de474f` changes runway-18 event comparisons and refreshes artifacts.

## Independent assignments

| Reviewer | Job | Required evidence |
|---|---|---|
| Opus | New data eligibility, availability and leakage | Map each additional source to existing loaders/joins/features; test duplicates, overlap, timezones/units, availability and whether new material is connected. Reconcile new archived-input filtering with the prior exclusion finding. |
| Muse | Learning choice informed by NASA/FRA literature | Separate transferable method ideas from incompatible targets. Compare bounded candidates: chronological calibration (R4), conditional wind correction (R5), event learning (R3). Select one feasible CPU Colab protocol with exact labels, split, controls and stopping rule; execute a targeted data/label feasibility check. |
| Kiro | Package integrity and executable integration | Run the supplied local verification/QA scripts where safe, verify manifests and row counts, compare new CSV schemas with current parquet loaders, and run focused tests of the new availability filtering. Distinguish byte integrity from training eligibility. |

Work only in the existing dedicated SSD review checkout and scratch area. Preserve first-round files; use `round2-review.md` for new results. No new production model, merge or publication by reviewers. No new dependency installs are needed unless a required package is absent; all caches/temp/venvs must remain on the external SSD. Do not read credentials. No broad downloads.

Each report ends with **Ran and saw / Inferred / Not verified**, exact commands, source SHA, pass/fail counts, file references and the smallest actionable next step. The coordinator replays material checks before incorporating claims. Where an answer is still missing, write a precise question with its consequence; do not invent a label or availability time.

## Decision gate for another Colab run

1. Freeze source, data hashes, feature order and environment.
2. Establish common eligible rows; changes in data coverage are a separate experiment from changes in learner.
3. Fit all transforms/corrections/calibration with explicit chronological boundaries; do not use October outcomes for selection.
4. Compare unchanged v5, one controlled candidate, persistence and rules on matched rows.
5. Report Brier, accuracy, event counts/false alarms and missingness; no claimed win from literature accuracy or one favorable slice.
