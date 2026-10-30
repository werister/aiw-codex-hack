> Archived worker report. Claims and paths below refer to the worker's stated snapshot and time. “Nothing committed” describes that worker's run; this report is now preserved by the coordinator. See [the consolidated timeline](../../experiments/REDTEAM_TIMELINE.md) for reconciled status and independently replayed checks.

# Delay-data routing eligibility — BTS Airline Delay Cause (2025)

Independent inspection of Luca/Kai's BTS source and the tracker-authored additions, to state
what delay experiments are **allowed** with this data versus **unsupported counterfactual
claims**. Scope: eligibility only — no large downloads, no training, no API deployment. The OD
forecast experiment stays separate; model comparisons only within the same target/horizon.

## Source and integrity (Ran and saw)

- File: `weather database/bts/raw2025/Airline_Delay_Cause.csv` — 22,687 data rows, 21 columns.
- **Integrity cross-check: PASS.** `shasum -a 256` of the CSV = `8b9379ac15e5b381991bae8330882f6615aba2a3c3e4ca39b0dd9df697b4aa77`, which **matches** the
  `source_sha256` recorded in the tracker's `bts/analysis_results.json`.
- Provenance (`bts/data_provenance.json`): downloaded from transtats.bts.gov (US DOT), requested
  period 2025-01..2025-12, retrieved 2026-10-30, 919,534-byte zip.
- Column definitions (`raw2025/Download_Column_Definitions.xlsx`): delays are **in minutes**;
  `arr_del15` = arrival ≥15 min late; `*_ct` = cause-apportioned counts; `airport` = US DOT
  3-char code.

## Granularity, dates, coverage (Ran and saw)

- **Granularity: MONTHLY aggregates per (year, month, carrier, airport).** Not flight-level.
  Rows carry counts (`arr_flights`, `arr_del15`, `arr_cancelled`, `arr_diverted`) and
  **summed minutes** (`arr_delay`, `carrier_delay`, `weather_delay`, `nas_delay`,
  `security_delay`, `late_aircraft_delay`), plus cause counts (`carrier_ct`, `weather_ct`,
  `nas_ct`, `security_ct`, `late_aircraft_ct`). `weather_ct` is **fractional** (e.g. 0.09, 1.80)
  — an apportioned share of delayed flights, not an integer count of weather-delayed flights.
- **Dates: full calendar year 2025, months 1–12.** Single year only.
- **Airport coverage: 364 US airports, 21 US carriers.**
- **FRA presence: NONE.** FRA is absent; so are MUC, LHR, CDG, AMS (all European hubs). Present:
  JFK, ATL, etc. This is US DOT domestic-carrier arrival data only.
- 11 rows have missing numeric values; the tracker's stated policy is preserve-as-null, sum
  available, never treat missing as "no cause" — correct.

## Decision-time feature availability

- These are **retrospective monthly totals**, published well after the month closes. There is no
  issue-time / decision-time structure: no timestamps, no hour, no per-flight scheduled vs actual
  arrival, no runway, no gate, no aircraft tail, no rotation link. BTS On-Time *Reporting Carrier*
  flight-level rotation data (which would have those) have **not** been acquired (confirmed in
  `weather database/DATA_SOURCES.md`, source 1).
- Consequence: nothing here can serve as an **issue-time predictor feature** for a 48-hour (or any)
  forecast. It cannot be joined to the OD/runway model at a decision time.

## Flight-level labels vs month aggregates

- **No flight-level delay labels exist in this file.** Every value is a monthly carrier×airport
  aggregate. `weather_delay` is total minutes attributed to weather for that cell, divided by
  nothing; `weather_ct` is the apportioned flight share. You cannot recover which flight, when, or
  under what observed weather.

## Allowed experiments (with this data, as-is)

1. **Descriptive cause-share analysis at US airports, 2025.** e.g. weather's share of
   `arr_del15` or of total delay minutes by airport/month/carrier; seasonality of `weather_ct`.
   Target = monthly aggregate; horizon = month. Compare models only within that monthly-aggregate
   target (never against the OD hourly target).
