# EDDF weather data

**Counts:** 4 public sources (DFLD.de recorded direction, IEM EDDF METAR, Open-Meteo previous runs: best match, ECMWF IFS, GFS, ICON and pressure boxes; DWD 01420 as a cross-check) · 154,718 METAR reports covering 77,380 hours (2018-01-01 to 2026-10-30) · 76,588 DFLD labelled hours (2018-01 to 2026-10-29) · 54 tests pass (30 Oct 2026, commit b2c48f1).

Most recent requested observation range: 2024-01-01 through 2026-10-30. METAR backfills append to existing reports; the inventory gives each file's full retained period. All timestamps are UTC. Data retrieval times and exact request URLs are recorded per file in [inventory.json](inventory.json).

Rebuild METAR history with `python -m ml.fetch --since 2018-01-01 --sources metar`. Backfill only the older years with `python -m ml.fetch --since 2018-01-01 --until 2022-12-31 --sources metar`; existing reports win on duplicate observation timestamp and raw METAR. Other weather sources can be fetched with `python -m ml.fetch --since 2023-01-01`. Raw responses and retrieval metadata are cached in ignored `data/raw/`. Completed calendar chunks are reused; current chunks expire after one hour and DWD recent archives/listings after six hours. `--refresh` explicitly redownloads. Use `--sources metar previous` to select sources, or `--until YYYY-MM-DD` for an inclusive end date. Live snapshots reuse the current UTC hour. No credentials or accounts are used.

## Inventory

| File | Source | Rows | UTC period | Size MB | Retrieved UTC | Columns and units | Terms |
|---|---|---:|---|---:|---|---|---|
| [eddf_metar.parquet](eddf_metar.parquet) | IEM | 154,718 | 2018-01-01 00:20:00+00:00 to 2026-10-30 10:20:00+00:00 | 3.429 | 2026-10-30T10:56:42.481236+00:00 to 2026-10-30T11:50:03.622330+00:00 | station; valid UTC; drct degrees; sknt/gust kn; raw METAR | Public domain |
| [eddf_taf.parquet](eddf_taf.parquet) | IEM | 0 | No records returned | 0.009 | 2026-10-30T10:56:48.495112+00:00 to 2026-10-30T10:56:51.808405+00:00 | station; issuance/validity UTC; raw TAF; IEM schema detailed below | Public domain |
| [openmeteo_previous_runs.parquet](openmeteo_previous_runs.parquet) | Open-Meteo | 24,816 | 2024-01-01 00:00:00+00:00 to 2026-10-30 23:00:00+00:00 | 0.963 | 2026-10-30T11:29:32.406070+00:00 to 2026-10-30T11:30:15.598151+00:00 | time UTC; 10/80 m speed and 10 m gust kn; direction degrees; MSL hPa; 2 m temperature Celsius | CC BY 4.0 |
| [openmeteo_historical_forecast.parquet](openmeteo_historical_forecast.parquet) | Open-Meteo | 33,576 | 2023-01-01 00:00:00+00:00 to 2026-10-30 23:00:00+00:00 | 0.551 | 2026-10-30T10:57:33.909668+00:00 to 2026-10-30T10:58:27.765632+00:00 | time UTC; 10/80 m speed and 10 m gust kn; direction degrees; MSL hPa; 2 m temperature Celsius | CC BY 4.0 |
| [dwd_01420_wind_hourly.parquet](dwd_01420_wind_hourly.parquet) | DWD | 32,956 | 2023-01-01 00:00:00+00:00 to 2026-10-29 23:00:00+00:00 | 0.493 | 2026-10-30T10:58:27.889289+00:00 to 2026-10-30T10:58:32.026553+00:00 | station ID; UTC time; quality code; mean speed m/s and kn; direction degrees | CDC CC BY 4.0 |
| [dwd_01420_wind_10min.parquet](dwd_01420_wind_10min.parquet) | DWD | 79,200 | 2025-04-28 00:00:00+00:00 to 2026-10-29 23:50:00+00:00 | 1.183 | 2026-10-30T10:58:33.224966+00:00 to 2026-10-30T10:58:34.451626+00:00 | station ID; UTC time; quality code; mean speed m/s and kn; direction degrees | CDC CC BY 4.0 |
| [live_forecast.parquet](live_forecast.parquet) | Open-Meteo | 72 | 2026-10-30 10:00:00+00:00 to 2026-11-02 09:00:00+00:00 | 0.008 | 2026-10-30T10:58:34.848728+00:00 to 2026-10-30T10:58:34.848728+00:00 | time UTC; 10/80 m speed and 10 m gust kn; direction degrees; MSL hPa; 2 m temperature Celsius | CC BY 4.0 |
| [live_metar.parquet](live_metar.parquet) | NOAA | 1 | 2026-10-30 10:50:00+00:00 to 2026-10-30 10:50:00+00:00 | 0.005 | 2026-10-30T10:59:08.249019+00:00 to 2026-10-30T10:59:08.249019+00:00 | station; valid UTC; drct degrees; sknt/gust kn; raw METAR | US government data |
| [live_taf.parquet](live_taf.parquet) | NOAA | 1 | 2026-10-30 08:23:00+00:00 to 2026-10-30 08:23:00+00:00 | 0.005 | 2026-10-30T10:59:09.464941+00:00 to 2026-10-30T10:59:09.464941+00:00 | station; issuance/validity UTC; raw TAF; IEM schema detailed below | US government data |
| [openmeteo_previous_runs_multimodel.parquet](openmeteo_previous_runs_multimodel.parquet) | Open-Meteo | 24,816 | 2024-01-01 00:00:00+00:00 to 2026-10-30 23:00:00+00:00 | 0.801 | 2026-10-30T11:59:19.615221+00:00 to 2026-10-30T12:01:21.538588+00:00 | time UTC; 10/80 m speed and 10 m gust kn; direction degrees; MSL hPa; 2 m temperature Celsius | CC BY 4.0 |
| [live_forecast_multimodel.parquet](live_forecast_multimodel.parquet) | Open-Meteo | 72 | 2026-10-30 12:00:00+00:00 to 2026-11-02 11:00:00+00:00 | 0.011 | 2026-10-30T12:02:05.365122+00:00 to 2026-10-30T12:02:07.716734+00:00 | time UTC; 10/80 m speed and 10 m gust kn; direction degrees; MSL hPa; 2 m temperature Celsius | CC BY 4.0 |

