# Recorded operating directions at Frankfurt

Retrieved on 30 October 2026. These are DFLD's recorded operating-direction labels, not labels inferred from METAR. They are a public proxy for actual operation, not a certified DFS movement log.

## Files and coverage

- `dfld_hourly.csv` has 76,588 rows with `time`, `od`, `source`. `time` is the UTC start of an hour and `od` is `07` or `25`. Read `od` as a string to preserve the leading zero.
- `dfld_half_hourly.csv.gz` retains all 154,752 source half-hour bins for local dates 2018-01-01 through 2026-10-29. It preserves the local date and clock time before conversion.
- `dfld_excluded_hours.csv` lists 788 excluded local hours. Of these, 770 contain a direction change between the two half-hour bins and 18 have an ambiguous or nonexistent daylight-saving clock time.
- `dfld_manifest.json` gives the URL, retrieval time, byte count, SHA-256 of the fetched HTML and extracted record count for each of 106 monthly requests.

The hourly file spans `2017-12-31T23:00:00Z` through `2026-10-29T22:00:00Z`, with gaps at excluded hours. It contains 27,196 eastbound and 49,392 westbound hours. The current, incomplete local day was excluded.

## Rebuild and availability

Run `python -m ml.dfld --since 2018-01-01 --until 2026-10-29` to rebuild the completed-day history. The extractor caches raw monthly HTML under ignored `data/raw/`, spaces network requests at least 1.2 seconds apart, retries transient errors, and records hashes and retrieval times in the manifest. Existing rows are retained and overlapping labels must match before any output is replaced. `--refresh` downloads pages again. The default end date is yesterday in Europe/Berlin.

The UTC timestamp is the start of the labeled hour. A label is an input only at `time + 1 hour`, when that entire source hour has ended. Upstream reporting delay remains unknown. All 24,546 rows from the original January 2024 through October 2026 extraction were retained without changes.

## Recorded runway-18 display

`dfld_r18_hourly.csv` has columns `time`, `r18_in_use`, `source`. It uses the third half-hour strip in each dated row, separate from wind direction and airport OD. The page legend identifies `Menu/180.gif` as operating direction 18 and `Menu/000.gif` as operating direction `--`. These become `True` and `False`. `Menu/Undef.gif` explicitly means no data; transparent `Menu/Trans.gif` bins carry no status label and are treated as missing too. A transparent strip must never become a string of false closures.

An hourly row requires both half-hours to exist, be known and agree. DST ambiguity and gaps are excluded under the same clock rules as OD. `dfld_r18_excluded_hours.csv` records unknown, partial, changing and DST hours. The manifest counts both total runway-18 bins and bins with a known symbol. Every requested month is inspected, including months without usable runway-18 status.

There are 28,140 retained status hours, from local January 2018 through May 2022, with substantial gaps. Of these, 25,889 show in use and 2,251 show `--`. No known status was found after UTC 2022-05-26T11:00:00Z through the end of the requested period. Later blank strips are missing observations, not evidence that the runway stopped operating.

This is the published operational display, not a movement count, a certified closure log, or a weather-usability label. Non-use may reflect maintenance, demand, night restrictions, other operational decisions or reporting limitations. Coincidence with a METAR tailwind threshold does not prove the cause. Never relabel every `False` hour as a wind closure or every `True` hour as weather-safe.

## Source and meaning

