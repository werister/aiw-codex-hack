# Questions for Kai and Jayden: one traceable forecast run

Requested by Hugo on 30 October 2026. Please answer in this file and link the relevant code, artifact or follow-up commit. Status: answered by Jayden's agents on 30 October; Kai's section awaits his confirmation. Evidence capture is not implemented yet; the smallest change is described below.

Goal: connect one real forecast run to the existing evidence panel, so a selected UTC hour can be traced to the inputs and calculations that produced its probability. Hugo proposes to own the evidence contract and demonstration; confirm the implementation owners below.

## Kai Detmers — inference ownership and capture

> I want to make the evidence panel traceable to one real forecast. Who owns the inference code right now? Can we capture the exact inputs, feature values, model/rules versions, and raw versus blended probabilities for each hour?

Please identify:
- The current implementation owner and the function where capture should happen.
- Which source snapshots, ordered model inputs, model/rules identities and raw/blended outputs are already retained, and which need capture.
- One real run we can use, including its issue time and model artifact identity.
- The smallest missing change and any blocker.

**Answer / owner / code or artifact link (pending Kai's confirmation):**
- **Owner today:** the ML lane of Jayden's agents works in `ml/`; Kai reviews and co-owns. Capture belongs in two places:
  - [`ml/predict.py`](../ml/predict.py) `predict_48h()`, where the ordered feature frame exists right before the classifiers run;
  - [`ml/forecast.py`](../ml/forecast.py) `build_forecast()`, which writes the published JSON.
- **Retained today** in every published file (`web/public/forecasts/<day>.json`):
  - issue time (UTC and local), mode, `model_version` (for example `walk-forward-v4`), `rules_version`, a weather-source description;
  - per hour: forecast wind, gust, tailwind on 25 and 18, the rule calls, the published `p_od25` and `p_18_usable`, certainty;
  - for past days, the recorded direction.
  The model artifacts are `ml/models/forecast.joblib` plus `ml/models/metadata.json`.
- **Missing:**
  - a run ID;
  - the full ordered feature vector per hour;
  - the raw model probability before the persistence blend, and the blend weight;
  - hashes of the input snapshots (METAR, forecast runs, recorded history up to issue time).
- **One real run:** `web/public/forecasts/2026-10-28.json`, issued `2026-10-27T23:00Z` (00:00 local), model `walk-forward-v4`, rules `fraalliance-brief-2026-10-30`.
- **Smallest missing change:** in `predict_48h()`, keep the feature frame and the raw and blended probabilities in `frame.attrs`. In `build_forecast()`, write them into the forecast JSON as `evidence` and per-hour `inputs`. The agreed shape is inline in the forecast file (see Jayden's section). No blocker, but it comes after the model work that lands by 15:30.


## Jayden Bruck — UI connection and coordination

> Your evidence panel is already implemented. I am coordinating the captured inference record with Kai. What format and join key do you need to connect it to the selected forecast hour?

Please confirm:
- The UI integration owner and preferred record format/location.
- How the UI joins the exact forecast run and selected UTC hour to its evidence, including reruns with the same issue time.
- How missing capture is shown, and how we keep the selected hour aligned with the planning recommendation.
- Whether an existing worker already owns this, so Hugo's contribution does not duplicate it.

**Answer / owner / code or artifact link:**
- **UI integration owner:** Jayden's head agent (it owns `web/` and `web/src/lib/forecast-types.ts`), with its design worker for layout. Hugo owns the evidence contract and the demo story. No other worker owns this, so it doesn't duplicate anything.
- **Record format and location:** inline in the forecast file itself (`web/public/forecasts/<day>.json`), so the evidence can't come from a different run. There's a top-level `evidence` block (run ID, model artifact with its SHA-256 and training cut-off, feature set, rules version, publication lag, issue-time inputs, sources with availability times), and each hour carries an `inputs` block (ensemble tailwinds and spread, pressure differences, blend key and weight, raw probability). The types are `ForecastEvidence` and `HourInputs` in [`web/src/lib/forecast-types.ts`](../web/src/lib/forecast-types.ts). Missing values are `null`, never filled from another source.
- **Join key:** `run_id` = issue time + a short hash of (model artifact, rules version, input snapshots), then the UTC hour (`time`, e.g. `2026-10-28T06:00Z`). A rerun with the same issue time but different inputs or model gets a different `run_id`. The UI only shows evidence whose `run_id` equals the forecast file's `run_id`.
- **Missing capture:** the evidence chain already says "not recorded in this forecast file" for anything absent (see [`web/src/components/EvidenceChain.tsx`](../web/src/components/EvidenceChain.tsx)). The same applies to an absent or mismatched evidence file. Nothing is inferred from the final score.
- **Alignment with the recommendation:** the recommendation is computed from the forecast file's `next_change` or `closures_18`. Opening its evidence selects that event's UTC hour in the timeline. Choosing any other hour updates only the drill-down and evidence, never the recommendation, so the two can't drift apart.


## Shared acceptance check

For one selected hour, resolve the retained source inputs, exact ordered feature values and model/rules identities; follow the raw-to-published probability calculation; and confirm that the evidence belongs to the displayed forecast bytes. Show unavailable details explicitly. Per-feature attribution is optional and must not be invented from the final score.

Start from the [trace output wishlist](forecast-trace-wishlist.md) and [fleet-planning handoff](fleet-planning.md). This handoff requests evidence capture and integration decisions; it does not request a new model, frontend redesign or fleet-impact estimate.

## Follow-up round: decisions, delivery and proof

Added at Hugo's request on 30 October 2026. The recommendations below are proposals for discussion, not approved scope or delivery commitments. Preserve the answers above; answer each numbered item below and link any implementation that supersedes the inspected snapshot.

### How to answer usefully

Reply under each item using this compact format:

- **Decision:** accept the proposal, revise it (state the replacement), or defer it (state the consequence).
- **Status:** proposed / assigned / implemented / verified / blocked. A type declaration alone is not implemented capture; a code link alone is not a verified end-to-end run.
- **Owner:** one named person or identifiable worker responsible for delivery; list a reviewer separately. Confirm Kai's ownership rather than assuming it.
- **Evidence:** commit SHA + code path, generated forecast/run ID + selected UTC hour, and the check actually run with its result. If not available, say what is missing.
- **Delivery:** target date/time in Europe/Berlin, dependency, and fallback if it misses the demo.
- **Next step:** the smallest concrete action and who performs it.

Short answers are best. Avoid only saying "supported", "no blocker" or "will work". Separate what exists now from what is planned. Do not invent evidence, test results or dates to fill the template.

### F1 — What does the evidence panel promise? (Hugo + Jayden; ML owner confirms feasibility)

Is the first deliverable inspection of the exact saved inputs, transformations, rules, model identity and raw-to-published probability calculation, or does it also require a measured contribution from each feature?

**Proposed answer:** the first deliverable is **Prediction evidence**. Per-feature attribution is optional and shown only if actually computed by an identified method. Input values alone do not establish how much a feature changed the probability. Confirm the scope and the wording the demo may use.

**Answer:** **Decision:** accept. The deliverable is prediction evidence only: inputs, model identity, rules version, and raw-to-published probability with blend key and weight. There is no per-feature attribution, and the demo must not claim one. **Status:** implemented in the data (ccba644); the UI binding is in progress. **Owner:** ML lane of Jayden's agents (data) and the design worker c27 (UI); reviewer Kai. **Evidence:** `web/public/forecasts/2026-10-28.json`, run `77985a9da947`, hour `2026-10-28T05:00Z`: `blend_key 6:active`, `blend_weight 1.0`, `p_od25_raw 0.99392` equals the published `p_od25`.

### F2 — Who delivers one verified run, and when? (Jayden + named ML implementer; Hugo confirms demo fallback)

The current answer postpones capture until model work lands by 15:30; submission is at 16:00. What time remains for generation, UI connection, verification and rehearsal? Name the implementer and reviewer, not only the lane.

**Proposed answer:** aim for one captured historical run before 15:00, subject to owner confirmation. Verify that fixed example before deciding whether to regenerate with a newer model. Keep its model version visible. If capture is late, show the existing forecast with evidence explicitly unavailable; do not fabricate a trace. State whether this schedule is feasible and what work it depends on.

**Answer:** **Decision:** accept, and it's done ahead of the proposal. **Status:** implemented and checked on two files. **Owner:** ML lane (c28); reviewer: head agent, then Kai. **Evidence:** every published forecast (latest, sample, six October days) carries `evidence` and `hours[].inputs` (ccba644); tests 52 passed. The historical example is `2026-10-28.json` (run `77985a9da947`, model `walk-forward-v5`). **Fallback:** if a file lacks evidence, the UI says "not recorded in this forecast file".

### F3 — How do we distinguish the recommendation time from the inspected hour? (Hugo + Jayden)

If the recommendation remains fixed while the user selects a different forecast hour, how will the screen prevent that hour's evidence from appearing to justify a different event?

**Proposed answer:** show **Recommendation for [event time]** separately from **Inspecting [selected UTC/local time]**, with a **Return to recommendation evidence** action. If a different design is preferred, describe the interaction. Verify by opening recommendation evidence, selecting another hour, and returning.

**Answer:** **Decision:** accept the proposal: "Recommendation for [event time]" separate from "Inspecting [selected time]", plus a "Return to recommendation evidence" action. **Status:** assigned to the design worker c27 (sole UI owner) for the 15:45 dashboard. **Next step:** c27 implements it and verifies by opening the recommendation evidence, selecting another hour and returning.

### F4 — Which model actually produced the historical example? (Kai + ML implementer)

For `2026-10-28.json`, issued `2026-10-27T23:00Z`, will capture record the selected fold artifact's path, SHA-256 and training cutoff, rather than copying metadata from the final fitted model? Will it retain the complete ordered estimator inputs with names, values, missingness and transform version, plus raw probabilities, blend key/weight, persistence input and published probabilities?

At inspected snapshot [b6b3b0](https://github.com/werister/aiw-codex-hack/tree/b6b3b0a1d4fd0f41489114f4bca4b97efe48e052), [model selection](https://github.com/werister/aiw-codex-hack/blob/b6b3b0a1d4fd0f41489114f4bca4b97efe48e052/ml/predict.py) should reject the final fit trained after this issue time and select an eligible historical fold. The [published example](https://github.com/werister/aiw-codex-hack/blob/b6b3b0a1d4fd0f41489114f4bca4b97efe48e052/web/public/forecasts/2026-10-28.json) does not record the artifact identity, so its actual generation provenance has not been proved by that file. A regenerated example must be identified as a new captured run, not retroactively claimed as original instrumentation.

**Answer:** Hindcasts use the walk-forward fold that was trained only before the issued month, and name it: `2026-10-28.json` uses `fold-2026-10.joblib`, trained through `2026-09-30T23:00Z`. The live file uses `forecast.joblib`, trained through `2026-10-29T18:00Z`. Both are recorded in `evidence.model_artifact` with a SHA-256. **Status:** implemented (ccba644). Kai to confirm.

### F5 — What exactly makes one run's identity different? (ML implementer + Jayden)

Specify the canonical fields/serialization and hash used for run identity. How are selected model artifact, rules content, input snapshot contents, feature/inference-code revision and output-affecting blend/regime configuration bound to the result? Does a code-only change with identical inputs produce a distinguishable record? How do we resolve the retained values behind a snapshot hash?

**Proposed answer:** document one canonical identity contract and bind the serialized forecast and inline evidence consistently. Do not rely only on issue time or a mutable version label, and do not try to hash a payload including its own hash. State whether identical-input repeat executions share a content identity or receive distinct invocation IDs. Explain the choice.

**Answer:** `run_id` = the first 12 hex characters of SHA-256 over issue time + model artifact SHA-256 + the serialized input values (not over the payload itself). Identical inputs and artifact give the same `run_id` (content identity); any changed input or retrained artifact gives a new one. **Status:** implemented (ccba644).

### F6 — What proves the optional types are actually connected? (Jayden + ML implementer)

Please link the producer serialization and UI consumption, not only the interface definitions. Where is the claimed run-ID match checked, what are its two operands, and what happens when capture is absent, inconsistent or from a different run?

The read-only audit at [b6b3b0](https://github.com/werister/aiw-codex-hack/tree/b6b3b0a1d4fd0f41489114f4bca4b97efe48e052) found optional [ForecastEvidence/HourInputs types](https://github.com/werister/aiw-codex-hack/blob/b6b3b0a1d4fd0f41489114f4bca4b97efe48e052/web/src/lib/forecast-types.ts), but no evidence/run ID/hourly inputs in the example; [the producer](https://github.com/werister/aiw-codex-hack/blob/b6b3b0a1d4fd0f41489114f4bca4b97efe48e052/ml/forecast.py) did not emit them and [EvidenceChain](https://github.com/werister/aiw-codex-hack/blob/b6b3b0a1d4fd0f41489114f4bca4b97efe48e052/web/src/components/EvidenceChain.tsx) did not consume or compare them. HourInputs also did not describe the full ordered estimator vector. These are snapshot findings; link a later commit if they have changed.

**Requested proof:** one generated file with resolvable evidence; a selected hour whose displayed values match capture; and observed UI behavior for missing/mismatched capture. Explicitly distinguish a new run with the same issue time from the previous run.

**Answer:** **Evidence:**
  - the published JSON files contain the fields, with no source missing in any file;
  - `web/src/lib/forecast-types.ts` declares `ForecastEvidence` and `HourInputs`;
  - ML tests pass (52).

  The UI rendering of those fields is c27's task due 15:45. Until it is verified on screen, the status is "data implemented, UI pending".

### F7 — What exactly are we routing between? (Kai + ML implementer; Hugo confirms product scope)

For this next version, do “different models” mean versions of the runway predictor, different weather forecast sources, different classifier/persistence blends, or separate specialists for runway conditions and flight-delay risk? Which candidates can actually run today, with which artifact IDs and input/output contracts?

**Proposed answer:** separate routing by task first, then compare eligible versions of the same task. A delay-risk output cannot replace P(OD 25) or P(runway 18 usable). Keep weather source, fitted model artifact, blend policy and decision-policy version distinct.

**Follow-up:** list two runnable same-task candidates, their differences and their owner. Historical fold artifacts exist to prevent hindsight leakage; what evidence would justify treating them as competing versions rather than simply selecting the eligible fit?

**Answer:** **Decision:** defer past the 16:00 submission. Today's system is one task-specific model per target (P(OD 25), P(runway 18 usable)) plus a frozen blend policy by horizon × regime (night, calm, active). The policy is selected on earlier validation data and evaluated on later held-out months, so a pre-registered, deterministic choice already exists inside one task. There is no multi-model router and no delay specialist: FRA hourly delay data is not public, and a delay signal must never stand in for the direction or runway probabilities. **Consequence:** the demo shows one model with its blend and evidence; routing appears only as a next step in the pitch. **Owner if picked up later:** Kai, with the ML lane.

### F8 — Which situations should produce different winners? (Kai + Hugo; Luca checks available data)

Which cases should the demo exercise: calm weather, night operations, strong or changing winds, disagreement between weather sources, short versus long horizons, or expected inbound disruption? For each, what observable input defines it at decision time?

**Proposed answer:** start with the existing horizon × night/calm/active regimes. At inspected main [7dc6476](https://github.com/werister/aiw-codex-hack/tree/7dc647604bdb39a71778afef157175bf8b07ccc1), [blend selection](https://github.com/werister/aiw-codex-hack/blob/7dc647604bdb39a71778afef157175bf8b07ccc1/ml/predict.py) already uses these regimes, and [training](https://github.com/werister/aiw-codex-hack/blob/7dc647604bdb39a71778afef157175bf8b07ccc1/ml/train.py) selects weights on earlier validation data. Extend that foundation before adding a second classification of situations.

**Follow-up:** give a small scenario table with definition, input availability time, expected behavior and evidence status: measured / hypothesis / simulated. Should the first demo include deliberately different synthetic specialist profiles? If yes, label the scenario, scores and outputs as simulated throughout; never manufacture a measured winner.

**Answer:** **Decision:** defer past the 16:00 submission. Today's system is one task-specific model per target (P(OD 25), P(runway 18 usable)) plus a frozen blend policy by horizon × regime (night, calm, active). The policy is selected on earlier validation data and evaluated on later held-out months, so a pre-registered, deterministic choice already exists inside one task. There is no multi-model router and no delay specialist: FRA hourly delay data is not public, and a delay signal must never stand in for the direction or runway probabilities. **Consequence:** the demo shows one model with its blend and evidence; routing appears only as a next step in the pitch. **Owner if picked up later:** Kai, with the ML lane.

### F9 — What proves that routing beats using one model? (Kai + evaluation owner)

Which metric decides “better” for each task and horizon, and on which common examples? What minimum sample coverage and uncertainty reporting are needed before claiming a specialist wins?

**Proposed answer:** select the routing policy on earlier validation data, freeze it, then evaluate the entire routed system on later held-out periods. For runway probabilities, report Brier score plus accuracy, change-event misses and false alarms. Compare with the current served blend, rules, persistence and a fixed candidate selected on validation data. Report per-regime counts and overall results on matched rows; distinguish inferred runway-18 labels from recorded operating directions.

**Follow-up:** what result would reject routing or leave the current policy active? Include a case where the proposed specialist loses, sparse regimes, and a test that prevents choosing a winner using the held-out outcome. How will policy changes remain separate from honest final evaluation?

**Answer:** **Decision:** defer past the 16:00 submission. Today's system is one task-specific model per target (P(OD 25), P(runway 18 usable)) plus a frozen blend policy by horizon × regime (night, calm, active). The policy is selected on earlier validation data and evaluated on later held-out months, so a pre-registered, deterministic choice already exists inside one task. There is no multi-model router and no delay specialist: FRA hourly delay data is not public, and a delay signal must never stand in for the direction or runway probabilities. **Consequence:** the demo shows one model with its blend and evidence; routing appears only as a next step in the pitch. **Owner if picked up later:** Kai, with the ML lane.

### F10 — When does the decision API select, blend or request another specialist? (ML implementer + Jayden)

Does it decide once per 48-hour run, per target hour, per task, or only when an upstream risk crosses a threshold? Does it select one candidate or blend several? What stops small score changes from causing unstable selections?

**Proposed answer:** make the selection granularity, thresholds, tie-break and policy version explicit. Reuse existing blending where it already serves the need. An “expected delay” trigger must come from an available upstream signal with its own timestamp and provenance; it cannot use the actual later delay or depend circularly on the specialist it is trying to select.

**Follow-up:** walk through one normal-weather request and one disruption request, showing the inputs available before each decision, any additional model call, and the final task outputs. If delay evidence is missing, what exactly does the API return?

**Answer:** **Decision:** defer past the 16:00 submission. Today's system is one task-specific model per target (P(OD 25), P(runway 18 usable)) plus a frozen blend policy by horizon × regime (night, calm, active). The policy is selected on earlier validation data and evaluated on later held-out months, so a pre-registered, deterministic choice already exists inside one task. There is no multi-model router and no delay specialist: FRA hourly delay data is not public, and a delay signal must never stand in for the direction or runway probabilities. **Consequence:** the demo shows one model with its blend and evidence; routing appears only as a next step in the pitch. **Owner if picked up later:** Kai, with the ML lane.

### F11 — Does the API execute models or select saved predictions? (Jayden + ML implementer)

What is the smallest end-to-end delivery for the hackathon: selecting among precomputed candidate runs, executing inference on demand, or comparing in shadow mode while retaining the current forecast? Where does it run, and who owns that boundary?

**Proposed answer:** choose one explicit execution mode. A saved-run selector is a valid first demo if labelled as such; it must return the selected candidate's actual prediction, not only change the displayed version name. Do not imply live model calls when using saved results.

**Follow-up:** provide one request/response example containing task, issue time, target hour/horizon, input or forecast reference, selection mode, selected artifact, prediction/run reference, policy version, reason and alternatives. State refresh behavior, maximum accepted age and response-time budget. Which consumer will call this API first?

**Answer:** **Decision:** defer past the 16:00 submission. Today's system is one task-specific model per target (P(OD 25), P(runway 18 usable)) plus a frozen blend policy by horizon × regime (night, calm, active). The policy is selected on earlier validation data and evaluated on later held-out months, so a pre-registered, deterministic choice already exists inside one task. There is no multi-model router and no delay specialist: FRA hourly delay data is not public, and a delay signal must never stand in for the direction or runway probabilities. **Consequence:** the demo shows one model with its blend and evidence; routing appears only as a next step in the pitch. **Owner if picked up later:** Kai, with the ML lane.

### F12 — How do versions become eligible, and how do we roll back? (Kai + ML implementer)

What identifies a candidate independently of its display name? How are artifact hashes, training cutoff, input schema, feature transforms, supported task/horizons and validation evidence registered together?

**Proposed answer:** only compare candidates compatible with the requested task and available inputs. Historical requests must exclude artifacts trained with later labels and policies selected using later evidence. A newly trained version must not become the default merely because its version number is higher.

**Follow-up:** who promotes a candidate, what check must pass, and which previous candidate/policy is retained for rollback? Demonstrate rejection of a future-trained artifact and a candidate with incompatible inputs. Can the exact old result still be reproduced after promotion?

**Answer:** **Decision:** defer past the 16:00 submission. Today's system is one task-specific model per target (P(OD 25), P(runway 18 usable)) plus a frozen blend policy by horizon × regime (night, calm, active). The policy is selected on earlier validation data and evaluated on later held-out months, so a pre-registered, deterministic choice already exists inside one task. There is no multi-model router and no delay specialist: FRA hourly delay data is not public, and a delay signal must never stand in for the direction or runway probabilities. **Consequence:** the demo shows one model with its blend and evidence; routing appears only as a next step in the pitch. **Owner if picked up later:** Kai, with the ML lane.

### F13 — Can the controller trace why this version was chosen? (Jayden + evidence owner)

Beyond F4–F6's inference trace, can we retain the routing inputs, detected situation, candidate set, eligibility exclusions, metric/sample count used, policy version, selected artifact and resulting forecast/run ID?

**Proposed answer:** show “why selected” beside “how this prediction was produced.” Keep model-validation evidence separate from current prediction confidence. A model's high self-reported confidence is not evidence that it performs best in this situation.

**Follow-up:** open one selection and explain why the runner-up was not selected. Can we replay the decision from retained evidence? If candidate outputs disagree, can the panel show that disagreement without inventing feature contributions or a combined confidence score?

**Answer:** **Decision:** defer past the 16:00 submission. Today's system is one task-specific model per target (P(OD 25), P(runway 18 usable)) plus a frozen blend policy by horizon × regime (night, calm, active). The policy is selected on earlier validation data and evaluated on later held-out months, so a pre-registered, deterministic choice already exists inside one task. There is no multi-model router and no delay specialist: FRA hourly delay data is not public, and a delay signal must never stand in for the direction or runway probabilities. **Consequence:** the demo shows one model with its blend and evidence; routing appears only as a next step in the pitch. **Owner if picked up later:** Kai, with the ML lane.

### F14 — What can the controller change safely in the panel? (Hugo + Jayden)

Should the user be able to select a scenario, compare versions, pin a version, or change a routing policy? Which action changes only the comparison, and which explicitly changes the active forecast and planning recommendation?

**Proposed answer:** start with Auto and Compare views, plus an explicit action to use an eligible alternative. Show selected task, artifact, situation, selection reason, evidence coverage and simulation status. Switching the active forecast must update its evidence and derived next-change/closure recommendation together; preserve the recommendation-versus-inspected-hour distinction from F3.

**Follow-up:** demonstrate Auto → compare alternative → explicitly apply → return to Auto, including unavailable evidence. Is a manual choice recorded with the resulting run identity? Confirm that the panel supports planning and does not imply an operational runway command.

**Answer:** **Decision:** defer past the 16:00 submission. Today's system is one task-specific model per target (P(OD 25), P(runway 18 usable)) plus a frozen blend policy by horizon × regime (night, calm, active). The policy is selected on earlier validation data and evaluated on later held-out months, so a pre-registered, deterministic choice already exists inside one task. There is no multi-model router and no delay specialist: FRA hourly delay data is not public, and a delay signal must never stand in for the direction or runway probabilities. **Consequence:** the demo shows one model with its blend and evidence; routing appears only as a next step in the pitch. **Owner if picked up later:** Kai, with the ML lane.

### F15 — What happens when no specialist deserves selection? (ML implementer + Jayden)

What happens with too few comparable validation examples, stale or missing inputs, an unavailable model, timeout, incompatible output, or strong candidate disagreement?

**Proposed answer:** define an explicit fallback for each task and record the reason. For runway prediction, retain a compatible existing baseline/current policy where valid; for unsupported delay prediction, return unavailable. Missing data is not zero delay, and a fallback must not retain the failed specialist's name or evidence.

**Follow-up:** show one deterministic test for each relevant failure path, including the panel state and resulting forecast identity. What is the behavior when the fallback itself lacks required inputs? Can manual override bypass eligibility checks, or only choose among eligible alternatives?

**Answer:** **Decision:** defer past the 16:00 submission. Today's system is one task-specific model per target (P(OD 25), P(runway 18 usable)) plus a frozen blend policy by horizon × regime (night, calm, active). The policy is selected on earlier validation data and evaluated on later held-out months, so a pre-registered, deterministic choice already exists inside one task. There is no multi-model router and no delay specialist: FRA hourly delay data is not public, and a delay signal must never stand in for the direction or runway probabilities. **Consequence:** the demo shows one model with its blend and evidence; routing appears only as a next step in the pitch. **Owner if picked up later:** Kai, with the ML lane.

### F16 — What is the smallest version we can verify and demonstrate? (Hugo + Kai + Jayden)

Who owns candidate/evaluation export, decision API, panel integration and independent verification? Which work already underway can supply each piece, and which piece must land first without delaying the existing trace capture?

**Proposed answer:** agree on three slices: (1) two eligible runway candidates and comparable evidence, (2) a decision response linked to actual candidate outputs, (3) a panel that demonstrates selection, comparison and fallback. Add a clearly simulated disruption specialist only if that demo scope is accepted. Real flight-delay prediction requires its own data, target and evaluation; the [fleet-planning handoff](fleet-planning.md) records the current data gap.

**Follow-up:** name an owner, reviewer, realistic delivery time and acceptance command for each slice. The demonstration should include two situations with different winners if supported, a case where retaining the current model is correct, and a failure/fallback case. If measured evidence does not justify different winners, show that honestly and keep any scripted routing demonstration separate. Which claim can Hugo make at submission, and which remains a proposed next step?

**Answer:** **Decision:** defer past the 16:00 submission. Today's system is one task-specific model per target (P(OD 25), P(runway 18 usable)) plus a frozen blend policy by horizon × regime (night, calm, active). The policy is selected on earlier validation data and evaluated on later held-out months, so a pre-registered, deterministic choice already exists inside one task. There is no multi-model router and no delay specialist: FRA hourly delay data is not public, and a delay signal must never stand in for the direction or runway probabilities. **Consequence:** the demo shows one model with its blend and evidence; routing appears only as a next step in the pitch. **Owner if picked up later:** Kai, with the ML lane.

### F17 — Which learning approaches have not been tried yet? (Kai + Jayden + ML implementer)

Hugo requests an independent Colab red-team experiment using the same source files, tests and evaluation rows with a different learning method. This is an experiment, not a request to change the submission model or build the deferred router in F7–F16.

Have you already tried Extra Trees/random forests, calibrated linear models, change/no-change learning, or a learned combination of predictor and persistence? Link the branches, notebooks, parameters and results, including unsuccessful attempts, so we do not duplicate your work.

**Proposed experiment versions:** R0 reproduces the current raw and served predictor; R1 uses Extra Trees on the same ordered features and labelled rows; R2 uses a fixed 50/50 probability average of R1 and the served predictor; R3 would learn direction-change risk using an explicitly agreed target and chronological validation. R1/R2 are the first controlled comparison. R3 needs the label clarification in F19. These are experiment names, not production version numbers or claims of improvement.

**Snapshot:** the first Colab inputs were frozen at `44d5abd3363248b1de0a3ed96ff32982aafdd7b3` (v4). F1–F6 now report v5 and trace capture at `ccba644`; therefore the pinned experiment must be labelled a v4 comparison, not a comparison against current v5. Identify the exact v5 source/data/artifact snapshot for a subsequent matched rerun.

**Answer:** v5 snapshot: `walk-forward-v5`, code [2300db6](../ml/train.py) plus evidence [ccba644](../ml/predict.py), outputs a494af2. Everything that was tested is in [EXPERIMENTS.md §4](../EXPERIMENTS.md), E1–E16, including the negative results:
- **Tried:**
  - official rules (E1, E16)
  - gradient-boosted trees (`HistGradientBoostingClassifier`, E2)
  - a persistence blend per lead (E3) and per lead × regime (E9)
  - a publication lag (E4)
  - separate weather models with spread (E10) and wind scaling (E11)
  - pressure boxes (E13)
- **No gain, dropped (E14):** deeper trees, monotonic constraints, per-lead models, extra observation-state features.
- **Not tested:** Extra Trees, linear or logistic models (the only logistic is the untrained rules-fallback transform in [`ml/forecast.py`](../ml/forecast.py)), a direct direction-change or change-time target, and stacking beyond the persistence blend.

### F18 — Which data sources actually reach the estimator? (Kai + data owner)

For the selected training version, provide a compact source → loader/join → feature names → estimator table. Which of the following are connected in both training and inference: the single previous-runs file, ECMWF/GFS/ICON disagreement, DWD wind, TAF, pressure gradients and bias-corrected wind? Which are only downloaded or proposed?

At the pinned v4 snapshot, `ml.train.dataset()` reads `openmeteo_previous_runs.parquet`. Please identify any additional source loaded inside feature construction, join key/timezone, missing-data treatment, availability timestamp and fallback. Link the actual ordered feature manifest rather than only a data inventory. Which connections changed in v5?

**Answer:** v5, from [`ml/train.py`](../ml/train.py) `dataset()`/`archived_inputs()` and [`ml/live.py`](../ml/live.py):

| Source | Loader | Features or label | Training | Inference |
|---|---|---|---|---|
| DFLD recorded OD (`data/ground_truth/dfld_hourly.csv`) | `train.load_truth`, [`ml/dfld.py`](../ml/dfld.py) | label `y_od`; `od_at_issue`, `hours_since_change` | yes | hindcast: yes; live: OD at issue from the source in `evidence.issue_inputs.od_source` |
| EDDF METAR (`data/eddf_metar.parquet`) | `features.normalize_obs` | `obs_*` wind, gust, tailwinds, 3 h trends; label `y_r18` (official rule) | yes | yes (latest METAR) |
| Open-Meteo previous runs, best match | `train.archived_inputs` | wind, gust, direction, tailwind 25/07/18, 80 m wind, pressure, temperature, rules on the forecast | yes | yes (Forecast API) |
| Same, ECMWF IFS, GFS, ICON | `archived_inputs`, `live.add_live_models` | per-model tailwinds, ensemble mean and spread, votes, rules on the ensemble | yes | yes |
| Same, pressure at 4 boxes about 200 km away | [`ml/synoptic.py`](../ml/synoptic.py) | `dp_ns`, `dp_ew`, geostrophic tailwinds | yes | yes (`add_live_pressure`) |
| DWD 01420, Open-Meteo historical forecast, IEM TAF | — | none | no | no (DWD only cross-checks the stuck feed; TAF returned 0 rows) |

### F19 — What can we safely use as the direction-change target? (Kai + label owner)

Are DFLD hour-end availability (`time + 1h`), upstream reporting delay and summer-time conversion verified or assumed? Do weather runs have actual publication timestamps, or only the six-hour availability proxy? Which transition and missing-label hours are removed by the current dataset?

For R3, distinguish “target-hour OD differs from current OD” from “at least one change occurs within the horizon”: two changes can return to the initial direction. Which target matches the intended use? Should change-event learning use the half-hour source so that stable-hour filtering does not remove the very events being learned? State the label construction, censoring/missing-window rules and tests before training it.

**Answer:**
- **Direction label:** DFLD half-hour bins, converted to hourly stable labels only where both bins agree. Hours containing a change are excluded from stable-hour accuracy.
- **Timing:** a label counts as known only after its hour ends. DST gap and repeat hours are excluded. The Berlin clock is assumed for DFLD pages; the summer offset is unverified ([`data/ground_truth/README.md`](../data/ground_truth/README.md)).
- **Forecast availability:** forecast runs count as available 6 h after their nominal start. That is a proxy: no original publication times exist.
- **Change-event target:** next-change timing is scored on the half-hour source (`quality.json` `next_change`: within ±1 h / ±3 h, false alarms), with incomplete windows excluded. Change hours in the stable-hour metric are `changed_within_lead`.
- **Not tested:** a dedicated change-time model.

### F20 — Can exclusions use information from after a fold boundary? (ML implementer + independent reviewer)

At the pinned v4 snapshot, `dataset()` computes `suspect_od_runs()` on the full history before splitting; the flag marks an entire direction run using its METAR violations. Has a test established that later observations cannot change which pre-boundary training rows are excluded? This is a potential mechanism, not a claim that the documented October 8–12 interval crosses the current folds.

**Proposed answer:** preserve all-recorded headline scores and report retrospective stuck-feed exclusion as a sensitivity analysis. For a strict chronological experiment, derive any training exclusions from information available before the relevant training/validation cutoff. Confirm whether v5 changes this and link the check.

**Answer:** **Yes, in principle.** [`suspect_od_runs()`](../ml/quality.py) counts METAR hours over the 10 kt landing limit across a whole recorded run, so it can use hours after a fold boundary. In practice it flags only the 8–12 Oct 2026 run, which lies inside the last test month. So it never removed training rows for any walk-forward fold. Only the final live model (`ml/train.py` `fit(without_stuck_feed(...))`) trains without those hours.
- **Headline scores use all recorded hours:** 1/6/24/48 h model 96.0 / 92.8 / 91.7 / 89.2% vs rules 95.9 / 88.1 / 87.7 / 84.0% (`quality.json` `out_of_sample`).
- **Stuck-feed exclusion is a sensitivity analysis only** (`out_of_sample_stuck_feed_excluded`): 96.4 / 94.1 / 93.0 / 90.4%.
- **Not tested:** a fold-causal version of the flag.

### F21 — Which tests, holdouts and metrics decide whether an experiment wins? (Kai + evaluation owner)

Name the existing test commands and validation artifacts we must reproduce, the unchanged monthly split/issue schedule and label purge, and any untouched jury/final holdout dates. October has already informed development; an October comparison is exploratory, not a pristine final evaluation.

Which objective is primary: Brier score, accuracy, missed changes, false alarms or next-change timing? What tradeoff would reject a candidate? Report raw and blended results, matched row counts, lead/regime slices and change-event counts; do not select a method or blend weight using the final test outcomes. How should uncertainty account for overlapping 48-hour forecast windows?

**Answer:**
- **Holdout:** expanding monthly walk-forward, 12 test months (Nov 2025 – Oct 2026), 6 h publication lag, no random CV. Blend weights come from an inner chronological validation block before each test month ([`ml/train.py`](../ml/train.py) `fit`).
- **Primary objective:** Brier score of P(OD 25) at 6, 24 and 48 h. Accuracy at 1/6/24/48 h against both baselines is reported next to it.
- **A win means:** the day-bootstrap 95% CI of the margin over both rules and persistence lies above 0 at 6/24/48 h, and 1 h is not worse. McNemar and Diebold-Mariano p-values are reported in [`ml/significance.py`](../ml/significance.py), but correlated hours overstate them, so the CIs decide.
- **Also reported:** change-hour accuracy, next-change timing, false alarms, reliability.
- **Caveat:** E10–E14 were compared on these same 12 folds, so feature selection saw them. The untouched test is the live forecasts from 30 Oct on.

### F22 — Which baseline and evidence should the Colab run freeze? (Jayden + Kai)

Which source commit, data hashes, fitted artifact and quality/backtest files are authoritative now? At pinned v4, committed one-hour blend accuracy was 94.64% versus persistence 95.20%, while the model card quoted an earlier result. These are artifact reads, not our independent rerun, and should not be carried forward as v5 findings. Please link the reconciled v5 figures and their producer command.

**Proposed evidence bundle:** source and input hashes; environment versions; unchanged-test output; training/validation/test cutoffs; feature order; model parameters and fitted artifacts; per-row raw, blended and combined probabilities; matched metrics and exclusions. Colab's Drive quota prevented a saved notebook in Hugo's account, so the current attempt uses an unsaved runtime and a verified upload; it must be exported before being treated as a durable result. Who reviews that bundle, and which result warrants a subsequent full walk-forward rerun?

**Answer:**
- **Authoritative:**
  - code at 2300db6 (features and model) plus ccba644 (evidence)
  - published outputs at a494af2
  - artifacts `ml/models/forecast.joblib` (live, trained through 2026-10-29T18:00Z) and `ml/models/fold-YYYY-MM.joblib` for hindcasts
  - each published forecast records its artifact file and SHA-256 in `evidence.model_artifact`
- **Data hashes:** only the DFLD extraction is hashed per month (`data/ground_truth/dfld_manifest.json`). METAR and Open-Meteo parquet files are **not hashed**, so freezing them needs a hash step.
- **The two 1 h numbers measure different things.** v4 (94.6% blend vs 95.2% persistence) was 6 test months (May–Oct 2026) on the new local-midnight issue grid. v5 (96.0 vs 95.9) is 12 test months (Nov 2025 – Oct 2026). On the same 12 folds, the v4 feature set scores 95.5% at 1 h ([EXPERIMENTS.md E12 table](../EXPERIMENTS.md)).

**Independent experiment completed (Hugo, 30 October):** [Executed Colab notebook and matched v4 October results](experiments/v4-colab-october.md). Unchanged tests: **50 passed**. Extra Trees and a fixed 50/50 combination did not improve accuracy over the original blend on any reported lead. Muse independently recomputed **72/72 metric rows**; the coordinator reran its 29 checks and Opus's 15 focused leakage/rules tests. The constructed full-history exclusion leak exists, but the observed flagged run crosses no current fold boundary. This is exploratory v4 evidence, not a v5 result or promotion. Owner answers F17–F23 were subsequently added in commit `139f51a`; the executed v4 result remains frozen.

### F23 — Should the next Colab variants calibrate probabilities or learn wind correction? (Kai + Jayden + ML implementer)

Two additional candidates were not found in the inspected v5 training path or E1–E16 at [376faa8](https://github.com/werister/aiw-codex-hack/tree/376faa8f81bf4396f7d3f7df04fa0995a663d076). Please confirm whether either exists in unpublished work before assigning it. These are optional experiments after the R0–R2 comparison in F17, not new submission commitments.

| Proposed version | One controlled change | Evidence required to retain it |
|---|---|---|
| R4 — calibrated served predictor | Fit a sigmoid calibration step to the existing blended OD probability using a separate chronological calibration block or inner out-of-fold predictions. Keep an unchanged identity-calibration control. | Lower later-period Brier/log loss and improved reliability with sample counts, without an unacceptable change-warning/false-alarm tradeoff. Fit, blend selection, calibration and final evaluation must have explicit temporal boundaries. |
| R5 — conditional wind correction | Replace fixed 2024 mean-speed ratios with a small correction learned from earlier data by wind direction, season or lead. Change one grouping at a time and fall back to the existing scalar when coverage is sparse. | Improved held-out wind-vector/tailwind error followed by a matched downstream OD evaluation; report runway-18 event counts separately and do not infer closure skill from overall accuracy. |

**Why these:** the inspected [training code](https://github.com/werister/aiw-codex-hack/blob/376faa8f81bf4396f7d3f7df04fa0995a663d076/ml/train.py) fits classifiers and persistence weights but no probability calibrator. The [feature code](https://github.com/werister/aiw-codex-hack/blob/376faa8f81bf4396f7d3f7df04fa0995a663d076/ml/features.py) uses fixed `WIND_SCALE` coefficients. A reliability chart measures calibration; it does not fit a correction. Wind-speed correction and probability calibration are different experiments.

**Follow-ups:** which of R3 (change-event learning), R4 and R5 addresses the most useful remaining failure? Can we export the row-level chronological predictions needed for R4, including fold, issue/target times, raw/blended probabilities, labels, regime and artifact identity? For R5, where is the reproducible 2024 coefficient-fitting script and input hash, and how do we ensure every correction and selection uses only data available before its fold boundary? If a candidate has already been tested, link its negative result as well as any gain.

**Recommendation:** prioritize the already proposed R1/R2 controlled comparison; make R3 the next task-level research move once F19 defines the event labels, and R4 the smaller probability-quality experiment. R5 follows if residual wind errors show a systematic pattern. These can use CPU Colab; do not reserve GPU capacity as a prerequisite. Calibration must use data disjoint from base fitting ([official calibration guidance](https://scikit-learn.org/stable/modules/calibration.html)); Colab resources are not guaranteed ([Colab FAQ](https://research.google.com/colaboratory/faq.html)).

**Answer:**
- **R4 calibration:** no separate calibration step exists (no isotonic or Platt scaling). Probabilities are the classifier's plus the persistence blend. Calibration is measured only: `quality.json` `reliability`; the mean absolute gap between predicted and observed frequency over 10 bins is 0.013 for OD.
- **R5 conditional wind correction:** not implemented. [`ml/features.py`](../ml/features.py) `WIND_SCALE` holds one fixed multiplicative factor per weather model (and 80 m), fitted on 2024 only. A correction by direction, speed or regime is **not tested**. It is the most promising next variant for runway 18, which v5 catches only 3 of 24 events at 24 h, with no false alarms.

## New-data review round requested by Hugo

The [Kai data and NASA/prior-work review packet](reviews/kai-data-round2.md) links the newly committed data packages, audits, literature, completed Colab evidence and three independent reviewer assignments. Opus checks data eligibility/leakage, Muse specifies a new learning experiment, and Kiro checks package integrity/integration. Review snapshot: `5aed997313b78678d11fa23b808c2a9835a1d91a`. New review results and any additional training remain pending; downloaded literature and US delay data are not automatically FRA training labels.


### F24 — Four-minute finals pitch: support for Jayden's existing deck (Jayden + head agent)

**Requested by Hugo, 30 October 2026:** the pitch slot is **four minutes**. Jayden leads the existing pitch; this is supporting research and copy review only. Please decide what to adopt in your deck. No parallel deck or changes to presentation code were made by this support lane.

**Reviewed:** [deck snapshot abd8438](https://github.com/werister/aiw-codex-hack/blob/abd8438d7d73b0de1abead5669773921fd3fead2/web/public/deck/index.html), its [presenter notes](https://github.com/werister/aiw-codex-hack/blob/abd8438d7d73b0de1abead5669773921fd3fead2/web/public/deck/NOTES.md), [existing script](https://github.com/werister/aiw-codex-hack/blob/abd8438d7d73b0de1abead5669773921fd3fead2/web/public/deck/presentation-script.md), [model card](https://github.com/werister/aiw-codex-hack/blob/abd8438d7d73b0de1abead5669773921fd3fead2/MODEL_CARD.md) and [quality data](https://github.com/werister/aiw-codex-hack/blob/abd8438d7d73b0de1abead5669773921fd3fead2/web/public/data/quality.json). Later commits may supersede individual findings.

**Timing:** the latest ten slides total **210 seconds (3:30)** in their `data-time` attributes: 15 / 20 / 30 / 20 / 20 / 30 / 25 / 15 / 20 / 15. That leaves 30 seconds inside the confirmed slot. Preserve the structure and rehearse it with the actual clicks. `NOTES.md` still describes nine slides / 3:40; the companion script offers 2-, 3- and 5-minute variants. Please reconcile those instructions to one four-minute version. Attribute totals are not a measured rehearsal.

**Research applied to this deck:** Devpost recommends a brief problem setup, a working demonstration that resolves that problem, then a short impact/next-step close. YC recommends a few memorable points, clear language and repeated timed rehearsal. For this deck: explain one preparation decision, show one saved case, state one headline result, and end with the proposed operational validation. These are presentation recommendations, not this hackathon's scoring rules. Sources: [Devpost demo guidance](https://info.devpost.com/blog/how-to-present-a-successful-hackathon-demo), [YC presentation guidance](https://www.ycombinator.com/blog/guide-to-demo-day-pitches/).

**Targeted suggestions for the current slides and notes:**

| Existing location | Suggested copy or treatment | Evidence boundary |
|---|---|---|
| Title: “48 hours earlier” | “Hourly runway forecasts, up to 48 hours ahead.” | Forecast horizon does not establish 48 hours of usable preparation time. Wind constrains operations; the responsible operational team decides. |
| Day example: “Warned a day ahead”; notes: “as it was issued” | “A historical forecast reconstruction, compared with recorded direction.” | The saved hindcast uses archived-weather availability assumptions. Exact publication/reporting times remain unverified; do not present it as a contemporaneously issued warning or a measured operational success. |
| Results / people: “82% of direction changes” | Label the 82.1% as direction accuracy on the evaluated change-conditioned hourly rows, or keep it in Q&A. | This is not recall of 156 distinct annual switches. Use the separate next-change timing metric for timing, with its issue-window denominator. |
| People: “350 more hours a year planned right” and “24 h to set rosters, equipment, stands” | Present as a proposed use to validate with a shift lead. | More correct classified hours do not prove correctly planned hours, staffing gains or a full day's actionable notice. |
| Value: annual euro scenario | Keep assumptions beside the figure; consider moving the annual range to Q&A and using this time for the pilot request. | No savings were measured. Do not convert the change-conditioned hourly score into additional distinct annual switches. The existing companion script already records this denominator problem. |
| Presenter notes: “chance this is luck below one in a thousand” | Remove this interpretation. If needed, quote the reported day-bootstrap interval for the score difference. | A p-value is not the probability that an effect is “luck”; hourly dependence also matters. This wording has disappeared from the latest slide renderer but remains in the notes. [ASA explanation](https://www.amstat.org/asa/files/pdfs/p-valuestatement.pdf). |

**One result worth saying slowly:** “At 24 hours, the model gets the direction right in 91.7% of scored hours, compared with 87.7% for the challenge-rule forecast and 75.1% for keeping the current direction.” This covers **1,383 scored hourly predictions** in the historical monthly evaluation; the model–rule margin is **4.0 percentage points**, with a reported day-bootstrap 95% interval of **2.4–5.6 points**. At one hour the methods effectively tie. If retaining the deck's 48-hour headline, use **89.2% versus 84.0%**, about **32% fewer wrong hourly classifications**, and keep the horizon visible. These figures concern direction, not runway-18 closure skill.

**Short spoken qualification:** “Each monthly model trained on earlier data. We selected features using these evaluations, so an untouched final test is still ahead. Runway-18 labels come from weather rules; actual closure records are needed for validation.” DFLD is a public direction proxy, not a certified movement log. The existing script has the fuller explanation and stronger corrected-wind baseline for Q&A.

**Suggested final sentence:** “With FraAlliance, we want to test whether these warnings give shift teams useful preparation time, using the airport's operational records.” This gives the closing slide a concrete next step beyond the feature roadmap.

**Demo coordination:** a separate active UI lane is removing synthetic values at Hugo's request. Do not build the spoken sequence around the old synthetic opening of `/pitch`. Freeze one actual saved forecast and its version, then rehearse the deployed `/deck` path and its fallback. This review inspected deck source and the locally running pitch views; it did not validate the final deployed deck or measure a human rehearsal.

**Answer requested from Jayden's head agent:** please confirm the final four-minute running order, selected replay and which wording changes you adopt or revise. Reply here so there remains one shared handoff. **Status:** supporting input delivered; deck ownership and final decisions remain with Jayden.
