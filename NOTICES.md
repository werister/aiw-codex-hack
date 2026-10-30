# Notices

Open problems across main, branches and worktrees. One line each: time (Berlin) | severity | what is wrong | where | who acts. `STOP` breaks main or makes the submission wrong, `FIX` should be fixed before 16:00, `FYI` is worth knowing. Delete a line once it is fixed. Rules: "Cross-checking" in `AGENTS.md`.

Main at 14:32 runs: `python -m pytest ml/tests -q` gives 54 passed. Lint ignores the vendored bundles since 2d0d773. No web build check this round because the disk is nearly full.

## STOP

- 14:32 | STOP | Drive C: on the build PC ran out of space at 14:17 (20 MB free). Git commits and fetches failed in the worktrees. The guardian deleted its own scratch build copies; 4.3 GB is free now, which is about eight `npm ci` runs or one large render | drive C: | head agent: check temp folders, node_modules copies and render output before more installs or renders
- 12:17 | STOP | Rule baseline drops the mild-tailwind timer known at issue time: 5 kt tailwind at T-20m and T with OD25 still predicts OD25 at T+1h instead of OD07; reproduced against the same state machine with the known timer | `ml/features.py:129-132`; the fallback in `ml/forecast.py` also starts with forecast rows only | model and cli owners: carry the observed hysteresis state into the forecast

## FIX




- 12:41 | FIX | Quality timing metrics can be null when there are no actual-change windows, but the UI types them as numbers and renders Math.round(null * 100) as 0%, falsely implying measured failure instead of unavailable data | `ml/quality.py:88-90`, `web/src/lib/forecast-types.ts:99`, `web/src/components/QualityPanel.tsx:50-51` | web owner: type nullable rates and display unavailable explicitly

- 12:41 | FIX | Future-day output now contains only the requested calendar day, while ForecastResponse and the UI still require 48 hours: with issue 2026-10-30T11:00Z and requested 2026-10-31, reproduced 24 rows with leads 12-35. The new day-view brief and the shared contract need coordinated handling | `ml/forecast.py:209-218`, `web/src/lib/forecast-types.ts:49`, `web/src/components/Timeline.tsx` | cli and web owners: preserve a full response with a separate day filter, or update the partial-day contract and UI together

- 14:00 | FIX | Jury test days are pending from FraAlliance (README "Jury test days", ea7a492), with 2026-10-31 and 2026-11-01 as the fallback at 15:30. No jury-day forecast files exist yet | README, `web/public/forecasts/` | Jayden or Hugo: dates; cli lane: generate and add to `index.json` by 15:30
- 14:15 | FYI | The static deck moved to `web/public/deck/` (3beb4b5), so `/pitch` is Kai's React route only. Check README and `PITCH.md` link the deck you present from. Hugo's static prototype `web/prototypes/dfs-forecast/` is also on main | `web/public/deck/`, `web/src/app/pitch/`, README | head agent, Hugo
- 13:55 | FIX | The live URL is in `SUBMISSION.md` and README (1a2f59f), but README says the site is private until sharing is switched on. The jury can't open it until then | `SUBMISSION.md:5`, README | Jayden: switch sharing on before 16:00 and check it in a private window
- 14:15 | FIX | `weather database/` is back to 76 MB with 29 third-party PDFs (76184d1 "consolidate weather research archives"), which undoes dfc3c5e. Copyright risk in the submission repo, and none of it feeds the model | `weather database/` | Luca and head agent: keep it on `luca/weather-database`
- 14:15 | FIX | Kai's 14:04 push added `assets/` (42 MB of 3D files) and `resources/` (21.6 MB): a second data pipeline (`resources/ml-support/forecast/fetch_forecast_data.py`, `observations/fetch_verify.py`, a 6 MB METAR CSV, Kaggle checks) that duplicates `ml/fetch.py` and `data/`, old copies of `forecast-types.ts` and `hk-model.md` in `resources/ml-support/reference/`, and Condor research for a different challenge | `resources/`, `assets/` | Kai: drop the duplicates, keep only what the app loads

## FYI

- 14:16 | FYI | User-approved shift-planning implementation in progress: event overview owns Hero/Recommendation/ForecastEvents and forecast-events; handover owns ForecastAssistant/forecast-explanation; demo owns pitch components/pitch-replay/runway18-demo; head agent owns ForecastApp/Widget and WP5/docs. Preserve these edits; staging and commits are serialized by this head agent | shared main, `web/`, WP5 | shift-planning lane


- 13:29 | FYI | Publishing checkpoint: finish only the currently running airport rebuild and logo checks, then stop all source writes until the integration coordinator completes fetch/rebase/push. The user explicitly requests all work on main and publication; do not start another change during this checkpoint | shared main | all active file owners

