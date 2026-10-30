# Pitch · Runway Outlook (FraAlliance challenge)

Draft for Hugo (presenter) and Luca (backup). Numbers come from `web/public/data/quality.json`; final numbers land at 15:30.

## 1. Problem (20 s)
At Frankfurt the wind alone decides which way aircraft land and take off. Frankfurt changes its operating direction about 156 times a year, three times a week. Six in ten departures use runway 18, and a strong north wind closes it. When the direction changes, everyone reacts at once: ground handling repositions, transfer passengers miss connections, flights are rescheduled. Today that reaction starts when the decision is made. We want it to start a day earlier.

## 2. What we built (20 s)
**Runway Outlook**: a 48-hour, hour-by-hour forecast of the operating direction (25 west or 07 east) and of runway 18. Every hour carries a probability and a certainty score, and the next likely change comes with a time window. It's built for the people in the tower. The first thing they see is one planning recommendation, such as "prepare for a switch to 07 East around 07:00, 79% likely", with the evidence one click away.

## 3. Live demo (60 s)
See `DEMO_SCRIPT.md`.

## 4. Why you can trust it (40 s)
- **Graded against what was flown.** We learn from DFLD's recorded operating directions, eight years of half-hourly records. The official rules alone match what was flown only 89% of the time, so a rule lookup is not enough.
- **Honest testing.**
  - Walk-forward: every test month is predicted by a model trained only on earlier months.
  - Forecasts are used as they were published, with a six-hour delay, and no hindsight.
  - The command the jury runs gives exactly the backtest's numbers.
- **It beats both baselines** on months it never saw. Accuracy for model / official rules / keep current:

  | Lead | Model | Official rules | Keep current |
  |---|---|---|---|
  | 6 h | 90.7% | 86.3% | 88.3% |
  | 24 h | 89.6% | 86.3% | 76.3% |
  | 48 h | 84.9% | 82.5% | 65.9% |

  Its probabilities are also 40–60% sharper by Brier score, and they're calibrated: when it says 85%, it happens about 85% of the time. [update at 15:30]
- **All public data:** DFLD.de recorded directions, EDDF METAR, and archived forecasts from three weather models through Open-Meteo. Cited in `MODEL_CARD.md`.

## 5. Built with Codex (15 s)
Spec-driven with OpenSpec in nine work packages. Codex workers built the data pipeline, the official rule engine with its tests, the model, the forecast CLI and the design scrape in parallel, each on its own branch and landing on main.

## 6. What's next (15 s)
- **Pilot:** feed it DFS's runway wind sensors and the airport's own direction log, and run it beside the shift supervisor for a month.
- **Portable:** one config file (runway headings and limits) plus a direction history, and it runs for Munich, Düsseldorf or Zurich.

**Close:** "The wind decides. Now you know a day ahead."
