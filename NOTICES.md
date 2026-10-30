# Notices

Open problems across main, branches and worktrees. One line each: time (Berlin) | severity | what is wrong | where | who acts. `STOP` breaks main or makes the submission wrong, `FIX` should be fixed before 16:00, `FYI` is worth knowing. Delete a line once it is fixed. Rules: "Cross-checking" in `AGENTS.md`.

Main at 13:10 runs: `python -m pytest ml/tests -q` gives 38 passed, `python -m ml.forecast --day 2026-10-31` gives `walk-forward-v3` issued at the current hour.

## STOP

- None open. The AI trailer on the model commit was amended (now 18cc95b, not pushed yet).

## FIX

- 12:16 | FIX | The jury test days are still not written down anywhere (README, model card, `index.json`), and there are no forecasts for them. Submission is at 16:00 | README | Jayden or Hugo: put the dates in README so the cli lane can generate them
- 12:16 | FIX | Open-Meteo 10 m wind at the airport grid cell averages 0.59x the METAR wind (3.97 vs 6.95 kt). On it, the rules never close runway 18 (0.0% of hours vs 0.21% in METAR), so the rules fallback and the rule baseline understate closures | rule features in `ml/features.py`, `ml/forecast.py:68-84` | model owner: bias-correct or use `wind_speed_80m`
- 13:10 | FIX | `ml.labels` does not exist. I removed it from the README run block; `ml/README.md:8` still lists it | `ml/README.md` | model lane, when committing
- 12:30 | FIX | `weather database/` is now 12.9 MB on main and outside the runway forecast: US BTS delay data stored twice (`delay_causes_2025.zip` and `raw2025/Airline_Delay_Cause.csv`), four third-party papers as PDFs (Borsky2019, Schultz2018, Rodriguez2021, an OIG report) plus their full text, and saved HTML pages. Third-party PDFs in the submission repo are a copyright risk, and the folder name has a space | `weather database/` (2ea41df) | Luca: keep it on `luca/weather-database`, take it off main
- 13:10 | FYI | October midnight issues: persistence still beats the model at 1-6 h (95.3% vs 84.2%). `MODEL_CARD.md` states it, and the model lane is tuning the blend | `web/public/data/october.json` | model lane
- 12:40 | FIX | Ola references: seven agent briefs contain local `C:\olawt\...` worktree paths (`c27-design.md` has two). No Ola names in commit messages, authors or other files | `briefs/c27-design.md`, `hk-cli.md`, `hk-cli3.md`, `hk-data.md`, `hk-model.md`, `hk-research.md`, `hk-scrape.md` | cleanup agent at the end
- 13:00 | FIX | Main now has the FraAlliance styling and the recommendation view (0cf65aa, c5d906e), but `origin/hugo/forecast-ui-spec` still carries a separate static prototype (`web/prototypes/dfs-forecast/`) and a wp5 spec written against the old placeholder page (`briefing/2026-10-30-ui-atc-context.md`). Hugo presents from an outdated picture of the UI | branch `hugo/forecast-ui-spec` | Hugo: rebase and review the current app
- 13:00 | FIX | Commit 18cc95b (not pushed) drops recorded OD hours that contradict the METAR rules (runs of 3+ hours with landing tailwind >= 10 kt, which removes 8-12 Oct) from targets and evaluation. That removes the cases where the rules fail and flatters both model and rules. `MODEL_CARD.md` doesn't mention it yet | `ml/train.py`, `ml/quality.py` in `aiw-wt-ml` | model lane: report scores with and without the filter, add it to the model card

## FYI

- 13:10 | FYI | UI details: the backup option says "Live sample (rules only)" but `sample.json` is the trained model (`ForecastApp.tsx:30`); the 40 kt crosswind limit is shown nowhere; nothing reads `backtest.json` or `october.json` | `web/src/components/` | web owner
- 13:00 | FYI | `data/ground_truth/dfld_hourly.csv` grew to 6.1 MB (history from 2018, 33a7847), and two new runway 18 CSVs add 3.9 MB. `ml/dfld.py` can rebuild them; gzip them like `dfld_half_hourly.csv.gz` if size matters | `data/ground_truth/` | data owner
- 13:00 | FYI | `origin/luca/weather-database` has one more commit (0c8f4da, 72 files, about 101k lines of weather archive and an advisory board) that is not on main. Keep it off main | branch `luca/weather-database` | Luca
- 12:52 | FYI | `README.md` now has a "fleet-wide planning" product direction (b8f1226) with planning recommendations and traffic exposure, which we don't build. The doc says so itself. Keep pitch claims to what runs | `README.md`, `briefing/fleet-planning.md` | Hugo
- 12:52 | FYI | Personal path in a committed file on Hugo's branch: `/Users/hugohader/dev/...` in `web/prototypes/dfs-forecast/README.md` | branch `hugo/forecast-ui-spec` | cleanup agent at the end
- 12:40 | FYI | Agent briefs the team doesn't need, for the final cleanup: `briefs/` (c27-design, hk-cli, hk-cli3, hk-data, hk-model, hk-research, hk-scrape). To decide: `briefing/` (event transcripts and brainstorm), and the OpenSpec tool copies in `.agents/skills/`, `.claude/` and `CLAUDE.md`. Keep `AGENTS.md`, `web/AGENTS.md` and `openspec/` | repo | cleanup agent at the end
- 12:16 | FYI | Duplicate fetch code: `ml/live.py` repeats the IEM and Open-Meteo downloads of `ml/fetch.py` with a second cache folder. `data/openmeteo_historical_forecast.parquet` duplicates `openmeteo_previous_runs.parquet` (day 0 identical) and no code reads it | `ml/live.py:22-159`, `data/` | cli owner, after 16:00
- 12:16 | FYI | `latest.json` was issued at 12:00 (11:00Z). It will be 5 h old at the 17:00 demo | `web/public/forecasts/latest.json` | cli owner: re-run `--now --out` before 16:00 and before the demo
- 12:16 | FYI | `origin/codex/condor-research` (Kai) has sources main lacks: DWD 01420 hourly gusts, MOSMIX station 10637, and Fraport's live OD and runway 18 status script, which would suit `--now`. Its README uses a 5 kt rule as the direction rule, which the official brief doesn't | branch `codex/condor-research` | Kai
- 12:16 | FYI | `origin/jayden/research`, `origin/jayden/data` and `origin/luca/weather-database` hold nothing that isn't on main | remote branches | head lane: delete when convenient
- 12:16 | FYI | OpenSpec tasks for wp1, wp5 and wp7 are all unchecked although the work landed. `briefs/hk-cli.md` and `hk-model.md` still say "PUSH IS PAUSED" | `openspec/changes/*/tasks.md`, `briefs/` | head lane
- 12:16 | FYI | `briefing/brainstorm-268.md:12,35` names a model and an agent account | `briefing/` | head lane
- 12:35 | FYI | Revised forecast uses persistence weights selected on inner chronological validation. OD accuracy at 1/6/24/48 h is 96.9/90.9/90.8/89.8%; 1 h matches rules and improves Brier 0.0310 to 0.0280. Publication-time limitations remain explicit in quality.json and ml/README.md; include them in the model card | `web/public/data/`, `ml/models/` | model-card owner
- 12:40 | FYI | All published forecasts now use walk-forward-v2. ForecastApp still labels the index-error fallback as "Live sample (rules only)" although sample.json now also uses the trained fit | `web/src/components/ForecastApp.tsx:26` | head lane: update fallback label
