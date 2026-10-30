# Lift-off · finals presentation

Hugo presents; Luca is the backup. One fourteen-slide version, **3:41 target duration**, matching the deck's slide times. This is a rehearsal target, not a measured delivery time. The [printable cue sheet](presenter-cues.html) mirrors the spoken text below. No separate two-, three- or five-minute narrative.

Core claim: an hourly runway outlook for ground-handling planning, with measured direction accuracy and explicit limits on change timing and runway 18. Model: **walk-forward-v6**. Figures come from the published [quality artifact](../data/quality.json), not an illustrative savings calculation. The historical example explains the product; the twelve-month evaluation supplies the performance evidence.

## 1 · Title · 0:00–0:15

**Show:** The airport and 48-hour outlook. The horizon is how far the forecast extends, not a guaranteed warning lead.

**Say:** “Lift-off is an hourly runway outlook for ground-handling planning at Frankfurt. It looks forty-eight hours ahead, so teams can examine a possible change before deciding how to prepare.”

## 2 · The planning problem · 0:15–0:31

**Show:** Direction change and ground-handling context. The airport animation illustrates the setting; it is not measured traffic or a delay simulation.

**Say:** “When the operating direction changes, people and equipment need to be coordinated. A shift lead needs to know which configuration to prepare for, when it may change, and how uncertain the forecast is.”

## 3 · The challenge baseline · 0:31–0:46

**Show:** Wind limits and the rule baseline. Describe the challenge comparator, not an audited account of current airport planning.

**Say:** “Our baseline applies the challenge wind limits to forecast weather. We also compare with keeping the current direction. These are reproducible reference methods, not a description of every tool the airport already uses.”

## 4 · The model · 0:46–1:06

**Show:** One tree from the published model. Describe the method without reading every split.

**Say:** “The model combines forecast wind, the challenge rules and recent recorded conditions. It learns patterns with boosted trees and blends direction forecasts with the current state. We compare it with applying the wind rules directly and simply keeping the current direction.”

## 5 · What we built · 1:06–1:31

**Show:** The dashboard inside the slide. Point to issue time, the 48-hour timeline and one selected hour. Keep the prepared `/pitch` tab ready for the historical reveal; do not type an assumed staffing duration.

**Say:** “There are two forecast targets: the operating direction, west or east, and runway-eighteen weather usability. Each hour also has a certainty score, and we show the next likely direction change. These are planning inputs. DFS retains the operating decision.”

## 6 · The data · 1:31–1:51

**Show:** Recorded-direction chart and its source block. Keep source attribution visible.

**Say:** “We combine public recorded directions from DFLD, airport weather observations from IEM, and archived forecasts from Open-Meteo. The direction archive reaches back to 2018; the joined forecast inputs start in 2024. These public records are proxies for operations, not certified movement logs.”

## 7 · How the forecast improved · 1:51–2:01

**Show:** Point to the matched twelve-month comparison. The left pair is the rounded E12 experiment-log result (earlier features versus v5); the separate right score is current v6. The full history link is for questions, outside the timed pitch. These test months informed development.

**Say:** “Better weather inputs raised our logged forty-eight-hour score from 84.9 to 89.2 percent. The current, corrected version scores 88.9 percent.”

## 8 · A historical example · 2:01–2:26

**Show:** 28–29 October chart. For the interactive reveal, use the prepared `/pitch` tab: choose **2026-10-28**, show the hidden outcome, then **Reveal recorded outcome**. Read the current shared-hour counts on screen. Open **Evaluation** and return to slide 9. If the tab switch was not rehearsed, stay with the chart.

**Say:** “This October twenty-eighth reconstruction shows the forecast against the later record. Both methods anticipate a change, but neither gets its timing exactly right. The example explains the product; the separate twelve-month evaluation measures its quality.”

## 9 · The measured result · 2:26–2:51

**Show:** Results at 1, 6 and 24 hours. Point to the 24-hour comparison; the 48-hour extension is secondary.

**Say:** “At twenty-four hours, the model gets the direction right in 91.8 percent of scored hours, versus 87.7 for the challenge wind rules and 75.1 for keeping the current direction. At one hour, keeping the current direction is slightly better. These scores measure direction, not exact change timing.”

## 10 · Change timing · 2:51–3:06

**Show:** Distinct-event result and false-alarm count together. Do not describe the separate change-subset hourly accuracy as event detection.

**Say:** “Direction accuracy does not guarantee exact change timing. The separate event evaluation matches 115 of 193 recorded changes within three hours, with 138 false-alarm clusters. That limits how warnings should be used.”

## 11 · Runway 18 and certainty · 3:06–3:21

**Show:** Zero of twelve positive 24-hour windows; 307 complete windows and 1,125 exclusions. These are overlapping windows, not twelve independent closures.

**Say:** “Runway eighteen remains weak: no warnings in twelve positive twenty-four-hour windows. The labels are inferred from weather, not actual closures. Our certainty score is not a calibrated chance of being correct.”

## 12 · The pilot · 3:21–3:27

**Show:** Next step: frozen forecasts, a shift lead and recorded preparation decisions.

**Say:** “Test alongside a shift lead: which warnings change preparation?”

## 13 · Thank you · 3:27–3:35

