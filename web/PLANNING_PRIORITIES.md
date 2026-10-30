# Planning priorities

The cockpit can select a preparation or evidence-review focus from the published
forecast. The weather model still owns every forecast probability. A separate
Decisions request selects one supported issue for each of two perspectives:
ground operations and forecast review.

## Why this integration

The previous recommendation chose the first direction change or runway-18
restriction. That misses an earlier model/rule disagreement which may deserve
attention before preparing for the event. Intent routing in the forecast guide
would improve question matching but would not address this planning choice.

This implementation uses fixed-option `choice` questions and structured JSON
evidence, as described in the [Decisions guide](https://developers.openai.com/api/docs/guides/decisions).
Both perspectives share the same forecast and candidate list. The API selects an
ID; titles, actions, source hours and preparation calculations are produced by
code. No free-text action, staffing quantity or operational instruction is
generated. API confidence describes the selection, not weather probability.

## Data path

1. `tools/forecast_decisions.py` validates the saved forecast's probabilities and
   time/lead alignment, including partial-day coverage.
2. It creates candidates for each contiguous direction transition, runway-18
   restriction, model/rule disagreement, missing provenance, and monitoring.
   Gaps do not become invented transitions or continuous restriction windows.
3. Model/rule conflict or a new-state probability below 0.6 makes an event a
   **review** candidate. The 0.6 threshold is an explicit planning heuristic,
   not a calibrated operational threshold. Runway-18 usability retains the
   forecast contract's 0.5 threshold.
4. Two independent `choice` questions select a candidate for each perspective.
   Inputs include forecast values, rule comparisons and source metadata.
   Later `observed` outcomes are excluded. No model training happens here.
5. Refusal, invalid responses, missing credentials or network errors produce a
   labelled deterministic fallback. A single candidate needs no API call.
6. The CLI writes `/decisions/<forecast filename>.json`. The browser accepts it
   only when the full pre-outcome basis matches the selected forecast, including
   probabilities, issue time, source bundle and model/rules versions.

The static export needs no server endpoint or browser credential. If a forecast
is regenerated, regenerate its review too. A stale or absent review displays an
unavailable state with retry while the forecast remains usable. Retry reloads
the saved artifact; it does not call the API.

## Run

From the repository root, with only the files intended for external review:

```sh
python3 tools/forecast_decisions.py \
  web/public/forecasts/2026-10-29.json \
  web/public/forecasts/latest.json --prompt-key
```

The prompt masks the key and uses it for this process only. Alternatively export
`DECISIONS_API_KEY` (preferred) or the existing `OPENAI_API_KEY` in the CLI's
environment. `DECISIONS_MODEL` overrides the documented model default. The CLI
does not automatically load `.env.local`; example files list the variable names.

For an offline review with no transmission:

```sh
python3 tools/forecast_decisions.py web/public/forecasts/2026-10-02.json --offline
```

Every artifact records its status, reason, generation time and policy version.
Successful API artifacts also record the request hash and requested model.
Provider error bodies and credentials are never written to public artifacts.

## Demo and observed result — 30 October 2026

Open the cockpit for **29 October** and the Planning priorities panel. The real
API selected `disagreement-1` for both perspectives, from three candidates.
The deterministic operations fallback would select `direction-6` instead:
the difference is reviewing conflicting evidence before the predicted switch.
Selection confidence was 0.91 for operations and 1.0 for forecast review. These
are neither measured accuracy nor a probability of switching.

The saved latest forecast has only the monitoring candidate. Its initial API
attempt returned HTTP 400; the producer now bypasses unnecessary single-option
requests and labels the result “no ranking needed”. Other published examples
have explicitly offline reviews. Only the two user-approved forecasts were sent.

Select **2 October** to exercise the deterministic preparation path. Enter your
own preparation duration; the UI subtracts it in UTC and displays the scenario
start in Berlin time. Insufficient lead is explicit. This is a scenario based
on a predicted hour, not a deadline or measured cost saving.

Suggested pitch wording:

> Unser ML berechnet die Wetter- und Betriebsprognose. Eine getrennte
> Entscheidungsschicht wählt aus belegten Ereignissen den nächsten sinnvollen
> Planungsschwerpunkt. Im getesteten Fall priorisiert sie den Widerspruch
> zwischen Modell und Regeln vor der Vorbereitung auf den Richtungswechsel.
> Die zugehörigen Stunden und Quellen bleiben direkt prüfbar.

This historical review was generated today from saved forecast evidence. It is
not a decision recorded on the historical forecast day. One successful example
establishes integration, not better operational decisions. A follow-up evaluation
needs shift-lead labels, comparison with the deterministic policy, disagreement
and rejection cases, and measured review/preparation outcomes.

## Verification

```sh
python3 -m unittest tools.test_forecast_decisions -v
cd web
node --experimental-strip-types --test src/lib/planning-decisions.test.mjs
npx eslint src/components/PlanningPriorities.tsx src/lib/planning-decisions.ts src/lib/planning-decisions.test.mjs
npx tsc --noEmit
```

Tests cover competing events, source gaps, outcome exclusion, invalid probability
and time alignment, invalid/refused API answers, authentication/network fallback,
exact Python-to-browser artifact matching and UTC/DST preparation arithmetic.
Browser/build evidence is recorded after the shared UI integration is complete.
