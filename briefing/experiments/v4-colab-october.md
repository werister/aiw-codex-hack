# Colab red-team comparison: frozen v4, October 2026

Executed in Google Colab on 30 October 2026 at Hugo's request. **Neither Extra Trees nor the fixed 50/50 combination improved accuracy over the original blend on the matched October rows. No candidate is promoted.** This is an exploratory v4 comparison, not a benchmark against current v5.

## Ran and saw

- Source pinned to `44d5abd3363248b1de0a3ed96ff32982aafdd7b3`; the same source/data archive was uploaded through Colab's browser UI and its SHA-256 checked before extraction.
- Unchanged command `python -m pytest ml/tests -q`: **50 passed in 2.76 seconds** in Colab.
- Original classifier and its chronological persistence blend were refitted with the existing training code. Extra Trees used the identical 25 feature inputs and available OD labels; median imputation was fitted on training data only.
- Extra Trees settings: 100 trees, maximum depth 15, minimum leaf size 50, all features eligible per split, random seed 42. The combination was fixed at 50% original blend + 50% Extra Trees before viewing alternative scores.
- Training: labels available before 2026-10-01 UTC; 189,000 rows after the existing training exclusion. October issues with labels available before November: 5,136 test rows, 5,068 common scorable rows. Actual available test issues run October 1–27. Training's latest label availability was September 30 at 23:00 UTC.
- Every method used the same scorable rows. All-recorded headline results retain suspect test intervals; the export includes retrospective-exclusion sensitivity and midnight-issue slices.
- The model comparison completed in 229.9 seconds on Colab CPU (Python 3.13.18, scikit-learn 1.6.1).
- Downloaded evidence ZIP matched Colab's SHA-256. Independently verified all 50 source/data file hashes against the uploaded source archive and parsed both exported notebook code cells.

### Matched all-recorded accuracy

| Method | 1 hour (n=105) | 6 hours (n=107) | 24 hours (n=107) | 48 hours (n=107) |
|---|---:|---:|---:|---:|
| Original blend | 94.29% | 81.31% | 75.70% | 72.90% |
| Extra Trees | 80.95% | 79.44% | 73.83% | 71.96% |
| Fixed 50/50 combination | 89.52% | 81.31% | 72.90% | 72.90% |
| Persistence | 96.19% | 90.65% | 73.83% | 65.42% |

At 48 hours, Brier scores were 0.22694 original blend, 0.22393 Extra Trees, and 0.22474 combination (lower is better). That small probability-score difference does not establish an overall improvement. At 1 hour the blend and both alternatives correctly predicted **0 of 4 changed-direction rows**; overall accuracy alone hides this weakness. The change slice uses an increase in the recorded direction-change counter since the last known state. Its accuracy still measures the target-hour direction conditional on that flag; it is not an event-detection recall measure, and missing/transition-hour handling still needs F19.

## Independent checks

- Muse independently recomputed all **72/72 metric rows** from the exported probabilities: **29 checks passed, 0 failed**. The coordinator reran the audit with the same result.
- Opus supplied a constructed cross-boundary case where post-boundary METAR flags earlier labels through the whole-run stuck-feed exclusion. The coordinator reviewed the test and reran it with the existing focused tests: **15 passed, 0 failed**. Two of those tests deliberately assert the problematic behavior; passing demonstrates the vulnerability, not a fix.
- The real-data probe found one 103-hour flagged interval, entirely in October, with **0 crossings** of either the v4 or v5 fold boundaries. The coordinator reran the probe. No current fold-score effect from this boundary mechanism was demonstrated.
- Opus also identified repeated feature/hyperparameter selection on the evaluation months in the experiment log. Reported walk-forward performance should not be presented as an untouched final test; its selection-bias magnitude is not measured.

## Inferred

A different classifier or naive averaging is not enough on this slice. The more distinct next research move is learning change-event risk, **after F19 defines the event target and missing-window rules**. Chronological probability calibration is a smaller separate candidate (F23), with calibration data disjoint from base fitting and final evaluation. Both can be tested on CPU Colab.

## Not verified

- No full six-month alternative walk-forward sweep or v5 retraining was performed.
- October already informed development; it is not an untouched final holdout.
- Forecast windows overlap; no independent-row significance or confidence claim is made.
- Public labels and weather publication-lag assumptions were inherited; runway-18 alternatives were not evaluated.
- Existing training exclusions are computed by the inherited pipeline and may use full-history information. The strict time-purge assertion does not establish that every preprocessing decision is causal. F20 requests that separate check.
- Answers to F17–F22 remain pending. The submitted v5 model is unchanged.

## Reproduction and evidence

The [executed two-cell notebook](v4-colab-october.ipynb) retains the successful setup and experiment outputs; the earlier failed private-repository clone attempt is excluded. Open the notebook in Colab and upload the frozen source archive when prompted.

The notebook installs the source requirements, runs the unchanged tests, refits the candidates and exports metrics, per-row inputs/predictions, fitted models and a manifest to `/content/fra-red-team-results`.

To recreate the source archive in an authorized local clone:

```sh
git archive --format=zip --output=fra-red-team-source.zip 44d5abd3363248b1de0a3ed96ff32982aafdd7b3 ml data
```

Expected source archive SHA-256: `74f91c3a19fb545989f48a5bd0478a5915529ff797d09addfead48b117ea6b18`.

Complete downloaded evidence bundle SHA-256: `e219bf2d2749dd3f6e0002a0e99f6ae545eeab90f4c2584086081537c85566a9`. Hugo's local copy is `~/Downloads/fra-red-team-evidence.zip`; extracted evidence is on `/Volumes/AthenaSSD/fra-red-team-evidence`. The binary bundle is not uploaded to this repository. The notebook and this report are durable repository artifacts; the original browser notebook is unsaved because Drive quota prevented saving.

Related questions: [F17–F23 in the requested briefing](../forecast-trace-questions.md#f17--which-learning-approaches-have-not-been-tried-yet-kai--jayden--ml-implementer).
