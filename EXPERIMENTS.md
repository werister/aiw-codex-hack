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
- Expanding monthly walk-forward over 12 test months (2025-11 to 2026-10). Each month is predicted by a model trained only on earlier data, with issues at 00:00, 06:00, 12:00 and 18:00 local.
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
| E9 | Persistence blend by regime (night, calm, active) and lead; issues on the local clock from 00:00 (walk-forward-v4) | 6 test months, all recorded hours, model / rules / persistence: 1 h 94.6 / 95.2 / 95.2, 6 h 90.7 / 86.3 / 88.3, 24 h 89.6 / 86.3 / 76.3, 48 h 84.9 / 82.5 / 65.9%. October midnight issues at 1–6 h: 83.6 vs persistence 95.3% on all hours, 95.9 vs 94.6% without the stuck feed (E9b). |
| E9b | Stuck DFLD feed: OD 07 from 8 Oct 12:00 to 12 Oct 18:00 local against 8–17 kt westerlies (METAR and DWD 01420) | The only recorded run in 2018–2026 with 3+ hours over the 10 kt landing limit (103 h). Left out of fitting; every score is reported with and without it. |
| E10 | Separate-model forecasts (ECMWF IFS, GFS, ICON previous runs) as features: per-runway tailwinds scaled to METAR level, ensemble mean and spread, direction spread, model votes, rules rerun on the corrected ensemble wind | Biggest gain. Same 12 test months: 48 h 84.9 → 88.6%, Brier 0.108 → 0.084. |
| E11 | Correcting forecast wind to METAR for runway 18 (METAR / forecast mean speed, fitted on 2024 only: best match ×1.68, ECMWF ×1.27, GFS ×1.34, ICON ×1.68, 80 m ×0.83) | Rules on the raw forecast wind never close 18 in the 12 test months. Issue-level closure events (any inferred closure within H): 5 / 12 / 24 events at 1 / 6 / 24 h. Model hits 0 / 1 / 3 with 0 false alarms, persistence 3 / 3 / 3, rules 0. Too few events to claim skill. |
| E12 | Final model walk-forward-v5: base + E10 + E13, regime blend, 12 test months (Nov 2025 – Oct 2026) | See the table below. Beats rules and persistence at 6, 24 and 48 h with p < 1e-5 on both tests. 1 h is a tie. |
| E13 | Forecast pressure about 200 km N, S, W and E of FRA (north-south and east-west differences, geostrophic tailwind on 25 and 18) | +0.1 to +0.6 points over E10 alone. 2nd driver after the ensemble tailwind. |
| E14 | Tried without gain on the same folds: deeper trees (300 iterations, 31 leaves), monotonic constraints on tailwinds, separate models per lead bucket, observation-state features (tailwind on the current direction and its duration) | Within ±0.6 points, Brier equal or worse. Not adopted. |
| E15 | ICON-D2 ensemble spread (Zinkhan et al. 2023, DWD) | Open-Meteo has no ensemble archive before 29 Jul 2026, so it cannot be backtested. Not used. |
| E16 | Rules rerun on the corrected ensemble wind as a stronger baseline | 95.6 / 88.8 / 89.2 / 85.8% at 1 / 6 / 24 / 48 h. The model still leads by 4.0 / 2.5 / 3.4 points at 6 / 24 / 48 h. |

### E12 before / after (12 walk-forward test months, all recorded hours)

Before is the E9 feature set on the same folds. 95% CIs resample issue days (346–361 days). p-values: McNemar on accuracy, Diebold-Mariano on daily Brier differences.

| Lead | Before acc / Brier | After acc [95% CI] | After Brier | Rules acc / Brier | Persistence acc / Brier | After − rules [CI], McNemar p, DM p | After − persistence [CI], McNemar p, DM p | Changes caught (model / rules / persistence) |
|---|---|---|---|---|---|---|---|---|
| 1 h | 95.5 / 0.039 | 96.0 [95.0–97.0] | 0.035 | 95.9 / 0.041 | 95.9 / 0.041 | +0.1 [−0.6–0.8], 1.0, 0.1 | +0.1 [−0.6–0.8], 1.0, 0.1 | 21 / 0 / 0% (n=58) |
| 6 h | 92.0 / 0.060 | 92.8 [90.9–94.5] | 0.053 | 88.1 / 0.119 | 88.8 / 0.112 | +4.7 [2.9–6.4], 2e-7, 1e-15 | +4.0 [2.1–5.6], 1e-6, 5e-10 | 62 / 76 / 11% (n=178) |
| 24 h | 90.3 / 0.079 | 91.7 [89.7–93.5] | 0.063 | 87.7 / 0.123 | 75.1 / 0.249 | +4.0 [2.4–5.6], 2e-6, 3e-13 | +16.6 [13.4–19.6], 3e-36, 5e-25 | 82 / 80 / 28% (n=480) |
| 48 h | 84.9 / 0.108 | 89.2 [87.0–91.2] | 0.082 | 84.0 / 0.160 | 64.2 / 0.358 | +5.2 [3.2–7.1], 5e-8, 2e-14 | +25.0 [21.1–29.0], 3e-55, 3e-31 | 83 / 80 / 34% (n=727) |

Without the 8–12 Oct stuck feed (E9b): model 96.4 / 94.1 / 93.0 / 90.4%, rules 95.9 / 89.3 / 89.0 / 85.2%, persistence 95.9 / 88.9 / 75.2 / 64.4% at 1 / 6 / 24 / 48 h. Margins: +4.7 / +4.0 / +5.2 over the rules and +5.2 / +17.8 / +26.0 over persistence at 6 / 24 / 48 h.

The +5-point target over both baselines is met at 48 h only. At 6 h and 24 h the margin over the rules is +4.7 and +4.0, and at 6 h over persistence +4.0 (+5.2 without the stuck feed). At 6 h the model catches fewer actual changes than the rules (62 vs 76%) but makes far fewer false switches.

## 5. Key drivers (current model)
Permutation importance on the final test month, walk-forward-v5:
1. ensemble-mean forecast tailwind on 25
2. north-south pressure difference
3. recorded direction at issue time
4. ECMWF tailwind on 25
5. official rules rerun on the corrected ensemble wind
6. geostrophic tailwind on 25
7. lead time
8. observed tailwind on 25 now

## 6. Open limits
- Runway 18 has no public closure history, so its labels are inferred from METAR with the official rule (28 events 2024–2026).
- DFLD is a public proxy for the flown direction. Change hours are excluded from stable-hour accuracy, and the summer clock offset is unverified.
- Forecast-run publication times are not published; the 6 h lag is a conservative assumption.
