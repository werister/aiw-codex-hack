# First completed ICON and scenario-selection findings
Recorded 2026-10-30. Branch: `hugo/redteam-evidence`.

Both runs completed in Google Colab CPU: publication-lag proxy 6 h (286.7 s) and 12 h (286.1 s), exit code 0. The frozen source's existing 54 tests passed in 2.45 s before training. This is an exploratory October comparison, not an untouched forward test and not a comparison against current v6.

## What we tested
Within each lag, the baseline and candidate use identical training/test rows and byte-identical original 45 feature columns. The candidate adds seven raw ICON columns. Both use the same gradient-boosting architecture. We also tested a 50/50 probability combination and a validation-selected model choice by horizon and weather regime.

122,280 training rows; 5,136 October forecast rows; 5,068 rows with usable OD labels/comparators. At leads 1/6/24/48 there are 105/107/107/107 scored rows. The separate runway-18 population has 3,744 rows. The restricted 2025+ training population differs from the team's full-history evaluation.

## First measured results
Numbers below are rounded from completed Colab stdout. [Independently recomputed CSV](v5-icon/audited_headline_all_lags.csv), [version decision ledger](MODEL_VERSION_RESULTS.csv), [chart](v5-icon/colab_comparison.svg), and [executed evidence](v5-icon/executed-evidence.ipynb) are committed. All 80 original headline rows (40 per lag) recomputed successfully; the expanded CSV has 88 rows. An independent reviewer checked all 152 ledger rows against those outputs and pinned v5/v6 artifacts. Seven-day paired block intervals include zero for all nonzero primary Brier differences. October runway-18 evaluation contains no closure-positive complete windows, so its 100% hourly accuracy does not demonstrate closure detection.

| Lag proxy | Method | 1 h accuracy | 6 h accuracy | 24 h accuracy | 48 h accuracy | Brier 6 / 24 / 48 h |
|---|---|---:|---:|---:|---:|---|
| 6 h | Paired v5 baseline blend | 91.429% | 82.243% | 80.374% | 76.636% | .14923 / .18649 / .19829 |
| 6 h | v5 + raw ICON blend | 90.476% | 81.308% | 80.374% | 78.505% | .15029 / .18551 / .19671 |
| 6 h | Equal combination | 90.476% | 82.243% | 79.439% | 78.505% | .14965 / .18588 / .19738 |
| 6 h | Transferred selector | 90.476% | 81.308% | 79.439% | 78.505% | .15029 / .18601 / .19671 |
| 12 h | Paired v5 baseline blend | 91.429% | 82.243% | 80.374% | 77.570% | .15051 / .18047 / .19800 |
| 12 h | v5 + raw ICON blend | 91.429% | 81.308% | 80.374% | 78.505% | .15114 / .18016 / .19654 |
| 12 h | Equal combination | 91.429% | 81.308% | 80.374% | 78.505% | .15067 / .18014 / .19713 |
| 12 h | Transferred selector | 91.429% | 81.308% | 80.374% | 78.505% | .15114 / .17963 / .19738 |

Lower Brier is better. ICON improves 24/48 h Brier slightly but worsens 6 h in both lag settings and worsens 1 h Brier. It does not satisfy an across-horizon promotion case.

The selector was learned from September out-of-fit predictions, with August blend validation and purged boundaries. A transferred selector uses the policy on refitted core models; a separate frozen selector uses unchanged early models. Compare each with the corresponding single global arm selected on September, not with a different model generation. Outcomes are mixed: no consistent selector win. Do not select a deployment policy from October subgroup winners.

## Kai's latest changes: v6 is now served
Reviewed source pin: [410d2b9](https://github.com/werister/aiw-codex-hack/tree/410d2b9baa1cc6e44b5265feb8954c2b18224b9f).
Kai's explanation: [ML_VERBESSERUNGEN.md](https://github.com/werister/aiw-codex-hack/blob/410d2b9baa1cc6e44b5265feb8954c2b18224b9f/ML_VERBESSERUNGEN.md), introduced in commit 3820257.

v6 preserves the architecture and improves observed tailwind-state initialization, forecast-time eligibility, event direction/timing evaluation, complete-window runway-18 scoring, uncertainty estimates, and display of OD observations when runway-18 labels are missing. These are correctness/evaluation improvements; a general accuracy gain over v5 is not established.

The committed twelve-month v6 artifact reports OD accuracy 95.7%, 92.7%, 91.8%, 88.9% at 1/6/24/48 h and Brier .0341/.0530/.0637/.0818. These are source-artifact results, not this experiment's retraining. Rules score 93.1/88.1/87.7/84.0%; persistence 95.9/88.8/75.1/64.2%. Population and scoring differ from the table above.

Critical weakness: v6 detects 0/12 inferred closure-positive complete 24-hour windows among 307 eligible windows; 1,125 windows excluded. Those are overlapping weather-rule-derived windows, not confirmed operational closures. This is not directly comparable with v5's earlier 3/24 under different completeness rules.

## Evidence and limits
- Preserve raw and blended probabilities, validation policy, model/data hashes and matched-row traces.
- Archive offsets with 6/12 h lags are availability proxies, not demonstrated historical release times.
- October influenced prior development. October 30 onward remains a proposed untouched forward test; no results are claimed here.
- US BTS aggregated delay data does not provide FRA flight-level counterfactual delay outcomes. Model probability replay is possible; causal delay savings are not established.
- Router deployment remains deferred. This is a historical shadow experiment, not a live decisions API.
- Existing reviewer findings and safeguards: [review archive](../reviews/redteam-archive/) and [test index](redteam/README.md).
- Required submission metrics remain 1/6/24 h; 48 h supplements them. OD accuracy cannot stand in for runway-18 closure detection or change-time quality.

Decision: keep the current served v6 as the team baseline; do not promote ICON or scenario routing from these results. This is a deployment-status decision with unresolved weaknesses, not proof that v6 is universally best.
