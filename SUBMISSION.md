# Submission · Liftoff (FraAlliance challenge)

**Team:** Jayden Bruck, Kai Detmers, Hugo Hader, Luca Schultz
**Repo:** https://github.com/werister/aiw-codex-hack
**Live demo:** https://fraalliance-runway-forecast.statworx-par-2884.chatgpt.site
**Model card:** `MODEL_CARD.md` · **Experiments:** `EXPERIMENTS.md`

## One line
A 48-hour, hour-by-hour forecast of Frankfurt's operating direction (25 or 07) and of runway 18, with a probability, a certainty score and the next likely change, trained on the directions actually flown.

## What it does
For each of the next 48 hours, Liftoff predicts:
- the probability that the airport operates west (25) or east (07)
- whether runway 18 is usable for departures
- how certain it is
- when the next change is likely, with a time window

It is built for tower and apron staff: one planning recommendation first, the evidence one click away, and an iPad view.

## Data (public)
- Recorded operating directions from DFLD.de, 2018 to 2026, half-hourly.
- EDDF METAR from the Iowa Environmental Mesonet.
- Archived ECMWF, GFS and ICON wind forecasts and pressure differences, as they were issued 1–3 days ahead, from Open-Meteo.
- The official FraAlliance rules as the baseline.

## Quality (12 held-out months, walk-forward, six-hour publication lag)
Operating direction at 1 / 6 / 24 / 48 h:
- **model:** 95.7 / 92.7 / 91.8 / 88.9%
- **official rules:** 93.1 / 88.1 / 87.7 / 84.0%
- **keep-current:** 95.9 / 88.8 / 75.1 / 64.2%

From 6 h the model beats both baselines by margins whose 95% day-bootstrap intervals stay above +2 points (vs rules: +4.6 / +4.1 / +4.9 at 6 / 24 / 48 h), with a Brier score about half the rules'. The feature set was chosen on these months; today's live forecasts are the untouched test. Runway 18 is inferred from METAR and isn't predictable beyond persistence with these public inputs: the model catches none of the 12 closure windows at 24 h.

## Jury test days
`python -m pip install -r ml/requirements.txt`, then `python -m ml.forecast --day YYYY-MM-DD` (add `--json` for machine-readable output). Forecasts for the jury days: `web/public/forecasts/<day>.json`.