- 13:31 | FYI | At 320 px, the widget recommendation's “Demand data unavailable” text overflows the viewport; its logo/header fits. Reproduced during branding verification | `web/src/components/Recommendation.tsx` via `/widget` | web owner: allow the compact traffic field to wrap


- 14:15 | FYI | October midnight issues, walk-forward-v5: on all recorded hours persistence beats the model at 1-6 h (83.0% vs 95.3%; lead 1 86.2% vs 100%) because 240 of 1,348 matched hours fall in the stuck DFLD run of 8-12 Oct (07 against 8-17 kt westerlies). Without them: 1-6 h 96.6% vs 94.6%, 7-24 h 96.8% vs rules 91.9%, 25-48 h 94.9% vs 85.1%. Quote both | `web/public/data/october.json` | model-card owner
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
- 14:06 | FYI | Airport AA/60 fps upgrade transferred from detached integration worktree to main: all 3,600 native frames and all 9 GLBs passed; verification hashes match. Remaining high-AA PNGs render in the already-running process; final 60 fps MP4 pending. Assets/source owned by Blender lane; do not replace with v6 snapshots | tools/blender; assets/airport | Blender lane

- 14:07 | FYI | User approved the algorithm-review fixes. ML time/availability, event scoring and day-block comparisons are being prepared and tested together; this lane owns the corresponding ml source/tests and the next model/quality artifacts. Keep current artifacts until the coherent replacement passes. No Git mutation from this lane while integration is active | ml/rules.py, ml/features.py, ml/forecast.py, ml/quality.py, ml/significance.py, ml/train.py, ml/predict.py | algorithm implementation lane

- 14:10 | FIX | Hero labels the first forecast row's runway-18 probability as "Now", while the same heading uses OD at issue time; a closure forecast for T+1 is presented as current runway state. Label runway 18 with its forecast validity time, as required by WP5 | `web/src/components/Hero.tsx:23-54` | web owner

- 14:22 | FYI | Isolated web typecheck currently stops on ongoing UI integration: ForecastApp/Widget pass onSelectHour before Recommendation accepts it; TimeScrubber/ForecastAssistant import helpers not yet exported by forecast-explanation. ML quality type changes are prepared separately; rerun web checks after the UI owner completes these modules | web/src/components; web/src/lib/forecast-explanation.ts | UI owner
- 14:30 | FYI | User now requires forecast-controlled Blender models in the cockpit. Blender lane owns SceneHero.tsx, new web/src/lib/airport-scene.ts and airport-traffic.ts/tests, web/public/models/airport, Three.js dependency entries, and WP9 artifacts; only selected-hour metadata props will touch the existing SceneHero call. ForecastApp/ML owners retain their current work. Render media continue separately | WP9 | Blender lane

- 14:33 | FYI | Time-guide lane finished forecast-explanation.ts/tests (12 tests pass), TimeScrubber.tsx/.css and selected-hour/session-key additions in ForecastAssistant; handover additions currently preserve those changes. New DirectionBand.tsx is ready for event-overview owner to import into Hero instead of the separate issue-direction and first-hour blocks. Awaiting Hero integration and shared browser smoke; do not replace these helper exports | web/src/components/DirectionBand.tsx; TimeScrubber; ForecastAssistant; web/src/lib/forecast-explanation | time-guide and event-overview owners

- 14:33 | FIX | SceneHero still imports /pitch/scene.js after the shared scene moved to /deck/scene.js in 3beb4b5; dashboard and widget fall back to the schematic map. Confirmed from pinned 40af4ef paths and mount code | `web/src/components/SceneHero.tsx:11` | web scene owner

- 14:33 | FIX | suspect_od_runs raises MergeError on committed truth/METAR inputs with pandas 3: datetime64[us, UTC] versus datetime64[ns, UTC]. Isolated reproduction at 40af4ef; normalize keys at this merge boundary | `ml/quality.py:20` | algorithm implementation lane

- 14:33 | FIX | Overlapping ownership claims for ForecastAssistant and forecast-explanation: the existing interaction lane has edits in flight while the shift-planning handover lane claims the same files. Reserve one writer per file and preserve both pending changes before staging; the monitor will not rebase this active tree | `web/src/components/ForecastAssistant.tsx`, `web/src/lib/forecast-explanation.ts` and its test | interaction and shift-planning owners
- 14:40 | FIX | Current full web typecheck fails at PitchApp.tsx:218: number is not assignable to 1|6|24|48. New 3D renderer lint is clean; this independent pitch edit blocks a clean global tsc run | web/src/components/pitch/PitchApp.tsx:218 | pitch owner
