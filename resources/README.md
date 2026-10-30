# Frankfurt runway forecast: preparation

Prepared 30 October 2026. Question: which verified resources can support the
FraAlliance 48-hour runway forecast challenge before the presentation arrives?

The refined [product concept](runway-concept.md) focuses on the next operational
change to prepare for, with separate runway-18 and 07/25 forecasts and an explicit
test of planning value.

## Challenge from the supplied transcript

Predict the next 48 hours of:

- Runway 18 availability for departures, including likely closure/reopening times.
- Parallel-runway operating direction: 07 (eastbound) or 25 (westbound), including changes.

The intended users plan ground handling, staffing and connections. The presentation
and one-pager are **pending from the user**. Exact challenge thresholds, averaging
periods, gust handling and evaluation criteria remain unconfirmed.

## Downloaded locally

21 source files (5.94 MB) are under `resources/raw/`. Original files are ignored by
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
| Forecast backtest samples | Two ICON-EU API responses with 72 complete hourly rows each: a fixed +48 h series and the individual run initialized 28 October at 00:00 UTC. See [access check](forecast-access-check.json). |

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
  [redacted access check](windy-access-check.json). This check contains no key;
  configure credentials locally using `.env.example` and the ignored `.env`.
- Historical DWD wind records include missing values and changes between MEZ
  and UTC. The embedded station parameter metadata identifies continuous UTC
  reporting from September 2003. Retain the original metadata when normalizing;
  do not interpret the entire archive as UTC. See
  `Metadaten_Parameter_ff_stunde_01420.txt` inside the wind ZIPs.
- The station geography metadata records a relocation on 22 October 2014, about
  5.9 km from the previous position. MOSMIX 10637 is about 6.2 km from the current
  observation station. Preserve station-era and location when comparing them;
  see `Metadaten_Geographie_01420.txt` inside the wind ZIPs.
- Direction code `990` means variable, not 990 degrees. Keep it distinct from
  missing (`-999`) and calm; never feed it directly to trigonometric features.
  Wind/gust archives contain missing hours. Their overlapping portions match
  exactly: 5,847 wind rows and 5,839 gust rows must be deduplicated.
  Source: the archived products and their DWD descriptions.
- Umwelthaus already publishes GFS-based direction probabilities in eight-hour
  windows. This is a useful comparison source, not a replacement for actual
  operating-state labels. [Umwelthaus](https://www.umwelthaus.org/fluglaerm/anwendungen-service/aktuelle-betriebsrichtung-und-prognose/)
- The downloaded Fraport script contains both operating direction and runway-18
  status, with its own update time. It is a current snapshot, not historical
  training data. [Status script](https://sslapps.fraport.de/betriebsrichtung/betriebsrichtungsvg.js)

## Still needed

1. Presentation and one-pager: confirm exact runway rules and scoring.
2. Historical **actual** direction and runway-18 availability labels.
3. Join the verified archived forecast source to actual operating-state labels;
   establish historical publication/availability times. Fixed +48 h samples
   support point scoring; individual runs are needed to replay a complete
   48-hour planning view. [Open-Meteo documentation](https://open-meteo.com/en/docs/historical-forecast-api)

Implementation inference: start with a rule-based weather baseline after the
rules arrive, then evaluate ML against actual operating-state labels using
chronological splits. Rule-derived labels would measure agreement with those
rules, not real airport decisions.

## Verification

All downloaded ZIP/KMZ archives passed CRC checks; PDFs have PDF headers. CSV
products and forecast XML were parsed to verify station identity, date ranges,
row counts and wind-field coverage. The deeper [data-quality check](data-quality-check.json)
records archive overlap, variable/missing directions, station geography and
48-hour forecast coverage at the stated replay cutoff. The
[forecast access check](forecast-access-check.json) records the archived API
samples and their units. No application or trained model exists yet;
there is no app startup or model-accuracy result to report.
