# How we tested and selected the current runway model

**Evidence cut: 30 October 2026. Branch: `hugo/redteam-evidence`.** This is a presentation-ready history of the team's modelling work and Hugo's independent red-team work. The current served model is **walk-forward-v6** at reviewed pin `410d2b9`. v5 was the preceding adopted feature set. v6 improves correctness and evaluation; a general accuracy gain over v5 is not established. No version is proven best for every regime or operational outcome.

Latest evidence: [first findings](COLAB_ICON_FIRST_FINDINGS.md), [version decision CSV](MODEL_VERSION_RESULTS.csv), [audited Colab CSV](v5-icon/audited_headline_all_lags.csv), [executed cells and outputs](v5-icon/executed-evidence.ipynb), and [comparison chart](v5-icon/colab_comparison.svg). CSV accuracies are fractions; multiply by 100 for percent. Compare only within the same experiment, target and lag.

**Judge-facing takeaway:** We started with a rules baseline, corrected timing assumptions even when scores fell, improved weather features, tested alternatives on matched rows, and retained negative results. Our independent Extra Trees / simple-ensemble trial did not justify replacing the original model. Runway-18 closure prediction and a genuinely untouched forward evaluation remain open.

## Timeline: what changed, what we measured, what we decided

All times below are **30 October 2026, Europe/Berlin (CET, UTC+1)**. Times attached to commits are source-control timestamps, **not training start/finish times**. Where a precise execution time was not recorded, the stage is shown without an invented timestamp. Historical stages E1–E17 come from the team's [pinned experiment log](https://github.com/werister/aiw-codex-hack/blob/5aed997313b78678d11fa23b808c2a9835a1d91a/EXPERIMENTS.md); the later red-team run has its own executed notebook and evidence.

