# Notices

Open problems across main, branches and worktrees. One line each: time (Berlin) | severity | what is wrong | where | who acts. `STOP` breaks main or makes the submission wrong, `FIX` should be fixed before 16:00, `FYI` is worth knowing. Delete a line once it is fixed. Rules: "Cross-checking" in `AGENTS.md`.

Main at 12:52 runs: `python -m pytest ml/tests -q` gives 30 passed, `python -m ml.forecast --day 2026-10-31` gives `walk-forward-v3` issued at the current hour, and `web/` passes lint and build.

## STOP

- The previous 24 h backtest leak was fixed in a979070 (6 h publication lag).
- 13:07 | STOP | The documented CLI exits 1 under allowed pandas 3.1.0: METAR time is datetime64[ns, UTC], newly read DFLD availability is datetime64[us, UTC], and merge_asof rejects them. Align timestamp units at input boundaries; an in-memory ns alignment merges all 67,119 observations successfully, but the full CLI still needs rerunning | ml/forecast.py build_forecast; resources/ml-depth/runtime-check.json | ML/CLI owner

## FIX

- 12:16 | FIX | `MODEL_CARD.md` does not exist. It is a required deliverable, and the demo path in README and AGENTS.md points to it | repo root | Hugo, Luca (wp6)
- 12:16 | FIX | The jury test days are not written down anywhere, so nobody can generate them | `openspec/changes/wp4-forecast-cli/tasks.md` 2.3 | Jayden or Hugo: put the dates in README
- 12:16 | FIX | Open-Meteo 10 m wind at the airport grid cell averages 0.59x the METAR wind (3.97 vs 6.95 kt). On it, the rules never close runway 18 (0.0% of hours vs 0.21% in METAR), so the rules fallback and the rule baseline understate closures | rule features in `ml/features.py`, `ml/forecast.py:68-84` | model owner: bias-correct or use `wind_speed_80m`
- 12:22 | FIX | ml.train, fitted artifacts and runtime metrics have landed. ml.labels still does not exist and is outside the model lane brief | `ml/README.md`, `openspec/changes/wp2-labels-rule-baseline/tasks.md` | head agent: assign or drop the unused label command
- 12:30 | FIX | `weather database/` is now 12.9 MB on main and outside the runway forecast: US BTS delay data stored twice (`delay_causes_2025.zip` and `raw2025/Airline_Delay_Cause.csv`), four third-party papers as PDFs (Borsky2019, Schultz2018, Rodriguez2021, an OIG report) plus their full text, and saved HTML pages. Third-party PDFs in the submission repo are a copyright risk, and the folder name has a space | `weather database/` (2ea41df) | Luca: keep it on `luca/weather-database`, take it off main
- 12:52 | FIX | The October daily hindcast still has the model below persistence at 2-6 h: 84.2% vs 95.3% for 1-6 h (n=171), all three 100% at lead 1. `cli-parity.csv` shows the CLI and training give identical features and probabilities, so this is the model itself on midnight issues, not a pipeline gap. It wins at 7-24 h and 25-48 h | `web/public/data/october.json` | model owner: extend the persistence weight to about 6 h, or say this plainly in the model card and pitch
- 12:52 | FIX | Three UI efforts at once: the main app (head agent), the design worker restyling all eight components uncommitted in `aiw-wt-design`, and `origin/hugo/forecast-ui-spec` with a separate static prototype (`web/prototypes/dfs-forecast/`) and a new wp5 spec. Hugo's UI notes (`briefing/2026-10-30-ui-atc-context.md`) describe the old placeholder page, so the presenter's picture of the UI is out of date | `aiw-wt-design`, branch `hugo/forecast-ui-spec` | head agent and Hugo: agree on one UI before 15:00

## FYI

- 12:52 | FYI | `README.md` now has a "fleet-wide planning" product direction (b8f1226) with planning recommendations and traffic exposure, which we don't build. The doc says so itself. Keep pitch claims to what runs | `README.md`, `briefing/fleet-planning.md` | Hugo
- 12:52 | FYI | Personal path in a committed file on Hugo's branch: `/Users/hugohader/dev/...` in `web/prototypes/dfs-forecast/README.md` | branch `hugo/forecast-ui-spec` | cleanup agent at the end
- 12:52 | FYI | Overlapping edits: the design worker changes every component in `web/src/` uncommitted, while the head agent also works in `web/` | `aiw-wt-design` | head agent: land the design worker's changes in small commits
- 12:16 | FYI | Several docs say `web/src/data/` for `backtest.json`/`quality.json`, but the code writes and reads `web/public/data/` | The model brief, wp3 `proposal.md:13`, wp8 `proposal.md:11`, `tasks.md:13` (`ml/README.md` is already fixed in `aiw-wt-ml`) | model owner, when committing
- 12:16 | FYI | Duplicate fetch code: `ml/live.py` repeats the IEM and Open-Meteo downloads of `ml/fetch.py` with a second cache folder. `data/openmeteo_historical_forecast.parquet` duplicates `openmeteo_previous_runs.parquet` (day 0 identical) and no code reads it | `ml/live.py:22-159`, `data/` | cli owner, after 16:00
- 12:16 | FYI | `latest.json` was issued at 12:00. It will be 5 h old at the 17:00 demo | `web/public/forecasts/latest.json` | cli owner: re-run `--now --out` before 16:00 and before the demo
- 12:16 | FYI | DFLD ground truth has no extraction script on main yet. The CLI worker is writing `ml/dfld.py` and `ml/tests/test_dfld.py` (untracked in `aiw-wt-cli`) | `data/ground_truth/` | CLI worker
- 12:16 | FYI | `origin/codex/condor-research` (Kai) has sources main lacks: DWD 01420 hourly gusts, MOSMIX station 10637, and Fraport's live OD and runway 18 status script, which would suit `--now`. Its README uses a 5 kt rule as the direction rule, which the official brief doesn't | branch `codex/condor-research` | Kai
- 12:16 | FYI | `origin/jayden/research`, `origin/jayden/data` and `origin/luca/weather-database` hold nothing that isn't on main | remote branches | head agent: delete when convenient
- 12:16 | FYI | OpenSpec tasks for wp1, wp5 and wp7 are all unchecked although the work landed. the CLI and model briefs still say "PUSH IS PAUSED" | `openspec/changes/*/tasks.md` | head agent
- 12:16 | FYI | `briefing/brainstorm-268.md:12,35` names a model and an agent account | `briefing/` | head agent
- 12:35 | FYI | Revised forecast uses persistence weights selected on inner chronological validation. OD accuracy at 1/6/24/48 h is 96.9/90.9/90.8/89.8%; 1 h matches rules and improves Brier 0.0310 to 0.0280. Publication-time limitations remain explicit in quality.json and ml/README.md; include them in the model card | `web/public/data/`, `ml/models/` | model-card owner
- 12:40 | FYI | All published forecasts now use walk-forward-v2. ForecastApp still labels the index-error fallback as "Live sample (rules only)" although sample.json now also uses the trained fit | `web/src/components/ForecastApp.tsx:26` | head agent: update fallback label
