# Forecast pipeline

Python 3.12 or 3.13. Install from the repository root:

```sh
python -m pip install -r ml/requirements.txt
python -m ml.forecast --demo
python -m ml.forecast --demo --json --out web/public/forecasts/sample.json
python -m pytest ml/tests -q
```

The offline example computes a 48-hour weather-rule forecast for 28 October
2026 using bundled, licensed IEM and Open-Meteo snapshots. It needs no network
or API key. Its `rules-demo` version and output note distinguish it from the
historically evaluated trained model. Its probability margins and certainty
are heuristic and uncalibrated. No recorded operating-direction outcomes enter
this example.

The original fitted artifacts and DFLD direction labels are withheld pending
permission. Their absence is deliberate; see [data rights](../docs/DATA_SOURCES.md).
The dashboard's historical quality results describe the earlier classifier,
not the bundled rule demonstration.

## Modules and commands

| Module | Purpose |
|---|---|
| `forecast` | 48-hour JSON/table CLI, evidence serialization and offline demo |
| `rules` / `rules.json` | Wind components and the documented rule state machine |
| `fetch` / `live` / `synoptic` | Public weather downloads, caching and issue-time availability |
| `dfld` | Direction-history parser and opt-in downloader; processing permission required |
| `features` | Shared ordered feature construction |
| `predict` | Eligible fitted-artifact selection and persistence blending |
| `train` | Expanding monthly evaluation and fitting, with local authorized labels |
| `quality` / `significance` | Metrics, complete-window event scoring and intervals |
| `evaluate` | Display historical aggregates or replay saved monthly fits without fitting |
| `challengers` / `first_event_experiment` | Separate research experiments, never automatic model promotion |

```sh
python -m ml.evaluate                    # historical aggregate report only
python -m ml.forecast --day 2026-10-28   # trained artifact if supplied; otherwise explicit rules fallback
python -m ml.forecast --now              # current public weather; network required
```

The full research pipeline needs source permission and local labels first:

```sh
python -m ml.fetch --since 2024-01-01 --sources metar previous multimodel
python -m ml.synoptic
python -m ml.dfld --permission-confirmed --since 2018-01-01 --until 2026-10-29
python -m ml.train --months 12 --compare-label-policy
python -m ml.evaluate --replay --out verification/replay.json
```

Do not run the DFLD command unless you have authorization for your processing.
Downloading a publicly readable page does not grant redistribution rights.
`train` and `evaluate --replay` fail with a clear explanation when required
labels or artifacts are absent. Training writes `ml/models/` and
`web/public/data/`; back up any research outputs you want to retain first.

## Issue-time inputs

All supplied `issued_at` and `retrieved_at` timestamps, observed wind and
recorded direction availability must be no later than issue time T. Archived
weather uses previous-day 1 for leads 1–18 h, day 2 for 19–42 h and day 3 for
43–48 h. A six-hour publication proxy must also be no later than T. Actual
historical publication timestamps remain unverified.

`ml.features.FEATURES` contains the ordered base, multimodel and pressure-gradient
columns. ECMWF, GFS and ICON wind speeds use fixed scaling ratios fitted on
2024 data, before the evaluation months. Missing optional inputs remain missing.
The rule state machine carries the observed continuous tailwind duration at
issue time into the forecast. It never backdates forecast wind to issue time.

For a past `--day`, issue time is midnight Europe/Berlin. Today and future
requests use live weather; a future date must intersect the current 48-hour
horizon. `--now` uses the current floored hour. Future observations are excluded.
The UI contract is [forecast-types.ts](../web/src/lib/forecast-types.ts).

## Training and evaluation design

OD targets use all recorded stable-hour labels. Transition hours are excluded
from the stable-hour accuracy score. A whole-run rule-disagreement flag is
sensitivity-only: it can use later weather and is not proof of a faulty feed.
It must never silently filter the primary labels. The retained counterexample
tests document that temporal limitation.

Runway-18 targets are inferred from METAR wind limits, not observed closures.
Unknown or variable wind remains unlabelled. Monthly training purges any target
whose label availability crosses the test boundary. Persistence weights use an
earlier 60-day validation block; test months never select those weights.
OD weights depend on horizon and weather regime; runway-18 weights depend on
horizon. Sparse or closure-free runway-18 validation retains the raw classifier.
The test months nevertheless informed feature selection and repeated review;
they are not an untouched final test.

Accuracy and Brier scores compare identical eligible rows. Paired bootstrap
intervals resample issue days, or contiguous three/seven-day blocks. A block
interval is unavailable if any scored day lacks a complete block. Overlapping
forecast windows remain dependent. Nominal row-level McNemar and daily-loss
Diebold–Mariano p-values are not adjusted for multiple comparisons.

Change timing requires all 48 forecast hours and 97 half-hour truth bins,
including state at issue. Missed or wrong-direction forecasts count as misses.
The unique-event report separately matches directional first-change warnings
one to one within three hours and clusters false warnings. Its exposure is the
union of valid forecast windows. Runway-18 reports complete overlapping positive
issue windows, not unique closure episodes.

See [measured evaluation](../docs/EVALUATION.md) for reproduced numbers and limits.