| Time / stage | Version or experiment | What was tested or corrected | Result and decision |
|---|---|---|---|
| Early baseline, E1 | Official rules on observed wind | Compare the brief's rules with recorded operating direction | Early log: **89.2% agreement**. Rules are a benchmark, not ground truth; a later refreshed artifact reports 89.9% on its own coverage. |
| 12:15 commit `5b82df2`; E2 | Initial gradient boosting | Monthly chronological evaluation, before persistence blending and the later publication-lag correction | Logged 1/6/24/48 h accuracy: **93.8 / 91.5 / 90.8 / 89.8%**. Lost at 1 h to persistence/rules (**96.9%**). Superseded; not a final claim. |
| 12:24 commit `4fc8472`; E3 | Classifier + persistence | Select blend weights before each held-out month | Logged 1 h improved to **96.9%**; other leads unchanged in that experiment. Keep short-lead persistence as a serious comparator. |
| 12:35 commit `a979070`; E4 | Availability-corrected forecast bands | Add six-hour publication buffer and day-3 weather for longer leads | Logged **97.0 / 91.5 / 90.3 / 84.1%**. 48 h fell from 89.8% to 84.1%; accept the lower score after fixing optimistic timing. Exact publication times remain unverified. |
| 12:57 commit `6447eb3`, 13:12 `d9a58cc`; E9/E9b | walk-forward-v4 | Blend by lead × night/calm/active regime; local-clock issues; examine the stuck direction feed | Six-month log: **94.6 / 90.7 / 89.6 / 84.9%**. Report all-recorded results and a separate hindsight-cleaned sensitivity. Do not compare this six-month aggregate directly with the later twelve-month aggregate. |
| 13:45 commit `2300db6`; E10/E12/E13 | walk-forward-v5, **45 features** | Separate ECMWF/GFS/ICON weather forecasts, ensemble statistics, pressure gradients; same tree family | Twelve-month matched before/after: 48 h **84.9 → 89.2%**, Brier **0.108 → 0.082**. Ensemble features alone reached 88.6%; pressure contributed roughly 0.1–0.6 percentage points by lead. Adopt v5. |
| Same development cycle; E14/E17 | Rejected alternatives | Deeper trees, monotonic constraints, separate lead-bucket models, extra observation-state features; denser 3-hour training issues | First group: within ±0.6 points, Brier equal/worse. Denser issues: 6/24/48 h **92.7 / 91.5 / 89.1%**, with 1 h **95.0%**, versus v5 **96.0 / 92.8 / 91.7 / 89.2%**. Not adopted. |
| E5 and later contract checks | Training/CLI agreement | Compare features and probabilities; verify source/artifact identity | Original E5 reports **144 lead rows** on three October days matching. Independent v5 contract tests later passed; synthetic-input contract checks are not accuracy experiments. |
| Independent Colab session, completed before evidence export at approximately 14:08 | Frozen v4 vs Extra Trees vs fixed 50/50 combination | Same inputs, rows, chronological training cutoff and scores; untouched source tests first | **50 tests passed in 2.76 s**; model run **229.9 s on Colab CPU**. Neither alternative improved accuracy at any reported lead. No promotion. Full table below. |
| 14:11 commit `6de474f`; E11/E16 | Stronger corrected-wind rules and runway-18 events | Check the model against stronger rules, and examine rare inferred closures | Stronger-rule OD accuracy **95.6 / 88.8 / 89.2 / 85.8%**. v5 still leads at 6/24/48 h. Runway-18 model detected only **3/24 issue-level closure windows at 24 h**; no broad closure-skill claim. |
| 14:12 commit `5ecf04e` | Explicit availability metadata | Reject archived inputs explicitly published/retrieved after issue time where the relevant metadata is supplied | Guard added. The historic archive lacks verified publication timestamps, so this does not prove all historic weather was available at issue time. |
| Independent review rounds, following the Colab run | Opus, Muse, Kiro | Leakage counterexample, metric recomputation, feature/trace contracts, new-data eligibility | Metric recomputation matched **72/72 rows**; **29 checks** passed. Focused leakage suite: **15 passed**, including tests demonstrating a vulnerability. v5 CLI/contract suite: **27 passed**. Counts overlap existing tests; do not add them into one total. |
| Later new-data round | Pinned v5 + raw ICON-Global candidate | Freeze data, retain baseline 45 features, append 7 ICON features, pair issue masks and 6/12 h lag assumptions | Adapter/protocol tests: **27 passed**; final bundle/source checks: **49 passed**. These are software/data checks. Both Colab fits completed: 286.7 s / 286.1 s at lag proxies 6 / 12 h. ICON worsens 6 h Brier, slightly improves 24/48 h; not promoted. |
| Latest selector exploration | Experimental per-case choice | Learn lead × regime preference on earlier out-of-fit predictions; compare frozen selector, transferred policy, global arm, equal blend and fixed models in October | Completed Colab experiment; mixed results, not a demonstrated consistent improvement. No production router deployed. No October outcomes may select the policy. |
| Latest delay-data review | Luca/Kai BTS data | Check geography, granularity, timing and provenance before using delay labels | **22,687 monthly US carrier–airport rows, 364 airports, 21 carriers; no FRA**. Cannot validate Frankfurt flight-level delay counterfactuals. Keep as contextual analysis. |

“Before” and “after” refer only to the stated matched comparison. Earlier experiment-log snapshots changed folds, coverage and timing assumptions; they are not one continuous leaderboard on identical test rows. E2–E4 are historical experiment identifiers; no unverified v1/v2/v3 release names are assigned here.

## Preceding adopted version: v5 historical evaluation (superseded by v6)

