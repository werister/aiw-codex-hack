# Design: FRA forecast operations view

## Context

This design implements WP5 for Jayden and the head agent, using the official brief and `briefing/brainstorm-268.md`. Baseline inspected: `4cf1ccd` (30 October 2026). At that commit `web/src/app/page.tsx` is a placeholder; the Python pipeline and forecast-serving UI are planned, not implemented. This document describes proposed behavior. Browser and operational-system evidence is in `briefing/2026-10-30-ui-atc-context.md`.

`web/src/lib/forecast-types.ts` is the shared shape contract; the CLI brief now owns file publication, thresholds and certainty semantics; the model brief owns prediction/evaluation. WP1–4 produce forecast data; WP8 produces model-quality evidence; WP5 displays both. The pipeline described in `ml/README.md` writes static forecast JSON under `web/public/forecasts/`. There is no existing Next.js API route or live DFS/Fraport connection to reuse.

## Goals and scope

- Help an operations user answer: which direction, is runway 18 likely usable, when might this change, and how certain is the forecast?
- Use a simple tower-inspired view with FraAlliance branding from supplied assets, clear text states, and one-click detail. Keep the 48-hour forecast and model evidence prominent.
- Work on laptop and iPad with keyboard and touch input; communicate states with text as well as color.
- Cover forecast evidence, failure states and jury-day replay. Aircraft tracking, clearance controls, movement scheduling and operational ATC integration are outside this change. The schematic ops view in WP5 shows runway directions and illustrative traffic marked `SIMULATION`, without implying real aircraft positions. WP9 owns optional 3D separately and drops it if not ready by 15:00.

## Decisions

### 1. Read the documented forecast index and files

These publication conventions already appeared in the model brief at `0f227428`; they are not new WP5 proposals. At `4cf1ccd`, the CLI brief specifies `days` as an array of `YYYY-MM-DD` strings. Validate each as a calendar date. File existence, refresh cadence and freshness remain separate from that source-confirmed shape.

The CLI brief requires `/forecasts/index.json` with `{ "days": [...], "latest": "latest.json" }`, `/forecasts/latest.json` generated with `--now`, and `/forecasts/YYYY-MM-DD.json` examples. Use that documented manifest to populate published-day choices and resolve the default `Latest available` selection. Validate the manifest and restrict referenced files to the forecast directory. A native date picker supplements the listed examples so a new jury date can be requested without application code changes. Publishing a dated file and updating the manifest are producer data changes, not UI source edits.

If the index is unavailable or malformed, show that the published-day list is unavailable, allow explicit date selection, and allow a labelled attempt to load the documented `latest.json` file. If any forecast file is absent, show unavailable rather than switching silently to another date. These artifacts are documented producer deliverables; they have not yet been generated at this baseline.

Selecting a day fetches its file and validates it before replacing the display. A slow response for a previously selected day cannot replace the current selection. Display the selected day during loading; do not retain another day's forecast under the new date. A failed date remains selectable so the user can retry or choose another day.

Read the existing producer artifact `web/src/data/backtest.json` as `BacktestResult`. A server-only page loader reads and validates this optional file while rendering, passing serializable evidence or an unavailable state into the UI; it does not use a static import that would fail the build when the file is absent. Deployment must include the artifact when present, and publishing changed evidence requires rebuilding/redeploying the web app. Use the same pattern for WP8's `web/src/data/quality.json` after its joint `QualityResult` contract lands. These files do not move to a new public path. Failure to load backtest data does not hide a valid forecast, and failure to load a forecast does not hide valid model evidence. No browser call trains a model or fetches historical observations.

### 2. Put provenance above the operational summary

Header: FRA / EDDF, selected day, `Live forecast` or `Historical forecast`, issue time, elapsed time since issue, weather source (`nwp`), model version and rules version. `Live forecast` means the payload's `mode: live`; it does not mean a live ATC feed or continuous refresh. The `Latest available` alias is a selection convenience, not a freshness guarantee. When `model_version` is `rules-fallback`, show `Rules fallback` prominently rather than presenting it as a trained model.

Treat UTC `issued_at` and each hourly `time` as authoritative for ordering and elapsed time. Display Europe/Berlin local time with date and UTC offset, including repeated hours at daylight-saving transitions. Keep UTC visible in the detail view. Use `issued_local`/`local` only when consistent with those timestamps. No arbitrary stale-data SLA is introduced; show issuance age and say when the full forecast horizon has elapsed.

### 3. Summarize, then drill into one hour

