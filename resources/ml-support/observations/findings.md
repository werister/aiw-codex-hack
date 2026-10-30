# EDDF observation data handoff

Retrieved 30 October 2026 UTC. The package contains real EDDF METAR observations from the Iowa Environmental Mesonet (IEM), plus an independent DWD hourly wind/gust series for reference. It contains observations only: no operating-direction or runway-usability labels were made.

## IEM METAR archive

The archive covers **2024-12-29 through 2026-10-29 UTC inclusive**. The downloader requested month-sized chunks and separately selected IEM report types 3 and 4 (routine and special). The API uses an inclusive start and exclusive end; the last request ends at 2026-10-30 00:00 UTC. There are 46 byte-preserved CSV responses in `raw/iem/`, fetched with at least two seconds between requests. Each raw response, exact URL, retrieval time, byte count, SHA-256, fields, and row count are recorded in `manifest.json`.

IEM defines `drct` as wind direction from true north, `sknt` and `gust` in knots, `valid` as the observation timestamp, and `metar` as the unprocessed report. These meanings are described on the [IEM archive download page](https://mesonet.agron.iastate.edu/request/download.phtml?network=CI__ASOS). The same page warns that its archive is provided as-is with little quality control and that `M` can mean reported missing, QC-masked, or never reported. IEM explains its routine/special separation and the limits of classifying those reports in its [METAR report types note](https://mesonet.agron.iastate.edu/onsite/news.phtml?id=1434).

`eddf_metar_observations.csv` has **32,156 rows**: 16,082 IEM type-3 rows and 16,074 type-4 rows. Observations span `2024-12-29T00:20:00Z` to `2026-10-29T23:50:00Z`; all timestamps are unique, there are no exact duplicate rows, and there are no missing hourly routine slots between the first and last routine observation. A notable property is that type 3 occurs almost entirely at :50 UTC, while type 4 occurs almost entirely at :20 UTC, each at about one record per hour. The export preserves the IEM query class; verify the meaning of that cadence before treating every type-4 row as an exceptional event.

The normalized wind values come from both IEM's parsed columns and the raw METAR group. All 32,156 reports contained a readable wind group, and all were encoded in knots. Raw-group speed and gust values agree with IEM's parsed columns in every report. Wind speeds range from 0 to 29 kt. Direction statuses are `DIRECTIONAL` (18,009), `VARIABLE_RANGE` (9,782), `VARIABLE_VRB` (4,289), and `CALM` (76). `VRB` and calm remain distinct; calm directions are null rather than north. The raw report and raw IEM columns are retained for reprocessing.

A gust is **not** converted to zero when its group is absent. The export has 460 reported gusts; 31,696 rows have `wind_gust_kt` blank and `wind_gust_status=NOT_ENCODED`. The [Aviation Weather Center METAR reference](https://aviationweather.gov/help/data/) explains that gust groups represent qualifying rapid speed fluctuations over the preceding 10-minute evaluation period. An absent group therefore does not prove the peak gust was zero. This matters when applying a runway rule that depends on a crosswind component including gusts: the gust component is unknown for those records and should remain missing until the ML/rules owner chooses an explicit policy.

Relevant columns are `observation_time_utc`, `wind_direction_deg`, `wind_speed_kt`, `wind_gust_kt`, `wind_direction_status`, `wind_speed_status`, `wind_gust_status`, `report_type`, and `raw_metar`. `quality.json` includes counts, intervals, value ranges, missingness, and known interpretation limits.

## Separate DWD reference series

The two DWD recent archives already present in the repository were read and copied under `raw/dwd/`; their URLs, original retrieval times, archive sizes, member names, and hashes are in `manifest.json`. The extracted `dwd_01420_hourly_wind_gust_overlap.csv` contains **13,090 hourly records** from 2025-04-28 00:00 UTC through 2026-10-29 23:00 UTC. From its first through last timestamp there are 13,200 expected hourly slots, so **110 timestamps are absent**. This gap count is separate from the 11 rows whose mean speed and hourly maximum wind-speed cells are missing; direction has no missing cells. The quality-code columns are retained, and the recent DWD products have not completed final quality control.

The hourly wind file uses `F` (m/s), `D` (degrees), and `QN_3`; the separate hourly extreme-wind file uses `FX_911` (m/s) and `QN_8`. The DWD output includes original m/s values and a transparent conversion to knots (`1 m/s = 1.9438444924406 kt`); the recorded maximum conversion error is 0.0 kt. DWD's official descriptions specify hourly mean wind values in m/s/degrees and hourly maximum wind-speed values in m/s: [hourly wind](https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/wind/DESCRIPTION_obsgermany_climate_hourly_wind_en.pdf), [hourly extreme wind](https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/extreme_wind/DESCRIPTION_obsgermany_climate_hourly_extreme_wind_en.pdf). UTC is verified for this requested 2025-04-28 through 2026-10-29 overlap from the embedded station parameter metadata: the `F` and `D` entries covering 2003-09-01 through 2026-10-29 say `Stundenwerte in UTC`, and the `FX_911` entry covering 2001-04-01 through 2026-10-29 says `in UTC`. The exact rows are retained in `quality.json`.

This is a separate DWD station/product. Hourly aggregation and sensor equivalence to the EDDF METAR stream are not established here; do not silently substitute it for METAR. It is a lower-frequency comparison series, not a runway-state label source.

## Reproduction and package integrity

Run from this folder to fetch any missing IEM chunks and reproduce the normalized data; the DWD ZIP cache is included in `raw/dwd/`:

```bash
python3 fetch_verify.py --pause-seconds 2
```

To reproduce normalization and QA from the included IEM and DWD caches without network access:

```bash
python3 fetch_verify.py --skip-fetch
```

Both commands use Python standard library only. `--skip-fetch` verifies the 46 cached IEM response hashes before normalization and regenerates the 13,090-row DWD overlap from the included ZIPs. Original DWD retrieval times are read from the packaged source registry, or preserved from the manifest if the registry is unavailable. The normalized CSV and DWD CSV hashes and sizes are recorded in `manifest.json`.
