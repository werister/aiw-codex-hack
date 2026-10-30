# What we compare against, in plain words

Our model is only good if it beats what a planner could already do without it. We compare it with two simple methods, on exactly the same hours.

## 1. "The official rules"

**Where they come from:** FraAlliance's official challenge brief (PDF), transcribed in [`frankfurt-airport-operating-direction-forecast.md`](frankfurt-airport-operating-direction-forecast.md), section "Decision rules". The numbers live in one file, [`ml/rules.json`](ml/rules.json), and nowhere else in the code.

**The rules themselves:**
- Aircraft land and take off **into the wind**. Only wind from straight behind counts as tailwind.
- **Landings decide the direction.** If the tailwind on the landing runways is **10 knots or more**, the airport switches direction **immediately**.
- A **smaller tailwind (under 10 knots)** is accepted for **up to 30 minutes**, so the airport doesn't flip back and forth. If it lasts longer, the airport switches to the direction with headwind.
- **Runway 18** (departures to the south) **closes** when the tailwind from the north reaches **15 knots or more**, or when the crosswind including gusts is **over 40 knots**.
- All parallel runways always run in the **same** direction, west (25) or east (07).

**How we use them as a forecast:** we take the **weather forecast** for every future hour, as it was available at the time, calculate the tailwind on runways 25, 07 and 18, and run the rules hour by hour, including the 30-minute tolerance. That gives "what the rulebook would predict". It's the smart way to forecast today without our model.

## 2. "Same as now"

**The simplest possible forecast:** whatever direction Frankfurt flies right now, assume it's still the same in 6, 24 or 48 hours. Forecasters call this *persistence*.

It sounds naive, but it's hard to beat because the direction only changes about 3 times a week. It's also roughly how planning works when nobody looks at a forecast: you plan for today's situation.

## How it's done today

- **Live:** the tower decides when to switch, based on the **measured** wind and these rules, with weather advice from the national weather service.
- **For planning 1 to 2 days ahead**, there's no hour-by-hour direction forecast with a certainty number. Planners effectively assume the current direction holds ("same as now"), or read a general weather forecast. A public neighbourhood service (UNH) gives a rough outlook in 8-hour blocks.

## How we compare, and the result

Every method forecasts the same hours. All three are checked against the direction **actually flown**, from public records (DFLD), over 12 months the model never saw.

| how far ahead | our model | official rules | same as now |
|---|---|---|---|
| 6 hours | **92.8%** | 88.1% | 88.8% |
| 24 hours | **91.7%** | 87.7% | 75.1% |
| 48 hours | **89.2%** | 84.0% | 64.2% |

Our model makes about **a third fewer mistakes than the rules** at 24 and 48 hours, and about **three times fewer than "same as now"** at 48 hours. Its certainty number is about twice as reliable as the rules'. Details: [`RESULTS.md`](RESULTS.md).
