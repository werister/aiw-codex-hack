# Questions for Kai and Jayden: one traceable forecast run

Requested by Hugo on 30 October 2026. Please answer in this file and link the relevant code, artifact or follow-up commit. Status: awaiting owner confirmation; these questions do not claim that evidence capture is implemented.

Goal: connect one real forecast run to the existing evidence panel, so a selected UTC hour can be traced to the inputs and calculations that produced its probability. Hugo proposes to own the evidence contract and demonstration; confirm the implementation owners below.

## Kai Detmers — inference ownership and capture

> I want to make the evidence panel traceable to one real forecast. Who owns the inference code right now? Can we capture the exact inputs, feature values, model/rules versions, and raw versus blended probabilities for each hour?

Please identify:
- The current implementation owner and the function where capture should happen.
- Which source snapshots, ordered model inputs, model/rules identities and raw/blended outputs are already retained, and which need capture.
- One real run we can use, including its issue time and model artifact identity.
- The smallest missing change and any blocker.

**Answer / owner / code or artifact link:** Pending.

## Jayden Bruck — UI connection and coordination

> Your evidence panel is already implemented. I am coordinating the captured inference record with Kai. What format and join key do you need to connect it to the selected forecast hour?

Please confirm:
- The UI integration owner and preferred record format/location.
- How the UI joins the exact forecast run and selected UTC hour to its evidence, including reruns with the same issue time.
- How missing capture is shown, and how we keep the selected hour aligned with the planning recommendation.
- Whether an existing worker already owns this, so Hugo's contribution does not duplicate it.

**Answer / owner / code or artifact link:** Pending.

## Shared acceptance check

For one selected hour, resolve the retained source inputs, exact ordered feature values and model/rules identities; follow the raw-to-published probability calculation; and confirm that the evidence belongs to the displayed forecast bytes. Show unavailable details explicitly. Per-feature attribution is optional and must not be invented from the final score.

Start from the [trace output wishlist](forecast-trace-wishlist.md) and [fleet-planning handoff](fleet-planning.md). This handoff requests evidence capture and integration decisions; it does not request a new model, frontend redesign or fleet-impact estimate.
