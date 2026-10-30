# Frankfurt runway forecast: preparation

Prepared 30 October 2026. Question: which verified resources can support the
FraAlliance 48-hour runway forecast challenge before the presentation arrives?

The refined [product concept](runway-concept.md) focuses on the next operational
change to prepare for, with separate runway-18 and 07/25 forecasts and an explicit
test of planning value.

The [pitch strategy](hackathon-pitch-strategy.md) turns that concept into a
three-minute narrative, a verifiable demo sequence and priorities before submission.
Its [arithmetic checks](pitch-evidence-check.json) are explicitly synthetic;
they do not substitute for measured model performance.

## Challenge from the supplied transcript

Predict the next 48 hours of:

- Runway 18 availability for departures, including likely closure/reopening times.
- Parallel-runway operating direction: 07 (eastbound) or 25 (westbound), including changes.

The intended users plan ground handling, staffing and connections. The team
repository contains a [Markdown transcription of the challenge brief](../frankfurt-airport-operating-direction-forecast.md)
and [derived rules](../ml/rules.json). They provide working thresholds, but the
original PDF and presentation have not been located or compared in this review.
The [source audit](challenge-source-audit.md) distinguishes transcribed requirements
from team assumptions. Observation gaps, sub-hourly timing and the meaning of
certainty still require explicit handling.

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

- The general Fraport page describes a five-knot rule. Use the **transcribed
  challenge limits as the working baseline pending original-source verification**:
  10 kt landing tailwind triggers immediate
  direction change; smaller positive tailwind is tolerated for 30 minutes;
  runway 18 closes at 15 kt tailwind or crosswind including gusts above 40 kt.
  [Challenge rules](../ml/rules.json)
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

1. Obtain the original one-pager and pitch deck from the participant dashboard;
   verify the transcription and distinguish source requirements from assumptions.
   Apply the working brief consistently, including its 30-minute state rule;
   document how observation gaps and hourly forecast resolution are handled.
2. Historical **actual** direction and runway-18 availability labels.
3. Join the verified archived forecast source to actual operating-state labels;
   establish historical publication/availability times. Fixed +48 h samples
   support point scoring; individual runs are needed to replay a complete
   48-hour planning view. [Open-Meteo documentation](https://open-meteo.com/en/docs/historical-forecast-api)

The team's model can learn forecast error by using past forecasts as inputs and
rules applied to later observed winds as proxy labels. This can outperform the
rules applied directly to forecast winds; it does not establish performance
against actual airport decisions. Report proxy-label skill and operational
validation separately, using chronological splits.

## Verification

All downloaded ZIP/KMZ archives passed CRC checks; PDFs have PDF headers. CSV
products and forecast XML were parsed to verify station identity, date ranges,
row counts and wind-field coverage. The deeper [data-quality check](data-quality-check.json)
records archive overlap, variable/missing directions, station geography and
48-hour forecast coverage at the stated replay cutoff. The
[forecast access check](forecast-access-check.json) records the archived API
samples and their units. These resource/concept checks do not establish app
startup, model accuracy or the status of the team's separate implementation.
