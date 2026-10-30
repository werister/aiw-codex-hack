# Red-team evidence checkpoint — 30 October 2026

This checkpoint separates executed experiments, independently replayed checks and experiment code still awaiting execution. It incorporates the F17–F23 answers in [forecast-trace-questions.md](../forecast-trace-questions.md). Source for the new ICON experiment is pinned to `5aed997313b78678d11fa23b808c2a9835a1d91a`; this is not a claim about every subsequent main-branch change.

## Completed model experiment

The [v4 Colab report](../experiments/v4-colab-october.md) and [executed notebook](../experiments/v4-colab-october.ipynb) preserve the completed original-blend / Extra Trees / fixed 50:50 comparison. Extra Trees and the combination did not improve accuracy over the original v4 blend at any reported lead. This is not a comparison against v5. All 50 original tests passed in that Colab run. The independent trace recomputation matched all 72 reported metric rows.

October already informed development; these results are exploratory, not an untouched forward test. “Changed” accuracy is target-direction accuracy conditional on an intervening recorded transition, not event-detection recall.

## Completed reviews and checks

- **Opus:** demonstrated that full-history exclusion flags can use future observations across an arbitrary boundary. The observed flagged run did not cross the current evaluation fold boundaries. This is a possible mechanism, not proof that the reported folds leaked. Identified the fixed-key dataset-cache hazard for a supplemental-data ablation and supplied eight protocol safeguards.
- **Kiro:** built the raw ICON adapter and protocol helpers. Coordinator independently ran the two pytest suites: **27 passed in 2.90 seconds** (13 adapter + 14 protocol). They cover offset boundaries, units, tailwind conventions, missingness, explicit publication-time rejection, retrospective download-time separation, source alignment and matched-arm safeguards. These tests are not model-performance evidence.
- **Muse:** produced the v5 versus v5+raw ICON Colab notebook/script, paired 6-hour/12-hour publication-proxy sensitivity, preserved raw/blended predictions and a pre-October selector study. Initial review fixes included metadata-derived 45-feature order, index-safe baseline hashing and removal of an inappropriate borrowed wind correction. Final review still requires handling missing selector labels, a separate runway-18 evaluation population and an explicit global-arm comparator before the new run.

The 133-file support package previously passed its integrity verification. Integrity alone does not establish issue-time availability or training eligibility. New normalized METAR/DWD files largely overlap existing observations; supplemental ICON-Global provides a different weather-model input, not new runway labels.

## Delay-data eligibility: independently checked

Inspected `weather database/bts/raw2025/Airline_Delay_Cause.csv` from the reviewed snapshot:

| Check | Result |
|---|---|
| Rows / columns | 22,687 / 21 |
| Period | January–December 2025 |
| Airports / carriers | 364 / 21 |
| Granularity | Monthly carrier × airport aggregates |
| FRA present | No |
| Rows containing missing values | 11 |
| SHA-256 | `8b9379ac15e5b381991bae8330882f6615aba2a3c3e4ca39b0dd9df697b4aa77` |

The coordinator recomputed these counts and hash; the same hash is recorded in the tracker's analysis artifact. Delay minutes and cause counts are retrospective totals; cause counts can be fractional allocations. There are no individual flights, scheduled/actual flight timestamps, runway states or decision-time fields.

This supports descriptive US monthly cause-share analysis. A separate monthly forecasting study would require a defensible chronological design and publication-availability assumptions; it would not validate Frankfurt hourly forecasts. These data cannot establish that a Frankfurt runway decision would reduce flight delays. No such causal or flight-level claim has been tested.

## Case-by-case model selection: hypothesis, not a win

The proposed controlled study compares both candidates on identical issue/target rows, retaining raw and persistence-blended probabilities. Learn a small lead × weather-regime selection table using earlier out-of-fit predictions; score it later against both fixed arms, an earlier-validation-selected global arm, a fixed equal blend, persistence and rules. Preserve eligibility, selection reason, model identity and both candidate probabilities per case.

Primary score: OD Brier at 6/24/48 hours; also report 1-hour guardrail, accuracy, change-conditioned accuracy, false alarms and timing where the target supports them. A selector evaluated on refitted candidates must disclose that policy-transfer step. October must not determine the selection table. A later genuinely untouched test requires frozen predictions, source/data hashes and labels acquired afterward.

The current archive lacks verified historical weather-publication timestamps. Six- and twelve-hour lag studies are sensitivity analyses of proxies, not proof of historical availability. Full-history exclusion remains an inherited limitation; fold-causal filtering is still untested.

## Status at this commit

**Executed:** v4 learner comparison; independent trace checks; data integrity/coverage checks; 27 adapter/protocol tests.

**Built, under final review:** matched v5/ICON comparison and chronological selector experiment.

**Not yet established:** v5/ICON improvement, selector advantage, calibration or conditional-correction gains, Frankfurt delay counterfactuals, or a production decision-API router. No new model-performance result is claimed by this checkpoint.
