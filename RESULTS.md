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

## Economic value

Being researched now: an illustrative estimate from public unit costs, not measured savings. This section will be filled in shortly.
