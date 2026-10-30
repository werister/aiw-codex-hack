# Notices

Open problems across main, branches and worktrees. One line each: time (Berlin) | severity | what is wrong | where | who acts. `STOP` breaks main or makes the submission wrong, `FIX` should be fixed before 16:00, `FYI` is worth knowing. Delete a line once it is fixed. Rules: "Cross-checking" in `AGENTS.md`.

Main at 14:15 runs: `python -m pytest ml/tests -q` gives 53 passed, `python -m ml.forecast --day 2026-10-31` gives `walk-forward-v5`. The repo is now 165 MB of tracked files (`.git` 247 MB) after 33 commits from Kai's branch landed at 14:04.

## STOP

- 12:17 | STOP | Rule baseline drops the mild-tailwind timer known at issue time: 5 kt tailwind at T-20m and T with OD25 still predicts OD25 at T+1h instead of OD07; reproduced against the same state machine with the known timer | `ml/features.py:129-132`; the fallback in `ml/forecast.py` also starts with forecast rows only | model and cli owners: carry the observed hysteresis state into the forecast

## FIX



- 12:17 | FIX | Archived offset inputs bypass explicit `issued_at`/`retrieved_at` filtering: a fixture issued at T+2h is accepted for all 48 forecast rows at T despite the function contract | `ml/features.py:43-58` | model owner: enforce explicit availability metadata on archived inputs too

- 12:41 | FIX | Quality timing metrics can be null when there are no actual-change windows, but the UI types them as numbers and renders Math.round(null * 100) as 0%, falsely implying measured failure instead of unavailable data | `ml/quality.py:88-90`, `web/src/lib/forecast-types.ts:99`, `web/src/components/QualityPanel.tsx:50-51` | web owner: type nullable rates and display unavailable explicitly

- 12:41 | FIX | Future-day output now contains only the requested calendar day, while ForecastResponse and the UI still require 48 hours: with issue 2026-10-30T11:00Z and requested 2026-10-31, reproduced 24 rows with leads 12-35. The new day-view brief and the shared contract need coordinated handling | `ml/forecast.py:209-218`, `web/src/lib/forecast-types.ts:49`, `web/src/components/Timeline.tsx` | cli and web owners: preserve a full response with a separate day filter, or update the partial-day contract and UI together

- 14:00 | FIX | Jury test days are pending from FraAlliance (README "Jury test days", ea7a492), with 2026-10-31 and 2026-11-01 as the fallback at 15:30. No jury-day forecast files exist yet | README, `web/public/forecasts/` | Jayden or Hugo: dates; cli lane: generate and add to `index.json` by 15:30
- 13:10 | FIX | `ml.labels` does not exist. I removed it from the README run block; `ml/README.md:8` still lists it | `ml/README.md` | model lane, when committing
- 14:15 | FIX | Two decks claim `/pitch`: the head agent's static deck `web/public/pitch/index.html` (README "Finals deck") and Kai's React route `web/src/app/pitch/page.tsx` (AGENTS.md demo path "Pitch mode"). Next serves the React route at `/pitch`, so the README link doesn't open the deck it names. Hugo's static prototype `web/prototypes/dfs-forecast/` is also on main now | `web/public/pitch/`, `web/src/app/pitch/`, README, AGENTS.md | head agent, Kai, Hugo: pick one deck and one URL
- 13:55 | FIX | The live URL is in `SUBMISSION.md` and README (1a2f59f), but README says the site is private until sharing is switched on. The jury can't open it until then | `SUBMISSION.md:5`, README | Jayden: switch sharing on before 16:00 and check it in a private window
- 14:15 | FIX | `weather database/` is back to 76 MB with 29 third-party PDFs (76184d1 "consolidate weather research archives"), which undoes dfc3c5e. Copyright risk in the submission repo, and none of it feeds the model | `weather database/` | Luca and head agent: keep it on `luca/weather-database`
- 14:15 | FIX | Kai's 14:04 push added `assets/` (42 MB of 3D files) and `resources/` (21.6 MB): a second data pipeline (`resources/ml-support/forecast/fetch_forecast_data.py`, `observations/fetch_verify.py`, a 6 MB METAR CSV, Kaggle checks) that duplicates `ml/fetch.py` and `data/`, old copies of `forecast-types.ts` and `hk-model.md` in `resources/ml-support/reference/`, and Condor research for a different challenge | `resources/`, `assets/` | Kai: drop the duplicates, keep only what the app loads
- 14:15 | FIX | `npm run lint` in `web/` now fails with 23 errors, all `no-this-alias` in the vendored `web/public/pitch/vendor/three.module.min.js` (plus 1,441 warnings from the same file). `npm run build` still passes and serves `/pitch` from the React route | `web/eslint.config.mjs` | web owner: ignore `public/**/vendor/**`

## FYI

- 13:30 | FYI | Airport rebuild from shared main now passes all 9 GLB reimports, 1440-frame hull clearance/state/end-point checks, same-height surface checks and 3530 ground-position raycasts; verification.json hashes match current .blend and GLBs. Old-worktree media are stale; use main only. Motion preview is under separate validation | assets/airport/verification.json | Blender lane

- 13:29 | FYI | Publishing checkpoint: finish only the currently running airport rebuild and logo checks, then stop all source writes until the integration coordinator completes fetch/rebase/push. The user explicitly requests all work on main and publication; do not start another change during this checkpoint | shared main | all active file owners

- 13:31 | FYI | At 320 px, the widget recommendation's “Demand data unavailable” text overflows the viewport; its logo/header fits. Reproduced during branding verification | `web/src/components/Recommendation.tsx` via `/widget` | web owner: allow the compact traffic field to wrap


- 14:00 | FYI | October midnight issues: persistence still beats the model at 1-6 h (now 83.0% for the model; at lead 1 it is 86.2% vs 100%, n=29). The model card states it | `web/public/data/october.json` | model lane
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