The keyless monthly URL is `https://www.dfld.de/Mess/StatWetter.php?R=1&D=01.MM.YYYY`, with a two-digit month. Region `1` is Frankfurt. For example, [January 2025](https://www.dfld.de/Mess/StatWetter.php?R=1&D=01.01.2025) and [October 2026](https://www.dfld.de/Mess/StatWetter.php?R=1&D=01.10.2026).

The page has separate rows for wind direction, operating direction and runway 18. Extract only image titles ending in `BR07` or `BR25`. Do not convert the wind arrows into labels. DFLD calls its operating-direction display the distribution of the real operating direction [reale Betriebsrichtungsverteilung]. Its [weather-statistics help](https://www.dfld.de/Mess/Language/StatWettHelpG.html) explicitly separates that from its wind-derived decision rule. Its [data-provenance help](https://www.dfld.de/Mess/Language/MessHelpG.html) says operating-direction information uses multiple Internet sources, especially airport-operator websites.

## Conversion and limitations

1. Read each HTML table row's `DD.MM.YYYY` date. Extract image titles matching `HH:MM - HH:MM: BR07` or `BR25`.
2. Treat the page clock as `Europe/Berlin`. This is an explicit assumption, supported by a spot check: DFLD switches from 25 to 07 at its 10:00 bin on 29 October 2026; [UNH's current display](https://www.umwelthaus.org/fluglaerm/anwendungen-service/aktuelle-betriebsrichtung-und-prognose/) reports the switch at 09:54 local. The wind-alignment check below also supports the seasonal offset. DFLD's retrieved help does not explicitly specify the timezone. Verify against a dated movement log before final jury scoring.
3. Exclude an hour when Python `zoneinfo` gives different UTC offsets for `fold=0` and `fold=1`. This removes the spring gap and autumn repeated hour rather than inventing a timestamp.
4. Retain an hourly label only when both source bins exist and agree. There is no majority vote for a tied change hour. These labels mean a stable displayed direction over the hour, not an exact direction-change instant.
5. Convert the start of each retained hour to UTC. Keep the monthly URL in `source`. No interpolation, METAR inference or forward filling was used.

DFLD provides half-hour bins, not individual flight events. The within-bin sampling convention and upstream reporting delay are not documented on the retrieved page. A displayed direction can remain during a night with no movements. Do not present these data as proof that an aircraft flew in every labeled hour. The 770 change hours must remain visible in evaluation coverage, since excluding them makes the task easier. Use the half-hour source for a separate change-event analysis.

This extraction does not establish runway 18 weather usability. The source also displays an operational runway-18 status, but absence of departures, a maintenance closure and wind-driven unavailability are different labels.

### Timezone alignment check

Compared DFLD's separate wind-direction bins against the nearest IEM METAR within 20 minutes, using candidate offsets of UTC+0, UTC+1 and UTC+2. The score is mean circular angular difference in degrees. Calm or variable reports with no numeric direction were skipped. This analysis uses wind solely to check the clock, not to create OD labels.

| Local month | Assume UTC+0 | Assume UTC+1 | Assume UTC+2 | Best alignment |
|---|---|---|---|---|
| January 2025 | 24.14 degrees, 1,412 pairs | 20.04 degrees, 1,410 pairs | 32.22 degrees, 1,408 pairs | UTC+1 |
| July 2025 | 45.49 degrees, 1,365 pairs | 35.54 degrees, 1,363 pairs | 28.75 degrees, 1,361 pairs | UTC+2 |

Sources: [DFLD January](https://www.dfld.de/Mess/StatWetter.php?R=1&D=01.01.2025), [DFLD July](https://www.dfld.de/Mess/StatWetter.php?R=1&D=01.07.2025), [IEM January UTC wind](https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=EDDF&data=drct&year1=2025&month1=1&day1=1&year2=2025&month2=2&day2=1&tz=Etc%2FUTC&format=onlycomma), [IEM July UTC wind](https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=EDDF&data=drct&year1=2025&month1=7&day1=1&year2=2025&month2=8&day2=1&tz=Etc%2FUTC&format=onlycomma). A lower error at the expected seasonal offset supports Europe/Berlin time. It does not prove exact sampling times or remove the half-hour resolution limit. Windows Python needs the `tzdata` package for `zoneinfo`; it is included in `ml/requirements.txt`.

## Access checks

DFLD monthly pages returned HTTP 200 without an account for all 106 downloaded months from January 2018 through October 2026. January 2013 was also probed successfully, but older years were not downloaded or exhaustively checked.

OpenSky anonymous EDDF arrival and departure requests for 29 October 2026 both returned HTTP 403, `You cannot access historical flights`. An anonymous bounding-box live-state request returned HTTP 200 with eight state vectors. See the [official REST documentation](https://openskynetwork.github.io/opensky-api/rest.html).

Jayden: OpenSky account and historical-data permission would let us validate runway directions from archived tracks; registration is at https://opensky-network.org/ and does not itself guarantee historical database access. DFLD removes the need to wait for this account for an initial OD dataset.