Top summary: issue-time direction, selected forecast hour's runway-18 yes/no call, next likely change (`next_change`) and runway-18 closure intervals (`closures_18`). `current_od` is an issue-time reference whose label depends on provenance: `DFLD-recorded OD`, `UNH-published OD`, `INFERRED — METAR + rules`, or `Source not established`. Do not describe a third-party recorded reference as DFS-confirmed without evidence. Keep the source time visible; issue-time direction is not necessarily current at viewing time. The producer brief defines `closures_18` as runs where `p_18_usable < 0.5`; use that same documented threshold for `Likely unavailable`, and `p_18_usable >= 0.5` for `Likely usable`. Show the probability beside the call and the selected forecast timestamp. The first row is T+1, not the issue-time/current runway-18 state; no issue-time runway-18 boolean is present in the shared response. The UI must not show contradictory usability and closure states for the same hour, and does not independently change the threshold or recompute closure intervals. A null `next_change` means `No direction change predicted within this forecast`, not a promise that none will occur. Empty closure intervals mean no closures predicted by this payload.

Render the supplied 48 hourly cells in chronological order. Each displays local date/hour, `OD 25 west` or `OD 07 east`, `P(18 usable)` as a percentage, and `certainty` as a score out of 100. The producer defines `certainty = round(100 × min(abs(2*p_od25 - 1), abs(2*p_18_usable - 1)))`: it is the smaller probability margin, not a calibrated joint probability of correctness. Label it `Certainty score`, with that explanation in detail. Preserve the distinction between probabilities (0–1), the margin score (0–100), and measured accuracy. Highlight the producer's next-change time and window. Closure intervals are start-inclusive/end-exclusive because `end` is the first usable hour in the contract. If the final forecast hour still has `p_18_usable < 0.5`, mark the interval `Continues through forecast horizon; reopening unknown`. The current `Closure18.end` type expects a first usable hour, which cannot be known for a closure extending past the horizon; WP4 and WP5 must resolve a censored-end representation before claiming an exact reopening time. Do not fabricate a reopening at hour 49 or treat the last available timestamp as observed reopening.

Selecting an hour updates an adjacent panel containing its UTC/local timestamps, lead hours, model OD and probabilities, wind direction/mean/gusts, signed tailwind components, and rule-baseline direction/runway-18 usability. Label a negative tailwind value as headwind. A null wind direction is shown as `Direction unavailable / calm`, without drawing a wind arrow. Keep model and rule outputs visibly named.

### Reference provenance: reconcile the producer brief and type comments

The backend report identifies unmerged DFLD artifacts on `jayden/research` at `bb1dd7f589eeef4aa54a7a9aa213a2b68e90b384`. This is reported branch evidence, not a merged integration or an independent dataset audit. DFLD is a recorded-OD proxy, not certified aircraft-movement logs or runway-18 usability. Its retained hourly rows exclude change hours and some DST hours; preserve coverage exclusions and the difference between stable-within-hour DFLD labels and full-hour METAR-rule labels. Do not count excluded hours as correct predictions or claim change-timing performance from stable-hour coverage alone.

At this baseline the TypeScript comments still describe `current_od` and `observed` as rule-derived, but the newer CLI brief specifies DFLD-recorded issue-time and hindcast ODs where available, METAR-rule fallback otherwise, and potentially UNH-published live OD. The new model brief trains/evaluates OD against recorded DFLD directions and runway-18 usability against **INFERRED** METAR-rule labels. This is an unresolved metadata contract conflict, not evidence that every OD is synthetic or every reference is recorded.

Proposed joint WP4/WP5 extension, to be agreed before implementation: a small provenance object with `kind: recorded | inferred | unknown`, source name/URL, derivation method where inferred, and reference timestamp/coverage. Attach it separately to `current_od`, each reference row's `od`, and each reference row's `r18_usable`; dataset-level defaults are acceptable only when explicit overrides can represent mixed coverage. Keep OD and runway-18 evaluation provenance separate in backtest/quality metadata as well. These are proposed fields, not fields present in today's TypeScript contract; agree their exact names/shapes with the owners and update producer/type/UI together.

Render DFLD OD as `DFLD-recorded`, UNH OD as `UNH-published`, and each METAR-plus-rule fallback as `INFERRED`. For the presently documented runway-18 target, show `INFERRED — METAR + rules` wherever it is supplied as a reference or evaluation label. Do not transfer a recorded OD label onto runway-18 usability. If the payload has no usable provenance and its schema/model version does not establish it, show `Source not established`, without guessing from a number or a field name.

Missing reference rows have no comparison. The current `observed` shape requires both `od` and `r18_usable`, while DFLD only establishes the OD. WP4/WP5 must agree per-target absence (for example nullable/optional reference values) rather than invent a runway-18 boolean to complete a recorded OD row. Use a runway-18 rule label only when genuinely computed and mark its provenance inferred. The UI may show the known OD comparison while runway-18 reference remains unavailable.