## Exact URL patterns

- IEM METAR: `https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=EDDF&data=drct&data=sknt&data=gust&data=metar&year1={Y1}&month1={M1}&day1={D1}&year2={Y2}&month2={M2}&day2={D2}&tz=Etc/UTC&format=onlycomma&latlon=no&missing=M&report_type=3&report_type=4`. Year chunks; end exclusive. Type 3 alone omits half-hour reports.
- IEM TAF: `https://mesonet.agron.iastate.edu/cgi-bin/request/taf.py?station=EDDF&year1={Y1}&month1={M1}&day1={D1}&year2={Y2}&month2={M2}&day2={D2}&tz=Etc/UTC&fmt=csv`. Year chunks; limits issuance time.
- Open-Meteo: `https://{previous-runs|historical-forecast}-api.open-meteo.com/v1/forecast?latitude=50.033&longitude=8.570&hourly={variables}&wind_speed_unit=kn&timezone=UTC&models=best_match&start_date={YYYY-MM-DD}&end_date={YYYY-MM-DD}`. Month chunks, both dates inclusive. Previous runs start 2024-01-01; historical forecast starts at the requested date. Variables listed below; previous runs request each unsuffixed, `_previous_day1`, `_previous_day2`, and `_previous_day3`.
- DWD hourly historical directory: `https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/wind/historical/`, station file `stundenwerte_FF_01420_{start}_{end}_hist.zip`.
- DWD hourly recent: `https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/wind/recent/stundenwerte_FF_01420_akt.zip`.
- DWD 10-minute recent: `https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/wind/recent/10minutenwerte_wind_01420_akt.zip`.
- Live forecast: `https://api.open-meteo.com/v1/forecast?latitude=50.033&longitude=8.570&hourly={variables}&wind_speed_unit=kn&timezone=UTC&start_hour={UTC-hour}&end_hour={UTC-hour+71h}`.
- Live observations/TAF: `https://aviationweather.gov/api/data/{metar|taf}?ids=EDDF&format=json`. Retrieved in a local hourly cache namespace, without limiting observations to the start of that hour.

## Columns and units

