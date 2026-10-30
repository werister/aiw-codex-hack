# Submission · Liftoff (FraAlliance challenge)

**Team:** Jayden Bruck, Kai Detmers, Hugo Hader, Luca Schultz
**Repo:** https://github.com/werister/aiw-codex-hack
**Live demo:** LIVE_URL
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
- Archived ECMWF, GFS and ICON wind forecasts, as they were issued 1–3 days ahead, from Open-Meteo.
- The official FraAlliance rules as the baseline.

## Quality (held out, walk-forward, six-hour publication lag)
Operating direction at 6 / 24 / 48 h: model 90.7 / 89.6 / 84.9%, official rules 86.3 / 86.3 / 82.5%, keep-current 88.3 / 76.3 / 65.9%. The model's Brier score is 40–60% better than either baseline. [final numbers at 15:30]

## Jury test days
`python -m pip install -r ml/requirements.txt`, then `python -m ml.forecast --day YYYY-MM-DD` (add `--json` for machine-readable output). Forecasts for the jury days: `web/public/forecasts/<day>.json`.
