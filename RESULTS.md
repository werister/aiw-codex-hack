# Results: what we achieved and what it means

Source of every number: `web/public/data/quality.json` (walk-forward-v5) on main, 30 Oct about 14:05. It uses 12 monthly test folds, Nov 2025 to Oct 2026, never seen in training. Truth is the operating direction actually flown, recorded by DFLD. Each forecast only uses information available at its issue time, including a 6 h publication lag for weather-model runs. The 95% intervals come from resampling whole days. If `quality.json` changes after the 15:30 model update, that file wins.

## In plain words

> - **About a third fewer mistakes than the official rules,** at 24 and 48 hours.
> - **About three times fewer mistakes than "same as now"** 48 hours ahead.
> - **The certainty number is about twice as reliable as the rules'.** When the model says "85% sure", that's much closer to reality.
>
> **How significant:** it was tested on 12 months that the model never saw, about 350 days and around 1,400 forecasts per horizon. For 6, 24 and 48 hours, the range for our lead never touches zero. The chance that this is luck is below 1 in 1,000.

"The rules" means FraAlliance's official rulebook applied to the weather forecast for each hour. "Same as now" means assuming the direction flown now is still flown later.

## The five numbers that matter

1. **89.2% correct 48 h ahead**, against 84.0% for the official rules and 64.2% for "same as now". That's +5.2 points over the rules [95% CI +3.2 to +7.1] and +25.0 over persistence.
2. **91.7% correct 24 h ahead**, against 87.7% for the rules and 75.1% for persistence: +4.0 over the rules [+2.4 to +5.6] and +16.6 over persistence [+13.4 to +19.6].
3. **About 50% better probabilities than the rules at every lead from 6 to 48 h.** Brier score 0.053 vs 0.119 at 6 h, 0.063 vs 0.123 at 24 h, 0.082 vs 0.160 at 48 h. The certainty score means something.
4. **82 to 83% of real direction changes are seen 24 to 48 h ahead.** "Same as now" sees 28 to 34%, and the rules 80%.
5. **Significant at every lead from 6 to 48 h,** against both baselines. McNemar and Diebold-Mariano both give p < 0.001.

## Full table (operating direction, held-out)

| lead | our model | official rules | same as now | gain vs rules [95% CI] | gain vs persistence [95% CI] | Brier model / rules |
|---|---|---|---|---|---|---|
| 1 h | 96.0% | 95.9% | 95.9% | +0.1 [−0.6, +0.8], a tie | +0.1, a tie | 0.035 / 0.041 |
| 6 h | **92.8%** | 88.1% | 88.8% | **+4.7 [+2.9, +6.4]** | **+4.0 [+2.1, +5.6]** | 0.053 / 0.119 |
| 24 h | **91.7%** | 87.7% | 75.1% | **+4.0 [+2.4, +5.6]** | **+16.6 [+13.4, +19.6]** | 0.063 / 0.123 |
| 48 h | **89.2%** | 84.0% | 64.2% | **+5.2 [+3.2, +7.1]** | **+25.0 [+21.1, +29.0]** | 0.082 / 0.160 |

Each lead has about 1,340 to 1,420 forecasts over about 350 test days.

**Direction changes caught** (hours where the flown direction differs from the direction at issue time):

| lead | model | rules | persistence |
|---|---|---|---|
| 6 h | 62% | **76%** | 11% |
| 24 h | **82%** | 80% | 28% |
| 48 h | **83%** | 80% | 34% |

**Next-change timing:** within ±1 h in 28% of change windows and within ±3 h in 53%. The false alarm rate is 13%, and the mean timing error is 5.3 h.

## What it means

