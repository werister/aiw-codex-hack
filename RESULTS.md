# Results: what we achieved and what it means

Source of every number: `web/public/data/quality.json` (walk-forward-v6) on main. It uses 12 monthly test folds, Nov 2025 to Oct 2026: each month is predicted by a model trained only on earlier data, but these months informed development choices, so they are not an untouched final test. Truth is the recorded operating direction from DFLD, a public proxy for what was flown. Each forecast only uses information available at its issue time, including an assumed 6 h publication lag for weather-model runs. The 95% intervals resample seven-day calendar blocks. If `quality.json` changes, that file wins.

## In plain words

> - **About a third fewer wrong hours than the official rules,** at 24 and 48 hours.
> - **About three times fewer wrong hours than "same as now"** at 24 and 48 hours.
> - **Probabilities about twice as good as the rules',** measured by the Brier score.
> - **Weak spots:** the exact time of a change, and runway 18.
>
> **How significant:** about 350 test days and around 1,400 forecasts per horizon. For 6, 24 and 48 hours, the interval for our lead never touches zero. The p-values are nominal and not adjusted for multiple comparisons.

"The rules" means FraAlliance's official rulebook applied to the weather forecast for each hour. "Same as now" means assuming the direction recorded now still holds later.

## The numbers that matter

1. **88.9% correct 48 h ahead**, against 84.0% for the official rules and 64.2% for "same as now": +4.9 points over the rules [95% CI +3.5 to +7.2] and +24.7 over persistence [+19.6 to +30.3].
2. **91.8% correct 24 h ahead**, against 87.7% for the rules and 75.1% for persistence: +4.1 over the rules [+3.1 to +6.3] and +16.8 over persistence [+13.2 to +20.6].
3. **About half the probability error of the rules at every lead.** Brier score 0.034 vs 0.069 at 1 h, 0.053 vs 0.119 at 6 h, 0.064 vs 0.123 at 24 h, 0.082 vs 0.160 at 48 h. In the 80 to 90% band (mean 85.9%) the direction occurs 88.6% of the time. The certainty score is a separate ranking, not a calibrated probability.
4. **115 of 193 unique direction changes are matched within ±3 h** (59.6%), with 138 false-warning clusters over about 358 days.
5. **No proven skill on runway 18:** 0 of 12 positive windows at 24 h.

## Full table (operating direction, held-out)

| lead | our model | official rules | same as now | gain vs rules [95% CI] | gain vs persistence [95% CI] | Brier model / rules |
|---|---|---|---|---|---|---|
| 1 h | 95.7% | 93.1% | 95.9% | **+2.6 [+1.3, +4.3]** | −0.2 [−1.1, +0.6], a tie | 0.034 / 0.069 |
| 6 h | **92.7%** | 88.1% | 88.8% | **+4.6 [+2.7, +6.5]** | **+3.9 [+1.3, +6.0]** | 0.053 / 0.119 |
| 24 h | **91.8%** | 87.7% | 75.1% | **+4.1 [+3.1, +6.3]** | **+16.8 [+13.2, +20.6]** | 0.064 / 0.123 |
| 48 h | **88.9%** | 84.0% | 64.2% | **+4.9 [+3.5, +7.2]** | **+24.7 [+19.6, +30.3]** | 0.082 / 0.160 |

Each lead has 1,338 to 1,416 forecasts over about 350 test days. Against the stronger rule baseline on corrected ensemble wind (93.3 / 88.8 / 89.2 / 85.8%), the model still leads at every lead.

**Target hours in windows containing a change** (the recorded direction differs from the direction at issue time). This measures the direction in those hours. It does not count how many individual changes were foreseen:

| lead | model | rules | persistence |
|---|---|---|---|
| 1 h | 19% | **29%** | 0% |
| 6 h | 62% | **76%** | 11% |
| 24 h | **82%** | 80% | 28% |
| 48 h | **83%** | 80% | 34% |

**Next-change timing** (750 overlapping change windows): within ±1 h in 27% and within ±3 h in 53%. The false alarm rate is 15% of 593 no-change windows, and the mean timing error is 5.4 h.

