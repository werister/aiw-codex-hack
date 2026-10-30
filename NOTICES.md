# Notices

Open problems across main, branches and worktrees. One line each: time (Berlin) | severity | what is wrong | where | who acts. `STOP` breaks main or makes the submission wrong, `FIX` should be fixed before 16:00, `FYI` is worth knowing. Delete a line once it is fixed. Rules: "Cross-checking" in `AGENTS.md`.

Main at 12:24 runs: `python -m pytest ml/tests -q` gives 25 passed, `python -m ml.forecast --day 2026-10-31` prints 48 rows, and `web/` passes lint and build.

## STOP

- 12:16 | STOP | Backtest leak at the 24 h headline lead. `_previous_day1` is used up to lead 24 and `_previous_day2` up to lead 48, and availability is taken as `time - offset` with no publication lag. Leads of about 19-24 h and 43-48 h can see model runs that were not out at issue time | `ml/features.py:61-65,79`, same in `ml/live.py` | model owner: switch to day2 from about lead 18, or state the limit in the model card
- 12:16 | STOP | For a future `--day`, the CLI skips the model and quietly uses the rules. The issue time is local midnight of that day, there is no METAR before it, and `predict_48h` raises "No METAR within two hours". If the jury days are after today, every jury forecast is just the rule baseline | `ml/forecast.py:31-36,99-104`, `ml/features.py:98-99` | cli owner: issue at "now" and take that day's hours from the 48 h

## FIX

- 12:16 | FIX | No trained model on main. Every published forecast says `rules-fallback`, and the quality panel shows "missing". The models and `backtest.json` are committed as 5b82df2 (12:15) but not pushed | `aiw-wt-ml` (jayden/model) | model worker: push, then regenerate the forecasts
- 12:24 | FIX | In that backtest the model loses at 1 h: OD accuracy 93.8% vs 96.9% for both rules and persistence (Brier 0.049 vs 0.031). It wins at 6 h and 24 h | `web/public/data/backtest.json` in 5b82df2 | model owner: use persistence for the first hours or blend
- 12:16 | FIX | `MODEL_CARD.md` does not exist. It is a required deliverable, and the demo path in README and AGENTS.md points to it | repo root | Hugo, Luca (wp6)
- 12:16 | FIX | The jury test days are not written down anywhere, so nobody can generate them | `openspec/changes/wp4-forecast-cli/tasks.md` 2.3 | Jayden or Hugo: put the dates in README
- 12:16 | FIX | Open-Meteo 10 m wind at the airport grid cell averages 0.59x the METAR wind (3.97 vs 6.95 kt). On it, the rules never close runway 18 (0.0% of hours vs 0.21% in METAR), so the rules fallback and the rule baseline understate closures | rule features in `ml/features.py`, `ml/forecast.py:68-84` | model owner: bias-correct or use `wind_speed_80m`
- 12:16 | FIX | Train and serve differ. `hours_since_change` gets the full DFLD history in training but only 48 h in the CLI (NaN if no change in 48 h), and `live.normalize_metar` handles missing values differently from `features.normalize_obs` | `ml/live.py:42,55`, `ml/predict.py:61-64` vs `train.py` in `aiw-wt-ml` | model and cli owners
- 12:16 | FIX | Two runway 18 truths. The backtest takes the latest METAR up to 2 h old, the hindcast overlay up to 1 h old | `train.py:45-47` in `aiw-wt-ml` vs `ml/forecast.py:173-180` | model and cli owners: pick one
- 12:16 | FIX | Run commands name modules that are not on main: `ml.labels` exists nowhere and has no owner, `ml.train` is untracked | `README.md` Run, `AGENTS.md` Project, `ml/README.md:8-11`, `ml/predict.py:16` | head agent: drop `ml.labels` or assign it
- 12:16 | FIX | AI vendor names and unused config: both `.env.example` files hold `OPENAI_API_KEY` and `OPENAI_MODEL`, and `web/package.json` lists `openai`, `@openai/agents` and `zod`, which nothing imports | `.env.example`, `web/.env.example`, `web/package.json` | Jayden (web)

## FYI

- 12:16 | FYI | Several docs say `web/src/data/` for `backtest.json`/`quality.json`, but the code writes and reads `web/public/data/` | The model brief, wp3 `proposal.md:13`, wp8 `proposal.md:11`, `tasks.md:13` (`ml/README.md` is already fixed in `aiw-wt-ml`) | model owner, when committing
- 12:16 | FYI | Duplicate fetch code: `ml/live.py` repeats the IEM and Open-Meteo downloads of `ml/fetch.py` with a second cache folder. `data/openmeteo_historical_forecast.parquet` duplicates `openmeteo_previous_runs.parquet` (day 0 identical) and no code reads it | `ml/live.py:22-159`, `data/` | cli owner, after 16:00
- 12:16 | FYI | `latest.json` was issued at 12:00. It will be 5 h old at the 17:00 demo | `web/public/forecasts/latest.json` | cli owner: re-run `--now --out` before 16:00 and before the demo
- 12:16 | FYI | DFLD ground truth has no extraction script anywhere, so it can't be rebuilt from code. It is cited with URLs and hashes | `data/ground_truth/` | data owner
- 12:16 | FYI | `origin/codex/condor-research` (Kai) has sources main lacks: DWD 01420 hourly gusts, MOSMIX station 10637, and Fraport's live OD and runway 18 status script, which would suit `--now`. Its README uses a 5 kt rule as the direction rule, which the official brief doesn't | branch `codex/condor-research` | Kai
- 12:16 | FYI | `origin/jayden/research`, `origin/jayden/data` and `origin/luca/weather-database` hold nothing that isn't on main | remote branches | head agent: delete when convenient
- 12:24 | FYI | `weather database/` (from Luca's branch) is a German analysis of US BTS delay causes, outside the runway forecast. Its links to `bts/` and `empirical/` point to files that are not in the repo, and the folder name has a space | `weather database/` | Luca
- 12:16 | FYI | OpenSpec tasks for wp1, wp5 and wp7 are all unchecked although the work landed. the CLI and model briefs still say "PUSH IS PAUSED" | `openspec/changes/*/tasks.md` | head agent
- 12:16 | FYI | `briefing/brainstorm-268.md:12,35` names a model and an agent account | `briefing/` | head agent
