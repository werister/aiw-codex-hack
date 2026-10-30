# Spec Delta

## Purpose
Download, cache and document the public EDDF observation and weather-model data that labels, features and the live forecast use.

## ADDED Requirements

### Requirement: Cached, reproducible download
`python -m ml.fetch` SHALL download every source idempotently into `data/`, reuse cached raw files, and use UTC timestamps everywhere.

#### Scenario: Re-run uses the cache
- **WHEN** the fetch runs a second time
- **THEN** no file that is already complete is downloaded again

### Requirement: Every source cited
`data/README.md` SHALL list each file with its source URL, period, row count, units and licence.

#### Scenario: A reviewer checks provenance
- **WHEN** Luca opens `data/README.md`
- **THEN** each data file has a source URL and a period
