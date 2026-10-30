# Pitch — Lift-off · FraAlliance challenge

## Short pitch

“The FraAlliance challenge asks for an hourly, 48-hour forecast of Frankfurt’s operating direction and runway-18 weather usability, plus a certainty score and the next likely direction change. Lift-off returns those four outputs for each hour. The horizon is forecast range, not a guaranteed warning lead. It uses DFLD’s recorded direction archive, EDDF METAR and archived ECMWF, GFS and ICON forecasts.

“We compare the v6 direction forecast with the official challenge rules and with keeping the current direction, across 12 expanding monthly folds. On stable-hour targets, accuracy is 92.7% at six hours and 91.8% at 24 hours, versus 88.1% and 87.7% for the rules. At one hour, persistence is slightly higher than the model: 95.9% versus 95.7%. These folds informed model choices, and the six-hour forecast publication lag is an assumption, so the result needs prospective validation.

“Next-change timing is a separate task: 115 of 193 distinct recorded transitions were matched within three hours. Deduplicated precision was 45.5%, with 138 false-warning clusters. Runway-18 targets are inferred from weather; at 24 hours the model warned on none of 12 positive issue windows. The next step is to test alongside a shift lead: which warnings change preparation?”

## Direction accuracy

Stable-hour operating-direction accuracy; each method is scored on the same rows at each lead. Transition-hour targets are excluded.

| Lead | Model | Official rules | Keep current direction | Corrected-ensemble rules |
|---|---:|---:|---:|---:|
| 1 h | 95.7% | 93.1% | 95.9% | 93.3% |
| 6 h | 92.7% | 88.1% | 88.8% | 88.8% |
| 24 h | 91.8% | 87.7% | 75.1% | 89.2% |
| 48 h | 88.9% | 84.0% | 64.2% | 85.8% |

The 12 monthly folds run from November 2025 through October 2026. Each fold trains on earlier data. Feature and model choices were reviewed on these same folds, so they are not an untouched final validation set. Archived weather uses a six-hour publication-lag proxy; exact historical publication times are unavailable.

## Separate challenge outputs

- **Next direction change:** 115/193 distinct recorded transitions matched within ±3 h (59.6%); matched-event median warning lead 12 h; deduplicated precision 45.5%; 138 false-warning clusters. These are event-level results.
- **Window-level timing:** 394/750 overlapping change windows matched within ±3 h (52.5%); 87/593 no-change windows were false alarms (14.7%). Do not combine these window counts with the distinct-event metric.
- **Runway 18:** inferred weather-usability labels, not observed operational closures. At 24 h: 0/12 positive issue windows warned, with 307 complete windows and 1,125 unknown or incomplete windows excluded. Positive issue windows overlap; they are not unique closure events.
- **Certainty:** a 0–100 margin score from the smaller probability margin across the direction and runway-18 calls. It is not a calibrated probability of being correct.

## Claim boundaries

- Call the rule tree the **official challenge-rule baseline**, not a complete model of the current DFS/FRA control-room workflow.
- Say the DFLD series is a recorded operating-direction proxy, not a certified movement log. Runway-18 usability is inferred from weather.
- Do not claim a demonstrated day-ahead operational benefit, avoided delay, financial savings, or fleet-wide capability.
- Do not say the model beats persistence at one hour or beats every baseline at every lead.
- Explain that fold choices and the assumed six-hour publication lag limit how strongly the retrospective results support deployment.

If asked about the next step: freeze and timestamp forecasts before outcomes; record which warnings changed preparation; measure false alarms and the cost of acting.

Evidence and definitions: `MODEL_CARD.md`, `web/public/data/quality.json`, `ml/rules.json`, and the official FraAlliance brief.
