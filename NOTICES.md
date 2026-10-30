# Notices

Open problems across main, branches and worktrees. One line each: time (Berlin) | severity | what is wrong | where | who acts. `STOP` breaks main or makes the submission wrong, `FIX` should be fixed before 16:00, `FYI` is worth knowing. Delete a line once it is fixed. Rules: "Cross-checking" in `AGENTS.md`.

Main at 14:00 runs: `python -m pytest ml/tests -q` gives 52 passed, `python -m ml.forecast --day 2026-10-31` gives `walk-forward-v5` issued at the current hour, and `web/` passes lint and build.

## STOP

- None open.

## FIX

- 14:00 | FIX | Jury test days are pending from FraAlliance (README "Jury test days", ea7a492), with 2026-10-31 and 2026-11-01 as the fallback at 15:30. No jury-day forecast files exist yet | README, `web/public/forecasts/` | Jayden or Hugo: dates; cli lane: generate and add to `index.json` by 15:30
- 13:10 | FIX | `ml.labels` does not exist. I removed it from the README run block; `ml/README.md:8` still lists it | `ml/README.md` | model lane, when committing
- 13:20 | FYI | `weather database/` is down to 5.7 MB on main after dfc3c5e moved the PDFs and the BTS zip to Luca's branch. It is still outside the runway forecast and has a space in its name | `weather database/` | cleanup agent at the end
- 13:10 | FYI | October midnight issues: persistence still beats the model at 1-6 h (95.3% vs 84.2%). `MODEL_CARD.md` states it, and the model lane is tuning the blend | `web/public/data/october.json` | model lane
- 13:00 | FIX | Main now has the FraAlliance styling and the recommendation view (0cf65aa, c5d906e), but `origin/hugo/forecast-ui-spec` still carries a separate static prototype (`web/prototypes/dfs-forecast/`) and a wp5 spec written against the old placeholder page (`briefing/2026-10-30-ui-atc-context.md`). Hugo presents from an outdated picture of the UI | branch `hugo/forecast-ui-spec` | Hugo: rebase and review the current app
- 13:55 | FIX | The live URL is in `SUBMISSION.md` and README (1a2f59f), but README says the site is private until sharing is switched on. The jury can't open it until then | `SUBMISSION.md:5`, README | Jayden: switch sharing on before 16:00 and check it in a private window
- 13:30 | FIX | Kai's `origin/codex/blender-airport-assets` branched from 9558d79 (about 11:20) and carries 11 duplicate copies of early main commits, 51 MB of 3D files (`airport-environment.glb` is 16 MB, plus a 3 MB `.blend`), a 71-line README rewrite, AGENTS.md edits, and old file versions that name an AI model as head agent. Merging it as is would conflict and bring that back | branch `codex/blender-airport-assets` | Kai and head agent: take only the needed assets, no merge

## FYI

- 13:30 | FYI | `PITCH.md` section 5 is titled "Built with Codex" and names Codex workers. That fits a Codex hackathon if intended, but AGENTS.md bans AI names in files | `PITCH.md:30-31` | head agent: decide
- 13:20 | FYI | The optional tower briefing (c0d210e) brings back `OPENAI_API_KEY` and `OPENAI_MODEL` in both `.env.example` files and `openai` in `ml/requirements.txt`. It reads keys only from git-ignored `.env.local` files and is off by default. Keep it that way, and don't show briefing text as model output | `ml/forecast.py:196`, `.env.example` | head agent
- 13:10 | FYI | UI details: the backup option says "Live sample (rules only)" but `sample.json` is the trained model (`ForecastApp.tsx:30`); the 40 kt crosswind limit is shown nowhere; nothing reads `backtest.json` or `october.json` | `web/src/components/` | web owner
- 13:00 | FYI | `data/ground_truth/dfld_hourly.csv` grew to 6.1 MB (history from 2018, 33a7847), and two new runway 18 CSVs add 3.9 MB. `ml/dfld.py` can rebuild them; gzip them like `dfld_half_hourly.csv.gz` if size matters | `data/ground_truth/` | data owner
- 13:00 | FYI | `origin/luca/weather-database` has one more commit (0c8f4da, 72 files, about 101k lines of weather archive and an advisory board) that is not on main. Keep it off main | branch `luca/weather-database` | Luca
- 12:52 | FYI | `README.md` now has a "fleet-wide planning" product direction (b8f1226) with planning recommendations and traffic exposure, which we don't build. The doc says so itself. Keep pitch claims to what runs | `README.md`, `briefing/fleet-planning.md` | Hugo
- 12:52 | FYI | Personal path in a committed file on Hugo's branch: `/Users/hugohader/dev/...` in `web/prototypes/dfs-forecast/README.md` | branch `hugo/forecast-ui-spec` | cleanup agent at the end
- 12:16 | FYI | Duplicate fetch code: `ml/live.py` repeats the IEM and Open-Meteo downloads of `ml/fetch.py` with a second cache folder. `data/openmeteo_historical_forecast.parquet` duplicates `openmeteo_previous_runs.parquet` (day 0 identical) and no code reads it | `ml/live.py:22-159`, `data/` | cli owner, after 16:00
- 12:16 | FYI | `latest.json` was issued at 12:00 (11:00Z). It will be 5 h old at the 17:00 demo | `web/public/forecasts/latest.json` | cli owner: re-run `--now --out` before 16:00 and before the demo
- 12:16 | FYI | `origin/codex/condor-research` (Kai) has sources main lacks: DWD 01420 hourly gusts, MOSMIX station 10637, and Fraport's live OD and runway 18 status script, which would suit `--now`. Its README uses a 5 kt rule as the direction rule, which the official brief doesn't | branch `codex/condor-research` | Kai
- 12:16 | FYI | `origin/jayden/research`, `origin/jayden/data` and `origin/luca/weather-database` hold nothing that isn't on main | remote branches | head agent: delete when convenient
- 12:16 | FYI | OpenSpec tasks for wp1, wp5 and wp7 are all unchecked although the work landed. the CLI and model briefs still say "PUSH IS PAUSED" | `openspec/changes/*/tasks.md` | head agent
- 12:16 | FYI | `briefing/brainstorm-268.md:12,35` names a model and an agent account | `briefing/` | head agent
- 12:35 | FYI | Revised forecast uses persistence weights selected on inner chronological validation. OD accuracy at 1/6/24/48 h is 96.9/90.9/90.8/89.8%; 1 h matches rules and improves Brier 0.0310 to 0.0280. Publication-time limitations remain explicit in quality.json and ml/README.md; include them in the model card | `web/public/data/`, `ml/models/` | model-card owner
- 12:40 | FYI | All published forecasts now use walk-forward-v2. ForecastApp still labels the index-error fallback as "Live sample (rules only)" although sample.json now also uses the trained fit | `web/src/components/ForecastApp.tsx:26` | head agent: update fallback label
