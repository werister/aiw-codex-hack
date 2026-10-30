# Submission · Lift-off (FraAlliance challenge)

**Team:** Jayden Bruck, Kai Detmers, Hugo Hader, Luca Schultz
**Repo:** [Source code](https://github.com/werister/aiw-codex-hack)

**Live demo:** [Cockpit](https://fraalliance-runway-forecast.statworx-par-2884.chatgpt.site) · [Historical replay](https://fraalliance-runway-forecast.statworx-par-2884.chatgpt.site/pitch)

**One-page model card:** [PDF](output/pdf/liftoff-model-card.pdf) · [Text](MODEL_CARD_ONE_PAGE.md)

**Technical model card:** [MODEL_CARD.md](MODEL_CARD.md) · **Experiments:** [EXPERIMENTS.md](EXPERIMENTS.md)

## One line
A 48-hour, hour-by-hour forecast of Frankfurt's operating direction (25 or 07) and runway-18 weather usability, with probabilities, a certainty score and the next likely change, trained on publicly recorded operating directions and observed weather.

## What it does
For each of the next 48 hours, Lift-off predicts:

- the probability that the airport operates west (25) or east (07)
- the probability that runway 18 is usable for departures under the weather rules
- how certain it is
- when the next change is likely, with a time window

It is designed for tower and apron planning: one recommendation first, supporting evidence and a tablet view. The certainty score measures probability margin; the change window is a heuristic. Neither is a calibrated confidence interval or an operational clearance.

## Data (public)
- [DFLD](https://www.dfld.de/Mess/StatWetter.php?R=1&D=01.10.2026): half-hourly recorded operating directions, 2018-2026; a public operational proxy, not a certified movement log.
- [Iowa Environmental Mesonet](https://mesonet.agron.iastate.edu/request/download.phtml): EDDF METAR observations and inferred runway-18 weather labels.
- [Open-Meteo Previous Runs](https://open-meteo.com/en/docs/previous-runs-api): archived ECMWF, GFS and ICON forecasts and pressure differences from 2024 onward. Historical availability uses day offsets and a six-hour publication proxy; exact publication times are unavailable.
- [Official FraAlliance brief](frankfurt-airport-operating-direction-forecast.md) and [rule configuration](ml/rules.json): rule baseline and model features.

## Model and forecast drivers

Version `walk-forward-v6` uses two gradient-boosted classifiers with 45 features and persistence blending. The leading measured drivers in the final test month are the north-south pressure difference, current operating direction, ensemble tailwind on 25, ECMWF tailwind on 25 and pressure-derived tailwind.

## Quality

Twelve expanding monthly folds, November 2025-October 2026; training labels end before each test month. Stable-hour operating-direction accuracy, on matched labelled rows:

| Lead | Model | Official rules, base wind | Keep-current | Scored rows |
|---|---:|---:|---:|---:|
| 1 h | 95.7% | 93.1% | 95.9% | 1,416 |
| 6 h | 92.7% | 88.1% | 88.8% | 1,416 |
| 24 h | 91.8% | 87.7% | 75.1% | 1,383 |
| 48 h | 88.9% | 84.0% | 64.2% | 1,338 |

At 6, 24 and 48 h the model exceeds both baselines; at 1 h persistence is slightly more accurate. At 24 h, model Brier score is 0.0637 versus 0.1229 for base-wind rules. Seven-day block-bootstrap 95% intervals for the accuracy advantage over those rules are +2.7 to +6.5, +3.1 to +6.3 and +3.5 to +7.2 percentage points at 6, 24 and 48 h.

These folds informed feature selection and subsequent review, so they are not an untouched final test. Publication delays and DFLD summer-clock alignment remain unverified. Runway-18 skill is not established: at 24 h, the model catches 0 of 12 positive windows with 0 false alarms among 307 complete windows; 1,125 incomplete or unknown windows are excluded. These are overlapping issue windows with METAR-inferred weather labels, not unique operational closure episodes. Full results: [quality.json](web/public/data/quality.json).

## Jury test days

**Official jury dates remain unconfirmed in the repository.** Prepared fallback forecasts: [31 October 2026](web/public/forecasts/2026-10-31.json) and [1 November 2026](web/public/forecasts/2026-11-01.json), each containing 48 hourly predictions. These are current-issue forecasts, not forecasts issued at the future day's midnight. Historical examples and the latest issue are listed in the [forecast index](web/public/forecasts/index.json).

Run from the repository root with Python 3.13:

```bash
python -m pip install -r ml/requirements.txt
python -m ml.forecast --day 2026-10-31
python -m ml.forecast --day 2026-10-31 --json --out web/public/forecasts/2026-10-31.json
```

Replace the example date with each assigned jury day. Historical requests use that day's issue; future-day requests retain the current 48-hour horizon and report the actual issue time. A requested day outside that horizon cannot be represented as a complete day-ahead forecast.
