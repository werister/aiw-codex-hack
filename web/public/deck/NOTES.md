# Presenter notes — FraAlliance finals

These cues follow the current 14-slide deck and canonical speaker script. The timings total 3:41 (221 seconds) and match autoplay. Lead with the planning task, then show the model and the evidence separately.

Use the browser-hosted `/deck/index.html`. Arrow keys or the clicker advance; `A` toggles autoplay; `End` jumps to the last slide. The dashboard is a planning forecast, not an operational clearance.

## Slide cues

### 1 · 0:00–0:15 · 48-hour runway forecast

**Say:** “Lift-off is an hourly runway outlook for ground-handling planning at Frankfurt. It looks forty-eight hours ahead, so teams can examine a possible change before deciding how to prepare.”

**Keep straight:** The 48-hour horizon is forecast range, not a guaranteed warning lead.

### 2 · 0:15–0:31 · Why the task matters

**Say:** “When the operating direction changes, people and equipment need to be coordinated. A shift lead needs to know which configuration to prepare for, when it may change, and how uncertain the forecast is.”

**Keep straight:** This is the operational problem described by the challenge, not a measured delay or savings result from our model.

### 3 · 0:31–0:46 · The official rule baseline

**Say:** “Our baseline applies the challenge wind limits to forecast weather. We also compare with keeping the current direction. These are reproducible reference methods, not a description of every tool the airport already uses.”

**Keep straight:** This diagram illustrates the rule implementation used as a baseline. It is not a complete description of DFS’s control-room workflow.

### 4 · 0:46–1:06 · The direction model

**Say:** “The model combines forecast wind, the challenge rules and recent recorded conditions. It learns patterns with boosted trees and blends direction forecasts with the current state. We compare it with applying the wind rules directly and simply keeping the current direction.”

### 5 · 1:06–1:31 · Four hourly outputs

**Say:** “There are two forecast targets: the operating direction, west or east, and runway-eighteen weather usability. Each hour also has a certainty score, and we show the next likely direction change. These are planning inputs. DFS retains the operating decision.”

### 6 · 1:31–1:51 · Recorded direction data

**Say:** “We combine public recorded directions from DFLD, airport weather observations from IEM, and archived forecasts from Open-Meteo. The direction archive reaches back to 2018; the joined forecast inputs start in 2024. These public records are proxies for operations, not certified movement logs.”

Sources on this slide: [DFLD](https://www.dfld.de/Mess/StatWetter.php?R=1) supplies the recorded directions shown in the chart. Weather inputs come from [Open-Meteo live forecasts](https://open-meteo.com/en/docs) and [archived Previous Runs](https://open-meteo.com/en/docs/previous-runs-api), plus [EDDF METAR observations via the Iowa Environmental Mesonet](https://mesonet.agron.iastate.edu/request/download.phtml). Open-Meteo data are attributed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

Windy is only a separate connection test. Its Testing-tier values are excluded from forecasts, training and evaluation.

### 7 · 1:51–2:01 · How we tested it

**Say:** “We test on successive months, training each model on earlier data. Those months also informed development; a frozen prospective test is still needed.”

**Show:** 12 monthly folds, three archived weather-model inputs, two baselines and 1-, 6- and 24-hour scores. Do not reuse older audit counts as v6 results.

### 8 · 2:01–2:26 · Historical forecast against the record

**Say:** “This October twenty-eighth reconstruction shows the forecast against the later record. Both methods anticipate a change, but neither gets its timing exactly right. The example explains the product; the separate twelve-month evaluation measures its quality.”

**Demo path:** In the prepared `/pitch` tab choose **2026-10-28**, show the hidden outcome, then click **Reveal recorded outcome**. Read the shared-hour counts shown on screen. If the tab switch is not rehearsed, stay with the chart.

**Keep straight:** The saved file currently has 47 recorded hours: model 41/47, rules 39/47, persistence 33/47. Refresh these figures after forecast regeneration. The first different hourly record is 29 October at 10:00 Europe/Berlin; the previous matching sample is 09:00. Hourly bins cannot establish the exact transition instant or rule out temporary changes. Do not use the earlier 40-hour subset.

### 9 · 2:26–2:51 · Direction accuracy

**Say:** “At twenty-four hours, the model gets the direction right in 91.8 percent of scored hours, versus 87.7 for the challenge wind rules and 75.1 for keeping the current direction. At one hour, keeping the current direction is slightly better. These scores measure direction, not exact change timing.”

**Keep straight:** Transition hours are excluded from this accuracy score. The stronger corrected-ensemble rule comparison is 93.3%, 88.8% and 89.2% at 1, 6 and 24 hours; include it if asked about baseline strength.

### 10 · 2:51–3:06 · Next-change timing

**Say:** “Direction accuracy does not guarantee exact change timing. The separate event evaluation matches 115 of 193 recorded changes within three hours, with 138 false-alarm clusters. That limits how warnings should be used.”

**Keep straight:** The median lead applies only to matched events. The separate window score is 394 of 750 overlapping change windows within three hours (52.5%); the false-alarm rate is 87 of 593 no-change windows (14.7%). These are different denominators, not independent events.

### 11 · 3:06–3:21 · Runway 18 and certainty

**Say:** “Runway eighteen remains weak: no warnings in twelve positive twenty-four-hour windows. The labels are inferred from weather, not actual closures. Our certainty score is not a calibrated chance of being correct.”

**Keep straight:** The 12 positive windows overlap and are not twelve independent closures. There were 307 complete windows and 1,125 exclusions.

**Certainty:** “The 0–100 score is the smaller probability margin across the direction and runway-18 calls. It is not a calibrated chance that either forecast is correct.”

### 12 · 3:21–3:27 · Next step

**Say:** “Test alongside a shift lead: which warnings change preparation?”

### 13 · 3:27–3:35 · Team

**Say:** “Thank you.”

### 14 · 3:35–3:41 · Model card

**Say:** “The full model card is public on our site. Scan to read it.”

**Show:** QR to `/model-card/`, generated from `MODEL_CARD.md`.

## V6 figures for questions

Stable-hour operating-direction accuracy. All methods use the same scored rows in each lead-time comparison.

| Lead | Model | Official rules | Keep current direction | Corrected-ensemble rules |
|---|---:|---:|---:|---:|
| 1 h | 95.7% | 93.1% | 95.9% | 93.3% |
| 6 h | 92.7% | 88.1% | 88.8% | 88.8% |
| 24 h | 91.8% | 87.7% | 75.1% | 89.2% |
| 48 h | 88.9% | 84.0% | 64.2% | 85.8% |

Twelve expanding monthly folds cover November 2025 through October 2026. Forecast archive availability uses a six-hour publication-lag assumption; exact historical publication times are unavailable. The folds informed feature and model choices, so they are not a final independent validation set.

The certainty score is `100 × min(|2p_OD25−1|, |2p_R18−1|)`. Runway 18 targets are inferred weather usability. Stable-hour accuracy excludes transition hours; next-change event scores use separate half-hour data. See `MODEL_CARD.md` and `web/public/data/quality.json` for definitions and exclusions.

## Do not claim

- That the model has demonstrated day-ahead operational benefit, avoided delays, or financial savings.
- That the 1-hour model beats persistence, or that every lead beats every baseline.
- That 12 positive runway-18 windows are 12 distinct closure events, or that the model warned on any of them.
- That the certainty score is calibrated probability, or that the R18 target records actual operational closure.
- That the challenge-rule diagram describes the full current DFS/FRA operating workflow.
