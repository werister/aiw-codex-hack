# Tasks

## 1. Tower-staff view (persona: tower and ops staff under stress)

- [ ] 1.1 One glance: current OD, runway 18 yes/no, next change time with confidence, in large type
- [ ] 1.2 Plain yes/no states first; click to drill into the details
- [ ] 1.3 FraAlliance look (colours and type from their public material)

## 2. Timeline

- [ ] 2.1 48 h hourly strip: OD, 18, confidence, probabilities
- [ ] 2.2 Next change window and runway-18 closures
- [ ] 2.3 Day picker (latest plus jury days)

## 3. Simulated ops screen

- [ ] 3.1 Schematic FRA runway map (07L/25R, 07C/25C, 07R/25L, 18) showing the active direction and 18 open or closed
- [ ] 3.2 Arrivals and departures flowing along the active runways, clearly labelled as simulated

## 4. Model quality, widget, deploy

- [ ] 4.1 Model quality panel from WP8: walk-forward out-of-sample skill at 1/6/24 h vs rules and persistence, in-sample vs out-of-sample, data used
- [ ] 4.2 iPad widget layout
- [ ] 4.3 Vercel from `main`, `web/` root

## 5. Forecast context and drilldown

- [ ] 5.1 Show issue time, age, Europe/Berlin date and UTC offset, mode, NWP source, model version and rules version
- [ ] 5.2 Agree per-field provenance with WP4/WP7: label DFLD/UNH OD by source, METAR-rule fallback and runway-18 targets `INFERRED`, unknown sources explicitly; keep probabilities, the documented margin-based certainty score and measured accuracy distinct
- [ ] 5.3 Add keyboard/touch hourly selection and detail using the existing contract's probabilities, wind, tailwind and rule-baseline fields
- [ ] 5.4 Show null next-change and empty closure states accurately; apply end-exclusive closure intervals and show ongoing-at-horizon closures without inventing reopening
- [ ] 5.5 Apply supplied FraAlliance branding, readable text states and visible keyboard focus; label any optional animation `SIMULATION`

## 6. Published data and evidence

- [ ] 6.1 Read the documented `/forecasts/index.json` manifest and latest/date files; supplement with native date input and prevent earlier requests replacing a later selection
- [ ] 6.2 Validate required forecast fields and 48 unique hourly leads; show loading, missing/request-failed and invalid-data states with retry
- [ ] 6.3 Load WP3's existing `web/src/data/backtest.json` independently through an optional server-only loader and show model/rule/persistence accuracy, Brier scores and counts at 1/6/24 h for OD and runway 18
- [ ] 6.4 Show train/test dates and label provenance; keep missing metrics unavailable and inferred references explicit
- [ ] 6.5 Agree WP8 `QualityResult` and load `web/src/data/quality.json`: data sources, walk-forward folds, in/out-of-sample metrics, calibration with an explicit target event/score and next-change timing accuracy

- [ ] 6.6 Reconcile stale type comments with the new CLI brief: per-target reference absence/provenance, and visible `rules-fallback` mode

## 7. Acceptance walkthrough

- [ ] 7.4 Check first-hour and later OD changes in both directions: `next_change.p` matches the new-OD probability; agree abrupt-jump/no-neighbour and DST window handling with WP4
- [ ] 7.5 Reject a time/lead mismatch; confirm T+1 is not labelled current; record WP2/WP3 ownership of hourly-wind hysteresis and WP4 ownership of issue-time cutoffs
- [ ] 7.6 Verify manifest date strings and the 0.5 usable tie; retain DFLD proxy provenance and excluded-hour coverage without inventing runway-18 references

- [ ] 7.1 Verify latest and hindcast day selection, keyboard/touch drilldown, change/closure display and backtest evidence at laptop/iPad widths
- [ ] 7.2 Verify missing/malformed files, absent reference rows, null change, closures continuing after hour 48, index failure, overlapping requests and Berlin daylight-saving repeated hours
- [ ] 7.3 Confirm every displayed value comes from the selected payload, no simulated feed appears live, and recorded, inferred and unknown references remain correctly labelled per target
