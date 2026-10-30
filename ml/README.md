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
- **Archived weather-model forecasts**, Open-Meteo Previous Runs API: `https://previous-runs-api.open-meteo.com/v1/forecast` at EDDF (50.033 N, 8.570 E). `<var>_previous_day1` and `<var>_previous_day2` are values from runs issued about 1 and 2 days before the target hour, which keeps the backtest honest about lead time.
- **Live forecast**, Open-Meteo Forecast API: `https://api.open-meteo.com/v1/forecast`, same variable names.
- **Flown operating directions**, if found (DFLD, UNH/Fraport statistics, OpenSky): used to validate the METAR-derived labels. See `ml/SOURCES.md`.

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
  - archived forecast offsets `previous_day1` for lead 1–24 h and `previous_day2` for lead 25–48 h
- Train and test split by time. The test period comes after the training period and is never used for fitting.
- Report accuracy and Brier score at lead 1, 6, 24 (and 48) h against two baselines:
  - persistence
  - the official rules applied to the forecast wind

The offsets are a proxy for availability. The archive does not supply original
publication timestamps. At leads 24 and 48 the nominal availability equals T,
so strict publication before T cannot be proved. Live forecasts with explicit
issuance or retrieval metadata are rejected if that timestamp exceeds T.

Training uses 6-hourly issues by default, each with all 48 hourly leads, and the
last six calendar months as expanding walk-forward folds. Change this with
`--issue-stride` and `--months`. Training labels must end before the fold starts.
Early stopping is disabled to avoid a random internal validation split.
OD probabilities blend the classifier with persistence. For each fold, a separate
fit and the final 60 days of its training period select the blend by Brier score.
The inner fit excludes labels crossing that validation boundary. Weights are
selected for lead buckets 1, 2–6, 7–24 and 25–48 hours, then the classifier is
refitted on the full pre-test history. The held-out month never selects weights.
Saved monthly fits allow hindcasts to select a model trained before issue time;
the final fit uses all available targets for future forecasts.

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
explicit `r18_label_type: "inferred"`.

`quality.json` has this shape, for the UI owner to add as `QualityResult`:

```typescript
type Period = { start: string; end: string };
type Score = {
  lead_h: 1 | 6 | 24 | 48; n: number; change_n: number;
  model_acc: number | null; rule_acc: number | null; persistence_acc: number | null;
  model_brier: number | null; rule_brier: number | null; persistence_brier: number | null;
  model_change_acc: number | null; rule_change_acc: number | null;
  persistence_change_acc: number | null;
};
type Scores = { od: Score[]; r18: Score[] };
type Bin = {
  lower: number; upper: number; n: number;
  mean_predicted: number | null; observed_frequency: number | null;
};
type QualityResult = {
  schema_version: number; evaluation: string; r18_label_type: "inferred";
  issue_stride_h: number;
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
