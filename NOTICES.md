# Notices

Open problems across main, branches and worktrees. One line each: time (Berlin) | severity | what is wrong | where | who acts. `STOP` breaks main or makes the submission wrong, `FIX` should be fixed before 16:00, `FYI` is worth knowing. Delete a line once it is fixed. Rules: "Cross-checking" in `AGENTS.md`.

Main at 14:32 runs: `python -m pytest ml/tests -q` gives 54 passed. Lint ignores the vendored bundles since 2d0d773. No web build check this round because the disk is nearly full.

## STOP

- 14:32 | STOP | Drive C: on the build PC ran out of space at 14:17 (20 MB free). Git commits and fetches failed in the worktrees. The guardian deleted its own scratch build copies; 4.3 GB is free now, which is about eight `npm ci` runs or one large render | drive C: | head lane: check temp folders, node_modules copies and render output before more installs or renders
- 12:17 | STOP | Rule baseline drops the mild-tailwind timer known at issue time: 5 kt tailwind at T-20m and T with OD25 still predicts OD25 at T+1h instead of OD07; reproduced against the same state machine with the known timer | `ml/features.py:129-132`; the fallback in `ml/forecast.py` also starts with forecast rows only | model and cli owners: carry the observed hysteresis state into the forecast

## FIX




- 12:41 | FIX | Quality timing metrics can be null when there are no actual-change windows, but the UI types them as numbers and renders Math.round(null * 100) as 0%, falsely implying measured failure instead of unavailable data | `ml/quality.py:88-90`, `web/src/lib/forecast-types.ts:99`, `web/src/components/QualityPanel.tsx:50-51` | web owner: type nullable rates and display unavailable explicitly

- 12:41 | FIX | Future-day output now contains only the requested calendar day, while ForecastResponse and the UI still require 48 hours: with issue 2026-10-30T11:00Z and requested 2026-10-31, reproduced 24 rows with leads 12-35. The new day-view brief and the shared contract need coordinated handling | `ml/forecast.py:209-218`, `web/src/lib/forecast-types.ts:49`, `web/src/components/Timeline.tsx` | cli and web owners: preserve a full response with a separate day filter, or update the partial-day contract and UI together

- 14:00 | FIX | Jury test days are pending from FraAlliance (README "Jury test days", ea7a492), with 2026-10-31 and 2026-11-01 as the fallback at 15:30. No jury-day forecast files exist yet | README, `web/public/forecasts/` | Jayden or Hugo: dates; cli lane: generate and add to `index.json` by 15:30
- 14:15 | FIX | Ola references: local `C:\olawt\...` paths in the seven `briefs/*.md` and in `resources/ml-support/reference/hk-model.md:3` (new), plus the guardian's commit message f57b695. Personal paths too: `/Users/U751725/...` in `AGENTS.md:29` and `INTEGRATION.md:7`, `/Users/hugohader/...` in `web/prototypes/dfs-forecast/README.md:8` | listed files | cleanup agent at the end
- 14:15 | FYI | The static deck moved to `web/public/deck/` (3beb4b5), so `/pitch` is Kai's React route only. Check README and `PITCH.md` link the deck you present from. Hugo's static prototype `web/prototypes/dfs-forecast/` is also on main | `web/public/deck/`, `web/src/app/pitch/`, README | head lane, Hugo
- 13:55 | FIX | The live URL is in `SUBMISSION.md` and README (1a2f59f), but README says the site is private until sharing is switched on. The jury can't open it until then | `SUBMISSION.md:5`, README | Jayden: switch sharing on before 16:00 and check it in a private window
- 14:15 | FIX | `weather database/` is back to 76 MB with 29 third-party PDFs (76184d1 "consolidate weather research archives"), which undoes dfc3c5e. Copyright risk in the submission repo, and none of it feeds the model | `weather database/` | Luca and head lane: keep it on `luca/weather-database`
- 14:15 | FIX | Kai's 14:04 push added `assets/` (42 MB of 3D files) and `resources/` (21.6 MB): a second data pipeline (`resources/ml-support/forecast/fetch_forecast_data.py`, `observations/fetch_verify.py`, a 6 MB METAR CSV, Kaggle checks) that duplicates `ml/fetch.py` and `data/`, old copies of `forecast-types.ts` and `hk-model.md` in `resources/ml-support/reference/`, and Condor research for a different challenge | `resources/`, `assets/` | Kai: drop the duplicates, keep only what the app loads
- 14:32 | FIX | AI model names in files: `resources/ml-support/reference/forecast-types.ts:1`, `resources/ml-support/reference/hk-model.md:3`, `shared-skills/better/SKILL.md:6`, and new `briefing/experiments/v4-colab-october.md:30,32` and `briefing/reviews/kai-data-round2.md:50` ("Opus" as a reviewer). `resources/condor-challenge-research.md:69` cites Anthropic as a source | `resources/`, `shared-skills/`, `briefing/` | Kai, Hugo

## FYI

- 13:30 | FYI | Airport rebuild from shared main now passes all 9 GLB reimports, 1440-frame hull clearance/state/end-point checks, same-height surface checks and 3530 ground-position raycasts; verification.json hashes match current .blend and GLBs. Old-worktree media are stale; use main only. Motion preview is under separate validation | assets/airport/verification.json | Blender lane

- 13:29 | FYI | Publishing checkpoint: finish only the currently running airport rebuild and logo checks, then stop all source writes until the integration coordinator completes fetch/rebase/push. The user explicitly requests all work on main and publication; do not start another change during this checkpoint | shared main | all active file owners

- 13:31 | FYI | At 320 px, the widget recommendation's “Demand data unavailable” text overflows the viewport; its logo/header fits. Reproduced during branding verification | `web/src/components/Recommendation.tsx` via `/widget` | web owner: allow the compact traffic field to wrap


- 14:15 | FYI | October midnight issues, walk-forward-v5: on all recorded hours persistence beats the model at 1-6 h (83.0% vs 95.3%; lead 1 86.2% vs 100%) because 240 of 1,348 matched hours fall in the stuck DFLD run of 8-12 Oct (07 against 8-17 kt westerlies). Without them: 1-6 h 96.6% vs 94.6%, 7-24 h 96.8% vs rules 91.9%, 25-48 h 94.9% vs 85.1%. Quote both | `web/public/data/october.json` | model-card owner
- 13:30 | FYI | `PITCH.md` section 5 is titled "Built with Codex" and names Codex workers. That fits a Codex hackathon if intended, but AGENTS.md bans AI names in files | `PITCH.md:30-31` | head lane: decide
- 13:20 | FYI | The optional tower briefing (c0d210e) brings back `OPENAI_API_KEY` and `OPENAI_MODEL` in both `.env.example` files and `openai` in `ml/requirements.txt`. It reads keys only from git-ignored `.env.local` files and is off by default. Keep it that way, and don't show briefing text as model output | `ml/forecast.py:196`, `.env.example` | head lane
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
