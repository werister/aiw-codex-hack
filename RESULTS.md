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

## Economic value (illustrative estimate, FRA scale)

**This is an illustrative estimate from public unit costs, not measured FRA savings.** No public source gives a cost per direction change at FRA. *A* marks an assumption.

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

1. "Frankfurt changes direction about 156 times a year. 24 hours ahead, our model anticipates 82% of those changes, against 28% if planners assume today's direction holds."
2. "On EUROCONTROL unit costs that is worth an illustrative €0.13M to €3.2M a year at FRA, about €0.4M in our central case, plus a similar amount in passengers' time. These are estimates, not measured FRA savings."
3. "Against the official rules it catches about as many changes but has the right direction for about 350 more hours a year, and FraAlliance's change logs would let us measure what that is worth."
