# ml/ · data, labels, model, backtest, forecast CLI (Python 3.13)

Owners: Kai (co-lead) and our agents. Rules: `ml/rules.json` (from the official FraAlliance brief). Never hard-code a threshold anywhere else.

```bash
python -m pip install -r ml/requirements.txt
python -m ml.fetch            # raw data into data/raw/ (cached)
python -m ml.labels           # data/labels.parquet (half-hourly states from METAR + rules)
python -m ml.train            # models -> ml/models/, metrics -> web/public/data/
python -m ml.forecast --day 2026-10-31            # 48 h hourly table from 00:00 local that day
python -m ml.forecast --day 2026-10-31 --json     # same, as ForecastResponse JSON (web/src/lib/forecast-types.ts)
python -m pytest ml/tests -q                      # rule and leakage tests
```

## Sources (cite all of them in the model card)
- **EDDF METAR**, Iowa Environmental Mesonet ASOS archive: `https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=EDDF&...` (half-hourly wind direction, speed, gusts).
- **Archived weather-model forecasts**, Open-Meteo Previous Runs API: `https://previous-runs-api.open-meteo.com/v1/forecast` at EDDF (50.033 N, 8.570 E). `<var>_previous_day1`, `<var>_previous_day2` and `<var>_previous_day3` give values from forecasts about 1, 2 and 3 days before target time. Evaluation adds a six-hour publication lag.
- **Live forecast**, Open-Meteo Forecast API: `https://api.open-meteo.com/v1/forecast`, same variable names.
- **Flown operating directions**, if found (DFLD, UNH/Fraport statistics, OpenSky): used to validate the METAR-derived labels. See `ml/SOURCES.md`.

## Forecast inputs and features

`ml.features.FEATURES` = base + ensemble + synoptic + state groups:
- **Base:** recorded OD at issue, hours since change, METAR wind now and its 3 h trend, best-match forecast wind, runway tailwinds and the rule states, hour and season, lead.
- **Ensemble:** ECMWF IFS, GFS and ICON previous runs (`data/openmeteo_previous_runs_multimodel.parquet`), each scaled to METAR level with `WIND_SCALE` (fitted on 2024 only, before every test month). Per-model tailwind on 25 and 18, the ensemble mean and spread of those tailwinds, direction spread (1 minus mean resultant length), share of models favouring 25, 80 m tailwinds, and the official state machine rerun on the corrected ensemble-mean wind (`rule_od25_ens`, `rule_18_ens`).
- **Synoptic:** forecast pressure about 200 km north, south, west and east of FRA (`ml/synoptic.py`), as north-south and east-west differences and their geostrophic tailwind on 25 and 18.
- **State:** observed tailwind on the direction in use now, how many hours it has stayed positive (max 5), the ensemble tailwind on the current direction, and the METAR direction.

All forecast inputs use the same day1/day2/day3 offsets and six-hour lag. Live runs
take separate models and pressure from a pre-issue snapshot, otherwise from a dated
run with a 12 h publication proxy. A missing model stays missing; it is never filled
with another model. The ICON-D2 ensemble spread (Zinkhan et al. 2023) has no archive
before 29 Jul 2026, so it cannot be backtested and is not used.

## Labels
The official rules run as a state machine over the half-hourly METARs:
- A tailwind of 10 kt or more on the landing direction switches the OD immediately.
- A tailwind between 0 and 10 kt switches it after more than 30 minutes.
- Calm or variable wind keeps the current OD.
- Runway 18 is unusable when its tailwind is 15 kt or more, or its crosswind including gusts is over 40 kt.

The weather-rule hourly label is the state at the full hour. OD training targets
instead use recorded DFLD stable-hour directions in `data/ground_truth/dfld_hourly.csv`.
Read that folder's README for source and clock assumptions. The current recorded
state becomes an input only after its full hour has ended. Runway 18 usability is
always inferred from METAR and the official rules, not recorded closure history.

## Honest evaluation
- Issue time T. The model only uses what was known at T:
  - observations up to T
  - archived forecast offsets with a six-hour publication lag: `previous_day1` for leads 1-18 h, `previous_day2` for 19-42 h and `previous_day3` for 43-48 h
- Train and test split by time. The test period comes after the training period and is never used for fitting.
- Report accuracy and Brier score at lead 1, 6, 24 (and 48) h against two baselines:
  - persistence
  - the official rules applied to the forecast wind

An offset N is eligible only when `lead_h <= 24*N - 6`. Buffered availability
is `target_time - N days + 6 hours` and must be no later than T. At leads 18
and 42 the buffered availability equals T; leads 24 and 48 now use older runs.
The archive does not supply exact publication timestamps, so the six-hour lag
remains a conservative availability assumption. Day 3 is required for leads
43-48; missing fields raise an error rather than substituting a newer run.
Live forecasts with explicit issuance or retrieval metadata are rejected if
that timestamp exceeds T.

Training uses 6-hourly issues on the Europe/Berlin clock (00:00, 06:00, 12:00,
18:00 local, like the jury days), each with all 48 hourly leads, and the
last twelve calendar months as expanding walk-forward folds. Change this with
`--issue-stride` and `--months`. Training labels must end before the fold starts.
Early stopping is disabled to avoid a random internal validation split.
OD probabilities blend the classifier with persistence. For each fold, a separate
fit and the final 60 days of its training period select the blend by Brier score.
The inner fit excludes labels crossing that validation boundary. Weights are
selected per lead bucket (1, 2–6, 7–24, 25–48 h) and target regime: `night`
(23:00–05:00 local, the night-flight restriction), `calm` (forecast 10 m wind
below 2.5 kt, about 4 kt METAR) or `active`. A regime with fewer than 50
validation rows uses its lead bucket's weight. Keys look like `6:night` in
`od_model_weight`. The classifier is then refitted on the full pre-test history. The held-out month never selects weights.
Saved monthly fits allow hindcasts to select a model trained before issue time;
the final fit uses all available targets for future forecasts.

