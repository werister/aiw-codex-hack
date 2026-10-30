# Model card · Frankfurt operating direction and runway 18

Plain-language German explanation: [ML_VERBESSERUNGEN.md](ML_VERBESSERUNGEN.md).

## Model and intended use

`walk-forward-v6` predicts operating direction 25/07 and inferred runway-18 weather
usability at each of the next 48 hourly targets. It also reports the first predicted
direction change and a certainty score, `100 × min(|2p_OD25−1|, |2p_R18−1|)`.
This margin is not a calibrated probability. The displayed change window is a
probability-band heuristic, not a calibrated event-time interval.

The system supports planning in the FraAlliance challenge. DFS decides the actual
operating direction; these forecasts are not operational clearances.

Two scikit-learn histogram gradient-boosted classifiers use 45 features: recorded
state, METAR wind/trends, forecast wind, rules, separate weather models, pressure
differences, local hour, season and lead. OD is blended with persistence by horizon
and regime; R18 uses horizon-only weights. Each fold selects weights by Brier score
on its preceding 60-day validation block, with labels purged across the inner
boundary. Sparse or closure-free R18 validation and unknown current R18 state use
the raw classifier. The model architecture remains unchanged.

## Data and availability

| Source | Use | Limitation |
|---|---|---|
| [DFLD recorded directions](https://www.dfld.de/Mess/StatWetter.php?R=1&D=01.10.2026) | Stable-hour OD targets and completed-hour current state; half-hour transitions for event scoring | Public operational proxy, not a certified movement log |
| [IEM EDDF METAR](https://mesonet.agron.iastate.edu/request/download.phtml) | Observed winds; inferred R18 targets | Actual operational closures are not labels |
| [Open-Meteo Previous Runs](https://open-meteo.com/en/docs/previous-runs-api) | Best-match, ECMWF, GFS, ICON and four pressure boxes | Offset archive; exact historical publication times are unavailable |
| FraAlliance brief, `ml/rules.json` | Official rule baseline and rule features | Challenge thresholds govern this implementation |

Inputs cover 2024 onward for weather forecasts; longer METAR/DFLD history supports
state and label checks. Archived runs use day 1 for leads 1–18, day 2 for 19–42,
and day 3 for 43–48, with a six-hour publication proxy. Every explicit issuance
and retrieval timestamp must also be no later than issue time. Observed positive
tailwind duration seeds both rule paths and the CLI fallback.

Live issues are rounded down to the hour. A newly fetched snapshot after that
timestamp is ineligible; the existing dated-run fallback uses a twelve-hour
publication proxy. Neither buffer proves actual historical availability.
DFLD publication delay and summer-clock alignment remain unverified. Wind scales
are existing fixed constants documented as fitted on 2024; this change neither
refits them per fold nor independently reconstructs that calibration.

### Independent data verification (Kai Detmers)

Offline checks, all exit 0 ([`resources/ml-depth/verification.md`](resources/ml-depth/verification.md)):
- **DFLD labels:** all 76,588 hourly labels are rebuilt exactly from 154,752 half-hour values; the 788 excluded hours and 2,880 raw HTML samples match.
- **METAR:** 46/46 raw file hashes match, with 32,156 wind groups and zero normalisation deviations.
- **Forecast wind:** 144,072 values from 22 monthly responses re-checked. 72 hourly ICON vectors match their assigned runs; the six-hour publication buffer is still an assumption.
- **TAF:** the IEM archive returned zero EDDF rows, so TAF is not used ([`resources/ml-support/taf/findings.md`](resources/ml-support/taf/findings.md)).
- **Wind bias:** ICON surface wind runs about 3.3 kt below the airport sensor, stable across 22 months (7-day blocks −3.49 to −3.15 kt; against the DWD station −3.07 kt). That is why forecast wind is scaled to airport level.

**Further limits:**
- **Change hours:** 770 of the 1,681 detectable direction changes fall in transition hours that the stable-hour accuracy excludes, so changes are scored on the half-hour data instead.
- **Runway 18 and variable wind:** 4,289 VRB reports and 24 direction ranges make the 15 kt rule ambiguous. VRB hours with wind stay unlabelled (2,067 DFLD hours, 2024-12 to 2026-10). Labelling them usable is planned, not applied.
- **Threshold:** Fraport's public page describes a lower tailwind threshold for direction changes than the official brief's 10 kt or more. We use the brief's.

## Evaluation

Twelve expanding monthly folds, 2025-11 to 2026-10,
with six-hourly local issue times and no random train/test split. Training target
labels end before each test month. The feature dataset contains
194,352 rows; 74 issue
times lack required inputs. Stable-hour accuracy excludes transition-hour targets.
Each score below uses the same labelled rows for its compared methods.

Accuracy / Brier score (lower Brier is better):

| Lead | Scored rows | Served model | Official rules, base wind | Persistence | Rules, corrected ensemble |
|---|---:|---:|---:|---:|---:|
| 1 h | 1416 | 95.7% / 0.0341 | 93.1% / 0.0692 | 95.9% / 0.0410 | 93.3% / 0.0671 |
| 6 h | 1416 | 92.7% / 0.0530 | 88.1% / 0.1186 | 88.8% / 0.1116 | 88.8% / 0.1116 |
| 24 h | 1383 | 91.8% / 0.0637 | 87.7% / 0.1229 | 75.1% / 0.2495 | 89.2% / 0.1085 |
| 48 h | 1338 | 88.9% / 0.0818 | 84.0% / 0.1599 | 64.2% / 0.3580 | 85.8% / 0.1420 |

Paired 95% percentile intervals for model accuracy minus baseline, in percentage
points, using seven-day contiguous calendar blocks:

| Lead | Versus base-wind rules | Versus persistence | Versus ensemble rules |
|---|---:|---:|---:|
| 1 h | [+1.3, +4.3] | [-1.1, +0.6] | [+1.0, +4.2] |
| 6 h | [+2.7, +6.5] | [+1.3, +6.0] | [+2.2, +5.7] |
| 24 h | [+3.1, +6.3] | [+13.2, +20.6] | [+1.4, +4.8] |
| 48 h | [+3.5, +7.2] | [+19.6, +30.3] | [+1.6, +5.3] |

The JSON also contains one-day and three-day intervals. A block interval is
unavailable when any scored day is not covered by a complete contiguous block;
gaps are never bridged. Overlapping forecasts remain dependent. McNemar p-values
are nominal row-level results, DM uses daily losses with lag-one covariance,
and comparisons are not adjusted for multiplicity. These folds informed feature
choices and subsequent review: they are not an untouched final validation set.

Primary training and scoring retain all recorded OD labels. The rule-disagreement
flag marks 103 hours for sensitivity, not proven
feed failure. The requested training-policy comparison completed:
12 folds with identical training labels and
0 refitted folds. Identical-label folds reuse the exact same fit; they cannot
establish robustness to exclusions that never occurred in their training period.

Daily midnight October CLI issues provide a separate view: lead-one model
86.2%, rules 82.8%,
persistence 100.0%, n=29.
`web/public/data/cli-parity.csv` verifies all 45 features and both probabilities
against the training path for six saved dates and all 48 leads.

## Changes and rare runway-18 cases

First-change timing is direction-sensitive and uses actual half-hour state at
issue time. It scores 750 overlapping change windows:
27.2% within ±1 h and 52.5% within ±3 h.
False-alarm rate is 14.7% over 593
no-change windows, not the fraction of warnings that were false.
89 incomplete or invalid windows are excluded.

The separate unique-event view matches 115 of
193 actual transitions within ±3 h:
recall 59.6%, deduplicated precision 45.5%,
138 false-warning clusters across
358.5 covered days. Matching requires the warning to have been
issued before the event. A minimum-error assignment summarizes matched warning
lead; it does not measure earliest useful preparation time.

R18 outcomes are overlapping positive issue windows, **not unique closure episodes**.
Every target and compared prediction within the horizon must be known. Unknown
or variable METAR direction stays unlabelled. Method cells show **hits / false alarms**:

| Horizon | Complete windows | Positive windows | Model | Base rules | Persistence | Ensemble rules | Excluded windows |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 h | 1073 | 5 | 0 / 0 | 0 / 0 | 3 / 0 | 0 / 5 | 359 |
| 6 h | 760 | 10 | 0 / 0 | 0 / 0 | 3 / 0 | 0 / 16 | 672 |
| 24 h | 307 | 12 | 0 / 0 | 0 / 0 | 3 / 0 | 0 / 10 | 1125 |

Rare positive windows and inferred labels do not establish operational closure
forecasting skill. DFLD runway-18 non-use is not equivalent to a weather closure.
Permutation drivers for the final held-out month: dp_ns, od_at_issue, ens_tailwind_25_mean, ecmwf_ifs025_tailwind_25, geo_tailwind_25.

## Prior work and next experiments

- Zinkhan et al. (2023), DWD Offenbach with a university group: "Intrinsic Explainable Self-Enforcing Networks Using the ICON-D2-Ensemble Prediction System for Runway Configurations", *Engineering Proceedings* 39, 41 (CC BY). This is related work, not a benchmark: it shows one illustrative 15 h case at FRA with no backtest score and no calibration, and its text uses COSMO-DE-EPS although the title names ICON-D2. Review: Luca Schultz, `weather database/models/NOTES.md` (commit 0c8f4da on his branch).
- Puranik et al. (2023), NASA Ames: "Predicting airport runway configurations for decision-support using supervised learning". This is a method reference for METAR-derived features. Their 93.9% (CLT) and 73.5% (DEN) predict the configuration only **15 minutes** ahead, on a **random 80:20 split**, against baselines of 81.6% and 53.7%. That is not comparable to our 6–48 h chronological walk-forward.

**Next (not yet tested):**
- ICON-D2 ensemble spread as a *candidate* certainty feature. Zinkhan et al. motivate it, but Open-Meteo has no ensemble archive before 29 Jul 2026, so it cannot support this twelve-month comparison.
- A wind correction conditional on direction and regime, for runway 18.
- No cost per direction change is claimed: that needs FRA operations data.


## Reproduce

```bash
python -m pip install -r ml/requirements.txt
python -m pytest ml/tests -q
python -m ml.train --months 12 --compare-label-policy
python -m ml.forecast --day 2026-10-31
```

Future-day requests retain the complete current 48-hour forecast and state the
actual issue time. Results and exclusions are in `web/public/data/quality.json`;
implementation details and input contracts are in `ml/README.md`.
