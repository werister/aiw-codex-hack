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
| Open-Meteo Previous Runs API ([docs](https://open-meteo.com/en/docs/previous-runs-api)) | Wind forecasts **as issued** 1, 2 and 3 days earlier | 2024-01 to 2026-10 |
| FraAlliance official rules (`ml/rules.json`) | Baseline and one input feature | n/a |

Details: `data/README.md`, `data/ground_truth/README.md`, `DATA_AND_DECISIONS.md`.

## Model
Gradient-boosted decision trees (scikit-learn `HistGradientBoostingClassifier`), one for the operating direction and one for runway 18. Lead time is an input. At short leads the output is blended with persistence ("keep the current direction"), with blend weights chosen on training data only.

Inputs at issue time T (only what was known at T):
- the recorded direction and hours since the last change
- METAR wind, gusts and tailwinds, with their 3 h trend
- forecast wind, gusts, 80 m wind, pressure and temperature
- forecast tailwind on 25, 07 and 18
- the official rules run forward on the forecast wind
- hour, season and lead

## Evaluation
- **Method:** expanding monthly walk-forward over six months the model never trained on (2026-05 to 2026-10).
- **Publication lag:** forecast runs count as available only 6 h after their nominal issue (day 1 for leads 1–18 h, day 2 for 19–42 h, day 3 for 43–48 h).
- **CLI parity:** the CLI and the training path give identical features and probabilities (`web/public/data/cli-parity.csv`).

Operating direction, accuracy on held-out hours (Brier score in brackets):

| Lead | Model | Official rules | Persistence |
|---|---|---|---|
| 1 h | **97.0%** (0.029) | 96.9% (0.031) | 96.9% (0.031) |
| 6 h | **91.5%** (0.060) | 85.9% (0.141) | 89.0% (0.110) |
| 24 h | **90.3%** (0.082) | 86.8% (0.132) | 76.7% (0.233) |
| 48 h | **84.1%** (0.114) | 83.1% (0.169) | 66.6% (0.334) |

- **Issued at local midnight, like the jury days** (October 2026, 29 days): the model beats the rules at every lead, 84.2 / 79.0 / 75.7% vs 71.9 / 77.3 / 70.2% at 1–6 / 7–24 / 25–48 h. Persistence is better at 1–6 h (95.3%), and the short-lead blend for night and calm hours is being tuned.
- **Direction changes:** 54% of real changes are timed within ±3 h (29% within ±1 h), with a 27% false-alarm rate.
- **Calibration:** stated probabilities match observed frequencies (the reliability chart is in the app).
- **The rules alone:** the official rules on observed METAR wind agree with the recorded direction in 89.2% of hours.

**Key drivers** (permutation importance): direction at issue time, 80 m forecast wind, forecast tailwind on 07 and on 18, lead time, hour of day, gusts.

## Limitations
- **Runway 18 is not scored yet.** No public record of weather closures exists. Its label is inferred from METAR with the official 15 kt rule (0.2% of hours, 28 events 2024–2026, one in the test months). DFLD's runway-18 "not in use" row is operational, not weather: only 1 of 2,251 such hours had a tailwind of 15 kt or more.
- **Wind bias:** the forecast 10 m wind averages 0.59× the METAR wind at the airport. A correction is in progress.
- **Label quality:** DFLD is a public proxy, not a certified movement log. Hours containing a change are excluded from the stable-hour accuracy, and the summer clock offset is unverified.

**Reproduce:** `python -m pip install -r ml/requirements.txt`, `python -m ml.train`, then `python -m ml.forecast --day YYYY-MM-DD`.