- METAR: `station` ICAO, `valid` observation timestamp, `drct` wind from degrees true, `sknt` mean wind knots, `gust` reported gust knots, `metar` original text. Missing direction can mean variable wind. Missing gust is unreported, not zero.
- IEM TAF: `station`, `valid` issuance UTC, `fx_valid`/`fx_valid_end` forecast interval UTC, `raw` text, `is_tempo` and `is_amendment` flags, `sknt`/`gust` knots, `drct` degrees true, `visibility` statute miles, `presentwx` weather codes, `skyc` cloud codes, `skyl` cloud heights feet, `ws_level` feet, `ws_drct` degrees, `ws_sknt` knots, `product_id` identifier, `ftype` forecast type. Empty EDDF response is retained honestly.
- Open-Meteo: `time` forecast valid UTC; `wind_speed_10m`, `wind_gusts_10m`, `wind_speed_80m` in knots; `wind_direction_10m`, `wind_direction_80m` in degrees true; `pressure_msl` hPa; `temperature_2m` degrees Celsius. Suffixes keep these units. Day 0 uses no suffix. Latitude 50.033, longitude 8.570; the API selects the surrounding land grid cell.
- DWD hourly: `STATIONS_ID` station 1420, `MESS_DATUM` original UTC YYYYMMDDHH, `QN_3` quality flag, `F` m/s, `D` degrees true, plus parsed `time`, converted `wind_speed_kn` knots and `wind_direction_deg` degrees true. Ten-minute uses `MESS_DATUM` YYYYMMDDHHMM, `QN`, `FF_10` m/s and `DD_10` degrees. Sentinel -999 becomes null; direction codes outside 0 to 360 become null in the normalized field.
- Live files also include `retrieved_at` UTC. Live METAR uses the METAR schema. Live TAF retains station, issuance, validity start/end and full raw text.

## Coverage and sanity

METAR has 154,718 reports across 77,380 UTC hours. Missing complete hours in the requested period: 1/24,804. Current incomplete hour is excluded. First missing hours: 2026-10-30 11:00:00+00:00.

Among 135,136 reports with known direction and nonzero speed, wind from a westerly component, 180 < direction < 360 degrees: 51.13%; easterly component, 0 < direction < 180: 42.27%. Exactly north/south directions are neither. Missing/variable directions: 19,244. Max reported gust: 54 knots; max mean wind: 35 knots. Gusts are only populated when reported.

- `eddf_metar.parquet`: Types 3 and 4 retain routine and additional METARs, including half-hour reports. Missing direction includes VRB; missing gust means no gust reported, not zero.
- `eddf_taf.parquet`: IEM returned no EDDF TAF records for the requested archive. Empty parquet preserves the returned schema; it is not training data. Live NOAA TAF is saved separately.
- `openmeteo_previous_runs.parquet`: Day 0 is a stitched series of short forecast leads, not a fixed archived issuance. Offsets denote 24/48/72 hours before valid time, not explicit run initialization timestamps. Evaluation adds a six-hour publication lag. Early archive offsets can be null; inspect non-null coverage before backtesting.
  - `wind_speed_10m`: 24,816 non-null hours; 2024-01-01 00:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 20.2.
  - `wind_direction_10m`: 24,816 non-null hours; 2024-01-01 00:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 360.
  - `wind_gusts_10m`: 24,816 non-null hours; 2024-01-01 00:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 41.8.
  - `pressure_msl`: 24,816 non-null hours; 2024-01-01 00:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 1044.4.
  - `temperature_2m`: 24,816 non-null hours; 2024-01-01 00:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 41.2.
  - `wind_speed_80m`: 24,816 non-null hours; 2024-01-01 00:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 37.5.
  - `wind_direction_80m`: 24,816 non-null hours; 2024-01-01 00:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 360.
  - `wind_speed_10m_previous_day1`: 24,372 non-null hours; 2024-01-19 12:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 16.
  - `wind_direction_10m_previous_day1`: 24,372 non-null hours; 2024-01-19 12:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 360.
  - `wind_gusts_10m_previous_day1`: 24,372 non-null hours; 2024-01-19 12:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 55.8.
  - `pressure_msl_previous_day1`: 24,372 non-null hours; 2024-01-19 12:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 1044.1.
  - `temperature_2m_previous_day1`: 24,372 non-null hours; 2024-01-19 12:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 41.2.
  - `wind_speed_80m_previous_day1`: 23,706 non-null hours; 2024-02-16 06:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 30.2.
  - `wind_direction_80m_previous_day1`: 23,706 non-null hours; 2024-02-16 06:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 360.
  - `wind_speed_10m_previous_day2`: 24,348 non-null hours; 2024-01-20 12:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 16.8.
  - `wind_direction_10m_previous_day2`: 24,348 non-null hours; 2024-01-20 12:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 360.
  - `wind_gusts_10m_previous_day2`: 24,348 non-null hours; 2024-01-20 12:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 39.8.
  - `pressure_msl_previous_day2`: 24,348 non-null hours; 2024-01-20 12:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 1044.3.
  - `temperature_2m_previous_day2`: 24,348 non-null hours; 2024-01-20 12:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 41.
  - `wind_speed_80m_previous_day2`: 23,682 non-null hours; 2024-02-17 06:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 33.8.
  - `wind_direction_80m_previous_day2`: 23,682 non-null hours; 2024-02-17 06:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 360.
  - `wind_speed_10m_previous_day3`: 24,324 non-null hours; 2024-01-21 12:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 20.1.
  - `wind_direction_10m_previous_day3`: 24,324 non-null hours; 2024-01-21 12:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 360.
  - `wind_gusts_10m_previous_day3`: 24,324 non-null hours; 2024-01-21 12:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 48.2.
  - `pressure_msl_previous_day3`: 24,324 non-null hours; 2024-01-21 12:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 1043.
  - `temperature_2m_previous_day3`: 24,324 non-null hours; 2024-01-21 12:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 40.4.
  - `wind_speed_80m_previous_day3`: 23,658 non-null hours; 2024-02-18 06:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 42.
  - `wind_direction_80m_previous_day3`: 23,658 non-null hours; 2024-02-18 06:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 360.
