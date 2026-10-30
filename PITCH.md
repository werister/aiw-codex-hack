# Pitch · Liftoff (FraAlliance challenge)

Draft for Hugo (presenter) and Luca (backup). Numbers come from `web/public/data/quality.json` (walk-forward-v5). The approach story is on the app's `/approach` page.

## 1. Problem (20 s)
At Frankfurt the wind alone decides which way aircraft land and take off. Frankfurt changes its operating direction about 156 times a year, three times a week. Six in ten departures use runway 18, and a strong north wind closes it. When the direction changes, everyone reacts at once: ground handling repositions, transfer passengers miss connections, flights are rescheduled. Today that reaction starts when the decision is made. We want it to start a day earlier. Across Europe, 8.0 of the 17.5 minutes of average departure delay are knock-on delay from earlier flights (EUROCONTROL CODA 2024), and weather causes 32% of air-traffic-flow delay minutes (EUROCONTROL NOR 2025), so a change you see coming early stops a chain, not just one flight.

## 2. What we built (20 s)
**Liftoff**: a 48-hour, hour-by-hour forecast of the operating direction (25 west or 07 east) and of runway 18. Every hour carries a probability and a certainty score, and the next likely change comes with a time window. It's built for the people in the tower. The first thing they see is one planning recommendation, such as "prepare for a switch to 07 East around 07:00, 79% likely", with the evidence one click away.

## 3. Live demo (60 s)
See `DEMO_SCRIPT.md`.

## 4. Why you can trust it (40 s)
- **Graded against what was flown.** We learn from DFLD's recorded operating directions, eight years of half-hourly records. The official rules alone match what was flown only 89% of the time, so a rule lookup is not enough.
- **Honest testing.**
  - Walk-forward: every test month is predicted by a model trained only on earlier months.
  - Forecasts are used as they were published, with a six-hour delay, and no hindsight.
  - The command the jury runs gives exactly the backtest's numbers.
- **It beats both baselines** on 12 months it never saw, and the margins hold up statistically. Accuracy for model / official rules / keep current:

  | Lead | Model | Official rules | Keep current |
  |---|---|---|---|
  | 1 h | 96.0% | 95.9% | 95.9% |
  | 6 h | 92.8% | 88.1% | 88.8% |
  | 24 h | 91.7% | 87.7% | 75.1% |
  | 48 h | 89.2% | 84.0% | 64.2% |

  1 h is a tie. From 6 h it wins by +4 to +5 points over the rules (95% intervals, resampled by day, all above +2) and up to +25 over keep-current. Its probability error (Brier) is about half the rules'. When it says 85%, it happens about 85% of the time. When it's unsure, the screen says so.
- **All public data:** DFLD.de recorded directions, EDDF METAR, and archived forecasts from three weather models (ECMWF, GFS, ICON) plus pressure about 200 km around FRA, all through Open-Meteo. Cited in `MODEL_CARD.md`.

## 5. Built with Codex (15 s)
Spec-driven with OpenSpec in nine work packages. Codex workers built the data pipeline, the official rule engine with its tests, the model, the forecast CLI and the design scrape in parallel, each on its own branch and landing on main.

## Value (10 s)
Estimated value: about €0.4M a year at Frankfurt (range €0.13M to €3.2M), plus a similar amount in passengers' time. Based on EUROCONTROL delay costs and published studies of runway direction changes.

## 6. What's next (15 s)
- **Pilot:** feed it DFS's runway wind sensors and the airport's own direction log, and run it beside the shift supervisor for a month.
- **Portable:** one config file (runway headings and limits) plus a direction history, and it runs for Munich, Düsseldorf or Zurich.

**Close:** "The wind decides. Now you know a day ahead."
