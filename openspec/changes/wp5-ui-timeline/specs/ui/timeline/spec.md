# Spec Delta

## Purpose
Show the 48 h forecast, its certainty and the next change at a glance, on a laptop and on an iPad.

## ADDED Requirements

### Requirement: Preparation overview retains both forecast risks
The UI SHALL show operating-direction changes and runway-18 restriction periods together, including additional transitions derivable from supplied hourly states. It SHALL support selecting each event's source hour, preserve only supplied change windows, label hourly marginal probabilities accurately, and distinguish issue-time references from first-hour predictions. Unvalidated operational firmness and joint no-change probability claims SHALL NOT be shown.

#### Scenario: Direction change and runway restriction overlap
- **WHEN** a forecast contains both risks in the same or different hours
- **THEN** both remain visible and selectable, and an earlier event does not hide the later one

#### Scenario: Restriction or coverage ends without a known reopening
- **WHEN** the last available hour is restricted or the supplied hours have a gap
- **THEN** the overview identifies the coverage limit and does not invent continuous availability or reopening

### Requirement: Handover answers use a bounded forecast window
The forecast guide SHALL offer a deterministic briefing, runway-18 restriction summary and separate direction/runway-18 model-rule comparison for the selected hour and up to five following consecutive UTC hours. Answers SHALL include issuance, actual coverage and supplied provenance; a copy action SHALL report success or failure. Unsupported questions SHALL NOT create new operational recommendations.

#### Scenario: The selected window crosses a clock change
- **WHEN** two UTC hours share a Berlin clock time
- **THEN** the guide preserves both hours and identifies their offsets rather than losing or duplicating an hour

#### Scenario: Fewer than six consecutive hours remain
- **WHEN** the forecast ends or has a gap before the window is complete
- **THEN** the answer states the actual coverage and does not extrapolate missing hours

### Requirement: Preparation demonstrations preserve evidence boundaries
The historical replay SHALL compare a user-entered preparation scenario with available recorded-state timing without asserting an exact transition time or validated operational benefit. The published pitch SHALL show saved forecast and evaluation values only. Synthetic runway-18 fixtures SHALL remain outside that pitch and contribute no observations or evaluation scores.

#### Scenario: Review time follows the first recorded opposite direction
- **WHEN** the scenario's calculated review time is later than an available recorded opposite-direction label
- **THEN** the replay identifies that the changed state was already recorded by then, without presenting the scenario as successful preparation

#### Scenario: Jury opens the pitch
- **WHEN** the pitch is displayed
- **THEN** it opens a saved historical forecast and offers the separate aggregate 1/6/24-hour evidence, without a synthetic restriction scenario

### Requirement: Timeline shows every deliverable
The timeline SHALL show, for each of the 48 hours, the OD, P(runway 18 usable) and the certainty, and SHALL highlight the next likely change time.

#### Scenario: Next change
- **WHEN** the forecast has an OD change at 14:00
- **THEN** the timeline marks 14:00 and shows the change window and probability

### Requirement: Backtest visible
The UI SHALL show the skill at 1, 6 and 24 h for the model, the rules and persistence from `backtest.json`.

#### Scenario: Judge asks how good it is
- **WHEN** the presenter opens the backtest panel
- **THEN** the three methods are compared at each lead

### Requirement: Next-change probability names its event
The UI SHALL use the producer's first forecast hour whose OD differs from `current_od`. It SHALL describe `next_change.p` as the probability of the new OD at that hour, not the probability of a change event. The supplied window SHALL retain the documented neighbouring-hour convention with p(new OD) between 0.35 and 0.65; unresolved boundary cases SHALL require producer agreement.

#### Scenario: First change is eastbound
- **WHEN** `current_od` is `25` and the first differing forecast hour has `od: 07` and `p_od25: 0.2`
- **THEN** the next-change display uses that hour and labels `p: 0.8` as the probability of OD 07 at that hour, without claiming an 80% probability of switching exactly then

