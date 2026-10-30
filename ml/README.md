# ml/ · data, labels, model, backtest, forecast CLI (Python 3.13)

Owners: Kai (co-lead) and the Codex workers. Rules: `ml/rules.json` (from the official FraAlliance brief). Never hard-code a threshold anywhere else.

```bash
python -m pip install -r ml/requirements.txt
python -m ml.fetch            # raw data into data/raw/ (cached)
python -m ml.labels           # data/labels.parquet (half-hourly states from METAR + rules)
python -m ml.train            # model + backtest -> ml/models/, web/src/data/backtest.json
python -m ml.forecast --day 2026-10-31            # 48 h hourly table from 00:00 local that day
python -m ml.forecast --day 2026-10-31 --json     # same, as ForecastResponse JSON (web/src/lib/forecast-types.ts)
python -m pytest ml/tests -q                      # rule and leakage tests
```

## Sources (cite all of them in the model card)
- **EDDF METAR**, Iowa Environmental Mesonet ASOS archive: `https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=EDDF&...` (half-hourly wind direction, speed, gusts).
- **Archived weather-model forecasts**, Open-Meteo Previous Runs API: `https://previous-runs-api.open-meteo.com/v1/forecast` at EDDF (50.033 N, 8.570 E). `<var>_previous_day1` and `<var>_previous_day2` are values from runs issued about 1 and 2 days before the target hour, which keeps the backtest honest about lead time.
- **Live forecast**, Open-Meteo Forecast API: `https://api.open-meteo.com/v1/forecast`, same variable names.
- **Flown operating directions**, if found (DFLD, UNH/Fraport statistics, OpenSky): used to validate the METAR-derived labels. See `ml/SOURCES.md`.

## Labels
The official rules run as a state machine over the half-hourly METARs:
- A tailwind of 10 kt or more on the landing direction switches the OD immediately.
- A tailwind between 0 and 10 kt switches it after more than 30 minutes.
- Calm or variable wind keeps the current OD.
- Runway 18 is unusable when its tailwind is 15 kt or more, or its crosswind including gusts is over 40 kt.

The hourly label is the state at the full hour.

## Honest evaluation
- Issue time T. The model only uses what was known at T:
  - observations up to T
  - forecast runs issued before T (`previous_day1` for lead 1–24 h, `previous_day2` for lead 25–48 h)
- Train and test split by time. The test period comes after the training period and is never used for fitting.
- Report accuracy and Brier score at lead 1, 6, 24 (and 48) h against two baselines:
  - persistence
  - the official rules applied to the forecast wind
