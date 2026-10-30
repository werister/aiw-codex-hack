# hk-model · model, backtest, forecast CLI (Codex worker, head lane `hackathon`)

Worktree `C:\olawt\aiw-wt-model`, branch `jayden/model`. Head lane merges and talks to you through this terminal. Worker `hk-data` (branch `jayden/data`) builds `ml/rules.py`, `ml/fetch.py`, `ml/labels.py`, `ml/data/labels.parquet` and `ml/data/nwp.parquet`. It pushes the rules first, then the data. Kai Detmers (human, ML co-lead) may push too.

Read first: `AGENTS.md`, `frankfurt-airport-operating-direction-forecast.md` (official brief: wins over everything), `ml/README.md`, `ml/rules.json`, `web/src/lib/forecast-types.ts` (**the JSON you output must match `ForecastResponse` and `BacktestResult` exactly**), `briefs/hk-data.md` (the schemas you consume).

## You own (create only these)
`ml/features.py`, `ml/train.py`, `ml/forecast.py`, `ml/live.py` (live observations and live forecast fetch), `ml/models/` (small saved models, committed), `ml/tests/test_no_leakage.py`, `web/src/data/backtest.json`, `web/public/forecasts/*.json`. Ask the head lane if you need something in `ml/requirements.txt`.

## Problem setup (honest, no leakage)
- Issue time T (every hour, or every 3 h if it's too slow). For lead h = 1..48, the target is the label at T+h: OD (25 or 07) and runway 18 usable.
- **Features may only use what was known at T:**
  - the state at T: OD, `r18_usable`, `minutes_since_change`, observed tailwinds and the 3 h trend, all from labels up to T;
  - weather-model values for the target hour, from `_previous_day1` for h ≤ 24 and `_previous_day2` for h > 24 (those runs were issued before T);
  - derived tailwind and crosswind components;
  - hour of day (local) and season (sin/cos day of year);
  - h itself;
  - **the rule baseline as a feature**: run `ml.rules.od_state_machine` forward from the state at T over the hourly forecast winds.
- Baselines:
  1. **persistence**: the state at T carried forward;
  2. **rules**: the official rules on the forecast wind, starting from the state at T. This is the bar to beat.
- Model: `HistGradientBoostingClassifier` (one model for P(OD 25), one for P(18 usable)). Time split: train on the earlier part, test on the last 4 or more months, never fitted on.

## Deliverables
1. `python -m ml.train`: builds features, trains, evaluates, saves the models to `ml/models/`, and writes `web/src/data/backtest.json` (`BacktestResult`). It holds accuracy and Brier score at leads **1, 6, 24, 48** for model / rules / persistence, base rates, and the top 8 drivers (permutation importance). Print the skill table.
2. `python -m ml.forecast --day YYYY-MM-DD [--json] [--out PATH]`: **first-class, the jury runs this on their test days.** Issue time = 00:00 Europe/Berlin on that day, horizon 48 h.
   - **Past day (hindcast):** observations from IEM up to the issue time, weather from the Previous Runs API (fetch the needed dates on demand if they aren't in `nwp.parquet`), plus `observed` (the rule labels after the fact) so the UI can show the hits.
   - **Today or future:** latest METAR (IEM, or `https://aviationweather.gov/api/data/metar?ids=EDDF&format=json&hours=3`), and the live forecast from `https://api.open-meteo.com/v1/forecast` (same variables, `wind_speed_unit=kn`).
   - Also support `--now` (issue time = the current hour).
   - Prints a readable 48-row table: local time, OD, P(OD 25), P(18 usable), certainty, rule OD, rule 18, wind. Then the next change line.
   - With `--json` it prints a `ForecastResponse`.
   - `certainty` = 0–100 from the two probabilities: `100 × min(|2·p_od25 − 1|, |2·p_18_usable − 1|)`.
   - `next_change` = the first hour where the model's OD differs from `current_od`. Its window spans the neighbouring hours where p(new OD) is between 0.35 and 0.65.
   - `closures_18` = runs of hours with p_18_usable < 0.5.
3. Write example outputs with `--json --out`: `web/public/forecasts/latest.json` (`--now`) and three hindcast days from the test period with at least one OD change and one runway-18 closure (name them `YYYY-MM-DD.json`), plus `web/public/forecasts/index.json` listing `{ "days": [...], "latest": "latest.json" }`.
4. `ml/tests/test_no_leakage.py`: for a few issue times, assert that no feature uses an observation after T, and that the weather-model offset matches the lead.

## Order and timing
Start now on `features.py`, `train.py` and `forecast.py` against the schemas. Use a tiny synthetic frame until `hk-data` pushes. The head lane tells you when `jayden/data` lands on `main`; then `git fetch && git rebase origin/main` and run on real data. **Target: first real skill table by 13:30.**

## Rules
- Small commits, `git fetch && git rebase origin/main` before every push, `git push -u origin jayden/model`. **Don't touch `main`**; the head fast-forwards it.
- Never read, print or write API keys or `.env*`. This work uses no API key.
- Keep memory low: this PC has about 4 GB free. No deep learning, no huge grids.
- Report each push in one line, and finish with the skill table and the CLI output for one test day.