- `openmeteo_historical_forecast.parquet`: Day 0 is a stitched series of short forecast leads, not a fixed archived issuance.
  - `wind_speed_10m`: 33,576 non-null hours; 2023-01-01 00:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 20.2.
  - `wind_direction_10m`: 33,576 non-null hours; 2023-01-01 00:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 360.
  - `wind_gusts_10m`: 33,576 non-null hours; 2023-01-01 00:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 41.8.
  - `pressure_msl`: 33,576 non-null hours; 2023-01-01 00:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 1044.4.
  - `temperature_2m`: 33,576 non-null hours; 2023-01-01 00:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 41.2.
  - `wind_speed_80m`: 33,576 non-null hours; 2023-01-01 00:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 37.5.
  - `wind_direction_80m`: 33,576 non-null hours; 2023-01-01 00:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 360.
- `dwd_01420_wind_hourly.parquet`: Original source columns and quality codes retained. F/FF_10 is m/s; D/DD_10 is degrees true. Recent wins on historical/recent overlap. Missing sentinel -999 is null. These products contain mean wind, not gusts.
- `dwd_01420_wind_10min.parquet`: Original source columns and quality codes retained. F/FF_10 is m/s; D/DD_10 is degrees true. Recent wins on historical/recent overlap. Missing sentinel -999 is null. These products contain mean wind, not gusts.
- `live_forecast.parquet`: 72 hourly values from the current UTC hour; retrieval timestamp retained.
- `live_metar.parquet`: Latest report available at the snapshot hour; raw report retained.
- `live_taf.parquet`: Latest report available at the snapshot hour; raw report retained.
- `openmeteo_previous_runs_multimodel.parquet`: Separate ecmwf_ifs025, gfs_seamless and icon_seamless requests; 10 m wind in knots and direction degrees. Previous-day offsets 1/2/3 are preserved without day0 substitution. Missing history and unsupported gusts remain null. Offset valid time minus N days is not a verified publication timestamp; apply the training publication buffer.
  - `ecmwf_ifs025__wind_speed_10m_previous_day1`: 24,000 non-null hours; 2024-02-04 00:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 21.2.
  - `ecmwf_ifs025__wind_direction_10m_previous_day1`: 24,000 non-null hours; 2024-02-04 00:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 360.
  - `ecmwf_ifs025__wind_gusts_10m_previous_day1`: 0 non-null hours; none through none; maximum nan.
  - `ecmwf_ifs025__wind_speed_10m_previous_day2`: 23,976 non-null hours; 2024-02-05 00:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 18.3.
  - `ecmwf_ifs025__wind_direction_10m_previous_day2`: 23,976 non-null hours; 2024-02-05 00:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 360.
  - `ecmwf_ifs025__wind_gusts_10m_previous_day2`: 0 non-null hours; none through none; maximum nan.
  - `ecmwf_ifs025__wind_speed_10m_previous_day3`: 23,952 non-null hours; 2024-02-06 00:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 19.1.
  - `ecmwf_ifs025__wind_direction_10m_previous_day3`: 23,952 non-null hours; 2024-02-06 00:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 360.
  - `ecmwf_ifs025__wind_gusts_10m_previous_day3`: 0 non-null hours; none through none; maximum nan.
  - `gfs_seamless__wind_speed_10m_previous_day1`: 24,372 non-null hours; 2024-01-19 12:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 21.7.
  - `gfs_seamless__wind_direction_10m_previous_day1`: 24,372 non-null hours; 2024-01-19 12:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 360.
  - `gfs_seamless__wind_gusts_10m_previous_day1`: 24,372 non-null hours; 2024-01-19 12:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 43.
  - `gfs_seamless__wind_speed_10m_previous_day2`: 24,348 non-null hours; 2024-01-20 12:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 19.1.
  - `gfs_seamless__wind_direction_10m_previous_day2`: 24,348 non-null hours; 2024-01-20 12:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 360.
  - `gfs_seamless__wind_gusts_10m_previous_day2`: 24,348 non-null hours; 2024-01-20 12:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 46.8.
  - `gfs_seamless__wind_speed_10m_previous_day3`: 24,324 non-null hours; 2024-01-21 12:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 20.8.
  - `gfs_seamless__wind_direction_10m_previous_day3`: 24,324 non-null hours; 2024-01-21 12:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 360.
  - `gfs_seamless__wind_gusts_10m_previous_day3`: 24,324 non-null hours; 2024-01-21 12:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 47.6.
  - `icon_seamless__wind_speed_10m_previous_day1`: 24,372 non-null hours; 2024-01-19 12:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 16.
  - `icon_seamless__wind_direction_10m_previous_day1`: 24,372 non-null hours; 2024-01-19 12:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 360.
  - `icon_seamless__wind_gusts_10m_previous_day1`: 24,372 non-null hours; 2024-01-19 12:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 55.8.
  - `icon_seamless__wind_speed_10m_previous_day2`: 24,348 non-null hours; 2024-01-20 12:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 16.8.
  - `icon_seamless__wind_direction_10m_previous_day2`: 24,348 non-null hours; 2024-01-20 12:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 360.
  - `icon_seamless__wind_gusts_10m_previous_day2`: 24,348 non-null hours; 2024-01-20 12:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 39.8.
  - `icon_seamless__wind_speed_10m_previous_day3`: 24,324 non-null hours; 2024-01-21 12:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 20.1.
  - `icon_seamless__wind_direction_10m_previous_day3`: 24,324 non-null hours; 2024-01-21 12:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 360.
  - `icon_seamless__wind_gusts_10m_previous_day3`: 24,324 non-null hours; 2024-01-21 12:00:00+00:00 through 2026-10-30 23:00:00+00:00; maximum 48.2.
