# Windy connection check

Set `WINDY_POINT_FORECAST_API_KEY` in the environment or the ignored root
`.env.local`, then run `python -m ml.windy` (or add `--json` for metadata).
`--model iconEu` checks ICON-EU instead of the default GFS. Use a **Point Forecast**
key from [Windy Keys](https://api.windy.com/keys); Plugins and Map Forecast keys
are different services. Never put this key in browser environment variables.

The command checks authentication, timestamps, units and matching wind/gust/pressure
arrays. It prints counts and response metadata, never the key or weather values,
and exits nonzero on missing credentials, HTTP errors or malformed responses.
It makes one request per invocation and does not cache data or write files.

Windy's free [Testing tier](https://api.windy.com/point-forecast/pricing) returns
randomly shuffled and slightly modified data for development only. A successful
check proves connectivity, not real Frankfurt weather or forecast quality.
The command always reports `operational_use: false`, including with another key.
These values are excluded from training, backtests, the forecast CLI and dashboard;
Open-Meteo and METAR remain their inputs. Using a Professional key as a model input
would require a separately evaluated integration.

Verification: `python3.13 -m unittest ml.tests.test_windy -v`.
