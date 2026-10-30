# Frankfurt runway forecast: preparation

Prepared 30 October 2026. Question: which verified resources can support the
FraAlliance 48-hour runway forecast challenge before the presentation arrives?

## Challenge from the supplied transcript

Predict the next 48 hours of:

- Runway 18 availability for departures, including likely closure/reopening times.
- Parallel-runway operating direction: 07 (eastbound) or 25 (westbound), including changes.

The intended users plan ground handling, staffing and connections. The presentation
and one-pager are **pending from the user**. Exact challenge thresholds, averaging
periods, gust handling and evaluation criteria remain unconfirmed.

## Downloaded locally

18 source files (5.91 MB) are under `resources/raw/`. Original files are ignored by
Git; [sources.json](sources.json) records their URLs, retrieval times, sizes and
SHA-256 hashes. [data-inventory.json](data-inventory.json) records inspected fields
and date ranges.

| Resource | Verified contents |
| --- | --- |
| DWD station 01420, Frankfurt/Main | Hourly wind speed and direction: 503,249 historical rows, 1967–2025; 13,090 recent rows, April 2025–29 October 2026. Archives overlap. |
| DWD station 01420, gusts | 219,192 historical rows, 1990–2025; 13,079 recent rows through 29 October 2026. Archives overlap. |
| DWD MOSMIX station 10637, FRANKFURT/M | Forecast issued 30 October 2026 at 03:00 UTC; 247 time steps through 9 November. Wind direction `DD`, wind speed `FF`, gusts `FX1` are present without missing values. |
| Windy | Point Forecast documentation and plan details; Map Forecast documentation and tutorials. |
| Fraport / Umwelthaus | Operating-direction explanations, current-status pages, Fraport status script and Umwelthaus forecast page. |
| DWD documentation | Hourly-wind description, MOSMIX method, parameter list and KML format. |

The row counts and dates above come from the downloaded products, not filename
assumptions. Sources: [wind archive](https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/wind/),
[gust archive](https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/extreme_wind/),
[MOSMIX station products](https://opendata.dwd.de/weather/local_forecasts/mos/MOSMIX_L/single_stations/10637/kml/).

## Findings that affect implementation

- Fraport describes a five-knot tailwind rule for changing the **parallel-runway
  direction**. This does not establish the runway-18 closure threshold. Upper
  winds and forecasts also influence the decision. [Fraport](https://www.fraport.com/en/sustainability/dialog-with-neighbors/noise-and-air/flight-operations/operation-direction.html)
- Windy Point Forecast returns the latest forecast, without historical forecast
  retrieval. Its Testing tier modifies/shuffles data; service-specific API keys
  are distinct. [Plans](https://api.windy.com/point-forecast/pricing),
  [documentation](https://api.windy.com/point-forecast/docs)
- A single Point Forecast request using the supplied key returned HTTP 400,
  `Invalid API key`. This establishes rejection by this endpoint only; it does
  not establish whether the key works for Map Forecast. See
  [redacted access check](windy-access-check.json). The key is in the ignored
  local `.env`; `.env.example` contains only a placeholder.
- Historical DWD wind records include missing values and changes between MEZ
  and UTC. The embedded station parameter metadata identifies continuous UTC
  reporting from September 2003. Retain the original metadata when normalizing;
  do not interpret the entire archive as UTC. See
  `Metadaten_Parameter_ff_stunde_01420.txt` inside the wind ZIPs.
- Umwelthaus already publishes GFS-based direction probabilities in eight-hour
  windows. This is a useful comparison source, not a replacement for actual
  operating-state labels. [Umwelthaus](https://www.umwelthaus.org/fluglaerm/anwendungen-service/aktuelle-betriebsrichtung-und-prognose/)
- The downloaded Fraport script contains both operating direction and runway-18
  status, with its own update time. It is a current snapshot, not historical
  training data. [Status script](https://sslapps.fraport.de/betriebsrichtung/betriebsrichtungsvg.js)

## Still needed

1. Presentation and one-pager: confirm exact runway rules and scoring.
2. Historical **actual** direction and runway-18 availability labels.
3. Archived forecasts with issue times for an honest 48-hour backtest. Historical
   observations alone cannot measure forecast performance.

Implementation inference: start with a rule-based weather baseline after the
rules arrive, then evaluate ML against actual operating-state labels using
chronological splits. Rule-derived labels would measure agreement with those
rules, not real airport decisions.

## Verification

All downloaded ZIP/KMZ archives passed CRC checks; PDFs have PDF headers. CSV
products and forecast XML were parsed to verify station identity, date ranges,
row counts and wind-field coverage. No application or trained model exists yet;
there is no app startup or model-accuracy result to report.
