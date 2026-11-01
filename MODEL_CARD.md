# Model card · Frankfurt Runway Outlook

## Purpose and distribution

Research into a 48-hour hourly forecast of airport-wide direction (25 west / 07 east), runway-18 weather usability, uncertainty and the next likely change. Independent decision-support demo, not for operational use; not affiliated with Fraport or any airline.

The historical fitted model is `walk-forward-v6`. Fitted weights and recorded direction inputs are withheld because their source does not establish open redistribution rights. The public package runs a weather-rule example labelled `rules-demo`; its scores are uncalibrated and do not inherit the historical model's measured accuracy.

## Inputs, targets and method

IEM EDDF METAR observations, archived Open-Meteo best-match and separate ECMWF/GFS/ICON weather forecasts, synoptic pressure differences, runway wind components and state-machine outputs. Wind scaling is fitted using data preceding the test months. Gradient-boosted trees predict direction and wind-inferred runway-18 usability. Short-lead persistence blending uses earlier validation data.

Historical direction labels came from a public DFLD proxy, available only after the labelled hour ends. Stable-hour filtering omits direction-change hours. Runway-18 targets come from weather thresholds; operational non-use is not a valid weather-closure label. Source rights, transformations and exclusions are documented in [the source inventory](docs/DATA_SOURCES.md).

## Evaluation

Expanding monthly walk-forward evaluation compares fitted predictions with the rule baseline and persistence. Each fit excludes its own test month. Test results informed development, so these are not untouched final test folds. Counts, 1/6/24/48-hour accuracy, Brier scores, 95% whole-day bootstrap intervals and paired comparisons are in [EVALUATION.md](docs/EVALUATION.md), generated or checked with the commands recorded there.

`python -m ml.evaluate` reads published aggregates only. `--replay` recomputes the saved folds when supplied with permission-cleared original fits and direction labels; it does not refit or tune. Those restricted inputs are absent from this distribution.

## Material limits

- The model does not beat persistence in 1-hour direction accuracy.
- Direction targets are a proxy, not certified DFS operations. Excluding change hours changes the evaluation population. A suspect multi-day source interval remains in primary scoring, with separate sensitivity analysis.
- Six-hour publication lag and archived previous-day offsets approximate historical availability. Exact publication times, reporting delays and some source clock semantics are not verified.
- Overlapping forecast windows are correlated; uncertainty intervals resample issue-days, with longer-block sensitivity retained in aggregate output. Statistical comparisons are not adjusted across all experiments.
- Hourly state accuracy is different from detecting a unique direction change. Event recall and false alarms must be reported separately.
- Runway-18 closure labels are inferred, rare, incomplete and poorly detected. They do not establish advance operational closure prediction.
- Certainty is the smaller of two probability margins, not a calibrated joint correctness probability. Next-change probability supports the new state at an hour; the timing window has no measured coverage guarantee.
- No certified aircraft eligibility, demand, capacity, staffing, separation, clearance or financial-benefit model is supplied. Aircraft motion is illustrative.

## Reuse

Proposed MIT code licence requires approval by Kai Detmers, Jayden Bruck, Hugo Hader and Luca Schultz. Weather retains provider terms and attribution. Written permission or an independent rights assessment is needed before distributing direction records or fitted weights. A new prospective test and domain review are needed before considering any operational application.