- **For planning 1 to 2 days ahead, the forecast is clearly better than what exists today.** "Same as now" is wrong a quarter to a third of the time at 24 to 48 h. Our model is wrong about 1 in 10 to 1 in 12 times, and it beats the official rules applied to the same weather forecast.
- **The biggest practical gain is how sure we are, not only right or wrong.** Our probabilities are about twice as accurate as the rules' (Brier). A planner can act on "85% east from 14:00" and wait on "55%". That's what the certainty score in the app is for.
- **At very short range, the direction now is already a strong forecast.** At 1 h every method ties, so we don't claim a gain there. At 6 h the rules still catch more changes (76% vs 62%), although our overall accuracy and probabilities are better.
- **Timing is the weakest part.** We usually see that a change is coming, but the exact hour is only within ±3 h about half the time.
- **Runway 18 is not a strength yet.** No public record of weather closures exists, so its labels are inferred from METAR and the 15 kt rule. That covers about 0.2% of hours. The model catches 3 of 24 closure events at 24 h, with no false alarms; the rules on raw forecast wind catch none. Don't quote runway 18 accuracy as a result.

## How it was tested (why the numbers are honest)

- **Expanding monthly walk-forward:** train on everything before a month, test on that month, repeat for 12 months. There's no random cross-validation.
- **Only information available at issue time:** archived forecast runs with a 6 h publication lag, and recorded directions only after their hour ended.
- **Baselines on identical rows:** the official rules on the same forecast wind, and persistence.
- **Intervals and tests:** day-resampled 95% intervals, plus McNemar on accuracy and Diebold-Mariano on Brier.
- **Sensitivity:** `quality.json` also reports scores with the stuck-feed hours of 8 to 12 Oct excluded (`out_of_sample_stuck_feed_excluded`). The headline numbers above include all recorded hours.

Details: `MODEL_CARD.md`, `EXPERIMENTS.md`, `briefing/weather-database-review-response.md` (reviewer cautions).

## Economic value (illustrative estimate)

**This is an illustrative estimate from public unit costs, not measured FRA savings.** No public source gives a cost per operating-direction change at FRA. Every FRA-specific number below is either an assumption (marked *A*) or one of our own results.

### Inputs