- `live_forecast_multimodel.parquet`: Separate ECMWF/GFS/ICON forecasts, 72 hourly UTC targets; model-prefixed 10 m wind columns. The maximum retrieval timestamp across the three requests is the earliest joint snapshot availability.

## Separate-model forecast history

Rebuild with `python -m ml.fetch --since 2024-01-01 --sources multimodel`. Requests use `https://previous-runs-api.open-meteo.com/v1/forecast?latitude=50.033&longitude=8.570&models={model}&hourly={variables}&wind_speed_unit=kn&timezone=UTC&start_date={YYYY-MM-DD}&end_date={YYYY-MM-DD}`. Each model is requested separately in cached calendar-month chunks, at most one network request per 1.2 seconds. Archive IDs `ecmwf_ifs025`, `gfs_seamless` and `icon_seamless` were accepted. Variables are `wind_speed_10m`, `wind_direction_10m`, `wind_gusts_10m`, each with `_previous_day1`, `_previous_day2` and `_previous_day3`. Columns are `<model>__<variable>_previous_dayN`. Speed/gust are knots; direction is degrees true. All timestamps are UTC. Licence: [CC BY 4.0](https://open-meteo.com/en/licence).

The output has 24,816 hourly rows from 2024-01-01 00:00:00+00:00 through 2026-10-30 23:00:00+00:00. Nulls preserve unavailable early history or variables; ECMWF archived gusts are unavailable in this extraction. The first non-null times below are valid times, not forecast publication times. Previous-run offsets do not establish exact publication timestamps. Apply the same availability/publication buffer as training before selecting an offset.

| Model | First non-null day1 direction UTC | Last non-null day1 direction UTC | Hours |
|---|---|---|---:|
| ecmwf_ifs025 | 2024-02-04 00:00:00+00:00 | 2026-10-30 23:00:00+00:00 | 24,000 |
| gfs_seamless | 2024-01-19 12:00:00+00:00 | 2026-10-30 23:00:00+00:00 | 24,372 |
| icon_seamless | 2024-01-19 12:00:00+00:00 | 2026-10-30 23:00:00+00:00 | 24,372 |

Direction disagreement uses the shortest circular angular distance, so 350 and 10 degrees differ by 20 degrees. All pairwise non-null day1 direction hours are included, including calm hours. See [openmeteo_multimodel_summary.json](openmeteo_multimodel_summary.json) for the pair counts and pooled mean.

| Model pair | Mean absolute direction difference | Paired hours |
|---|---:|---:|
| ecmwf_ifs025 / gfs_seamless | 24.687 degrees | 24,000 |
| ecmwf_ifs025 / icon_seamless | 26.818 degrees | 24,000 |
| gfs_seamless / icon_seamless | 29.888 degrees | 24,372 |

`python -m ml.fetch --sources live-multimodel` writes 72-hour snapshots to `live_forecast_multimodel.parquet`, with the same model prefixes and unsuffixed live variable names. `--sources live` also includes these models. The joint `retrieved_at` is the latest retrieval across the separate requests. `ml.live.live_weather` attaches those columns only from a snapshot retrieved by the issue time, otherwise it requests each named model from the Single Runs API using a dated run and the existing conservative 12-hour publication proxy. Per-model `__available_at`, and `__issued_at` for dated runs, remain on the returned input frame. Missing model data is reported and never replaced with another model. These are additional input columns for downstream features; prediction logic is unchanged.


Historical forecast day 0 stitches recent forecast leads and must not be used as an archived 24/48-hour forecast. Previous-day fields are lead offsets relative to valid time; preserve them separately and check availability at the evaluation issue time. Raw retrieval time is not a forecast initialization time.

## Licences and attribution

- IEM: Public domain; attribution appreciated. https://mesonet.agron.iastate.edu/disclaimer.php
- Open-Meteo: CC BY 4.0; https://open-meteo.com/en/licence and https://open-meteo.com/en/terms
- DWD: CDC terms, May 2024: CC BY 4.0. https://opendata.dwd.de/climate_environment/CDC/Terms_of_use.txt ; https://www.dwd.de/copyright . Older descriptions refer to GeoNutzV.
- NOAA: US government weather data; https://www.weather.gov/disclaimer ; https://aviationweather.gov/data/api/

## Recorded operational history

[DFLD recorded history](ground_truth/README.md) has 76,588 stable OD hours, from 2017-12-31T23:00:00Z through 2026-10-29T22:00:00Z. Rebuild with `python -m ml.dfld --since 2018-01-01 --until 2026-10-29`. Labels describe whole hours and are available only after hour end; the original 2024+ rows are retained.

Runway-18 display history has 28,140 known hours from 2017-12-31T23:00:00Z through 2022-05-26T11:00:00Z, with gaps. `r18_in_use` describes the published operational display, not weather closure. Transparent and unknown bins are excluded, not classified as non-use. All requested monthly pages were inspected, including later months without known status.


## Needs an account

None of the requested endpoints needs an account or key. No sign-up was attempted.

## Retrieval failures

None. Source coverage gaps are recorded above.

## Synoptic pressure (`openmeteo_previous_runs_pressure.parquet`)

`python -m ml.synoptic` caches Open-Meteo Previous Runs (best_match) `pressure_msl` day 1/2/3 at four points about 200 km from EDDF: north (51.83 N, 8.57 E), south (48.23 N, 8.57 E), west (50.03 N, 5.77 E) and east (50.03 N, 11.37 E). Columns are `time` (UTC) and `pressure_{n,s,w,e}_previous_day{1,2,3}` in hPa, 2024-01-01 to 2026-10-30, about 2% missing. They feed north-south and east-west gradient features under the same six-hour publication lag as the airport forecast.
