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
