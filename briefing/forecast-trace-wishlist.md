# First MVP: forecast evidence and trace wishlist

Review date: 2026-10-30. Implementation claims below are pinned to remote `f8b7ebb47c364b4e1c149600e6ce2472afa4b1e5`, not the older local prototype. This consolidates the two research briefings dated 2026-10-30; proposed fields are requests for review, not implemented interfaces.

## Minimal visual

[Source snapshots](#source-snapshots) -> [Feature computation](#feature-computation) -> [Model + rules](#model--rules) -> [Forecast](#forecast)

Separate branch: [Training runs + held-out references -> Validation](#validation). A forecast links to its later outcome; validation does not feed future observations into that forecast.

For the tower-controller persona, lead with one planning recommendation and an explicitly named score; expand this clickable evidence flow on demand. Until an action policy is supplied, show the forecast and **Recommendation unavailable**, not an invented instruction. Selecting a variant and UTC forecast hour is enough for the first MVP. Nodes open saved values and references; no graph library, tracing service, generated rationale or model retraining is inherently needed.

## Existing implementation versus requested capture

**Implemented at the inspected ref:** [ForecastResponse and QualityResult][types], [feature construction][features], [model inference][predict], [forecast CLI][forecast-code], [training][train] and [quality calculations][quality-code]. Published [latest forecast][latest] has 48 hours, issue `2026-10-30T11:00Z`, and `model_version: walk-forward-v2`. [Backtest][backtest] and [quality JSON][quality] exist; quality contains six monthly OOS folds, May–October 2026. Their existence is not an independent rerun or validation sign-off. Earlier `947ea97` latest used `rules-fallback`; that is not the state at this frozen ref.

**Proposed:** one immutable evidence sidecar per inference, linked to the exact forecast bytes. No existing serving contract retains all source identities, exact feature vectors, model hashes, structured fallback reasons or action-policy evidence below. Older forecasts without capture stay inspectable as outputs, with unavailable evidence nodes. A later replay must be labelled reconstructed, not original instrumentation.

| UI node | Producer fields required for the MVP | Producer owner; storage | Missing behavior |
|---|---|---|---|
| Sources | `source_id`, provider/product, request selection, location, source times, `retrieved_at`, availability basis, values/units, snapshot reference/hash | Data lane + CLI; persist snapshots and emit references | Show missing/unknown time explicitly; no substituted current API response |
| Features | `feature_schema_version`, ordered names/values, units, source-field lineage, missing/imputation flags, `feature_code_revision` | ML inference; persist exact estimator input before it is discarded | “Feature values not captured”; never reconstruct them from a probability |
| Model + rules | Model artifact/hash/version, raw probabilities, blend parameters/final probabilities, rules hash/version, input state, rule results, fallback status/reason | ML + rules + CLI; capture at inference and persist | Name rules fallback or failed target; never call fallback a learned prediction |
| Forecast | Existing `issued_at`, `hours[].time/lead_h`, `p_od25`, `od`, `p_18_usable`, `certainty`, `next_change`, `closures_18`; proposed run/hour references and per-target provenance | CLI emits/persists; UI derives display time and threshold labels only | Missing payload is unavailable; missing evidence does not hide a valid forecast |
| Validation | Evaluation/artifact ID, model/fold references, label provenance, periods, metrics/counts, exclusions, reliability event/scope, training-data references | Jayden/Luca own proof and SPX tracking; training/evaluation producers persist, UI links | “Validation unavailable” or “Compatibility not established”; no invented improvement |
| Recommendation | `policy_id/version`, forecast reference, permitted action, objective/constraints, action score definition, timing/flight-load evidence references | Policy owner to agree; separate proposed artifact | No action, buffer minutes or impacted-flight count without supporting evidence |

### Source snapshots

Use [actual input loading][live] and [training inputs][train] as the source map: IEM EDDF METAR (`data/eddf_metar.parquet`), Open-Meteo previous runs (`data/openmeteo_previous_runs.parquet`), and recorded DFLD stable-hour OD (`data/ground_truth/dfld_hourly.csv`). Live inputs use a retained pre-issue forecast snapshot or the documented single-run fallback. These are code paths, not proof every forecast used every listed source. DWD/TAF are not established inputs to this inspected feature vector.

Required time fields: forecast `issued_at`, hourly `valid_at` UTC, source report/valid time, source initialization/publication time where supplied, and actual `retrieved_at`. Keep `available_at` plus `availability_basis: verified | proxy | unknown` separate. Previous-day offsets and the single-run 12-hour publication buffer are proxies, not exact publication evidence. Historical retrieval after issue is possible; it does not prove historical availability. Persist raw values or a durable retrievable snapshot plus hash: a digest alone cannot recover data. Capture freshness ages; no operational refresh SLA is verified.

Proposed identity convention: unique `run_id` per invocation; `forecast_id = sha256(exact published forecast bytes)` held in the sidecar, avoiding self-hashing; `hour_id = forecast_id + valid_at_utc`; target keys `od25` and `r18_weather_usable`. Give each retained source/artifact an immutable ID, URI and content hash. A small evidence manifest maps forecast digest to sidecar; retain existing `index.json`/`latest.json` selection. `latest` is an alias, never a stable identity. Same issue time can have multiple runs.

### Feature computation

Persist the **actual 25-column vector** in [FEATURES order][features], not the smaller weather subset returned by `predict_48h`. Keep exact numeric precision; serialize missing numeric inputs as null with dtype/missing semantics, never JSON NaN. Preserve raw gust absence before its mean-wind substitution. Shared vectors may be referenced by both targets.

| Actual feature names | Units / calculation to preserve |
|---|---|
| `od_at_issue`, `hours_since_change` | 0/1 for OD25; hours since latest known change's availability time, not necessarily actual event time |
| `obs_wind_kt`, `obs_gust_kt`, `obs_tailwind_25`, `obs_tailwind_18` | Knots from issue-time observations and signed runway components |
| `wind_trend_3h`, `tailwind_trend_3h` | Differences in knots from selected earlier observation; not knots/hour; save both report times |
| `wind_kt`, `gust_kt`, `wind_sin`, `wind_cos` | Forecast knots and unitless direction encodings |
| `tailwind_25_kt`, `tailwind_07_kt`, `tailwind_18_kt` | Signed knots, positive tailwind; retain formula/headings and input references |
| `rule_od25`, `rule_18_usable` | 0/1 rule outputs; these are also model features, not merely an independent parallel display |
| `hour_sin`, `hour_cos`, `season_sin`, `season_cos`, `lead_h` | Unitless Berlin-hour/day-of-year encodings; lead in hours |
| `pressure_msl`, `temperature_2m`, `wind_speed_80m` | Preserve source/normalized units (expected hPa, Celsius, knots); optional missing values remain explicit |

### Model + rules

[Inference][predict] uses two classifiers. OD's published probability blends raw classifier probability with persistence: `p_od25 = alpha * raw_p_od25 + (1-alpha) * od_at_issue`. Capture raw probability, selected lead bucket, alpha, persistence value, final probability and exact model artifact hash. Runway18 uses its classifier probability. Record model/rules/feature-code versions separately; `walk-forward-v2` alone does not distinguish final and monthly fits. Retain training-run link/cutoff and optional dependency-lock reference in the model artifact metadata.

[Rules][rules] require wind inputs, initial OD, pending tailwind timestamp/state, step timestamps, thresholds, result and reason. Current forecast feature construction resets pending hysteresis and applies rules on hourly samples; it does not establish continuous half-hour wind history. Capture that stepping policy honestly. Rules feed model features as well as the comparison display. Fallback uses an explicitly uncalibrated 3-knot logistic scale in [CLI code][forecast-code]; persist its actual formula inputs and reason instead of hiding stderr-only failures.

### Forecast

Keep `p_od25` distinct from `p_18_usable`; label the latter **weather-derived departure usability**, not confirmed operational availability. OD call is 25 at `p_od25 >= .5`; runway18 likely usable at `p_18_usable >= .5`. Preserve `certainty = round(100 * min(abs(2*p_od25-1), abs(2*p_18_usable-1)))`: a margin score, not accuracy or joint calibrated confidence. Display the producer's rounded integer. `next_change.p` means probability of the new OD at that hour, not switch-event probability.

Issue-time `current_od` may be DFLD-recorded or METAR/rule-inferred; neither is automatically a current DFS observation. First forecast row is T+1. Persist provenance independently for issue-time OD and each outcome target; known OD must survive a missing runway18 reference. Status values should distinguish available, partial, unavailable and error; carry freshness, fallback and provenance separately. Null direction is not zero degrees or proof of calm.

The existing next-change window is a neighbouring-hour probability-band heuristic, not a coverage-tested timing interval. A probability/score cannot justify minutes of planning buffer. Proposed timing evidence needs `event_definition`, interval start/end UTC, method/version, nominal coverage if applicable, held-out coverage/counts and lead scope. Proposed buffer policy must cite that evidence plus its operational objective. A closure reaching the last hour needs `end: null`, `right_censored: true` in an agreed extension; current CLI emits a boundary beyond the last closed hour, which must not imply known reopening. Future-day CLI filtering can return fewer than 48 hours despite the current type/spec; owners must reconcile it before claiming strict contract acceptance.

Flight-load evidence is separate: require `kind: observed | forecast | historical | scheduled`, interval, airport/scope, arrival/departure definition, count/units, source/as-of time, coverage and artifact reference. Scheduled demand is not observed movement; historical aggregates are not selected-hour load. [Weather research][weather] and [its findings][weather-findings] are BTS airport/carrier/month delay research, without flight rotations or weather joins. They cannot produce FRA impacted-flight counts or fleet buffers. Responsibility and local flight-feed verification remain with the parent task.

### Validation

Jayden/Luca own training-data proof, runs, OOS holdouts, improvement claims and SPX tracking; this contract requests links, not execution ownership. Persist separate `training_run_id`, `evaluation_id`, model/fold artifact hashes, source manifests, label definitions, evaluation code version, train/test cutoffs, counts/exclusions and tracker URL when supplied. Metrics compare learned model, rules and persistence on the same target/lead/population; calculate improvement only from matched reported metrics and identify its direction/unit. No blanket “beats baseline” claim.

Existing [quality][quality] includes OOS metrics, probability reliability, selected-class confidence reliability and certainty-score reliability. Current probability bins pool leads; do not label them selected-hour calibration. OD event probability bins assess OD25 frequency; correctness bins assess a different event. Reliability evidence is not a fitted calibration transform. If a transform exists, link method/version/fitting data and record pre/post probabilities; otherwise say no calibration transform established. The final fitted model is not literally the monthly held-out model: link evaluation as procedure/fold evidence, not proof that this exact final artifact was tested unseen. [Calibration documentation][calibration] explains why Brier alone does not prove calibration.

**Optional attribution:** only display actually computed per-hour contributions with model/input IDs, target, method/version, baseline/background-data reference, output scale and reconciliation/limits. Otherwise show “Per-hour attribution unavailable.” Existing `drivers` are held-out permutation importance for blended OD performance, not reasons for this hour; correlated inputs complicate interpretation ([primary documentation][importance]). A scalar cannot reconstruct inputs, provenance, transformations or attribution. Captured inputs and snapshots suffice for the core evidence view.

## Illustrative selected-hour projection (not a real run or complete 48-hour payload)

```json
{"schema_version":"forecast-evidence-proposed-v1","illustrative":true,"run_id":"demo-run-1","forecast_id":"demo-forecast-1","issued_at":"2026-10-30T00:00:00Z","hour":{"valid_at":"2026-10-30T06:00:00Z","lead_h":6,"feature_vector_ref":"demo-features-6","source_ids":["demo-metar","demo-nwp","demo-od-history"],"model":{"artifact_id":"demo-model","raw_p_od25":0.6,"alpha":0.5,"persistence_od25":1,"p_od25":0.8,"p_18_usable":0.9,"calibration_transform":null},"rules":{"artifact_id":"demo-rules","rule_od":"25","rule_18_usable":true,"pending_tailwind_since":null,"step_minutes":60},"forecast":{"od":"25","certainty":60},"attribution":{"status":"unavailable","reason":"Not computed"}},"recommendation":{"status":"unavailable","reason":"No agreed action policy or timing evidence","buffer_minutes":null,"impacted_flights":null},"validation":{"status":"unavailable","evaluation_id":null}}
```

The `demo-*` references intentionally identify illustrative placeholders, not retrievable artifacts. Production requires resolving/hashing every reference and capturing all feature values/units above; this projection must not pass a production completeness check. No invented performance, action score or buffer is supplied.

## Five quick challenges / acceptance checks

1. **Can we recover the evidence?** Select a UTC hour; all run/source/model/feature references resolve to retained bytes with matching hashes. Capture unavailable is visible. Duplicate Berlin clock hours stay distinct.
2. **Can we follow the calculation?** Compare captured vector with estimator input; reproduce rules state and raw-to-blended probabilities. Confirm margin score and .5 thresholds, including fallback/missing cases.
3. **Can we defend time and provenance?** Separate issue, valid, retrieved and actual/proxy availability; no future observation enters inference. Recorded OD does not imply observed runway18 or live flight load.
4. **Can we defend the model proof?** Jayden/Luca's linked holdouts identify folds, sources, matched baselines, counts and exclusions; absent evidence stays unavailable. Pooled reliability and global importance are not per-hour explanations.
5. **Can we defend the recommendation?** It cites a versioned action policy; any minutes/counts cite appropriate timing/load evidence. With those absent, show unknown, not a suggested buffer or impact count.

## Team review: what is useful / challenging?

Please comment on this file or its PR: **useful field/node; hard-to-capture field and why; smallest acceptable substitute; owner; linked artifact/SPX item; acceptance evidence**. Proposed defaults above are reviewable, not agreed operational policy. Priority: exact input/output capture and identities first, validation links second, action-policy/timing evidence before numerical recommendations; attribution last.

**Research reconciliation:** both briefings agree on retained evidence and optional attribution. Their older-checkout absence claims do not describe current main; the evidence briefing subsequently qualified its scope. Their sketches omit the current OD blend and rules-as-features dependency. Per-hour validation and pooled model evaluation need different joins. One briefing's “do not derive calibration bins from certainty” means not from the score alone: paired score/outcome bins already exist and may be shown without calling the score a probability. Evaluation availability is not a prerequisite to showing a captured forecast.

**Ran and saw:** read both completed research files, contracts/briefs and pinned implementation/artifacts via GitHub; used existing MCP graph for discovery and checked newer source directly; verified the requested session model in Herdr. **Inferred:** the proposed sidecar/IDs and policy separation are the smallest sufficient capture design, not implemented interfaces. **Not verified:** independent training/inference reruns, reported metric correctness, original source publication times, live DFS responsibility/feeds, per-hour attribution, calibrated timing intervals, flight impacts or policy utility. No runtime tests, installs or validation execution were performed for this documentation handoff.

[types]: https://github.com/werister/aiw-codex-hack/blob/f8b7ebb47c364b4e1c149600e6ce2472afa4b1e5/web/src/lib/forecast-types.ts
[features]: https://github.com/werister/aiw-codex-hack/blob/f8b7ebb47c364b4e1c149600e6ce2472afa4b1e5/ml/features.py
[predict]: https://github.com/werister/aiw-codex-hack/blob/f8b7ebb47c364b4e1c149600e6ce2472afa4b1e5/ml/predict.py
[forecast-code]: https://github.com/werister/aiw-codex-hack/blob/f8b7ebb47c364b4e1c149600e6ce2472afa4b1e5/ml/forecast.py
[train]: https://github.com/werister/aiw-codex-hack/blob/f8b7ebb47c364b4e1c149600e6ce2472afa4b1e5/ml/train.py
[quality-code]: https://github.com/werister/aiw-codex-hack/blob/f8b7ebb47c364b4e1c149600e6ce2472afa4b1e5/ml/quality.py
[live]: https://github.com/werister/aiw-codex-hack/blob/f8b7ebb47c364b4e1c149600e6ce2472afa4b1e5/ml/live.py
[rules]: https://github.com/werister/aiw-codex-hack/blob/f8b7ebb47c364b4e1c149600e6ce2472afa4b1e5/ml/rules.py
[latest]: https://github.com/werister/aiw-codex-hack/blob/f8b7ebb47c364b4e1c149600e6ce2472afa4b1e5/web/public/forecasts/latest.json
[backtest]: https://github.com/werister/aiw-codex-hack/blob/f8b7ebb47c364b4e1c149600e6ce2472afa4b1e5/web/public/data/backtest.json
[quality]: https://github.com/werister/aiw-codex-hack/blob/f8b7ebb47c364b4e1c149600e6ce2472afa4b1e5/web/public/data/quality.json
[weather]: https://github.com/werister/aiw-codex-hack/blob/f8b7ebb47c364b4e1c149600e6ce2472afa4b1e5/weather%20database/README.md
[weather-findings]: https://github.com/werister/aiw-codex-hack/blob/f8b7ebb47c364b4e1c149600e6ce2472afa4b1e5/weather%20database/TOP_ERKENNTNISSE.md
[calibration]: https://scikit-learn.org/stable/modules/calibration.html
[importance]: https://scikit-learn.org/stable/modules/permutation_importance.html
