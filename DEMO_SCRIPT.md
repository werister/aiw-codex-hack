# Demo script — Lift-off · 3:35

Hugo presents; Luca is the backup. This run follows the 13-slide deck and its 215-second timing. Use manual navigation during the interactive reveal; autoplay cannot wait for a tab change.

## Before the demo

- Serve the same checked build for `/deck/index.html` and `/pitch`. Keep the prepared `/pitch` tab ready at **2026-10-28**.
- Confirm the dashboard frame and media load. Use the visible page values; do not memorise a recommendation or warning time.
- Keep the 2026-10-28 recorded outcome hidden until slide 8. If the tab switch or reveal is not rehearsed, stay with the deck’s historical chart.
- The airport animation illustrates the setting; it is not a traffic or delay simulation.

## Slide-by-slide

### 1 · 0:00–0:15 · Title

**Say:** “Lift-off is an hourly runway outlook for ground-handling planning at Frankfurt. It looks forty-eight hours ahead, so teams can examine a possible change before deciding how to prepare.”

**Show:** Airport view and 48-hour horizon. The horizon is forecast range, not a guaranteed warning lead.

### 2 · 0:15–0:31 · Planning problem

**Say:** “When the operating direction changes, people and equipment need to be coordinated. A shift lead needs to know which configuration to prepare for, when it may change, and how uncertain the forecast is.”

**Show:** Ground-handling context. Describe what the challenge asks the forecast to support; do not claim measured traffic impact.

### 3 · 0:31–0:46 · Challenge baseline

**Say:** “Our baseline applies the challenge wind limits to forecast weather. We also compare with keeping the current direction. These are reproducible reference methods, not a description of every tool the airport already uses.”

**Show:** Official challenge rule tree and persistence caption.

### 4 · 0:46–1:06 · Model

**Say:** “The model combines forecast wind, the challenge rules and recent recorded conditions. It learns patterns with boosted trees and blends direction forecasts with the current state. We compare it with applying the wind rules directly and simply keeping the current direction.”

**Show:** One tree from the real model; let the first branches make the explanation.

### 5 · 1:06–1:31 · What we built

**Say:** “There are two forecast targets: the operating direction, west or east, and runway-eighteen weather usability. Each hour also has a certainty score, and we show the next likely direction change. These are planning inputs. DFS retains the operating decision.”

**Show:** Issue time, 48-hour timeline and one selected hour. Point to all four outputs. If the embedded app is a fallback image, call it a screenshot.

### 6 · 1:31–1:51 · Data

**Say:** “We combine public recorded directions from DFLD, airport weather observations from IEM, and archived forecasts from Open-Meteo. The direction archive reaches back to 2018; the joined forecast inputs start in 2024. These public records are proxies for operations, not certified movement logs.”

**Show:** Direction chart and source attribution.

### 7 · 1:51–2:01 · How we tested it

**Say:** “We test on successive months, training each model on earlier data. Those months also informed development; a frozen prospective test is still needed.”

**Show:** 12 monthly folds, three weather-model inputs, two baselines and 1-, 6- and 24-hour scores. Do not reuse older audit counts as v6 results.

### 8 · 2:01–2:26 · Historical example

**Say:** “This October twenty-eighth reconstruction shows the forecast against the later record. Both methods anticipate a change, but neither gets its timing exactly right. The example explains the product; the separate twelve-month evaluation measures its quality.”

**Show:** The 28–29 October chart. For the interactive reveal, switch to the prepared `/pitch` tab, choose **2026-10-28**, show the hidden outcome, then click **Reveal recorded outcome**. Read the current shared-hour counts on screen. If the switch was not rehearsed, stay with the chart.

**Keep straight:** The current saved file has 47 recorded hours: model 41/47, rules 39/47, persistence 33/47. Refresh these figures after any forecast regeneration. The first different hourly record is 29 October at 10:00 Europe/Berlin; the previous matching sample is 09:00. Hourly data cannot establish the exact transition instant or rule out temporary changes. Do not carry over the earlier 40-hour subset.

### 9 · 2:26–2:51 · Measured result

**Say:** “At twenty-four hours, the model gets the direction right in 91.8 percent of scored hours, versus 87.7 for the challenge wind rules and 75.1 for keeping the current direction. At one hour, keeping the current direction is slightly better. These scores measure direction, not exact change timing.”

**Show:** Results at 1, 6 and 24 hours. Keep the 48-hour extension secondary. Stable-hour accuracy excludes transition-hour targets; these twelve folds also informed model choices.

### 10 · 2:51–3:06 · Change timing

**Say:** “Direction accuracy does not guarantee exact change timing. The separate event evaluation matches 115 of 193 recorded changes within three hours, with 138 false-alarm clusters. That limits how warnings should be used.”

**Show:** Distinct-event result and false-alarm count together. The event match is not the separate overlapping-window score.

### 11 · 3:06–3:21 · Runway 18 and certainty

**Say:** “Runway eighteen remains weak: no warnings in twelve positive twenty-four-hour windows. The labels are inferred from weather, not actual closures. Our certainty score is not a calibrated chance of being correct.”

**Show:** 0/12 positive 24-hour windows; 307 complete and 1,125 excluded. These positive windows overlap. The 0–100 certainty score is the smaller probability margin across the direction and runway-18 calls.

### 12 · 3:21–3:27 · The pilot

**Say:** “Test alongside a shift lead: which warnings change preparation?”

### 13 · 3:27–3:35 · Thank you

**Say:** “Thank you. We would welcome that operational test.”

## Follow-up, if asked

A prospective evaluation should freeze and timestamp forecasts before outcomes, record which warnings changed preparation, and measure false alarms and the cost of acting. That validation is proposed work; it is not a capability or benefit demonstrated by this prototype.

## Sources and checks

Use `web/public/data/quality.json` and `MODEL_CARD.md` for v6 definitions and denominators. For the case replay, read the numerator and denominator displayed by the prepared app after revealing the recorded outcome. The six-hour publication lag used for archived forecasts is an assumption; exact historical availability is unknown.