2. **Cross-sectional correlation / ranking** of airports or months by weather-delay share, as a
   *context/mechanism* study for the pitch ("weather is X% of US delay cause minutes"), clearly
   labelled as US and monthly.
3. **Provenance/quality reproduction**: re-run the tracker's `analyze_bts.mjs` counts (rows,
   airports, months, missing policy) as an integrity check — already reproduced here for the hash.

## Unsupported counterfactual claims (do NOT make)

- **Any FRA/German claim.** FRA is not in the data; no amount of modelling transfers US
  carrier×airport monthly aggregates to Frankfurt runway operations.
- **Flight-level or hourly delay prediction / labelling.** The data has neither; deriving a
  per-flight or per-hour weather-delay label from month totals is fabrication.
- **"Weather caused N minutes of delay" as an independent causal measurement.** `*_delay`/`*_ct`
  are *administrative cause attribution* by carriers under DOT rules, not measured causal effects
  (tracker's own caveat). Do not relabel BTS cause codes as runway outcomes.
- **Feeding BTS into the OD/runway forecast** as a feature, or scoring the OD model against BTS —
  different population (US), granularity (monthly), and target. Keep the OD experiment separate.
- **"Operating-direction changes cause delay X"** — no decision-time, no FRA, no counterfactual
  comparison set here. A counterfactual needs defensible comparison flights/days and controls for
  demand, season and time of day on matched FRA data, which this file cannot provide.

## Open questions (with consequence)

1. **Will 2016–2024 BTS aggregates or flight-level Reporting-Carrier data be acquired?** Without
   flight-level rotation + timestamps there is no decision-time delay label at all; the whole
   "delay routing" idea stays descriptive. (DATA_SOURCES says flight-level "not acquired",
   2016–2024 aggregates "underway".)
2. **Is any FRA/European delay source in scope?** If the goal is FRA delay, BTS is categorically
   the wrong geography; a Eurocontrol/DFS/Fraport source would be required. Consequence: without
   it, no FRA delay claim is defensible.
3. **If only month aggregates are ever available, is a monthly weather-delay-share model in
   scope at all,** given the challenge target is hourly OD / runway-18 usability? Consequence: it
   would be a separate deliverable, not comparable to the OD model, and must be scored on its own
   monthly target.

## Ran and saw / Inferred / Not verified

**Ran and saw**
- `shasum -a 256 raw2025/Airline_Delay_Cause.csv` == tracker `analysis_results.json.source_sha256` (MATCH).
- CSV: 22,687 rows; header = year,month,carrier,...,weather_ct,...,weather_delay,...; months {1..12} of 2025; 364 airports; 21 carriers; `FRA`/`MUC`/`LHR`/`CDG`/`AMS` all absent; `JFK`/`ATL` present; `weather_ct` fractional; 11 rows with missing numerics.
- `Download_Column_Definitions.xlsx`: delays in minutes, `arr_del15` ≥15-min arrival lateness, DOT airport codes.
- `data_provenance.json`: transtats.bts.gov, 2025-01..12, retrieved 2026-10-30.
- `weather database/DATA_SOURCES.md` + `README.md`: BTS for cause analysis, not a FRA substitute; flight-level rotation not acquired; cause codes = administrative attribution.

**Inferred**
- Only descriptive, monthly, US-scoped cause-share experiments are eligible. Any decision-time,
  flight-level, FRA, or causal claim is out of scope with the current file.
- Keeping the OD experiment separate is not just preference — BTS shares no target, horizon,
  geography or granularity with the OD model, so a cross-comparison would be meaningless.

**Not verified**
- Whether 2016–2024 aggregates or flight-level Reporting-Carrier data will arrive (not present now).
- The internal consistency of each numeric cell (I checked schema, coverage, FRA presence and the
  file hash, not row-by-row arithmetic of the cause decomposition).
- Any FRA/European delay source (none inspected; none referenced as acquired).

## Smallest actionable next step
Decide whether "delay routing" means (a) a US descriptive cause-share study on this monthly file —
feasible now, separate target — or (b) FRA delay prediction — blocked until a FRA/European
flight-level source with decision-time fields is acquired. Do not bridge (a) to (b).