Source: [frozen quality.json](https://github.com/werister/aiw-codex-hack/blob/5aed997313b78678d11fa23b808c2a9835a1d91a/web/public/data/quality.json), `out_of_sample.od`. Twelve expanding monthly folds, November 2025–October 2026. Each fold fit uses earlier labels; feature selection nevertheless used these same folds. The table below was read from the committed artifact, **not independently retrained in this red-team session**.

| Lead | Scored rows | v5 blend accuracy | v5 blend Brier ↓ | Official rules accuracy | Persistence accuracy |
|---|---:|---:|---:|---:|---:|
| 1 h | 1,416 | 95.97% | 0.03501 | 95.90% | 95.90% |
| 6 h | 1,416 | 92.80% | 0.05305 | 88.14% | 88.84% |
| 24 h | 1,383 | 91.68% | 0.06333 | 87.71% | 75.05% |
| 48 h | 1,338 | 89.16% | 0.08169 | 84.01% | 64.20% |

The same twelve-fold comparison with the earlier E9 feature set was:

| Lead | Earlier feature-set accuracy / Brier | v5 accuracy / Brier |
|---|---:|---:|
| 1 h | 95.5% / 0.039 | 96.0% / 0.035 |
| 6 h | 92.0% / 0.060 | 92.8% / 0.053 |
| 24 h | 90.3% / 0.079 | 91.7% / 0.063 |
| 48 h | 84.9% / 0.108 | 89.2% / 0.082 |

At 24 h, the reported model-minus-rule margin is **+4.0 percentage points**, day-bootstrap 95% interval **+2.4 to +5.6**. At 48 h it is **+5.2 points**, interval **+3.2 to +7.1**. At 1 h the methods effectively tie. These are historical evaluation intervals, not a guarantee of future operational performance.

**Why “selected,” not “best everywhere”:** in the same artifact the raw v5 classifier scores **93.22% accuracy at 6 h**, versus the served blend's **92.80%**. Raw probabilities also have slightly lower Brier at 6/24/48 h, while the blend is substantially better at 1 h. The comparison motivates a chronological case-by-case study; it does not authorize selecting the winner after seeing each test outcome.

## What we ran ourselves in Colab: independent alternative learners

Frozen source: `44d5abd3363248b1de0a3ed96ff32982aafdd7b3` (v4, **25 features**). Training labels available before **1 October 2026 UTC**. **189,000** fit rows, **5,136** test rows, **5,068** common scorable rows; actual October issues available through the 27th. Every method used identical scorable rows.

Extra Trees: 100 trees, depth 15, minimum leaf 50, seed 42; train-only median imputation. Combination: a predeclared 50% original blend + 50% Extra Trees. The original classifier/blend was refitted using the existing pipeline.

| Method | 1 h, n=105 | 6 h, n=107 | 24 h, n=107 | 48 h, n=107 |
|---|---:|---:|---:|---:|
| Original v4 blend | **94.29%** | **81.31%** | **75.70%** | **72.90%** |
| Extra Trees | 80.95% | 79.44% | 73.83% | 71.96% |
| Fixed 50/50 combination | 89.52% | 81.31% | 72.90% | 72.90% |
| Persistence | 96.19% | 90.65% | 73.83% | 65.42% |

48 h Brier: original **0.22694**, Extra Trees **0.22393**, combination **0.22474**. A small probability-score improvement on one lead is not an overall win. The alternatives lose accuracy at shorter leads, and persistence is strongest at 1/6 h in this October slice.

**Decision:** retain the original model; reject a replacement claim for Extra Trees or naive averaging. **This experiment does not establish their performance against v5.** It also does not establish that v5's twelve-month score beats an alternative's October-only score.

Evidence: [executed notebook](v4-colab-october.ipynb), [complete report](v4-colab-october.md), [independent recomputation script](redteam/check_evidence.py). Export includes per-row predictions, feature inputs, model artifacts and a source/data manifest.

## What red-teaming changed in our understanding

| Challenge | Check and observed outcome | Consequence |
|---|---|---|
| Could later observations change training-row exclusions? | Opus constructed a fold-boundary counterexample: a whole-run suspect flag uses later METAR to relabel earlier training rows. Two passing tests demonstrate that behavior. Actual flagged run: 103 hours in October, zero current fold-boundary crossings. | Record the possible leakage mechanism without claiming a demonstrated current-score effect. Fold-causal filtering is still untested. |
| Are metric tables faithful to saved probabilities? | Muse recomputed all 72 metric rows; 29 checks passed, coordinator replayed. | Negative learner results are supported by traces, not only screenshots or agent summaries. |
| Does the inference contract reject wrong inputs? | Kiro's 27-test CLI/contract run covered artifact hashes, feature order, missing required wind, future METAR exclusion and deterministic IDs with synthetic inputs. | Supports those contracts, not a full end-to-end live guarantee. |
| Is new data actually new training information? | 133-file support-package integrity verification passed; normalized METAR/DWD largely overlap existing observations. ICON-Global is a distinct supplemental forecast source. | Preserve provenance and avoid counting duplicate observations as added coverage. |
| Can the supplemental experiment accidentally compare identical cached data? | Cache signature omits supplemental ICON input. | New experiment calls the direct dataset builder and asserts identical baseline columns plus distinct supplemental columns. |
| Are wind units/corrections consistent? | Adapter tests check raw knots, lead-offset boundaries, tailwind sign and missingness. An early implementation borrowed a correction from another weather model; review removed it. | Raw ICON by default; any future fitted correction must be learned chronologically. |
| Is selector training valid? | Review found missing labels in selector validation and runway-18 scoring restricted by OD-valid rows. Both were corrected before training. | Export selector exclusions and a separate runway-18 population; compare a frozen selector with a validation-selected global arm. |
| Can BTS prove delay reductions at FRA? | Schema and hash audit: monthly 2025 US aggregates, no FRA, no flights or issue-time fields. | No fabricated hourly labels or causal delay-savings claim. |

## Accuracy does not answer every operational question

- **Change-conditioned accuracy:** v5 is right on **62.36 / 82.08 / 83.36%** of scored changed-flag rows at 6/24/48 h. This is target-hour direction accuracy conditional on a recorded intervening change, **not recall of distinct switches**. At 6 h the rules do better on that slice (**76.40%**).
- **Next-change timing:** in the frozen artifact, **28.10% within ±1 h**, **52.55% within ±3 h**, across **765 overlapping actual-change issue windows**. False-alarm rate is **12.80% of 578 no-change windows**, not “13% of warnings were false.” There are 89 incomplete windows excluded.
- **Runway 18:** labels are inferred from METAR and the brief's weather rule, not actual operational closure logs. At 24 h: **3 hits / 24 positive issue windows (12.5%)**, 21 misses, zero false alarms; persistence also hits 3. Near-perfect overall accuracy would hide this rare-event weakness.
- **Confidence:** Brier measures probability error (lower is better). A certainty score is not automatically a calibrated probability, and the reported reliability gap is not evidence that post-blend calibration was trained.

## Untried or unfinished work: no invented results

| Candidate | State | How it should be judged |
|---|---|---|
| v5 + 7 raw ICON-Global features | Completed in Colab at lag proxies 6 and 12 h; not promoted | Matched 2025+ full-48 h issue masks; preserve raw/blended predictions; separate lag-6 and lag-12 sensitivity runs. |
| Small lead × regime selector | Completed frozen and transferred-policy experiments; no consistent advantage | Early base fit → August blend validation → September selector validation → October exploratory score; purge labels at each boundary; compare global arm and fixed candidates. |
| Post-blend probability calibration | Owner confirmed untried | Disjoint chronological fit/calibration/test windows; OD Brier at 6/24/48 h. |
| Conditional wind correction | Owner confirmed untried and promising for runway 18 | Fit direction/speed/season/regime correction only on earlier data, before any inner validation; compare against fixed-factor rules and model. |
| Direct direction-change / change-time learning | Owner confirmed untried | First freeze event definition, missing-window policy and censoring; report event detection and timing, not only stable-hour accuracy. |
| Untouched forward evaluation from 30 October | Proposed; no completed result here | Freeze inputs/models/predictions before later labels arrive. Historical folds used for feature choice cannot be relabelled untouched. |

No production decision-API router was deployed by this work. Comparing alternative predictions against the same observed outcome is a model replay; it is not a causal demonstration that different runway decisions would have reduced delay.

## Evidence, tests and reproduction

The branch includes the existing executed v4 notebook and the new [v5/ICON notebook](v5-icon/fra-v5-icon.ipynb), [experiment script](v5-icon/experiment_v5_icon.py) and [adapter](v5-icon/icon_supplement.py), plus [red-team test sources](redteam/README.md). The latter include the leakage counterexample, independent metric audit and ICON tests/protocol helpers.

Test counts refer to named runs, not unique cumulative tests: **50 source tests in Colab**, **29 evidence-audit checks**, **15 focused leakage tests**, **27 v5 contract tests**, **27 ICON adapter/protocol tests**, **49 bundle/source checks**. Several suites reuse production tests; the 49 checks include static/hash checks and are not 49 model experiments. The v4 learner comparison and both v5/ICON runs are complete. Both archive hashes matched; 54 existing source tests passed in 2.45 seconds. Runtime checks confirmed 45 baseline + 7 supplemental features, 16,008 ICON hours, and same-hour METAR alignment (correlation 0.782 versus 0.360/0.382 at ±24-hour shifts). Independent recomputation matched all 40 headline metric rows per lag. The evidence CSV adds the corresponding global comparator and frozen-model arms (88 rows total). Seven-day paired block intervals for the nonzero primary Brier differences all include zero. October runway-18 hourly scores are 100%, but the evaluated windows contain no positive closure events; this provides no evidence of closure detection. All model training in this lane uses Colab.

Pins:
- v4 source archive SHA-256: `74f91c3a19fb545989f48a5bd0478a5915529ff797d09addfead48b117ea6b18`.
- v4 complete result ZIP SHA-256: `e219bf2d2749dd3f6e0002a0e99f6ae545eeab90f4c2584086081537c85566a9`.
- v5 source archive SHA-256: `ca160e76210755d6497e1120aed443664f343256b26d09ec4e50ba67eb980080`.
- Current raw ICON adapter SHA-256: `72f82ddc594ff07000f0caadcd95b645219faac0929f21d63ab08542cc9c953f`.

The binary v4 evidence is preserved on the SSD at `/Volumes/AthenaSSD/fra-red-team-evidence`; its ZIP is now in `local-backups/fra-red-team-evidence.zip` after a hash-verified move to free internal disk. This branch contains human-readable/code evidence, not that binary model bundle.

## Suggested 30-second explanation to the judges

> We tested the forecast in monthly chronological folds, corrected a weather-availability assumption even though it lowered our score, and then improved the weather inputs. The currently served v6 reports 91.8% direction accuracy at 24 hours ahead, versus 87.7% for the challenge rules on twelve historical folds. Its latest improvements strengthen timing and evaluation; they do not establish a general accuracy jump over v5. Independently, we ran Extra Trees and a simple combination in Colab on matched October data; neither improved accuracy over the original v4 blend. We also tested extra ICON inputs and case-by-case selection in Colab; small longer-lead improvements came with short-lead regressions and uncertain gains. We kept those negative results and audited the saved predictions. The historical folds informed model selection, so our untouched forward test is still ahead. Runway-18 closures remain a separate weak point.

This narrative distinguishes the team's v5 development from the independent v4 challenge, rather than implying that our red-team alternatives produced or outperformed v5.

## Latest stage: Kai's v6 and completed Colab sensitivity (30 October)

Kai's [forecast improvements explanation](https://github.com/werister/aiw-codex-hack/blob/410d2b9baa1cc6e44b5265feb8954c2b18224b9f/ML_VERBESSERUNGEN.md) documents observed tailwind-history initialization, all supplied availability timestamps checked, direction-sensitive and deduplicated switch evaluation, complete-window runway-18 evaluation, and OD display when runway-18 labels are absent. Existing architecture remains. E18 extra observation history was not adopted; E19 speed correction was not pursued after diagnosing grouping bias; E20 current forecast-error/trend and E21 QNH-tendency features were coded but not trained before freeze; E22 variable-wind label treatment was not applied in a retrain. Do not label these as completed improvements.

| Lead | v6 rows | v6 OD accuracy | Brier | Rules | Persistence |
|---|---:|---:|---:|---:|---:|
| 1 h | 1416 | 95.69% | .03414 | 93.08% | 95.90% |
| 6 h | 1416 | 92.73% | .05305 | 88.14% | 88.84% |
| 24 h | 1383 | 91.83% | .06368 | 87.71% | 75.05% |
| 48 h | 1338 | 88.86% | .08182 | 84.01% | 64.20% |

These are committed v6 artifact values, not an independent v6 retraining in this lane. v6 event results supersede the earlier v5 figures above: 27.2% of 750 actual-change windows within ±1 h, 52.5% within ±3 h; false alarms in 14.7% of 593 no-change windows; 89 excluded. Distinct-event recall is 115/193 (59.6%) with deduplicated precision 45.5%. Runway 18: 0/12 positive complete 24-hour windows detected among 307 eligible, 1125 excluded. Changed definitions and denominators prevent a simple v5/v6 event-gain claim.

The new ICON runs use a restricted paired v5 training population, not the served v6. The selector's global comparator is selected on September, and October outcomes never choose the policy. No causal flight-delay or production routing claim is supported. [Full results and limitations](COLAB_ICON_FIRST_FINDINGS.md).
