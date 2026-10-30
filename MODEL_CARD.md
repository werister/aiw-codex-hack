# Model card · FRA operating direction and runway 18, 48 h ahead

**What it predicts.** For each hour up to 48 h after an issue time, the forecast gives:
- the probability that Frankfurt operates in direction 25 (west) rather than 07 (east)
- the probability that runway 18 is usable for departures
- a certainty score: `100 × min(|2·p_od25 − 1|, |2·p_18 − 1|)`
- the next likely direction change, with a time window

**Intended use:** planning support for tower, apron and ground-handling staff (FraAlliance challenge). It is not an operational instruction: DFS decides the operating direction.

## Data (all public, no account needed)
| Source | Used for | Period |
|---|---|---|
| DFLD.de recorded operating direction, half-hourly ([monthly page](https://www.dfld.de/Mess/StatWetter.php?R=1&D=01.10.2026)) | **Label** (what was flown) and the state at issue time | 2018-01 to 2026-10 (76,588 hours) |
| EDDF METAR, Iowa Environmental Mesonet ([archive](https://mesonet.agron.iastate.edu/request/download.phtml)) | Observed wind at issue time; inferred runway-18 label | 2018-01 to 2026-10 |
| Open-Meteo Previous Runs API ([docs](https://open-meteo.com/en/docs/previous-runs-api)): ECMWF IFS, GFS and ICON separately, plus pressure at four points about 200 km N, S, E and W of FRA | Wind and pressure forecasts **as issued** 1, 2 and 3 days earlier | 2024-01 to 2026-10 |
| FraAlliance official rules (`ml/rules.json`) | Baseline and stacked feature | n/a |

Details: `data/README.md`, `data/ground_truth/README.md`, `DATA_AND_DECISIONS.md`.

## Model (walk-forward-v5)
Gradient-boosted decision trees (scikit-learn `HistGradientBoostingClassifier`), one for the operating direction and one for runway 18. Lead time is an input. At short leads the output is blended with persistence by horizon × regime (night, calm, active), with weights chosen on inner validation data only.

Inputs at issue time T (only what was known at T):
- the recorded direction and hours since the last change
- METAR wind, gusts and tailwinds
- per-model forecast tailwind on 25, 07 and 18, corrected to the airport sensor
- ensemble mean and spread across the three weather models
- north-south and east-west pressure differences
- the official rules run as a state machine on the corrected ensemble wind
- hour, season and lead

## Evaluation
- **Method:** expanding monthly walk-forward over **12 months the model never trained on** (2025-11 to 2026-10). Forecast runs count as available 6 h after their start (day 1 for leads 1–18 h, day 2 for 19–42 h, day 3 for 43–48 h). No random cross-validation.
- **Statistics:** 95% confidence intervals by bootstrap over days. McNemar test on accuracy, Diebold-Mariano on Brier.
- **CLI parity:** the CLI and the training path match exactly (`web/public/data/cli-parity.csv`).

Operating direction, all recorded hours (accuracy [95% CI], Brier):

| Lead | Model | Official rules | Persistence | Model − rules | Model − persistence |
|---|---|---|---|---|---|
| 1 h | **96.0%** [95.0–97.0], 0.035 | 95.9%, 0.041 | 95.9%, 0.041 | +0.1 (n.s.) | +0.1 (n.s.) |
| 6 h | **92.8%** [90.9–94.5], 0.053 | 88.1%, 0.119 | 88.8%, 0.112 | +4.7, p < 10⁻⁶ | +4.0, p < 10⁻⁵ |
| 24 h | **91.7%** [89.7–93.5], 0.063 | 87.7%, 0.123 | 75.1%, 0.249 | +4.0, p < 10⁻⁵ | +16.6, p < 10⁻²⁴ |
| 48 h | **89.2%** [87.0–91.2], 0.082 | 84.0%, 0.160 | 64.2%, 0.358 | +5.2, p < 10⁻⁷ | +25.0, p < 10⁻³⁰ |

- **Stuck feed:** DFLD shows 07 for 103 h on 8–12 Oct against steady westerlies, confirmed by DWD station data. With those hours excluded, the model scores 96.4 / 94.1 / 93.0 / 90.4% (rules 95.9 / 89.3 / 89.0 / 85.2%).
- **Direction changes:** at 24 h the model catches 82% of hours with a change (rules 80%, persistence 28%). Next-change timing lands within ±3 h in 53% of cases (28% within ±1 h), with a 13% false-alarm rate.
- **The rules alone:** on observed METAR wind they agree with the recorded direction in 89.9% of hours.

**Key drivers** (permutation importance):
- ensemble-mean forecast tailwind on 25
- north-south pressure difference
- direction at issue time
- ECMWF tailwind on 25
- the official rules on the ensemble wind
- lead time
- observed tailwind on 25

## Limitations
- **Runway 18 is weak.** No public record of weather closures exists, so its label is inferred from METAR with the official 15 kt rule, which applies to about 0.2% of hours. In the 12 test months the model catches 3 of 24 closure events at 24 h with no false alarms. The rules on raw forecast wind catch none. DFLD's runway-18 "not in use" row is operational, not weather: only 1 of 2,251 such hours had a tailwind of 15 kt or more.
- **Wind bias:** the forecast 10 m wind averages 0.59× the METAR wind at the airport. It is corrected on training folds before computing tailwinds.
- **Label quality:** DFLD is a public proxy, not a certified movement log. Hours containing a change are excluded from the stable-hour accuracy, and the summer clock offset is unverified.

**Prior work:**
- Zinkhan et al. (2023), DWD Offenbach with a university group: "Intrinsic Explainable Self-Enforcing Networks Using the ICON-D2-Ensemble Prediction System for Runway Configurations", *Engineering Proceedings* 39, 41 (CC BY). They forecast FRA's runway configuration from ensemble weather forecasts.
- Puranik et al. (2023), NASA Ames: "Predicting airport runway configurations for decision-support using supervised learning". METAR-derived features, 93% accuracy at CLT and 73% at DEN.

**Reproduce:** `python -m pip install -r ml/requirements.txt`, `python -m ml.train`, then `python -m ml.forecast --day YYYY-MM-DD`.