#### Scenario: Change window lacks neighbouring uncertainty hours
- **WHEN** an abrupt probability jump supplies no neighbouring hours in the documented window band
- **THEN** the producer and UI use their agreed edge-case representation without fabricating a probabilistic change interval

### Requirement: Forecast timestamps match their leads
Each hourly row SHALL represent `issued_at + lead_h hours`, with leads 1–48. The UI SHALL reject a payload whose time and lead disagree and SHALL distinguish forecast validity time from issue-time state.

#### Scenario: Sorted hours have the wrong origin
- **WHEN** a payload has 48 sorted hourly rows but lead 1 has the same timestamp as `issued_at`
- **THEN** the UI reports invalid data rather than displaying that row as a valid T+1 forecast

### Requirement: Recorded-direction proxies retain their limits
DFLD references SHALL be identified as recorded-OD proxies separately from METAR-rule labels. Any supplied evaluation coverage and exclusions SHALL remain visible. The UI SHALL NOT infer runway-18 usability or certified movement history from DFLD OD alone.

#### Scenario: Direction-change hours were excluded
- **WHEN** reported DFLD evaluation coverage excludes direction-change hours
- **THEN** the panel reports those exclusions and does not present stable-hour accuracy as measured next-change timing performance

### Requirement: Forecast provenance is visible
The UI SHALL display issue time and age, forecast mode, weather source, model version and rules version from `ForecastResponse`. It SHALL show Europe/Berlin date and UTC offset, using UTC timestamps for ordering, and SHALL distinguish a live forecast from a live operational feed.

#### Scenario: Historical forecast selected
- **WHEN** a payload has `mode: hindcast`
- **THEN** the UI labels it `Historical forecast`, shows its original issuance and source, and does not describe it as a live configuration

#### Scenario: Rules fallback forecast
- **WHEN** `model_version` is `rules-fallback`
- **THEN** the UI prominently says `Rules fallback` and does not present its probabilities as results from the trained model

#### Scenario: Local clock repeats
- **WHEN** two consecutive UTC hours map to the same Berlin clock hour during a daylight-saving transition
- **THEN** both hours remain separately selectable in UTC order and display their different UTC offsets

#### Scenario: Forecast horizon has elapsed
- **WHEN** all hourly validity times precede the current time
- **THEN** the UI says the forecast horizon has elapsed while retaining its original issue time and mode

### Requirement: Reference provenance is explicit per target
The UI SHALL identify recorded, published, inferred or unknown provenance separately for issue-time OD and each hindcast target. Recorded OD SHALL NOT imply recorded runway-18 labels. Before interpreting the updated CLI semantics, producer/type/UI owners SHALL agree provenance and per-target absence metadata; stale type comments SHALL NOT substitute for that agreement.

#### Scenario: Recorded issue-time direction shown
- **WHEN** the issue-time OD has explicit DFLD provenance
- **THEN** the summary says `DFLD-recorded OD at issue time` and shows the source/reference time without claiming DFS confirmation

#### Scenario: Rule fallback at issue time
- **WHEN** the issue-time OD is derived from METAR and the official rules
- **THEN** the summary labels it `INFERRED — METAR + rules` at the issue time

#### Scenario: Mixed hindcast reference targets
- **WHEN** a row's OD comes from recorded DFLD history and its runway-18 reference comes from METAR rules
- **THEN** OD is labelled `DFLD-recorded` and runway 18 is labelled `INFERRED`, separately

#### Scenario: Provenance metadata absent
- **WHEN** a payload does not establish a reference's provenance through agreed metadata or an explicit versioned semantic contract
- **THEN** that reference says `Source not established` rather than being silently classified as recorded or inferred

#### Scenario: Runway-18 reference missing
- **WHEN** a recorded OD comparison is available but no runway-18 reference was established
- **THEN** the UI shows the OD comparison and runway-18 reference as unavailable, without inventing a boolean to fill the existing row shape