## What it means

- **For planning 1 to 2 days ahead, the forecast is clearly better than either simple reference.** "Same as now" is wrong a quarter to a third of the time at 24 to 48 h. Our model is wrong about 1 in 12 to 1 in 9 times, and it beats the official rules applied to the same weather forecast.
- **The biggest practical gain is how sure we are, not only right or wrong.** A planner can act on a high probability and wait on 55%. The app shows that probability alongside the certainty score.
- **At very short range, the direction now is already a strong forecast.** At 1 h persistence is level with the model, so we claim no gain over it there. At 6 h the rules still get more change-window hours right (76% vs 62%), although our overall accuracy and probabilities are better.
- **Timing is the weakest part of the direction forecast.** At the level of unique events, 4 in 10 changes are not matched within ±3 h, and fewer than half of the warning clusters match a real change (45.5%).
- **Runway 18 is not a strength.** No public record of weather closures exists, so its labels are inferred from METAR and the rules (about 0.3% of hours). At 24 h, 12 of 307 complete windows are positive; the model catches none and raises no false alarm, and 1,125 windows are excluded. Don't quote runway 18 accuracy as a result.

## How it was tested (why the numbers are credible)

- **Expanding monthly walk-forward:** train on everything before a month, test on that month, repeat for 12 months. There's no random cross-validation.
- **Only information available at issue time:** archived forecast runs with an assumed 6 h publication lag, explicit timestamps checked where they exist, and recorded directions only after their hour ended.
- **Baselines on identical rows:** the official rules on the same forecast wind, the rules on corrected ensemble wind, and persistence.
- **Intervals and tests:** seven-day block intervals, plus nominal McNemar on accuracy and Diebold-Mariano on Brier.
- **Sensitivity:** `quality.json` also reports scores with the 103 flagged hours of 8 to 12 Oct excluded (`out_of_sample_stuck_feed_excluded`): 96.1 / 94.0 / 93.2 / 90.2% at 1 / 6 / 24 / 48 h. The headline numbers above include all recorded hours.

Details: `MODEL_CARD.md`, `EXPERIMENTS.md`, `briefing/weather-database-review-response.md` (reviewer cautions).

## Economic value (estimate, FRA scale)

**Estimate based on EUROCONTROL delay costs and published studies of runway direction changes.** No public source gives a cost per direction change at FRA. *A* marks an assumption.

**Not yet reworked for v6.** This estimate assumes 156 changes a year (`quality.json`: about 173) and treats the 82% vs 28% change-window scores as changes foreseen, which they are not. Quote the euro figures only as a rough, assumption-driven order of magnitude until this is recalculated.

### Bottom line (FRA only, per year, airline and handling)

| | conservative | **central** | upside |
|---|---|---|---|
| Against the official rules (lower bound) | €0.13M | | |
| Realistic middle (planning mix) | | **€0.40M** | |
| Against "same as now" | | €0.62M | €3.2M |

- **Passengers' time** (societal) adds another €0.11M to €1.75M.
- **CO2** adds €5k to €0.25M.
- **At 48 h** lead, the figures are 10 to 17% lower.

### How it is calculated

1. **Delay caused by a direction change at FRA.**
   - Method: a direction change costs throughput (Changi: 3 to 15 movements an hour lost for 30 to 60 min), and waiting aircraft-minutes ≈ movements lost × minutes the backlog lasts.
   - Assumed day profile (*A*): changes spread evenly over the day, 6 peak hours at about 105 movements/h, 12 shoulder hours at about 52/h, nights empty.
   - Result: 105 / **270** / 540 primary delay minutes per change. ×1.5 to 1.85 for knock-on delays (EUROCONTROL: reactionary delay is 46% of delay minutes).
   - **The 39 peak-hour changes a year carry 83% of that delay.** That's where the value sits.
