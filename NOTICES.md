# Notices

Open problems across main, branches and worktrees. One line each: time (Berlin) | severity | what is wrong | where | who acts. `STOP` breaks main or makes the submission wrong, `FIX` should be fixed before 16:00, `FYI` is worth knowing. Delete a line once it is fixed. Rules: "Cross-checking" in `AGENTS.md`.

Main at 12:26 runs: `python -m pytest ml/tests -q` gives 27 passed, `python -m ml.forecast --day 2026-10-31` prints 48 rows, and `web/` passes lint and build.

## STOP

- 12:16 | STOP | Backtest leak at the 24 h headline lead. `_previous_day1` is used up to lead 24 and `_previous_day2` up to lead 48, and availability is taken as `time - offset` with no publication lag. Leads of about 19-24 h and 43-48 h can see model runs that were not out at issue time | `ml/features.py:61-65,79`, same in `ml/live.py` | model owner: switch to day2 from about lead 18, or state the limit in the model card
- 12:16 | STOP | For a future `--day`, the CLI skips the model and quietly uses the rules. The issue time is local midnight of that day, there is no METAR before it, and `predict_48h` raises "No METAR within two hours". If the jury days are after today, every jury forecast is just the rule baseline | `ml/forecast.py:31-36,99-104`, `ml/features.py:98-99` | cli owner: issue at "now" and take that day's hours from the 48 h

## FIX

- 12:26 | FIX | The trained model is on main (5b82df2) and past days now run it (`--day 2026-10-02` gives `walk-forward-v1`), but every published file in `web/public/forecasts/` still says `rules-fallback` | `web/public/forecasts/*.json` | cli owner: regenerate them
- 12:24 | FIX | In that backtest the model loses at 1 h: OD accuracy 93.8% vs 96.9% for both rules and persistence (Brier 0.049 vs 0.031). It wins at 6 h and 24 h | `web/public/data/backtest.json` | model owner: use persistence for the first hours or blend
- 12:16 | FIX | `MODEL_CARD.md` does not exist. It is a required deliverable, and the demo path in README and AGENTS.md points to it | repo root | Hugo, Luca (wp6)
- 12:16 | FIX | The jury test days are not written down anywhere, so nobody can generate them | `openspec/changes/wp4-forecast-cli/tasks.md` 2.3 | Jayden or Hugo: put the dates in README
- 12:16 | FIX | Open-Meteo 10 m wind at the airport grid cell averages 0.59x the METAR wind (3.97 vs 6.95 kt). On it, the rules never close runway 18 (0.0% of hours vs 0.21% in METAR), so the rules fallback and the rule baseline understate closures | rule features in `ml/features.py`, `ml/forecast.py:68-84` | model owner: bias-correct or use `wind_speed_80m`
- 12:22 | FIX | Predictor now accepts full recorded history via obs.attrs["od_history"], but CLI still passes only asof-merged 48 h METAR history; attach the full known OD history before predict to retain long holds and changes after the latest METAR | `ml/predict.py`, `ml/forecast.py` | cli owner
- 12:22 | FIX | ml.train, fitted artifacts and runtime metrics have landed. ml.labels still does not exist and is outside the model lane brief | `ml/README.md`, `openspec/changes/wp2-labels-rule-baseline/tasks.md` | head lane: assign or drop the unused label command
- 12:16 | FIX | AI vendor names and unused config: both `.env.example` files hold `OPENAI_API_KEY` and `OPENAI_MODEL`, and `web/package.json` lists `openai`, `@openai/agents` and `zod`, which nothing imports | `.env.example`, `web/.env.example`, `web/package.json` | Jayden (web)

## FYI

- 12:16 | FYI | Several docs say `web/src/data/` for `backtest.json`/`quality.json`, but the code writes and reads `web/public/data/` | `briefs/hk-model.md:16,32`, wp3 `proposal.md:13`, wp8 `proposal.md:11`, `tasks.md:13` (`ml/README.md` is already fixed in `aiw-wt-ml`) | model owner, when committing
- 12:16 | FYI | Duplicate fetch code: `ml/live.py` repeats the IEM and Open-Meteo downloads of `ml/fetch.py` with a second cache folder. `data/openmeteo_historical_forecast.parquet` duplicates `openmeteo_previous_runs.parquet` (day 0 identical) and no code reads it | `ml/live.py:22-159`, `data/` | cli owner, after 16:00
- 12:16 | FYI | `latest.json` was issued at 12:00. It will be 5 h old at the 17:00 demo | `web/public/forecasts/latest.json` | cli owner: re-run `--now --out` before 16:00 and before the demo
- 12:16 | FYI | DFLD ground truth has no extraction script anywhere, so it can't be rebuilt from code. It is cited with URLs and hashes | `data/ground_truth/` | data owner
- 12:16 | FYI | `origin/codex/condor-research` (Kai) has sources main lacks: DWD 01420 hourly gusts, MOSMIX station 10637, and Fraport's live OD and runway 18 status script, which would suit `--now`. Its README uses a 5 kt rule as the direction rule, which the official brief doesn't | branch `codex/condor-research` | Kai
- 12:16 | FYI | `origin/jayden/research`, `origin/jayden/data` and `origin/luca/weather-database` hold nothing that isn't on main | remote branches | head lane: delete when convenient
- 12:24 | FYI | `weather database/` (from Luca's branch) is a German analysis of US BTS delay causes, outside the runway forecast. Its links to `bts/` and `empirical/` point to files that are not in the repo, and the folder name has a space | `weather database/` | Luca
- 12:16 | FYI | OpenSpec tasks for wp1, wp5 and wp7 are all unchecked although the work landed. `briefs/hk-cli.md` and `hk-model.md` still say "PUSH IS PAUSED" | `openspec/changes/*/tasks.md`, `briefs/` | head lane
- 12:16 | FYI | `briefing/brainstorm-268.md:12,35` names a model and an agent account | `briefing/` | head lane

- 12:22 | FYI | Six monthly walk-forward folds and final models are on main. OD accuracy at 1/6/24/48 h is 93.8/91.5/90.8/89.8%; 1 h is worse than rules at 96.9%. Publication-time limitations are explicit in quality.json and ml/README.md; copy them into the model card | `web/public/data/`, `ml/models/` | model-card owner
- 12:22 | FIX | QualityResult schema is documented in ml/README.md and quality.json is published at /data/quality.json, including bins for the displayed certainty margin; UI type and quality loader still need integration | `ml/README.md`, `web/public/data/quality.json` | head lane, WP5
