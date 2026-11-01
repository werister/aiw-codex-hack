# Using the runway outlook

Open `http://127.0.0.1:3000`. The bundled forecast is a fixed historical weather example, not current airport status. Its issuance and method are visible. This package computes a rules-only forecast; fitted weights and direction labels are withheld pending source permission.

Select an hour on the overview bar. Expand **Hourly forecast** to inspect the complete timeline, changes, runway-18 restrictions, wind, rule comparisons and uncertainty. The selected hour controls the illustration and detail panels. The forecast guide produces deterministic explanations locally and sends no data to a service. Its six-hour handover follows consecutive UTC rows and reports missing coverage.

`/widget` provides a tablet view. The theme control switches between light and dim-room modes. `/quality` shows historical fitted-model evaluation separately. `/approach` explains the method. `/model-card/` lists limitations.

The runway-18 illustration uses a 50% display threshold. Scores in the rules demo are uncalibrated margins, not measured probabilities. Aircraft, routes and timing are illustrative; there is no flight-demand, capacity or clearance feed.

## Regenerate the offline example

After installing the Python requirements, from the repository root:

```sh
python -m ml.forecast --demo
python -m ml.forecast --demo --json --out web/public/forecasts/latest.json
```

This reads committed IEM METAR and Open-Meteo archived weather, infers the issue-time direction from weather rules and computes 48 hours. It requires no network or key. The fixed example is 28 October 2026; it uses no recorded direction outcomes.

## Research pipeline

`python -m ml.fetch --help` documents weather downloads. Live requests can fail when offline or rate-limited. API access terms are separate from data licences; commercial use of the free Open-Meteo API requires an appropriate service arrangement. See [sources](DATA_SOURCES.md).

The ordinary `python -m ml.forecast --day YYYY-MM-DD` path supports dates covered by local inputs. Live requests require a network. With no fitted files it warns and uses the rule fallback, which is distinct from the evaluated model. Independent retraining requires permission-cleared direction labels in the documented schema.

`python -m ml.evaluate` reads the historical aggregate report; it does not recompute predictions. `python -m ml.evaluate --replay` requires lawfully supplied original fits and labels. Read [evaluation](EVALUATION.md) before quoting results.
