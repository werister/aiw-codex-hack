# Presenter notes: finals, 17:00

## Hugo’s story-first script and speaker cues

Start with the [speaker cue sheet](presenter-cues.html), then use the [full presentation script](presentation-script.md) for the two-minute story/demo opening, five-minute version and three-minute backup. The script includes source-pinned results, illustrative money assumptions, claim corrections and named rehearsal checks. These are review drafts; reconcile the final timing and figures before presenting.

After deployment, the cue sheet is at `/deck/presenter-cues.html` and the script at `/deck/presentation-script.md`. The original seven-slide notes below are preserved for comparison.

Hugo presents. About 3 minutes in total. Advance with the arrow keys, a click or the clicker; press F for full screen. Keys 1 to 7 jump to a slide.

## 1 · Title (15 s)
At Frankfurt, the wind alone decides which way aircraft land and take off. We built Liftoff. It tells the airport which way it will be flying, hour by hour, 48 hours ahead.

## 2 · The problem (25 s)
Frankfurt switches its operating direction about 156 times a year, three times a week. Six in ten departures use runway 18, and a strong north wind closes it. Every switch moves ground staff, puts transfers at risk and causes delays, and today that reaction only starts when the decision is made.

## 3 · What we built (30 s)
For every hour of the next 48, Liftoff gives the operating direction, whether runway 18 is usable, how certain we are, and when the next change is likely. Watch the scene: the wind turns to the north-east, the airport switches to 07, and runway 18 greys out because its tailwind passes 15 knots. That's the moment we predict, a day or two ahead.

## 4 · Live demo (45 s)
Click "Open the forecast" and follow `DEMO_SCRIPT.md`. Show the next 48 hours, the next change with its certainty, then the widget view for a tablet in the tower or on the apron.

## 5 · Results (35 s)
We tested month by month on 12 months the model never trained on, against the official rules and against keeping the current direction. Six hours ahead we're right 92.8% of the time, against 88.1% for the rules and 88.8% for keeping the current direction. Forty-eight hours ahead it's 89.2% against 84.0% and 64.2%, and the lead over the rules stays positive within the 95% confidence interval at 6, 24 and 48 hours. Then, verbatim: "Frankfurt changes operating direction about 156 times a year. 24 hours ahead, our model anticipates 82% of those changes, against 28% if you assume today's direction holds."

## 6 · How it works (20 s)
Only public data: EDDF weather reports, archived forecasts from three weather models, and the operating directions DFLD recorded. Every test month is predicted by a model trained only on earlier months, using forecasts as they were available at the time. We built it with Codex.

## 7 · What's next (15 s)
Next we want to test the spread of the DWD's ICON-D2 ensemble as a certainty feature, and take this to fleet-wide planning. Thank you.

## Numbers you can say out loud

All from `web/public/data/quality.json` (main, 12-month walk-forward). They get a final check at 15:40; if they change, the deck picks them up on its own and this list is updated.

| Lead | Model | Official rules | Same as now | Model 95% CI | Lead over rules, 95% CI |
|---|---|---|---|---|---|
| 6 h | 92.8% | 88.1% | 88.8% | 90.9–94.5 | +4.7 pts (+2.9 to +6.4) |
| 24 h | 91.7% | 87.7% | 75.1% | 89.7–93.5 | +4.0 pts (+2.4 to +5.6) |
| 48 h | 89.2% | 84.0% | 64.2% | 87.0–91.2 | +5.2 pts (+3.2 to +7.1) |

- 1 h ahead: 96.0% against 95.9% for both baselines. No real difference: in the first hour, keeping the current direction is hard to beat. Say so if asked.
- Direction changes seen 24 h ahead: model 82.1%, official rules 80.2%, same as now 28.1%. The rules catch about as many changes; our edge is accuracy and sharper probabilities.
- Timing: 52.5% of changes timed within 3 hours, with 12.8% false alarms in quiet windows. Whenever you quote accuracy, give these two as well.
- FraAlliance's own numbers (from their pitch): 156 changes a year, about 3 a week; 6 of 10 departures on runway 18; westbound about 61% of the time.

## Money, only if asked

The deck shows no money. If the jury asks, say this sentence verbatim and nothing else (from `RESULTS.md`, "Economic value"):

"Using EUROCONTROL's public delay costs and stated assumptions, that is worth an illustrative €0.1M a year against the official rules and €0.6M against no forecast, in central scenarios. This is an estimate, not a measured FRA saving."

Optional follow-up, also verbatim: "Compared with the official rules, it catches about as many changes, but its probabilities are about half as wrong. That means fewer hours planned for the wrong direction, and FraAlliance data would let us measure the real saving."

## Don't say

- Any comparison with the NASA study (Puranik et al.): its setup is not comparable to ours.
- A euro cost per runway switch, or a euro range without the full sentence above.
- That ensemble spread already drives the certainty score: it is a next step, a candidate feature.
- A runway 18 accuracy figure: its labels are inferred from weather, not recorded.