| Input | Value | Source |
|---|---|---|
| Airline cost of tactical delay, incl. knock-on (at gate, 2022 €) | €45/min for delays under 30 min; €166/min across all delays | [EUROCONTROL Standard Inputs 10.0.2, cost of delay](https://ansperformance.eu/economics/cba/standard-inputs/latest/chapters/cost_of_delay.html) |
| Network average cost of ATFM delay | €100/min ("a high-level average… use with considerable caution") | same; [Univ. of Westminster v4.1, Table 30](https://www.eurocontrol.int/sites/default/files/publication/files/european-airline-delay-cost-reference-values-final-report-4-1.pdf) |
| Airline hard cost per delayed passenger (rebooking, care, compensation), 2010 € | €52 / €173 / €525 per misconnected passenger (2 h / 3 h / 5 h) | [Westminster v4.1, Table 17](https://www.eurocontrol.int/sites/default/files/publication/files/european-airline-delay-cost-reference-values-final-report-4-1.pdf) |
| EU261 | €250/400/600, but weather counts as an extraordinary circumstance, so compensation is usually not owed. Care and rerouting are still owed. | [Your Europe, air passenger rights](https://europa.eu/youreurope/citizens/travel/passenger-rights/air/index_en.htm) |
| Throughput loss around a direction change (Singapore Changi, one day with 10 changes) | Throughput drops 10–15 min before the change. Losses run from 3–6 movements/h for 30–45 min up to 8–15 movements/h for 45–60 min. Planned metering cut overload by 81% in simulation. | [Asadi, Enea, Alam, Schultz, SESAR Innovation Days 2025](https://www.unibw.de/lvk-en/publications/2025_implications_of_runway_direction_changes) |
| Value of better configuration decisions | 20–30% congestion-cost saving against heuristics that mimic practice (JFK model) | [Jacquillat, Odoni, Webster 2017](https://dspace.mit.edu/handle/1721.1/102975) |
| Lead time ATC needs | 10–15 min is enough to reschedule arrivals, so the 24–48 h value lies in planning (rosters, equipment, buffers, connections), not in the tower | [Zelinski, NASA/AIAA 2014](https://ntrs.nasa.gov/api/citations/20180004219/downloads/20180004219.pdf) |
| Benchmark | Best entry in NASA's US configuration challenge caught 41% of changes 2 h ahead, at 49% precision | [NASA challenge](https://www.drivendata.org/competitions/89/competition-nasa-airport-configuration/) |
| Prior work at FRA | The national weather service already built a probabilistic wind forecast and decision support for the FRA direction choice | [DWD, DACH 2019](https://meetingorganizer.copernicus.org/DACH2019/DACH2019-189.pdf) |

### Scenario (per year, 24 h lead, about 156 changes/yr)

Value per change: **V = D·s·c + M·p + H·w**

| Term | Low | Mid | High |
|---|---|---|---|
| D: aircraft delay minutes per change (*A*, scaled from Changi) | 50 | 200 | 600 |
| s: share of D avoidable with 24 h notice (*A*; 81% from Changi is the ceiling) | 10% | 25% | 50% |
| c: €/min | 45 | 100 | 166 |
| M: misconnections avoided per change (*A*) × p: €/passenger | 0 × 52 | 10 × 173 | 40 × 525 |
| H: handling staff-hours saved (*A*) × w: €40/h (*A*) | 0 | 20 h | 60 h |
| **V per change** | **€225** | **€7,530** | **€73,200** |
| **A. vs persistence:** 156 × (0.82 − 0.28) = **84 more changes anticipated** × V | €19k | **€0.63M** | €6.1M |
| B1. vs rules: 156 × (0.82 − 0.80) = 3 more changes anticipated × V | €0.7k | €23k | €220k |
| B2. vs rules: 8,760 h × (0.917 − 0.877) = **350 fewer hours planned for the wrong direction** × €50 / €200 / €1,000 per hour (*A*) | €18k | €70k | €350k |
| **B. vs rules, total** | **≈€18k** | **≈€93k** | **≈€570k** |

At 48 h the picture is similar: 76 more changes anticipated than persistence, about 5 more than the rules, and about 455 fewer wrong-direction hours.

### What this means

- **Against "assume nothing changes",** 24 h foresight is worth about **€0.6M a year** in the central case. The range runs from €19k to €6M because nobody has published what one FRA change costs.
- **Against the official rules on the same forecast,** the central case is about **€0.1M a year**. About three quarters comes from better-calibrated probabilities, roughly 350 fewer hours a year planned for the wrong direction, not from extra changes caught.
- **The realistic baseline sits in between.** FRA already uses weather forecasts and decision support, so the rules comparison is the honest, conservative number.
- **The value comes from planning:** rosters, equipment positioning, schedule buffers and protecting connections. ATC itself needs only minutes of notice.

### Caveats and data needed to measure it

- **Assumptions:** D, s, M, H and w are assumed. Changi is not FRA. EUROCONTROL's unit costs are indicators. Price years are mixed and not inflated. Weather delays usually trigger no EU261 compensation, so only hard costs are counted and passenger time is excluded.
- **At 6 h the rules catch more changes** (76% vs 62%), so use the rules at short lead and the model at 24–48 h. No value is claimed for runway 18.
- **False alarms** (about 20 a year) would reduce scenario A by €0 / €16k / €48k. This deduction is not applied above.
- **Threshold mismatch:** the airport's public page describes a lower tailwind threshold than the official brief (≥10 kt). We use the brief.
- **Data needed for the real saving:**
  - time-stamped direction changes, with decision and announcement times
  - hourly demand and capacity per direction
  - flight-level delay by cause around each change
  - hourly misconnection counts from hub control
  - handling rosters and equipment moves on change days
  - a comparison of change days with and without a 24 h warning

### Pitch lines

1. "Frankfurt changes operating direction about 156 times a year. 24 hours ahead, our model anticipates 82% of those changes, against 28% if you assume today's direction holds."
2. "Using EUROCONTROL's public delay costs and stated assumptions, that is worth an illustrative €0.1M a year against the official rules and €0.6M against no forecast, in central scenarios. This is an estimate, not a measured FRA saving."
3. "Compared with the official rules, it catches about as many changes, but its probabilities are about half as wrong. That means fewer hours planned for the wrong direction, and FraAlliance data would let us measure the real saving."