### 4. Make unavailable data visible

Enforce `time = issued_at + lead_h hours`, not merely sorted timestamps and 48 entries. A dated forecast is issued at 00:00 Europe/Berlin and starts at T+1; `--now` uses the current full hour. WP4 must resolve how today's midnight and future dates satisfy the information cutoff when live inputs are fetched later or earlier. WP2/WP3 own initialization, pending tailwind duration and the stepping policy that applies 30-minute hysteresis to hourly winds; the UI must not invent these or claim their correctness from the payload alone.

Validate required fields, finite numeric values, OD/mode enums, probabilities in [0,1], certainty in [0,100], timestamps, and exactly 48 unique chronological UTC hours with leads 1–48 before rendering a forecast. Reject an invalid payload with a plain-language `Forecast unavailable` state and a retry action. Do not substitute fabricated, zero-valued or cached-other-day forecasts. Distinguish loading, request failure/missing file, invalid payload, and a valid forecast with no predicted change.

The timeline can scroll horizontally on narrow screens; the summary and selected-hour details remain readable without shrinking text. Use focusable hourly controls with visible focus and a selected state; taps and keyboard activation perform the same action. Avoid hover-only explanations.

### 5. Keep model evidence separate from probability

The backtest panel labels OD targets as DFLD-recorded where supported and runway-18 targets as inferred from METAR/rules; mixed or unknown coverage remains explicit. It displays OD and runway-18 results separately, comparing model, official rules and persistence at 1, 6 and 24 hours, with sample count `n`, accuracy and Brier score. An available 48-hour row is additional evidence, not a replacement for the required leads. Display train/test dates, `labels`, and `rules_version`; the panel explains what the evaluation target represents.

If `labels` describes rule-derived targets, mark those specific target metrics `INFERRED labels` and do not describe it as verified accuracy against flown operations. A missing/ambiguous label description says `Reference provenance not established`. Missing metrics remain unavailable, never zero or interpolated. Reported train/test dates and scores describe the submitted experiment; their presence alone does not establish absence of leakage. `drivers` may show the reported feature importance with its model context, without claiming causation.

WP8 extends the quality panel with data-source descriptions, walk-forward folds, in-sample versus out-of-sample results, reliability/calibration bins, and next-change timing accuracy within ±1 h and ±3 h. Display these only from its agreed `QualityResult` artifact. WP8 must specify the event being calibrated (OD correctness, runway-18 correctness, or both calls correct) and the score/probability being binned. The margin-based `certainty` is not already calibrated and cannot be described as an 80% chance both calls are right. Missing WP8 evidence stays unavailable; do not derive calibration from the margin score alone or label training fit as unseen-data performance.

## Dependencies and open decisions

- Next-change selection is already specified: the first hour whose model `od` differs from `current_od`. `next_change.p` is `p_od25` for `to: "25"` and `1 - p_od25` for `to: "07"`, the probability of the new OD at that hour, not a change-event probability. Label it accordingly. The documented window uses neighbouring hours where p(new OD) is between 0.35 and 0.65; WP4 still owns abrupt-jump/no-neighbour, first-hour, repeated-change, horizon and DST endpoint cases. Show only the producer's window, without inventing confidence-interval coverage.

- WP4 must implement its already documented date files, `latest.json` and `index.json` publishing contract. WP3 supplies `web/src/data/backtest.json`; WP8 supplies `web/src/data/quality.json` and agrees `QualityResult` with the UI owner. Neither data artifact exists at the inspected baseline.
- WP4 and WP5 must agree how `Closure18.end` represents a closure still in progress after hour 48; its existing mandatory first-usable-hour semantics cannot express that case honestly.
- WP7 owns source evidence; WP4/WP5 must resolve stale type comments versus the new recorded-OD brief with per-field provenance and optional per-target references. Existing metadata cannot distinguish mixed recorded OD / inferred runway-18 labels reliably.
- FraAlliance brand assets and exact color tokens need team-provided references; retain readable contrast and text status labels.
- The CLI brief defines `--now` as the current full hour. Automatic issuance cadence and a freshness SLA remain unverified. Display age and expired horizon honestly rather than inventing operational service guarantees.

## Verification before WP5 is marked complete

Walk the browser demo on laptop and iPad widths: latest available day, a published hindcast, hourly keyboard/touch detail, next-change/closure markers, and model evidence. Include one missing file, malformed probabilities or missing hours, a null change, a closure extending through hour 48, absent reference rows, manifest failure, overlapping day requests and a Berlin daylight-saving repeated hour. Confirm the UI uses only the selected published data and preserves field-specific recorded/inferred/unknown provenance labels. These are acceptance checks for implementation; writing this design does not mark them passed.
