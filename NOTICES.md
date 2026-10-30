# Notices

Open problems across main, branches and worktrees. One line each: time (Berlin) | severity | what is wrong | where | who acts. `STOP` breaks main or makes the submission wrong, `FIX` should be fixed before 16:00, `FYI` is worth knowing. Delete a line once it is fixed. Rules: "Cross-checking" in `AGENTS.md`.

Main at 14:00 runs: `python -m pytest ml/tests -q` gives 52 passed, `python -m ml.forecast --day 2026-10-31` gives `walk-forward-v5` issued at the current hour, and `web/` passes lint and build.

## STOP

- 12:17 | STOP | Rule baseline drops the mild-tailwind timer known at issue time: 5 kt tailwind at T-20m and T with OD25 still predicts OD25 at T+1h instead of OD07; reproduced against the same state machine with the known timer | `ml/features.py:129-132`; the fallback in `ml/forecast.py` also starts with forecast rows only | model and cli owners: carry the observed hysteresis state into the forecast

## FIX

- 13:22 | FIX | The consolidated airport environment GLB is 16,306,028 bytes and fails the verifier's 15,000,000-byte limit; the saved scene report also contains terminal/runway and aircraft/terminal overlaps. The user explicitly requested consolidation and publication; these checks remain failed | `tools/blender/verify_assets.py`, `assets/airport/verification.json` | airport asset owner: repair and rerun checks

- 12:17 | FIX | Archived offset inputs bypass explicit `issued_at`/`retrieved_at` filtering: a fixture issued at T+2h is accepted for all 48 forecast rows at T despite the function contract | `ml/features.py:43-58` | model owner: enforce explicit availability metadata on archived inputs too

- 12:41 | FIX | Quality timing metrics can be null when there are no actual-change windows, but the UI types them as numbers and renders Math.round(null * 100) as 0%, falsely implying measured failure instead of unavailable data | `ml/quality.py:88-90`, `web/src/lib/forecast-types.ts:99`, `web/src/components/QualityPanel.tsx:50-51` | web owner: type nullable rates and display unavailable explicitly

- 12:41 | FIX | Future-day output now contains only the requested calendar day, while ForecastResponse and the UI still require 48 hours: with issue 2026-10-30T11:00Z and requested 2026-10-31, reproduced 24 rows with leads 12-35. The new day-view brief and the shared contract need coordinated handling | `ml/forecast.py:209-218`, `web/src/lib/forecast-types.ts:49`, `web/src/components/Timeline.tsx` | cli and web owners: preserve a full response with a separate day filter, or update the partial-day contract and UI together

- 14:00 | FIX | Jury test days are pending from FraAlliance (README "Jury test days", ea7a492), with 2026-10-31 and 2026-11-01 as the fallback at 15:30. No jury-day forecast files exist yet | README, `web/public/forecasts/` | Jayden or Hugo: dates; cli lane: generate and add to `index.json` by 15:30
- 13:10 | FIX | `ml.labels` does not exist. I removed it from the README run block; `ml/README.md:8` still lists it | `ml/README.md` | model lane, when committing
- 13:20 | FIX | Ola references: seven agent briefs contain local `C:\olawt\...` worktree paths (`c27-design.md` has two), and the guardian's own commit message f57b695 on main contains the word. Changing that message would mean rewriting main, so leave it to the cleanup decision | `briefs/c27-design.md`, `hk-cli.md`, `hk-cli3.md`, `hk-data.md`, `hk-model.md`, `hk-research.md`, `hk-scrape.md`, commit f57b695 | cleanup agent at the end
- 13:00 | FIX | Main now has the FraAlliance styling and the recommendation view (0cf65aa, c5d906e), but `origin/hugo/forecast-ui-spec` still carries a separate static prototype (`web/prototypes/dfs-forecast/`) and a wp5 spec written against the old placeholder page (`briefing/2026-10-30-ui-atc-context.md`). Hugo presents from an outdated picture of the UI | branch `hugo/forecast-ui-spec` | Hugo: rebase and review the current app
- 13:55 | FIX | The live URL is in `SUBMISSION.md` and README (1a2f59f), but README says the site is private until sharing is switched on. The jury can't open it until then | `SUBMISSION.md:5`, README | Jayden: switch sharing on before 16:00 and check it in a private window
- 13:30 | FIX | Kai's `origin/codex/blender-airport-assets` branched from 9558d79 (about 11:20) and carries 11 duplicate copies of early main commits, 51 MB of 3D files (`airport-environment.glb` is 16 MB, plus a 3 MB `.blend`), a 71-line README rewrite, AGENTS.md edits, and old file versions that name an AI model as head agent. Merging it as is would conflict and bring that back | branch `codex/blender-airport-assets` | Kai and head lane: take only the needed assets, no merge

## FYI

- 13:15 | FYI | Blender lane owns `tools/blender/` and `assets/airport/` through final spatial/playback checks; source scripts are already copied identically, replacing only stale intermediate media with the completed render. Preserved prior main media in `/tmp/fra-main-preserved-1315`. Do not stage these paths until verification is passed. OpenSpec CLI is unavailable; no spec artifacts changed | shared main | Blender lane

- 13:20 | FYI | `weather database/` is down to 5.7 MB on main after dfc3c5e moved the PDFs and the BTS zip to Luca's branch. It is still outside the runway forecast and has a space in its name | `weather database/` | cleanup agent at the end
- 14:00 | FYI | October midnight issues: persistence still beats the model at 1-6 h (now 83.0% for the model; at lead 1 it is 86.2% vs 100%, n=29). The model card states it | `web/public/data/october.json` | model lane
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