### Stuck recorded OD

A tailwind of 10 kt or more on the landing runways forces an immediate change.
`ml.quality.suspect_od_runs` flags a recorded OD run with three or more METAR
hours at or above that limit as a stuck feed. In 2018–2026 it flags one run:
OD 07 from 8 Oct 2026 12:00 to 12 Oct 18:00 local (103 hours), against 8–17 kt
westerlies that DWD station 01420 also measured. Fitting and blend selection
leave out OD rows whose target or issue-time state comes from that run.
Headline scores (`od`, `out_of_sample`, `rows` in `october.json`) still count
those hours as recorded. The `*_stuck_feed_excluded` fields drop them, which
favours both the model and the rules; report both.

## Prediction interface

`ml.predict.predict_48h(issue_time_utc, obs, nwp, od_at_issue)` returns the 48-row
DataFrame described in its docstring, with probabilities and both rule baselines.
It accepts the data lane's METAR and previous-runs columns directly. Live NWP
needs `issued_at` or `retrieved_at`. Attach the full recorded state history as
`obs.attrs['od_history']`, with `time`, `od` and `available_at`, to supply time
since change even during long holds or changes after the latest METAR. An `od`
column in `obs` is a fallback; without history that feature is missing. Future observations are
filtered. Dates before the earliest saved walk-forward fit are rejected.

## Runtime quality files

Both outputs are runtime assets in `web/public/data/`, served as
`/data/backtest.json` and `/data/quality.json`.
`backtest.json` follows `BacktestResult`, with extra change-case metrics and an
explicit `r18_label_type: "inferred"`. Scores report `raw_model_*`, `blend_*`,
`rule_*` and `persistence_*` accuracy, Brier and change-case accuracy. Existing
`model_*` fields alias the served blend for compatibility. For runway 18 the
classifier is served directly, so its raw and blend scores are identical.

`quality.json` has this shape, for the UI owner to add as `QualityResult`:

```typescript
type Period = { start: string; end: string };
type Score = {
  lead_h: 1 | 6 | 24 | 48; n: number; change_n: number;
  model_acc: number | null; rule_acc: number | null; persistence_acc: number | null;
  model_brier: number | null; rule_brier: number | null; persistence_brier: number | null;
  model_change_acc: number | null; rule_change_acc: number | null;
  persistence_change_acc: number | null;
  raw_model_acc: number | null; raw_model_brier: number | null;
  raw_model_change_acc: number | null;
  blend_acc: number | null; blend_brier: number | null; blend_change_acc: number | null;
};
type Scores = { od: Score[]; r18: Score[] };
type Bin = {
  lower: number; upper: number; n: number;
  mean_predicted: number | null; observed_frequency: number | null;
};
type QualityResult = {
  schema_version: number; evaluation: string; r18_label_type: "inferred";
  issue_stride_h: number; publication_lag_h: number;
  forecast_offsets: { lead_start: number; lead_end: number; previous_day: number }[];
  folds: {
    month: string; train_period: Period; train_target_end: string;
    test_period: Period; train_n: number; test_n: number;
    od_model_weight: Record<string, number>; od_blend_validation_period: Period;
    in_sample: Scores; out_of_sample: Scores;
  }[];
  in_sample: Scores; out_of_sample: Scores;
  reliability: { od: Bin[]; r18: Bin[] };
  confidence_reliability: { od: Bin[]; r18: Bin[]; combined: Bin[] };
  certainty_reliability: Bin[];
  next_change: {
    n_actual_change_windows: number; within_1h: number | null; within_3h: number | null;
    n_no_change_windows: number; false_alarm_rate: number | null;
    n_predicted_changes: number; excluded_incomplete_windows: number;
    mean_absolute_error_h_when_predicted: number | null; truth: string;
  };
  drivers: { feature: string; importance: number }[];
  rule_label_comparison: { n: number; agreement: number };
  data_sources: { name: string; url: string; file: string }[];
  coverage: {
    feature_rows: number; skipped_issue_times: number;
    observed_base_rates: { od25_share: number; changes_per_year: number; r18_closed_share: number };
  };
  limitations: string[];
};
```

Reliability bins compare predicted event probability with observed frequency.
Confidence bins compare the probability of the selected class with correctness.
Combined confidence uses the smaller of the two class confidences, and its
observed frequency requires both calls to be correct. Missing metrics use null.
`certainty_reliability` checks the CLI's displayed score, which is the smaller
absolute probability margin `abs(2*p - 1)` on a 0..1 scale. That margin is not a
calibrated probability; its observed hit rate is reported without relabeling it.
In-sample aggregates repeat rows across expanding fits; out-of-sample folds do
not overlap. Timing scores count missed actual changes as misses and report
false alarms on no-change windows separately. Half-hour clock ambiguities and
incomplete truth windows are excluded.

In `backtest.json`, `train_period` describes the last fold's training issues,
while `test_period` spans all six held-out months. Those summary periods overlap
because earlier test months become training data in later folds. Each individual
fold remains separated in time. Inferred runway 18 targets require a METAR no
more than one hour old, matching the CLI's observed overlay.
Fold sizes count feature rows, including unlabelled transition-hour targets;
each score's `n` counts usable labelled targets. Permutation importance measures
the blended forecast's Brier score on the final held-out month.
