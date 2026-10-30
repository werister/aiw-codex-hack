# hk-cli · `forecast --day`: the command the jury runs (WP4)

Worktree `C:\olawt\aiw-wt-cli`, branch `jayden/cli`. The head lane merges and talks to you through this terminal. You may use heavy subagents. Worker `hk-model` (branch `jayden/model`) writes `ml/rules.py`, `ml/features.py` and `ml/predict.py` (`predict_48h(...)`, see `briefs/hk-model.md`). Worker `hk-data3` (branch `jayden/data`) writes `ml/fetch.py` and `data/`. Ground truth (DFLD recorded OD) is on `origin/jayden/research` in `data/ground_truth/`.

Read first: `AGENTS.md`, `frankfurt-airport-operating-direction-forecast.md`, `ml/rules.json`, `web/src/lib/forecast-types.ts` (**your JSON must match `ForecastResponse` exactly**), `briefs/hk-model.md`, `openspec/changes/wp4-forecast-cli/` (tick tasks off).

## Push rule
After each small commit: `git pull --rebase origin main && git push origin HEAD:main`. Never force, never merge.

## You own (create only these)
`ml/forecast.py`, `ml/live.py`, `ml/tests/test_forecast_cli.py`, `web/public/forecasts/*.json` (except `sample.json`, which belongs to the head lane).

## The command
`python -m ml.forecast --day YYYY-MM-DD [--json] [--out PATH]` and `python -m ml.forecast --now [--json] [--out PATH]`.
- **Issue time:** 00:00 Europe/Berlin on `--day` (zoneinfo + tzdata), or the current full hour with `--now`. **Horizon:** 48 hourly steps, lead 1..48.
- **Only information available at the issue time.**
  - **Past day (hindcast):**
    - METAR up to the issue time (IEM ASOS EDDF);
    - the OD at the issue time, from the DFLD recorded history if covered, else from the rules on METAR (mark it inferred);
    - weather values for the target hours from the Open-Meteo Previous Runs API (`_previous_day1` for leads 1–24, `_previous_day2` for 25–48), fetched on demand for the needed dates and cached;
    - plus `observed`: the DFLD recorded OD for those hours where available, so the UI can show hits and misses.
  - **Today or future (live):**
    - the latest METAR (IEM, or `https://aviationweather.gov/api/data/metar?ids=EDDF&format=json&hours=3`);
    - the current OD: the rules on recent METARs, or UNH's public current direction if you can read it keylessly (https://www.umwelthaus.org/fluglaerm/anwendungen-service/aktuelle-betriebsrichtung-und-prognose/), cited;
    - Open-Meteo Forecast API (`https://api.open-meteo.com/v1/forecast`, `wind_speed_unit=kn`, same variables).
- **Predictor:** `ml.predict.predict_48h(...)`. Until `hk-model` has it, use a fallback that runs `ml.rules.od_state_machine` and `r18_usable` on the forecast wind. Its probabilities come from the tailwind margin, and it says `model_version: "rules-fallback"`. If `ml/rules.py` isn't there yet either, copy it in from `jayden/model` uncommitted, or write a private minimal version in `ml/forecast.py` that is clearly marked temporary.
- **Derived fields:**
  - `od` is 25 if `p_od25 >= 0.5`.
  - `certainty` = `round(100 × min(|2·p_od25 − 1|, |2·p_18_usable − 1|))`.
  - `next_change` is the first hour whose `od` differs from `current_od`. Its window is the neighbouring hours where p(new OD) is between 0.35 and 0.65.
  - `closures_18` are runs with `p_18_usable < 0.5`.
- **Output:** a readable 48-row table (local time | OD | P(OD 25) | P(18 usable) | certainty | rule OD | rule 18 | wind dir/kt/gust), then a "Next change: ..." line and the runway-18 closures. `--json` prints `ForecastResponse`; `--out` writes it.
- **Files for the UI:** `web/public/forecasts/latest.json` (`--now`), three hindcast days from October 2026 that contain at least one OD change and, if any exist, an 18 closure (`YYYY-MM-DD.json`), and `web/public/forecasts/index.json` = `{ "latest": "latest.json", "days": ["YYYY-MM-DD", ...] }`.
- **Test** (`ml/tests/test_forecast_cli.py`): a hindcast for a fixed past day returns 48 rows with valid fields, and no input timestamp after the issue time.

## Rules
- No AI assistant, model or vendor names in commit messages, trailers or files (say "head agent" or "our agents"). Never read or print keys or `.env*`. Polite API use with caching.
- Report in one line at each milestone: CLI runs on the fallback, hindcast plus live work, switched to `predict_48h`, files for the UI written. **First runnable CLI by 13:30.**
