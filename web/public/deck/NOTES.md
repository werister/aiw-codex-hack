# Presenter notes: finals, 17:00

## Hugo's story-first script and speaker cues

Start with the [speaker cue sheet](presenter-cues.html), then use the [full presentation script](presentation-script.md) for the two-minute story/demo opening, five-minute version and three-minute backup. The script includes source-pinned results, illustrative money assumptions, claim corrections and named rehearsal checks. These are review drafts; reconcile the final timing and figures before presenting.

After deployment, the cue sheet is at `/deck/presenter-cues.html` and the script at `/deck/presentation-script.md`. The notes below match the eleven-slide deck as it is now; where the script differs, these numbers and the money sentence win.

Hugo presents. **3:39 in total**, one page: `/deck/index.html` on the site. Opened from the file, the 3D scene shows as a still and the dashboard as a screenshot; the charts need the site.

Keys: arrow keys, a click or the clicker advance; F full screen; 1 to 9 and 0 jump to slides 1 to 10, End to the last (12); **A toggles autoplay**, which uses the times below. A click inside the dashboard frame works the app; click outside it (or press the clicker) to move on. Charts replay each time you enter their slide.

## 1 · Title · 0:00–0:15
At Frankfurt Airport, the wind alone decides which way aircraft land and take off. We built Lift-off: it tells the airport which way it will fly, hour by hour, 48 hours ahead.

## 2 · 156 direction changes a year · 0:15–0:31
Frankfurt switches its operating direction about 156 times a year, three times a week, and six in ten departures need runway 18, which a strong north wind closes. Watch: an aircraft lands westbound, then the wind turns, the field switches to 07 and runway 18 greys out. Every switch moves staff, transfers and flights, and today that reaction starts when the decision is made.

## 3 · Every hour, 48 hours ahead · 0:31–1:01
This is the live dashboard, running inside the slide. The top line is the planning recommendation; below it the next 48 hours, hour by hour: direction, runway 18, how certain we are, and when the next change is likely.

## 4 · Eight years of flown directions · 1:01–1:21
Every column is a day, every row an hour, eight years of directions actually flown at Frankfurt: blue is west, berry is east. That's what we learn from and what we test against, all public data, independently verified by Kai.

## 5 · How the model decides · 1:21–1:41
This is one real tree from our model, the first three levels in plain words. Its first question is the forecast tailwind on runway 25, averaged over three weather models; its second is what the official rules would say. The model weighs eighty trees like this one for every hour.

## 6 · What we tried, and who checked it · 1:41–1:56
We logged 17 experiments in our own pipeline. Hugo reran the comparison independently in Colab: all 72 metric rows recomputed, and two other models did not beat ours. A red team's leakage tests pass 15 of 15, and Kai hash-checked every raw weather file and rebuilt all 76,588 hours of flown directions exactly.

## 7 · Warned a day ahead · 1:56–2:26
A real day, 28 to 29 October. The line is our model's chance of west, the thin step is the official rules, the strip below is what was actually flown. The switch came at 10:00 on the 29th: with this, the shift lead plans staff and equipment for it a day ahead instead of reacting on the spot.

## 8 · A third fewer mistakes than the rules · 2:26–2:51
Tested on 12 months the model never saw. Six hours ahead we're right 92.8% of the time, against 88.1% for the official rules and 88.8% for keeping today's direction; two days ahead it's 89.2% against 84.0% and 64.2%. The whiskers show the lead holds in every 95% range.

## 9 · Value · 2:51–3:06
Verbatim: "Estimated value: about €0.4M a year at Frankfurt (range €0.13M to €3.2M), plus a similar amount in passengers' time. Based on EUROCONTROL delay costs and published studies of runway direction changes."

## 10 · For the people doing the work · 3:06–3:21
82% of direction changes flagged a day ahead, instead of 28% if you assume nothing changes. About 350 more hours a year planned with the right direction than with the official rules. A day to set rosters, equipment and stands instead of reshuffling on the spot.

## 11 · Next · 3:21–3:29
Next: from one airport's direction to fleet-wide planning.

## 12 · Thank you · 3:29–3:39
Thank you. Hugo, Kai, Luca and Jayden; the 3D airport model and the data verification are Kai's.

## Numbers you can say out loud

All from `web/public/data/quality.json` (12-month walk-forward), `RESULTS.md` and Kai's verification reports. They get a final check at 15:40; the deck re-reads `quality.json` on its own.

| Ahead | Model | 95% range | Official rules | Same as now |
|---|---|---|---|---|
| 6 h | 92.8% | 90.9–94.5 | 88.1% | 88.8% |
| 24 h | 91.7% | 89.7–93.5 | 87.7% | 75.1% |
| 48 h | 89.2% | 87.0–91.2 | 84.0% | 64.2% |

- Lead over the rules: +4.7, +4.0 and +5.2 points at 6, 24 and 48 h; the 95% range never touches zero, and the chance it's luck is below 1 in 1,000.
- 1 h ahead all three tie at about 96%. Say so if asked: in the first hour, keeping the current direction is hard to beat.
- Changes seen 24 h ahead: model 82.1%, rules 80.2%, same as now 28.1%. The rules catch about as many changes; our edge is accuracy and sharper probabilities.
- Timing: 52.5% of changes timed within 3 hours, 12.8% false alarms. When you quote accuracy, give these too (they're under the chart).
- Data: 76,588 hours of flown directions since 2018, rebuilt exactly from 154,752 half-hour records; 46 of 46 raw weather files hash-checked; 144,072 forecast wind values re-checked (Kai's verification).
- FraAlliance's own numbers: 156 changes a year, about 3 a week; 6 of 10 departures on runway 18; westbound about 61% of the time.

Terms, if asked: "direction" = operating direction 25 (west) or 07 (east). "Same as now" = persistence, assuming today's direction holds. "Mistakes" = hours with the wrong direction. "95% range" = confidence interval from resampling whole days. Certainty already uses the spread across three weather models.

## Money

Only this sentence, verbatim (`RESULTS.md`, pitch line 2), and no other euro figure:

"Estimated value: about €0.4M a year at Frankfurt (range €0.13M to €3.2M), plus a similar amount in passengers' time. Based on EUROCONTROL delay costs and published studies of runway direction changes."

## Don't say

- Any comparison with the NASA study (Puranik et al.): its setup is not comparable to ours.
- A euro cost per runway switch, or any euro figure without the full sentence above.
- A runway 18 accuracy figure: its labels are inferred from weather, not recorded.
