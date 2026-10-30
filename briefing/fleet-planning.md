# Fleet-wide planning: product direction and team handoff

Recorded 30 October 2026 from the product discussion. Status: agreed direction; implementation, action thresholds and operational buffer policy still need specification. This note extends the product vision without replacing the FraAlliance forecast deliverables.

## Outcome and primary user

Help the tower controller / responsible shift supervisor anticipate airport-wide operating changes and prepare across arrivals and departures. Show one recommended planning response with its forecast, time window and uncertainty first; allow the user to expand a visual evidence panel. The controller retains the operational decision. Airport operations partners can use the same forecast to coordinate preparation.

The existing model predicts airport-wide OD 25/07 and runway-18 usability for each of the next 48 hours. It is not a single-aircraft prediction model. A single-flight example can explain the demo, but the full product must show how a shared runway constraint relates to traffic demand and potential downstream disruption.

Fraport assigns operating-direction decisions to DFS and identifies the responsible shift supervisor as considering upper winds and weather forecasts. Frankfurt A-CDM coordinates ATC, airport operators, airlines and handlers around shared operational information. These establish the context; they do not establish that this prototype is an operational controller system. Sources checked 2026-10-30: [Fraport operating direction](https://www.fraport.com/de/nachhaltigkeit/nachbarschaftsdialog/laerm-und-luft/flugbetrieb/betriebsrichtung.html), [Frankfurt A-CDM](https://cdm.frankfurt-airport.com/content/fraport-company-cdm/en/local-a-cdm-procedure.html).

## Three connected layers

1. **Forecast:** OD probabilities, runway-18 usability, likely change/closure periods, issue time and uncertainty. Keep the existing model and rules/persistence comparisons central.
2. **Planning recommendation:** a versioned policy turns forecasts into a suggested preparation or review action. Predicting that OD 07 will occur is not, by itself, evidence that switching at a particular time is the best action. Recommendation thresholds, disagreement behavior and preparation lead time must be explicit.
3. **Traffic exposure and impact:** align the forecast window with arrival/departure demand. First show flights scheduled or observed within the window, clearly distinguished. Estimating queues, delay minutes, capacity loss or onward effects additionally requires capacity/turnaround/rotation data and a validated impact method. A flight in the window is exposed, not necessarily delayed.

Here, fleet-wide means airport traffic across flights. Airline aircraft rotations and passenger connections are a further layer and require explicit links; they cannot be reconstructed from aggregate arrival counts.

## What the screen should communicate

- Start with the planning recommendation, affected runway/direction, relevant period, issue time and uncertainty flag. Keep the operating state now distinct from the selected future hour.
- Show arrival and departure demand beside change/closure windows when supported by data. Missing demand must say unavailable, not zero. Scenario traffic must be visibly illustrative.
- Make uncertainty useful: show a defensible timing window and the need for review/preparation. A probability or certainty score cannot be converted directly into minutes of buffer. Until a buffer policy is defined, do not invent a precise recommended buffer.
- Expand into **Sources → Features → Model + rules → Forecast → Planning response**. Selecting a node reveals the captured values, versions and status. Link traffic exposure to its separate flight-demand snapshot. Keep held-out validation as separate evidence about model reliability.
- Use one identifiable model artifact/run for the displayed recommendation. Model comparisons and training history belong in the evidence/validation view; they must not silently change the active prediction.

## Minimum producer data needed

| Producer | Emit or retain | Enables |
|---|---|---|
| Forecast/inference | Stable forecast/run ID; issue and valid timestamps in UTC; model artifact/version; rules and feature-transform versions; actual input values and source snapshots; per-target probabilities/calls; missing/fallback status | Reconstructable evidence for the selected hour |
| Recommendation policy | Policy version; linked forecast ID; action and reason codes; affected interval; review status; any buffer and its documented derivation | One auditable planning response, separate from a prediction |
| Flight-demand feed | Snapshot/as-of time; flight/movement ID; airport; arrival/departure; planned/estimated/actual event time and event type; status; runway assignment if known | Demand by interval and traceable exposed-flight lists |
| Impact method, when available | Version; capacity assumptions; scenario; demand/forecast references; estimated effect and uncertainty | Defensible impact estimates instead of invented delay totals |
| Rotation/connection feed, when available | Aircraft rotation or explicit predecessor/successor links; turnaround constraints; connection data where claimed | Downstream effects across flights |
| Training/evaluation | Model artifact join key; training data/version and cutoff; held-out periods/folds; target/lead/sample counts; model, rules and persistence metrics; calibration and change-event evidence | Proof that corresponds to the model actually displayed |

These are proposed integration requirements, not a new implemented API. Capture evidence when inference runs and retain resolvable snapshots: one output score cannot reconstruct the inputs, transformations, source history or feature contributions afterward. Showing recorded inputs does not require a generated explanation or retraining. Per-instance attribution is optional and must be computed by an identified method before it is displayed.

## What the available flight research supports

Checked remote main at `f8b7ebb47c364b4e1c149600e6ce2472afa4b1e5` and Luca's weather branch at `2ea41dfa6bd0c0b598dbafb2565ef4d3a08f0f16`; the weather-database files match. The BTS CSV contains 22,687 airport/carrier/month records for 2025, across 364 airports and 21 carriers, with no FRA/EDDF rows. It contains aggregate arrival counts and delay causes, not individual flight timestamps, aircraft rotations, runway assignments or future Frankfurt schedules.

That research supports the business motivation: disruption can propagate from previous flights. It cannot supply Frankfurt hourly traffic demand, exposed-flight counts or operational buffers. EDDF weather data and recorded operating-direction history support the runway forecast but do not fill this flight-demand gap. Sources: [weather research scope](https://github.com/werister/aiw-codex-hack/blob/f8b7ebb47c364b4e1c149600e6ce2472afa4b1e5/weather%20database/README.md), [research findings and limitations](https://github.com/werister/aiw-codex-hack/blob/f8b7ebb47c364b4e1c149600e6ce2472afa4b1e5/weather%20database/TOP_ERKENNTNISSE.md), [BTS source CSV](https://github.com/werister/aiw-codex-hack/blob/f8b7ebb47c364b4e1c149600e6ce2472afa4b1e5/weather%20database/bts/raw2025/Airline_Delay_Cause.csv), [EDDF data inventory](https://github.com/werister/aiw-codex-hack/blob/f8b7ebb47c364b4e1c149600e6ce2472afa4b1e5/data/README.md).

## Team handoff and demonstration

- **ML/inference:** preserve the core forecast targets; retain evidence and artifact identities needed by the UI. Evaluate any added impact model separately from runway prediction.
- **Jayden / frontend:** recommendation first, demand/exposure where available, visual evidence on expansion, explicit uncertainty and unavailable states.
- **Jayden and Luca / validation story:** connect the displayed artifact to training data, model improvements, run history and out-of-sample results. Keep this work with its existing owners. Historical hindcasts must use information available at issue time; forward walk-forward testing is distinct from a retrospective descriptive analysis.
- **Hugo / demo:** show an upcoming change or restriction, its planning implication and uncertainty, then open the evidence and held-out model results. Separate the implemented forecast from illustrative fleet scenarios and future impact features.

Before calling the fleet layer implemented, demonstrate one forecast linked to a real demand snapshot, a reproducible exposed-flight count, an explicit recommendation policy, and visible behavior when evidence is missing. To claim delay savings or buffer quality, add a defined impact evaluation; overall runway-classification accuracy alone does not prove those benefits.