**Show:** Team and invitation to questions.

**Say:** “Thank you. We would welcome that operational test.”

## 14 · Model card · 3:35–3:41

**Show:** QR to `/model-card/`, generated from `MODEL_CARD.md`.

**Say:** “The full model card is public on our site. Scan to read it.”

## Exact demo path and fallback

1. Before presenting, serve the same checked build for `/deck/index.html` and `/pitch`. Use manual slide navigation; autoplay is only a timing aid and cannot wait for an interactive demo.
2. In `/pitch`, choose **2026-10-28**. The earliest available date opens by default, so select the case explicitly. Leave the outcome hidden until the demonstration.
3. Point to **Issue time**, **First forecast direction change** and the hourly outlook. Say “historical reconstruction”; archived publication times and initial direction reporting delays are not verified.
4. Click **Reveal recorded outcome**. All methods use the same recorded hours. Read the displayed numerator and denominator; do not carry over the earlier 40-hour subset. The current saved file has 47 recorded hours: model 41/47, rules 39/47, persistence 33/47. Refresh these checks after any forecast regeneration.
5. The first different hourly record is 29 October at 10:00 Europe/Berlin. The previous matching sample is 09:00. An hourly series cannot establish the exact transition instant or rule out temporary changes.
6. Click **Evaluation** or **View evaluation →**, then return to deck slide 9. Separate the individual replay score from the twelve-month scores.
7. If interaction fails, continue with the deck's saved historical chart and results. Do not build, install packages or change the model on stage. The airport video illustrates the setting; it does not replace forecast evidence. Verify the local served deck and its assets before relying on an offline fallback.

## Q&A figures · published v6

Stable-hour operating-direction accuracy; twelve monthly walk-forward folds, November 2025–October 2026. Transition-hour targets are excluded. These evaluation months informed development.

| Lead | Model | Challenge rules, base wind | Keep current direction | Rules, corrected ensemble | Scored rows |
|---|---:|---:|---:|---:|---:|
| 1 h | 95.7% | 93.1% | 95.9% | 93.3% | 1416 |
| 6 h | 92.7% | 88.1% | 88.8% | 88.8% | 1416 |
| 24 h | 91.8% | 87.7% | 75.1% | 89.2% | 1383 |
| 48 h | 88.9% | 84.0% | 64.2% | 85.8% | 1338 |

- **Why not just the rules?** At 24 h the model gains 4.1 percentage points over the base-wind challenge rules, or 2.7 points over the stronger corrected-ensemble rule variant. Persistence is slightly better at 1 h. This does not establish superiority over existing airport decision-support systems.
- **Does it detect changes a day ahead?** The 82.3% change-subset score is target-hour direction accuracy on windows containing a change. It is not event recall. Unique-event recall is 59.6% (115/193), with deduplicated precision 45.5% and 138 false-alarm clusters. The reported 12 h median warning lead applies only to retrospectively matched warnings; it is not the earliest useful warning or a guaranteed preparation time.
- **What about the other timing percentages?** The separate overlapping-window evaluation has 52.5% within ±3 h across 750 change windows and 14.7% false alarms across 593 no-change windows. Those denominators differ from unique-event recall and precision.
- **Is runway 18 solved?** No. At 24 h, zero hits among twelve positive inferred-closure windows, from 307 complete windows; 1,125 windows were excluded. These are overlapping issue windows, not distinct actual closures. Weather usability does not establish an operational opening or clearance.
- **How much money does it save?** Savings have not been measured. A pilot must record forecasts before outcomes, actual preparation decisions, demand, delay causes, false alarms and action costs. Classification accuracy cannot be converted directly into avoided delays or annual savings.
- **Is this a clean final test?** Each monthly fit uses earlier labels, but feature choices and review used the evaluation months. Exact archived weather publication times are unavailable; a six-hour availability proxy does not prove historical availability. Freeze the model before collecting a new prospective test.
- **What does certainty mean?** A combined probability-margin score, not a calibrated probability of correct direction, correct timing or safe runway use.

## Evidence and rehearsal

- [Published quality artifact](../data/quality.json): accuracy, event matching, window metrics and exclusions. [Model card](https://github.com/werister/aiw-codex-hack/blob/main/MODEL_CARD.md): definitions and limitations. Check both against the model version in the deck footer.
- [Challenge brief](https://github.com/werister/aiw-codex-hack/blob/main/frankfurt-airport-operating-direction-forecast.md): both targets and required output. The repository brief is a transcription; do not imply an unavailable original PDF or a verified jury weighting scheme was inspected.
- [DFLD](https://www.dfld.de/Mess/StatWetter.php?R=1): recorded-direction proxy. [IEM](https://mesonet.agron.iastate.edu/request/download.phtml?network=DE__ASOS): EDDF METAR. [Open-Meteo Previous Runs](https://open-meteo.com/en/docs/previous-runs-api): archived forecasts; [live forecast API](https://open-meteo.com/en/docs): current weather inputs. Open-Meteo data are processed into runway features and attributed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Windy is a separate connection test and supplies no forecast, training or evaluation values.
- Hugo or Luca still needs to time a complete spoken rehearsal, including tab changes, and check readability from the audience position. A browser check or word count cannot establish that the jury understands the story.
