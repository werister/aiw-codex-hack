# ML pipeline

Python 3.13 data, training, evaluation, and 48-hour forecast CLI for the
Frankfurt Airport runway-direction challenge.

```bash
python -m pip install -r ml/requirements.txt
python -m ml.fetch
python -m ml.train                         # monthly walk-forward; default 12 months
python -m ml.train --compare-label-policy # optional OD label-policy sensitivity
python -m ml.forecast --day 2026-10-31
python -m ml.forecast --now               # issue at the current floored hour
python -m ml.forecast --day 2026-10-31 --json
python -m pytest ml/tests -q
```

`ml/rules.json` is the source for official operating limits. Training writes
model artifacts under `ml/models/` and evaluation JSON under
`web/public/data/`. The UI contract is `web/src/lib/forecast-types.ts`.

## Data and issue-time inputs

- **Observed wind:** EDDF METAR from the Iowa Environmental Mesonet ASOS archive.
- **Archived forecasts:** Open-Meteo Previous Runs at EDDF, with day 1, 2, and
  3 offsets.
- **Live forecasts:** Open-Meteo Forecast API.
- **OD reference:** recorded DFLD stable-hour directions; see
  `data/ground_truth/README.md` for source and clock assumptions.

Every forecast has an issue time T. Any explicit `issued_at` and `retrieved_at`
timestamp supplied with archive or live forecasts must each be no later than T;
observation availability is also bounded by T. Archived forecasts use day 1 for
leads 1–18, day 2 for 19–42, and day 3 for 43–48. Their exact publication time
is unavailable, so the conservative six-hour availability proxy must be no
later than T. Future observations and newer runs are excluded.

`ml.features.FEATURES` has 45 columns across three groups: base, model
ensemble, and synoptic pressure features. There is no separate state-feature
group. The ensemble combines ECMWF IFS, GFS, and ICON forecasts after wind-speed
scaling constants fitted on 2024 data and held fixed across walk-forward folds;
the synoptic group derives pressure differences and geostrophic tailwinds.
Missing model inputs remain missing.

For OD rule updates, `tailwind_since_issue()` carries the duration of the
observed positive landing-tailwind run into both the base-wind and ensemble-wind
state machines. The forecast fallback uses the same timer logic. It is
operational state, not an additional learned feature or an R18 timer.

## Labels and fitting

OD targets use all recorded DFLD stable-hour labels in the primary fit. A
rule-derived suspected-run flag is a review signal, not independent proof of a
bad recording; `--compare-label-policy` reports the flagged-row sensitivity
separately. It does not remove those labels from the primary fit.

Runway 18 targets are inferred from METAR using the official wind limits.
Unknown or variable wind remains unlabelled rather than being treated as usable.

Training uses time-ordered monthly walk-forward folds, with the most recent
12 months by default. Labels that extend across a test boundary are purged from
training. Held-out months never select blend weights.

The OD classifier blends with persistence using lead and weather-regime weights
selected on the preceding 60-day validation block. R18 similarly blends its raw
classifier with the issue-time persistence state, with weights selected on the
preceding 60 days by horizon only. Sparse or closure-free validation horizons,
unknown current R18 state, and artifacts without saved R18 weights use the raw
R18 probability.

## Evaluation and denominators

Lead scores report accuracy and Brier score at 1, 6, 24, and 48 hours against
persistence and the official rule forecast. The corrected multimodel-weather
rule (`rule_od25_ens` / `rule_18_ens`) is a separate comparator on the same
eligible rows. Accuracy, Brier, and difference confidence intervals use 1-day,
3-day, and 7-day block resampling. A block-length interval is null unless all
scored days are covered by complete contiguous blocks of that length. The
significance output also reports paired McNemar and Diebold–Mariano comparisons.
McNemar p-values are nominal despite dependence in the data and are not adjusted
for multiple comparisons. Undefined rates, scores, and intervals are JSON
`null`.

OD change timing requires a complete 48-hour hourly forecast and 97 half-hour
DFLD bins including the issue-time state. Actual changes are counted strictly
after issue time. `within_1h` and `within_3h` divide direction-correct timing
hits by issue windows that contain an actual change; missing predictions and
wrong-direction predictions are misses. The no-change false-alarm rate divides
warned no-change windows by all complete no-change windows. These issue windows
overlap and are not independent events.

The separate OD event metric deduplicates actual half-hour transitions across
complete overlapping windows and uses only the first forecast change per issue.
Directional warnings match unique actual events one to one within three hours.
Event recall is matched unique events / unique actual events; precision is
matched warnings / matched warnings plus false-alert clusters. False alerts per
exposure day use the union of valid 48-hour issue windows, so overlapping
forecasts do not inflate exposure. Timing error and warning lead are summarized
over matched pairs.

R18 event scores are issue-window outcomes, not unique closure episodes. For
each horizon (1, 6, or 24 hours), only issues with every target hour labelled
and every compared prediction valid enter the shared cohort. A positive window
means any target hour is inferred closed. Counts and recall/precision therefore
use complete issue windows as their denominator.

## Runtime outputs

`web/public/data/backtest.json` and `quality.json` include out-of-sample skill,
significance, reliability, event metrics, and coverage/exclusion counts.
`p_18_usable` is the served R18 probability; raw scores remain separately
available when blending applies. `next_change` preserves its existing UI fields
and adds direction-error and per-reason exclusion counts. `quality.json` is typed
by `web/src/lib/forecast-types.ts`.

For CLI inputs, `ml.predict.predict_48h(issue_time_utc, obs, nwp, od_at_issue)`
returns 48 hourly rows. Supply observed direction history through
`obs.attrs['od_history']` with `time`, `od`, and `available_at`; otherwise a
recorded `od` column may be used with its availability time. Saved hindcast
models must have training labels ending before the requested issue time.

For a past or today's `--day`, the issue is that date's 00:00 Europe/Berlin;
today runs in live mode. A future `--day` and `--now` use the current floored
hour as issue time. A future requested date must intersect that 48-hour horizon;
the CLI returns the complete 48-hour trajectory and identifies the requested
date in the response. It never fetches future observations.
