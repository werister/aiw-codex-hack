# hk-data · data, official rules, labels (Codex worker, head lane `hackathon`)

Worktree `C:\olawt\aiw-wt-data`, branch `jayden/data`. Head lane merges and talks to you through this terminal. A second worker, `hk-model`, builds the model in another worktree. Kai Detmers (human, ML co-lead) may push too, so always `git fetch && git rebase origin/main` before pushing.

Read first: `AGENTS.md` (repo rules: rebase only, small commits, `main` always runs), `frankfurt-airport-operating-direction-forecast.md` (the official brief, wins over everything), `ml/README.md`, `ml/rules.json`.

## You own (create only these)
`ml/__init__.py`, `ml/rules.py`, `ml/fetch.py`, `ml/labels.py`, `ml/tests/__init__.py`, `ml/tests/test_rules.py`, `ml/SOURCES.md`, `ml/requirements.txt` (add `pytest`), `ml/data/labels.parquet`, `ml/data/nwp.parquet`. Raw downloads go to `ml/data/raw/` (git-ignored).

## 1. `ml/rules.py`: the official rules as pure code (first, with tests)
Read every threshold from `ml/rules.json`.
- `tailwind(speed_kt, dir_deg, heading_deg)` = speed × cos(dir − heading − 180°). `crosswind(...)` = |speed × sin(dir − heading)|.
- `r18_usable(speed, gust, dir)`: False if the tailwind on heading 180 is ≥ 15 kt, or the crosswind with gusts is > 40 kt.
- `od_state_machine(obs, initial_od)`: `obs` is a time-ordered sequence of (time, dir or None, speed, gust). OD is "25" (heading 250) or "07" (heading 070). Landings decide it:
  - tailwind on the current OD ≥ 10 kt → switch now;
  - 0 < tailwind < 10 kt continuously for more than 30 minutes → switch to the headwind direction;
  - calm or variable (dir None) → keep the current OD.
  - Returns the OD after each observation.
- Tests in `ml/tests/test_rules.py` with the brief's own examples:
  - 090° at 20 kt gives about 19 kt tailwind on 25, so OD 07.
  - 330° at 20 kt gives about 17.3 kt tailwind on 18, so 18 closed.
  - 20 kt at 30° off straight behind gives 17.3, and at 45° off gives 14.1.
  - hysteresis: 5 kt tailwind for 20 min stays, for 40 min switches; 12 kt switches at once; VRB holds.

## 2. `ml/fetch.py`: cached downloads (`python -m ml.fetch`)
- **IEM METAR EDDF**, 2023-01-01 to today, chunked by year: `https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=EDDF&data=drct&data=sknt&data=gust&data=metar&year1=..&tz=Etc/UTC&format=onlycomma&latlon=no&missing=M&report_type=3` (I tested this URL; it works).
- **Open-Meteo Previous Runs API** at lat 50.033, lon 8.570, `wind_speed_unit=kn`, hourly, as far back as it serves data (probe; 2024-01 works), chunked by about 3 months. Get `wind_speed_10m`, `wind_direction_10m`, `wind_gusts_10m`, `pressure_msl`, `temperature_2m`, plus the 80 m or 100 m wind if available, each with `_previous_day1` and `_previous_day2`. Pressure-level variables are not supported with `_previous_dayN` (I tested this). Sleep between calls and set a User-Agent.
- `ml/data/nwp.parquet`: hourly UTC, one column per variable and day offset.

## 3. `ml/labels.py`: labels (`python -m ml.labels`)
- Parse the METARs (VRB → dir None). Run `od_state_machine` over the half-hourly sequence (start "25"). Compute `r18_usable` per observation.
- Hourly label = state after the last observation at or before the full hour. Write `ml/data/labels.parquet` with `time` (UTC), `od`, `r18_usable`, `obs_dir`, `obs_kt`, `obs_gust`, `tailwind_25`, `tailwind_18`, `minutes_since_change`.
- Print the sanity stats: OD 25 share (FraAlliance says 61%), changes per year (they say 156), share of hours with 18 closed. Do **not** tune the official rules to hit those numbers; just report them.

## 4. Flown operating directions (time-box 20 min)
The jury grades against **directions actually flown**. Look for a public history of the FRA operating direction: DFLD.de, UNH (umwelthaus.org: Betriebsrichtung statistics, a public Betriebsrichtungsprognose), Fraport. If you find usable daily or hourly data, download a sample and measure how well our labels agree. Either way, write `ml/SOURCES.md` listing every source with its URL, what we use it for and the retrieval date.

## Checks, then report
- `python -m pytest ml/tests -q` passes, and `python -m ml.labels` prints the stats.
- Commit in small steps (`feat: ...`), `git fetch && git rebase origin/main`, `git push -u origin jayden/data` (use `--force-with-lease` only on your branch). **Don't touch `main`**; the head fast-forwards it.
- Never read, print or write API keys or `.env*`.
- Push the **rules + tests first** (as soon as they pass), because `hk-model` needs `ml/rules.py`. Then data, then labels. Report each push in one line, and finish with the sanity stats.
