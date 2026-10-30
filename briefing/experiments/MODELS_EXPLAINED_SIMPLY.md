# Our runway experiments, explained simply

Imagine a computer trying to guess which runway direction the airport will use. We give it clues, ask for its answer before the outcome is known, then compare its answer with the recorded direction.

## What the names mean

| Name | Simple explanation | What happened |
|---|---|---|
| v4 | Our earlier contestant, using 25 clues. It also considers keeping the current direction. | It was the reference in our first Colab test. |
| Extra Trees | A different contestant, given the same clues. | It scored lower accuracy than v4 at every reported lead. |
| v4 + Extra Trees, 50/50 | Let the two contestants share an answer by averaging their probabilities. | It did not improve accuracy over v4. |
| v5 | The original model family gets 45 clues, including more weather forecasts and air pressure. | The team adopted this feature set. We also refitted it as the reference for our supplemental-data test. |
| v5 + raw ICON | Give v5 seven additional clues from another weather forecast dataset. | Small longer-lead probability-score improvements, but worse at 6 hours. No replacement justified. |
| v5/ICON, 50/50 | Average the two forecasts. | Mixed results; no convincing overall improvement. |
| Scenario selector | A referee chooses v5 or the ICON candidate according to horizon and weather regime, using older validation results. | It did not consistently beat choosing one global model. |
| v6 | Keep the model family, improve how it remembers current wind conditions, checks information timing, blends runway-18 probabilities and counts mistakes. | Current team model. Our independent Colab suite passed 103 tests; fresh prediction checks are being recorded separately. |

**Not promoted** means we saved the experiment but did not replace the main model with it. We do not erase an experiment just because it did not win.

## How the contest stays fair

For a January exam, the model can study only data available before January. We keep the same scored hours for the contestants we compare. We cannot give one contestant easier hours, or let it read the answer first.

Weather archives do not always tell us exactly when a forecast became available. Our 6-hour and 12-hour buffers are assumptions we test, not proof of historical release times.

The twelve-month team report and our October-only experiment are different exams. A higher percentage on one does not prove superiority on the other. The January, April and July extension checks different seasons, but those months were already used during development: they are not a new untouched final exam.

## Reading the numbers

- **Accuracy:** out of 100 scored hours, how often was the chosen direction right?
- **Probability / Brier score:** if the model says “80% chance,” was that confidence sensible? Lower Brier is better. A confident wrong answer is penalized heavily.
- **Change detection:** did it notice that the direction would switch?
- **Timing:** how close was its predicted switch time?
- **False alarm:** did it warn of a change or closure that did not happen?
- **103 passing software tests:** 103 checks of software behavior passed. This does not mean 103 correct runway forecasts.

For runway 18, “almost always correct” can be misleading. If unsuitable weather is rare, a model that always says “usable” can look excellent while missing every difficult event. Our closure labels are inferred from weather, not confirmed operational closure records.

## What we can honestly say

We tested a different learner, simple averaging, additional weather information and a case-by-case selector. None of our completed alternatives earned a general replacement claim. v6 is the team's current choice, not a proven winner in every situation.

The older October v4 test scored 94.29%, 81.31%, 75.70% and 72.90% at 1, 6, 24 and 48 hours. The current v6 team report scores 95.7%, 92.7%, 91.8% and 88.9% over twelve historical months. **Do not present that difference as our measured v4-to-v6 gain:** the evaluation populations differ.

## Where the evidence lives

- [Timeline and detailed explanation](REDTEAM_TIMELINE.md)
- [Version results CSV](MODEL_VERSION_RESULTS.csv): accuracy is stored as a fraction, so 0.92 means 92%.
- [Completed ICON/selector findings](COLAB_ICON_FIRST_FINDINGS.md)
- [Comparison chart](v5-icon/colab_comparison.svg)
- [Executed Colab cells and outputs](v5-icon/executed-evidence.ipynb)
- [New v6 protocol](v6-colab/experiment_v6.py): freshly refit October, never test October using final weights trained through October.
- [Team model card](../../MODEL_CARD.md)

Recorded 30 October 2026. New v6 and seasonal outputs must be marked complete only after the runs finish and the result files are checked.
