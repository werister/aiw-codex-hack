# FRA operating direction forecast (FraAlliance challenge, AI Week Codex Hackathon, 30 Oct 2026)

## Work packages (OpenSpec: `openspec/changes/`)

Pick yours, read its `proposal.md` and `tasks.md`, and tick tasks off as you go. `openspec list` shows progress.

| # | Package | Owner | Change |
|---|---|---|---|
| 1 | Data sources and download | our agents (worker `hk-data`); Luca checks the data | `wp1-data-sources` |
| 2 | Labels and rule baseline, with the 30-min hysteresis | Kai | `wp2-labels-rule-baseline` |
| 3 | Model and walk-forward backtest at 1/6/24 h | Kai, with our agents | `wp3-model-backtest` |
| 4 | CLI `forecast --day` and the jury-day forecasts | our agents | `wp4-forecast-cli` |
| 5 | UI: tower-staff view, 48 h timeline, simulated ops screen, quality panel, iPad widget | Jayden | `wp5-ui-timeline` |
| 6 | Model card, business case, pitch | Hugo, Luca | `wp6-model-card-pitch` |
| 7 | How the decision is made, which data exists, ground truth of flown ODs (`DATA_AND_DECISIONS.md`) | our agents (worker `hk-research`) | `wp7-data-decisions-research` |
| 8 | Model quality numbers: walk-forward, in- vs out-of-sample, confidence calibration | our agents | `wp8-model-quality` |
| 9 | Optional 3D demo scene (drop at 15:00 if not ready) | a separate agent | `wp9-3d-demo` |

Deadline: submissions at 16:00, finals at 17:00. Hugo presents; Jayden leaves at 16:45.

**Cross-checking.** Open problems are in `NOTICES.md`. Every agent reads it and pulls main before each task and at least every 15 minutes, checks the other branches and worktrees before building, and adds a line when it sees something wrong. Details: "Cross-checking" in `AGENTS.md`.

## What we are building

A 48 h hourly forecast for Frankfurt Airport. For each hour it gives:
- the operating direction (OD 25 west or OD 07 east)
- the probability that runway 18 is usable for departures
- a certainty score
- the next likely direction change

The model learns from public data: EDDF METAR, archived weather-model forecasts and DWD observations. It must beat the official rule baseline (`ml/rules.json`), measured on held-out days at 1, 6 and 24 h ahead. The jury compares our forecasts for their test days with the directions actually flown.

Official brief: `frankfurt-airport-operating-direction-forecast.md`. Background: `CHALLENGE_FRAALLIANCE.md`, `briefing/`.

## Stack

- `ml/`: Python 3.13, pandas, scikit-learn. Data download, labels, model, backtest and the forecast CLI.
- `web/`: Next.js 16, TypeScript, Tailwind 4 (npm). The ops timeline, deployed on Vercel with `web/` as the root.
- Contracts: `ml/rules.json` holds the official limits. `web/src/lib/forecast-types.ts` defines the JSON the CLI writes and the UI reads.

## Run

```bash
python -m pip install -r ml/requirements.txt
python -m ml.fetch                              # data into data/ (cached)
python -m ml.labels                             # labels from METAR + official rules
python -m ml.train                              # model + backtest
python -m ml.forecast --day 2026-10-31          # 48 h hourly table for any day
python -m ml.forecast --day 2026-10-31 --json   # same as JSON for the UI

cd web && npm install && npm run dev            # http://localhost:3000
```

Some of these commands land during the day. Each work package says when its part is ready.

## Demo path

1. Open the web app: the next 48 h, with OD per hour, runway 18, certainty and the next change.
2. Switch to a jury test day and show the forecast against the directions actually flown (DFLD records).
3. Open the backtest: skill at 1, 6 and 24 h against the rule baseline and persistence.
4. Show `MODEL_CARD.md`.

## Data

All sources are public and cited. The details are in `data/README.md` (files) and `DATA_AND_DECISIONS.md` (how FRA decides and which data exists).
- EDDF METAR and TAF from the Iowa Environmental Mesonet archive.
- Open-Meteo Previous Runs and Historical Forecast APIs: archived model forecasts, for an honest 48 h backtest.
- The Open-Meteo Forecast API for the live forecast.
- DWD Open Data, station 01420 Frankfurt/Main.
- DFLD recorded operating directions, the ground truth for scoring. Source and limits: `data/ground_truth/README.md`.

## Team

Kai Detmers (ML co-lead), Jayden Bruck (agents and UI), Hugo Hader (pitch), Luca Schultz (data, numbers, backup presenter). Rules for everyone, humans and agents: `AGENTS.md`.
