# Notices

Open problems across main, branches and worktrees. One line each: time (Berlin) | severity | what is wrong | where | who acts. `STOP` breaks main or makes the submission wrong, `FIX` should be fixed before 16:00, `FYI` is worth knowing. Delete a line once it is fixed. Rules: "Cross-checking" in `AGENTS.md`.

Main at 12:30 runs: `python -m pytest ml/tests -q` gives 27 passed, `python -m ml.forecast --day 2026-10-31` prints 48 rows, and `web/` passes lint and build.

## STOP

- 12:16 | STOP | Backtest leak at the 24 h headline lead. `_previous_day1` is used up to lead 24 and `_previous_day2` up to lead 48, and availability is taken as `time - offset` with no publication lag. Leads of about 19-24 h and 43-48 h can see model runs that were not out at issue time | `ml/features.py:61-65,79`, same in `ml/live.py` | model owner: switch to day2 from about lead 18, or state the limit in the model card In progress: hk-model2.

## FIX

- 12:16 | FIX | `MODEL_CARD.md` does not exist. It is a required deliverable, and the demo path in README and AGENTS.md points to it | repo root | Hugo, Luca (wp6)
- 12:16 | FIX | The jury test days are not written down anywhere, so nobody can generate them | `openspec/changes/wp4-forecast-cli/tasks.md` 2.3 | Jayden or Hugo: put the dates in README
- 12:16 | FIX | Open-Meteo 10 m wind at the airport grid cell averages 0.59x the METAR wind (3.97 vs 6.95 kt). On it, the rules never close runway 18 (0.0% of hours vs 0.21% in METAR), so the rules fallback and the rule baseline understate closures | rule features in `ml/features.py`, `ml/forecast.py:68-84` | model owner: bias-correct or use `wind_speed_80m`
- 12:22 | FIX | ml.train, fitted artifacts and runtime metrics have landed. ml.labels still does not exist and is outside the model lane brief | `ml/README.md`, `openspec/changes/wp2-labels-rule-baseline/tasks.md` | head agent: assign or drop the unused label command
- 12:16 | FIX | AI vendor names and unused config: both `.env.example` files hold `OPENAI_API_KEY` and `OPENAI_MODEL`, and `web/package.json` lists `openai`, `@openai/agents` and `zod`, which nothing imports | `.env.example`, `web/.env.example`, `web/package.json` | Jayden (web)
- 12:22 | FIX | QualityResult schema is documented in ml/README.md and quality.json is published at /data/quality.json, including bins for the displayed certainty margin; UI type and quality loader still need integration | `ml/README.md`, `web/public/data/quality.json` | head agent, WP5
- 12:30 | FIX | `weather database/` is now 12.9 MB on main and outside the runway forecast: US BTS delay data stored twice (`delay_causes_2025.zip` and `raw2025/Airline_Delay_Cause.csv`), four third-party papers as PDFs (Borsky2019, Schultz2018, Rodriguez2021, an OIG report) plus their full text, and saved HTML pages. Third-party PDFs in the submission repo are a copyright risk, and the folder name has a space | `weather database/` (2ea41df) | Luca: keep it on `luca/weather-database`, take it off main

## FYI

- 12:16 | FYI | Several docs say `web/src/data/` for `backtest.json`/`quality.json`, but the code writes and reads `web/public/data/` | The model brief, wp3 `proposal.md:13`, wp8 `proposal.md:11`, `tasks.md:13` (`ml/README.md` is already fixed in `aiw-wt-ml`) | model owner, when committing
- 12:16 | FYI | Duplicate fetch code: `ml/live.py` repeats the IEM and Open-Meteo downloads of `ml/fetch.py` with a second cache folder. `data/openmeteo_historical_forecast.parquet` duplicates `openmeteo_previous_runs.parquet` (day 0 identical) and no code reads it | `ml/live.py:22-159`, `data/` | cli owner, after 16:00
- 12:16 | FYI | `latest.json` was issued at 12:00. It will be 5 h old at the 17:00 demo | `web/public/forecasts/latest.json` | cli owner: re-run `--now --out` before 16:00 and before the demo
- 12:16 | FYI | DFLD ground truth has no extraction script anywhere, so it can't be rebuilt from code. It is cited with URLs and hashes | `data/ground_truth/` | data owner
- 12:16 | FYI | `origin/codex/condor-research` (Kai) has sources main lacks: DWD 01420 hourly gusts, MOSMIX station 10637, and Fraport's live OD and runway 18 status script, which would suit `--now`. Its README uses a 5 kt rule as the direction rule, which the official brief doesn't | branch `codex/condor-research` | Kai
- 12:16 | FYI | `origin/jayden/research`, `origin/jayden/data` and `origin/luca/weather-database` hold nothing that isn't on main | remote branches | head agent: delete when convenient
- 12:16 | FYI | OpenSpec tasks for wp1, wp5 and wp7 are all unchecked although the work landed. the CLI and model briefs still say "PUSH IS PAUSED" | `openspec/changes/*/tasks.md` | head agent
- 12:16 | FYI | `briefing/brainstorm-268.md:12,35` names a model and an agent account | `briefing/` | head agent
- 12:35 | FYI | Revised forecast uses persistence weights selected on inner chronological validation. OD accuracy at 1/6/24/48 h is 96.9/90.9/90.8/89.8%; 1 h matches rules and improves Brier 0.0310 to 0.0280. Publication-time limitations remain explicit in quality.json and ml/README.md; include them in the model card | `web/public/data/`, `ml/models/` | model-card owner

- 12:40 | FYI | All published forecasts now use walk-forward-v2. ForecastApp still labels the index-error fallback as "Live sample (rules only)" although sample.json now also uses the trained fit | `web/src/components/ForecastApp.tsx:26` | head agent: update fallback label
