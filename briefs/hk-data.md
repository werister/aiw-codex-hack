# hk-data · download the data (download worker)

Worktree `C:\olawt\aiw-wt-data`, branch `jayden/data`. Download and document only: no labels, no model yet. The head lane merges and talks to you through this terminal. Worker `hk-research` researches sources in parallel (branch `jayden/research`, writes `DATA_AND_DECISIONS.md`). It may hand you more URLs through the head lane.

Read first: `AGENTS.md` (repo rules; **never mention any AI agent in commit messages or trailers**), `frankfurt-airport-operating-direction-forecast.md`, `ml/README.md`.

## Deliverables
1. `ml/__init__.py` and `ml/fetch.py` (`python -m ml.fetch [--since 2023-01-01]`): idempotent and cached, with polite sleeps and a User-Agent. It writes to `data/`.
2. **At least 2 years of hourly-or-better EDDF data, 2023-01-01 to today:**
   - **METAR EDDF** (IEM ASOS, half-hourly): `https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=EDDF&data=drct&data=sknt&data=gust&data=metar&year1=..&tz=Etc/UTC&format=onlycomma&latlon=no&missing=M&report_type=3`. I tested this one; chunk it by year.
   - **TAF EDDF** (IEM TAF archive; find the request URL, e.g. `cgi-bin/request/taf.py`).
   - **Open-Meteo Previous Runs API** at lat 50.033, lon 8.570, `wind_speed_unit=kn`. Get `wind_speed_10m`, `wind_direction_10m`, `wind_gusts_10m`, `pressure_msl`, `temperature_2m`, plus 80 m or 100 m wind if available, each as `_previous_day1` and `_previous_day2` (and day 0). Go as far back as it serves; 2024-01 works. Pressure-level variables don't support `_previous_dayN`.
   - **Open-Meteo Historical Forecast API** (best_match, same variables, no suffix), 2023 to today.
   - **DWD Open Data, station 01420 Frankfurt/Main:** the hourly wind (historical + recent zips) and the 10-minute wind (recent) from `https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/`.
   - **Live snapshot:** Open-Meteo Forecast API (next 72 h) and the latest METAR, saved with a timestamp, to show the live path works.
3. **Storage:** parquet files in `data/` (e.g. `data/eddf_metar.parquet`, `data/eddf_taf.parquet`, `data/openmeteo_previous_runs.parquet`, `data/openmeteo_historical_forecast.parquet`, `data/dwd_01420_wind_hourly.parquet`, `data/dwd_01420_wind_10min.parquet`). Commit them if each is under about 20 MB. Raw downloads go to `data/raw/` (add it to `.gitignore`). If a file is too big, commit a 1-month sample in `data/sample/` and keep the fetch script as the way to rebuild.
4. **`data/README.md`:** one row per file with source, exact URL pattern, period, rows, columns with units, time zone (UTC everywhere), retrieval time, licence or terms (Open-Meteo CC BY 4.0, DWD GeoNutzV, IEM). Add a short sanity section: METAR coverage (missing hours), the wind-direction distribution (share with a westerly vs easterly component), and the max gusts.
5. If any source needs an account or a key, **don't sign up and don't enter anything**. Write one line in `data/README.md` under "Needs an account" (source, why, sign-up URL) and tell the head lane.

## Rules
- Small commits (`data: add EDDF METAR 2023-2026`), `git fetch && git rebase origin/main` before every push, `git push -u origin jayden/data`. **Don't touch `main`.**
- Never read, print or write API keys or `.env*`.
- This PC has about 4 GB of free memory, so stream big files and process them in chunks.
- Report each push in one line, and finish with the data inventory (files, rows, period, size).
