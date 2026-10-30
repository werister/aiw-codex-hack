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

**Answer:** Pending.

### F2 — Who delivers one verified run, and when? (Jayden + named ML implementer; Hugo confirms demo fallback)

The current answer postpones capture until model work lands by 15:30; submission is at 16:00. What time remains for generation, UI connection, verification and rehearsal? Name the implementer and reviewer, not only the lane.

**Proposed answer:** aim for one captured historical run before 15:00, subject to owner confirmation. Verify that fixed example before deciding whether to regenerate with a newer model. Keep its model version visible. If capture is late, show the existing forecast with evidence explicitly unavailable; do not fabricate a trace. State whether this schedule is feasible and what work it depends on.

**Answer:** Pending.

### F3 — How do we distinguish the recommendation time from the inspected hour? (Hugo + Jayden)

If the recommendation remains fixed while the user selects a different forecast hour, how will the screen prevent that hour's evidence from appearing to justify a different event?

**Proposed answer:** show **Recommendation for [event time]** separately from **Inspecting [selected UTC/local time]**, with a **Return to recommendation evidence** action. If a different design is preferred, describe the interaction. Verify by opening recommendation evidence, selecting another hour, and returning.

**Answer:** Pending.

### F4 — Which model actually produced the historical example? (Kai + ML implementer)

For `2026-10-28.json`, issued `2026-10-27T23:00Z`, will capture record the selected fold artifact's path, SHA-256 and training cutoff, rather than copying metadata from the final fitted model? Will it retain the complete ordered estimator inputs with names, values, missingness and transform version, plus raw probabilities, blend key/weight, persistence input and published probabilities?

At inspected snapshot [b6b3b0](https://github.com/werister/aiw-codex-hack/tree/b6b3b0a1d4fd0f41489114f4bca4b97efe48e052), [model selection](https://github.com/werister/aiw-codex-hack/blob/b6b3b0a1d4fd0f41489114f4bca4b97efe48e052/ml/predict.py) should reject the final fit trained after this issue time and select an eligible historical fold. The [published example](https://github.com/werister/aiw-codex-hack/blob/b6b3b0a1d4fd0f41489114f4bca4b97efe48e052/web/public/forecasts/2026-10-28.json) does not record the artifact identity, so its actual generation provenance has not been proved by that file. A regenerated example must be identified as a new captured run, not retroactively claimed as original instrumentation.

**Answer:** Pending.

### F5 — What exactly makes one run's identity different? (ML implementer + Jayden)

Specify the canonical fields/serialization and hash used for run identity. How are selected model artifact, rules content, input snapshot contents, feature/inference-code revision and output-affecting blend/regime configuration bound to the result? Does a code-only change with identical inputs produce a distinguishable record? How do we resolve the retained values behind a snapshot hash?

**Proposed answer:** document one canonical identity contract and bind the serialized forecast and inline evidence consistently. Do not rely only on issue time or a mutable version label, and do not try to hash a payload including its own hash. State whether identical-input repeat executions share a content identity or receive distinct invocation IDs. Explain the choice.

**Answer:** Pending.

### F6 — What proves the optional types are actually connected? (Jayden + ML implementer)

Please link the producer serialization and UI consumption, not only the interface definitions. Where is the claimed run-ID match checked, what are its two operands, and what happens when capture is absent, inconsistent or from a different run?

The read-only audit at [b6b3b0](https://github.com/werister/aiw-codex-hack/tree/b6b3b0a1d4fd0f41489114f4bca4b97efe48e052) found optional [ForecastEvidence/HourInputs types](https://github.com/werister/aiw-codex-hack/blob/b6b3b0a1d4fd0f41489114f4bca4b97efe48e052/web/src/lib/forecast-types.ts), but no evidence/run ID/hourly inputs in the example; [the producer](https://github.com/werister/aiw-codex-hack/blob/b6b3b0a1d4fd0f41489114f4bca4b97efe48e052/ml/forecast.py) did not emit them and [EvidenceChain](https://github.com/werister/aiw-codex-hack/blob/b6b3b0a1d4fd0f41489114f4bca4b97efe48e052/web/src/components/EvidenceChain.tsx) did not consume or compare them. HourInputs also did not describe the full ordered estimator vector. These are snapshot findings; link a later commit if they have changed.

**Requested proof:** one generated file with resolvable evidence; a selected hour whose displayed values match capture; and observed UI behavior for missing/mismatched capture. Explicitly distinguish a new run with the same issue time from the previous run.

**Answer:** Pending.
