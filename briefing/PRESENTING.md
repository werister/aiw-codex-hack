# Presenting · Hugo, with Luca as backup

Use one **2:46 target** story: planning problem → baseline and model → forecast demonstration → data and development history → aggregate evidence → future planning extension → model card. The duration needs a timed human rehearsal.

- **Slides:** `/deck/index.html`.
- **Canonical spoken text and exact demo clicks:** [presentation-script.md](../web/public/deck/presentation-script.md).
- **Printable cue sheet:** `/deck/presenter-cues.html`.
- **Full model history for questions:** `/deck/history.html` (versions, all logged experiments, external reruns and the three latest rejected candidates).
- **Historical reveal and separate evaluation:** `/pitch`. Select **2026-10-28** explicitly; the earliest published date opens by default.
- **Dashboard / iPad view:** `/` and `/widget`, optional during questions.

Team site: https://fraalliance-runway-forecast.statworx-par-2884.chatgpt.site. Verify access and the deployed model version before presenting; local validation does not verify this deployment. Prepare and check a local served build in advance if an offline fallback is needed. Do not install or rebuild on stage.

## What to emphasize

An hourly runway outlook for ground-handling planning. The challenge has two targets: operating direction and runway-18 weather usability. The measured strength is direction accuracy; operational benefit is the next test, not an established saving.

At 24 h, published v6 direction accuracy is **91.8%**, versus **87.7%** for the base-wind challenge rules, **75.1%** for keeping the current direction, and **89.2%** for the stronger corrected-ensemble rule variant. The twelve monthly folds informed development, so they are not an untouched final validation set.

The October 28 replay illustrates behavior. It is a historical reconstruction with availability limitations, not evidence of a forecast actually issued on that date. Reveal the recorded outcome, read the displayed shared-hour counts, then open **Evaluation** for the separate overall result.

The development-history slide separates the logged, matched twelve-month feature gain (**84.9% → 89.2% at 48 h; +4.3 percentage points**, earlier features versus v5) from current v6 (**88.9%**). The earlier pair is rounded evidence from `EXPERIMENTS.md`, not a newly replayed before/after run. v6 improves state handling and evaluation; it did not produce a broad accuracy jump. Keep the complete history appendix for questions.

## Limits to keep ready for questions

- **Change timing:** 115/193 unique recorded transitions matched within ±3 h, with 138 false-alarm clusters. The 82.3% change-subset hourly score is not event recall.
- **Runway 18:** zero hits in twelve positive inferred-closure windows at 24 h; 307 complete windows, 1,125 excluded. These are overlapping windows, not twelve independent closures. Actual runway openings and closures are not recorded labels here.
- **Certainty:** a probability-margin score, not a calibrated chance of a correct forecast.
- **Value:** no measured savings claim. Fleet-wide planning is a future extension. Any operational pilot should log which warnings change preparation and the costs of false alarms and action.

## Before going on stage

1. Check the deck, chart data, `/pitch` forecast and quality artifact all show the intended model version. Refresh the deck data and speaker figures together after a model update.
2. Prepare October 28 with its outcome hidden. Use manual deck navigation; autoplay cannot wait for clicks in the demo.
3. Keep the historical replay for questions: rehearse forecast → reveal → evaluation → slide 8. The main deck goes directly from development history to aggregate results.
4. Time the full delivery and check audience readability. Keep the original data-source links visible. The airport animation illustrates the setting; it is not observed traffic or a forecast accuracy fallback.

[Model card](../MODEL_CARD.md) and [quality.json](../web/public/data/quality.json) contain full definitions and exclusions. The [companion script](../web/public/deck/presentation-script.md) contains short answers to the likely jury questions.