#### Scenario: Reference row missing
- **WHEN** an hour has no matching reference row
- **THEN** the UI reports the reference as unavailable and does not construct an observed direction from the model call

### Requirement: Hour selection reveals forecast inputs and outputs
The UI SHALL let users select an hourly cell by touch or keyboard and inspect that hour's timestamps, lead, model probabilities and certainty, wind/gusts, signed tailwind components and rule-baseline outputs. Probability, certainty and backtest accuracy SHALL have distinct labels. The certainty score SHALL retain the producer's definition `round(100 × min(abs(2*p_od25 - 1), abs(2*p_18_usable - 1)))` and SHALL NOT be presented as calibrated joint correctness.

#### Scenario: Hourly detail opened
- **WHEN** the user selects an hour
- **THEN** its details show `od`, `p_od25`, `p_18_usable`, `certainty`, `rule_od` and `rule_18_usable` without substituting one for another

#### Scenario: Missing wind direction
- **WHEN** `wind_dir_deg` is null
- **THEN** the detail says `Direction unavailable / calm` and does not invent a wind bearing

#### Scenario: Certainty score explained
- **WHEN** an hour has `p_od25 = 0.9` and `p_18_usable = 0.9`
- **THEN** its producer-defined certainty is displayed as `80 / 100` with a margin-score explanation, not as an 80% chance that both calls are correct

#### Scenario: Forecast hour is not current state
- **WHEN** the summary shows runway-18 usability from the first forecast row
- **THEN** it labels the row's T+1 validity time and applies the documented probability threshold of 0.5 without calling that prediction the current or issue-time runway-18 state

### Requirement: Change and closure states reflect the payload
The UI SHALL show the supplied next-change window/probability and closure intervals using the documented producer threshold `p_18_usable < 0.5`. It SHALL treat null next-change and an empty closure list as valid states, and a known closure `end` as the first usable hour. If closure continues through the final forecast hour, the UI SHALL mark reopening unknown rather than invent an endpoint; the producer and UI owner SHALL agree an explicit representation for this case.

#### Scenario: No change predicted
- **WHEN** `next_change` is null
- **THEN** the UI says `No direction change predicted within this forecast`

#### Scenario: Closure ends
- **WHEN** an hourly validity time equals a closure's `end`
- **THEN** that hour is outside that closure interval

#### Scenario: Closure continues beyond the forecast
- **WHEN** the last forecast hour still has `p_18_usable < 0.5`
- **THEN** its closure is labelled `Continues through forecast horizon; reopening unknown` and the UI does not depict an invented reopening at the boundary

### Requirement: Published-day loading is explicit and reliable
The UI SHALL read the documented forecast index and latest/date files, accept explicit dates without code changes, and validate 48 unique chronological hours with leads 1–48. Loading, invalid and unavailable states SHALL be distinct. The UI SHALL never show another day’s or fabricated forecast under the selected date.

#### Scenario: Forecast index unavailable
- **WHEN** the manifest is missing or malformed
- **THEN** the published-day list shows unavailable, explicit date selection remains possible, and any attempt to load the documented latest file is labelled as such without inventing a list of published dates

#### Scenario: Published file missing
- **WHEN** the selected day's file is missing or its request fails
- **THEN** the UI shows `Forecast unavailable` with retry and other-day selection instead of a forecast for another date

#### Scenario: Malformed forecast
- **WHEN** a response has a missing required field, duplicate or missing hour, invalid timestamp, probability outside [0,1] or certainty outside [0,100]
- **THEN** the UI displays an invalid-data state and does not render it as a valid forecast

#### Scenario: User changes day during loading
- **WHEN** a request for an earlier selection completes after a request for the currently selected day
- **THEN** only the currently selected day's payload may populate the timeline

### Requirement: Backtest provenance accompanies metrics
The panel SHALL show train/test dates, reference provenance and rules version, with separate OD/runway-18 accuracy, Brier score and sample counts for model/rules/persistence at 1/6/24 h. Inferred labels SHALL be identified per target. Missing or ambiguous provenance SHALL NOT be presented as verified flown-OD accuracy.

