# Data, model and experiments

What we train on, which model we use, and every experiment so far with its result. The one-page summary for the jury is `MODEL_CARD.md`. The live numbers are in `web/public/data/quality.json` and `backtest.json`.

## 1. Data we train on

| What | Source | Rows | Period | Role |
|---|---|---|---|---|
| Recorded operating direction, half-hourly | DFLD.de monthly pages (`ml/dfld.py`) | 76,588 stable hours | 2018-01 to 2026-10-29 | Label for OD; state at issue time |
| Recorded runway-18 in use | DFLD.de, same pages | 28,140 hours | 2018-01 onward | Checked as a label, rejected (see E8) |
| EDDF METAR (wind, gusts) | Iowa Environmental Mesonet | 154,718 reports | 2018-01 to 2026-10-30 | Observed wind at issue time; inferred runway-18 label |
| Wind forecasts as issued 1, 2 and 3 days earlier | Open-Meteo Previous Runs API | about 24,800 hours | 2024-01 onward | Forecast features |
| Multi-model forecasts (ECMWF, GFS, ICON) | Open-Meteo Previous Runs API | fetching | 2024-01 onward | Model-disagreement features (E10) |
| Official rules | FraAlliance brief, `ml/rules.json` | n/a | n/a | Baseline and a feature |

**Not used:**
- flight schedules and delays: wind decides the direction, and no hourly FRA demand data is public;
- US BTS delay data: useful context for the pitch, but not FRA data.

## 2. Model
- Gradient-boosted trees (scikit-learn `HistGradientBoostingClassifier`): one classifier for P(OD 25), one for P(runway 18 usable).
- One training row = (issue time T, lead h). Issues every 6 h, leads 1 to 48, about 194,000 rows on the 2024+ forecast period.
- Features use only data known at T: the recorded OD at T, hours since the last change, METAR wind and tailwinds with their 3 h trend, the forecast for the target hour, the official rules run forward on the forecast wind, hour, season and lead.
- Why trees: tabular data with threshold-shaped decisions (10 kt, 15 kt, 30 min). They train in seconds, give probabilities, and are explainable through permutation importance. A neural network would need far more data.

## 3. Evaluation protocol
- Expanding monthly walk-forward. Each test month (2026-05 to 2026-10) is predicted by a model trained only on earlier data.
- Forecast runs count as available 6 h after their nominal issue: day 1 for leads 1–18 h, day 2 for 19–42 h, day 3 for 43–48 h.
- Baselines:
  - **official rules:** the FraAlliance state machine run on the forecast wind, starting from the recorded state at T;
  - **persistence:** keep the state at T.
- Metrics: accuracy and Brier score at 1, 6, 24 and 48 h; accuracy on hours with a change ("changes caught"); next-change timing; calibration.

## 4. Experiments and results

| # | Experiment | Result |
|---|---|---|
| E1 | Official rules on observed METAR vs recorded direction | Agree in **89.2%** of hours. The rules are a baseline, not the truth. |
| E2 | First model (no persistence blend, no publication lag) | 1/6/24/48 h: 93.8 / 91.5 / 90.8 / 89.8%. **Lost at 1 h** to rules and persistence (96.9%). |
| E3 | Persistence blend per lead, weights chosen on training data | 1 h fixed: 96.9%. Others unchanged. |
| E4 | Six-hour publication lag plus day-3 forecasts (closing a leak at 19–24 h and 43–48 h) | 1/6/24/48 h: **97.0 / 91.5 / 90.3 / 84.1%**. 48 h dropped from 89.8%: the honest number. Current model. |
| E5 | CLI path vs training path on 3 October days, 144 lead rows | Identical features and probabilities. |
| E6 | Daily forecasts issued at local midnight for October 2026 (as for the jury days) | Model 84.2 / 79.0 / 75.7% vs rules 71.9 / 77.3 / 70.2% at 1–6 / 7–24 / 25–48 h. **Persistence wins at 1–6 h** (95.3%). |
| E7 | Labels and METAR extended back to 2018 | 76,588 labelled hours (3× more), about 3× more direction changes. Retraining in progress. |
| E8 | DFLD runway-18 "not in use" as a closure label | Rejected: only 1 of 2,251 non-use hours had a tailwind of 15 kt or more, so it reflects operations, not weather. |
| E9 | Persistence blend by regime (night, calm, active) and lead, for midnight issues | In progress; target is to match persistence at 1–6 h in E6. Scores will be reported with and without the excluded 8–12 Oct stuck-feed hours. |
| E10 | Multi-model forecast disagreement (ECMWF, GFS, ICON) as features | Data fetch in progress. |
| E11 | Correcting forecast wind to METAR (forecast 10 m is about 0.59× METAR) for runway 18 | In progress. Runway 18 is scored as closure events over 2018–2026. |

## 5. Key drivers (current model)
1. recorded direction at issue time
2. 80 m forecast wind speed
3. forecast tailwind on 07
4. forecast tailwind on 18
5. lead time
6. hour of day
7. gusts

## 6. Open limits
- Runway 18 has no public closure history, so its labels are inferred from METAR with the official rule (28 events 2024–2026).
- DFLD is a public proxy for the flown direction. Change hours are excluded from stable-hour accuracy, and the summer clock offset is unverified.
- Forecast-run publication times are not published; the 6 h lag is a conservative assumption.
