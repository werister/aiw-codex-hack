# Weather inputs

The offline demo reads `eddf_metar.parquet` and `openmeteo_previous_runs.parquet` without a key or network. Files preserve UTC timestamps, meteorological wind direction, wind in knots where named, nulls and retrieval metadata.

- `eddf_metar.parquet`, `eddf_taf.parquet`: Iowa Environmental Mesonet EDDF reports, public domain under its policy.
- `openmeteo_previous_runs*.parquet`: normalized archived weather, separate ECMWF/GFS/ICON forecasts and synoptic pressure; Open-Meteo and upstream providers, CC BY 4.0. Previous-day offsets are preserved, not exact publication timestamps.
- `dwd_01420_wind*.parquet`: Deutscher Wetterdienst Climate Data Center, Frankfurt/Main, CC BY 4.0; times and units normalized, quality codes retained.
- `live_*.parquet`: saved snapshots, not a continuous feed; Open-Meteo CC BY 4.0 and NOAA/NWS public-domain weather.
- `inventory.json`: requests, retrieval dates, units, transformations and coverage.

[Full source/rights inventory](../docs/DATA_SOURCES.md) covers every original dataset and removed research file. The unused duplicate day-zero forecast file is excluded; it did not represent issued long-lead forecasts.

Direction records and fitted weights are absent because source terms do not establish open redistribution rights. See [research schema](ground_truth/README.md). Historical model evaluation cannot be reconstructed independently from this weather-only package.

`python -m ml.fetch --help` documents downloads. Provider terms and limits apply, including Open-Meteo free-API noncommercial restrictions. No account or credential is needed for the offline example.