#### Scenario: Evaluation uses inferred targets
- **WHEN** evaluation provenance describes DFLD-recorded OD targets and METAR-plus-rule runway-18 targets
- **THEN** the panel identifies recorded OD and `INFERRED` runway-18 labels separately and explains each metric's reference

#### Scenario: Required evidence missing
- **WHEN** a required lead metric or provenance field is missing
- **THEN** that evidence is shown as unavailable and is not replaced with zero, interpolation or a claim of verified performance

#### Scenario: Backtest cannot load
- **WHEN** backtest loading fails but the selected forecast is valid
- **THEN** the forecast remains usable and the backtest panel displays its own unavailable state

### Requirement: Operations presentation is accessible and honest
The dashboard SHALL provide text-labelled status, visible keyboard focus and touch-accessible hourly detail on laptop and iPad layouts. Its schematic FRA runway map SHALL show the selected forecast direction and predicted runway-18 state with illustrative arrivals/departures labelled `SIMULATION`. It SHALL NOT imply live flight tracking or operational clearance authority. Optional 3D remains a separate WP9 deliverable.

#### Scenario: User cannot rely on color or hover
- **WHEN** the user navigates hourly states with keyboard or touch
- **THEN** OD, runway-18 probability, certainty and selected-hour detail are available without interpreting color alone or hovering

#### Scenario: Simulated aircraft are shown
- **WHEN** the schematic ops view depicts aircraft movements
- **THEN** the view visibly says `SIMULATION` and keeps the actual forecast source and issuance visible

### Requirement: Model quality follows the agreed WP8 artifact
The UI SHALL display WP8 data sources, walk-forward folds, in/out-of-sample results, calibration and change-timing accuracy from its agreed quality artifact. Calibration SHALL identify its target event and binned score/probability. Missing evidence SHALL remain unavailable; existing backtest metrics or margin-based certainty SHALL NOT be presented as measured calibration.

#### Scenario: WP8 evidence is available
- **WHEN** a valid agreed quality artifact contains training/test folds, in-sample and out-of-sample scores, reliability bins and timing accuracy within ±1 h and ±3 h
- **THEN** the quality panel shows those reported values with their data sources and evaluation-label provenance

#### Scenario: Only the existing backtest artifact is available
- **WHEN** `backtest.json` is valid but `quality.json` or its agreed contract is absent
- **THEN** the UI shows the existing backtest metrics and marks the additional WP8 evidence unavailable without claiming measured calibration or walk-forward validation

### Requirement: Planning priorities select only supported forecast issues
The cockpit SHALL offer ground-operations and forecast-review perspectives using a saved selection from fixed forecast-derived candidates. The selection SHALL NOT modify weather probabilities or use later observed outcomes. Candidate titles, actions, source hours and preparation arithmetic SHALL be deterministic. An API error or refusal SHALL produce a labelled fallback; a single candidate SHALL need no external selection. The viewer SHALL require an exact match to the selected forecast's pre-outcome basis. Historical reviews SHALL be identified as newly generated from saved evidence, and selection confidence SHALL remain distinct from weather probability and measured accuracy.

#### Scenario: Review before preparation
- **WHEN** a model/rule disagreement precedes a predicted direction change
- **THEN** both issues are eligible for selection, and the user can inspect the selected issue's source hour without losing the other forecast events

#### Scenario: Forecast regenerated after review
- **WHEN** forecast values or source metadata no longer match the saved review
- **THEN** the viewer shows the review as unavailable with retry while preserving the forecast

#### Scenario: Conditional preparation time
- **WHEN** a preparation candidate is shown and the user supplies a duration
- **THEN** the viewer subtracts the duration in UTC, displays Berlin time, identifies insufficient lead from issuance and labels the result as a scenario rather than an operational deadline