2. **Airline cost** of all change-related delay at €45 / **€100** / €166 per minute (EUROCONTROL Standard Inputs): **€0.74M / €4.2M / €14M a year**.
3. **Share avoidable with 24 h notice** (*A*): 10 / 25 / 40%. That's anchored on a 20 to 30% congestion-cost saving from better configuration control at JFK, with the 81% Changi simulation as the ceiling.
4. **Changes our forecast anticipates better:**
   - against "same as now": 84 more a year at 24 h (82% vs 28% of 156)
   - against the rules: about 350 fewer wrong-direction hours a year, the equivalent of about 18 changes. That's 19.4 wrong planning hours per missed change, derived from our own results.
5. **Which baseline applies where:**
   - 24 to 48 h rostering, equipment, stands and connection protection: planners largely plan as if nothing changes, so persistence applies (still to be verified).
   - Same-day switching by ATC: the official rules plus weather service support.
   - The central case splits the difference.

### Main sources

| Input | Source |
|---|---|
| Cost of delay €45 / €100 / €166 per min, knock-on factor | [EUROCONTROL Standard Inputs 10.0.2](https://ansperformance.eu/economics/cba/standard-inputs/latest/chapters/cost_of_delay.html), [Univ. of Westminster v4.1](https://www.eurocontrol.int/sites/default/files/publication/files/european-airline-delay-cost-reference-values-final-report-4-1.pdf), [CODA 2024](https://www.eurocontrol.int/publication/all-causes-delays-air-transport-europe-annual-2024) |
| Passenger value of time €22.89/h | [Standard Inputs ch. 42](https://ansperformance.eu/economics/cba/standard-inputs/latest/chapters/passenger_value_of_time.html) |
| Throughput loss around a direction change | [Asadi et al., SESAR Innovation Days 2025](https://www.unibw.de/lvk-en/publications/2025_implications_of_runway_direction_changes) |
| Value of better configuration decisions (20 to 30%) | [Jacquillat, Odoni, Webster 2017](https://dspace.mit.edu/handle/1721.1/102975) |
| Taxi fuel, CO2 factor and price | Westminster v4.1 Annex F; Standard Inputs [ch. 7](https://ansperformance.eu/economics/cba/standard-inputs/latest/chapters/amount_of_emissions_released_by_fuel_burn.html), [ch. 8](https://ansperformance.eu/economics/cba/standard-inputs/latest/chapters/cost_of_emissions.html) |
| FRA night rule (no scheduled movements 23 to 05) | [Hessen FAQ](https://wirtschaft.hessen.de/sites/wirtschaft.hessen.de/files/2021-07/18-08-29_faq_nachtfluege_online_0.pdf) |
| Prior FRA decision support by the national weather service | [DWD, DACH 2019](https://meetingorganizer.copernicus.org/DACH2019/DACH2019-189.pdf) |

### Caveats

- **Assumptions drive the result.** The time-of-day spread, lost movements, backlog duration, avoidable share and handling hours (*A*) can each move the result about 10×. The Changi evidence is a single day from 2019. EUROCONTROL unit costs are indicators, and price years are mixed.
- **The floor is very low:** about €2k a year if planners already use the rules and changes are cheap.
- **Not counted:** diversions past the night curfew, EU261 compensation (weather is usually exempt), hub-specific misconnections and business passengers' time.
- **Use both forecasts:** at 6 h the rules catch more changes (76% vs 62%). No value is claimed for runway 18.
- **Threshold check:** the airport's public page describes a lower tailwind threshold than the brief (≥10 kt). We use the brief.
- **Data needed to measure it for real:**
  - time-stamped changes (decided, announced, effective)
  - hourly demand and capacity per direction
  - delay by cause within ±3 h of each change
  - misconnections by hour
  - handling rosters and overtime
  - which 24 to 48 h decisions a warning would change

### Pitch lines

1. "Frankfurt changes direction about 170 times a year. 24 hours ahead, our model has the right direction in 82% of the hours around such changes, against 28% if planners assume today's direction holds."
2. "Estimated value: about €0.4M a year at Frankfurt (range €0.13M to €3.2M), plus a similar amount in passengers' time. Based on EUROCONTROL delay costs and published studies of runway direction changes."
3. "Against the official rules it has the right direction for about 350 more hours a year, and FraAlliance's change logs would let us measure what that is worth."
