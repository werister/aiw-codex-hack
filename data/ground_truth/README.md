# Recorded operating directions at Frankfurt

Retrieved on 30 October 2026. These are DFLD's recorded operating-direction labels, not labels inferred from METAR. They are a public proxy for actual operation, not a certified DFS movement log.

## Files and coverage

- `dfld_hourly.csv` has 24,546 rows with `time`, `od`, `source`. `time` is the UTC start of an hour and `od` is `07` or `25`. Read `od` as a string to preserve the leading zero.
- `dfld_half_hourly.csv.gz` retains all 49,584 source half-hour bins for local dates 2024-01-01 through 2026-10-29. It preserves the local date and clock time before conversion.
- `dfld_excluded_hours.csv` lists 246 excluded local hours. Of these, 240 contain a direction change between the two half-hour bins and six have an ambiguous or nonexistent daylight-saving clock time.
- `dfld_manifest.json` gives the URL, retrieval time, byte count, SHA-256 of the fetched HTML and extracted record count for each of 34 monthly requests.

The hourly file spans `2023-12-31T23:00:00Z` through `2026-10-29T22:00:00Z`, with gaps at excluded hours. It contains 8,690 eastbound and 15,856 westbound hours. The current, incomplete local day was excluded.

## Source and meaning

The keyless monthly URL is `https://www.dfld.de/Mess/StatWetter.php?R=1&D=01.MM.YYYY`, with a two-digit month. Region `1` is Frankfurt. For example, [January 2025](https://www.dfld.de/Mess/StatWetter.php?R=1&D=01.01.2025) and [October 2026](https://www.dfld.de/Mess/StatWetter.php?R=1&D=01.10.2026).

The page has separate rows for wind direction, operating direction and runway 18. Extract only image titles ending in `BR07` or `BR25`. Do not convert the wind arrows into labels. DFLD calls its operating-direction display the distribution of the real operating direction [reale Betriebsrichtungsverteilung]. Its [weather-statistics help](https://www.dfld.de/Mess/Language/StatWettHelpG.html) explicitly separates that from its wind-derived decision rule. Its [data-provenance help](https://www.dfld.de/Mess/Language/MessHelpG.html) says operating-direction information uses multiple Internet sources, especially airport-operator websites.

## Conversion and limitations

1. Read each HTML table row's `DD.MM.YYYY` date. Extract image titles matching `HH:MM - HH:MM: BR07` or `BR25`.
2. Treat the page clock as `Europe/Berlin`. This is an explicit assumption, supported by a spot check: DFLD switches from 25 to 07 at its 10:00 bin on 29 October 2026; [UNH's current display](https://www.umwelthaus.org/fluglaerm/anwendungen-service/aktuelle-betriebsrichtung-und-prognose/) reports the switch at 09:54 local. DFLD's retrieved help does not explicitly specify the timezone. Verify the summer offset against a dated movement log before final jury scoring.
3. Exclude an hour when Python `zoneinfo` gives different UTC offsets for `fold=0` and `fold=1`. This removes the spring gap and autumn repeated hour rather than inventing a timestamp.
4. Retain an hourly label only when both source bins exist and agree. There is no majority vote for a tied change hour. These labels mean a stable displayed direction over the hour, not an exact direction-change instant.
5. Convert the start of each retained hour to UTC. Keep the monthly URL in `source`. No interpolation, METAR inference or forward filling was used.

DFLD provides half-hour bins, not individual flight events. The within-bin sampling convention and upstream reporting delay are not documented on the retrieved page. A displayed direction can remain during a night with no movements. Do not present these data as proof that an aircraft flew in every labeled hour. The 240 change hours must remain visible in evaluation coverage, since excluding them makes the task easier. Use the half-hour source for a separate change-event analysis.

This extraction does not establish runway 18 weather usability. The source also displays an operational runway-18 status, but absence of departures, a maintenance closure and wind-driven unavailability are different labels.

## Access checks

DFLD monthly pages returned HTTP 200 without an account for all 34 downloaded months. January 2013 was also probed successfully, but older years were not downloaded or exhaustively checked.

OpenSky anonymous EDDF arrival and departure requests for 29 October 2026 both returned HTTP 403, `You cannot access historical flights`. An anonymous bounding-box live-state request returned HTTP 200 with eight state vectors. See the [official REST documentation](https://openskynetwork.github.io/opensky-api/rest.html).

Jayden: OpenSky account and historical-data permission would let us validate runway directions from archived tracks; registration is at https://opensky-network.org/ and does not itself guarantee historical database access. DFLD removes the need to wait for this account for an initial OD dataset.
