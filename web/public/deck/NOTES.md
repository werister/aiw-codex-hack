# Presenter notes: finals, 17:00

## Hugo's story-first script and speaker cues

Start with the [speaker cue sheet](presenter-cues.html), then use the [full presentation script](presentation-script.md) for the two-minute story/demo opening, five-minute version and three-minute backup. The script includes source-pinned results, illustrative money assumptions, claim corrections and named rehearsal checks. These are review drafts; reconcile the final timing and figures before presenting.

After deployment, the cue sheet is at `/deck/presenter-cues.html` and the script at `/deck/presentation-script.md`. The notes below match the nine-slide deck as it is now.

Hugo presents. **3:40 in total**, one page: `/deck/index.html` on the site, or open `web/public/deck/index.html` from the file (the scene then shows as a still, and the dashboard and replay as screenshots).

Keys: arrow keys, a click or the clicker advance; F full screen; 1 to 9 jump to a slide; **A toggles autoplay**, which uses the times below. A click inside the dashboard or replay frame works the app; click outside the frame (or press the clicker) to move on.

## 1 · Title · 0:00–0:15
At Frankfurt, the wind alone decides which way aircraft land and take off. We built Liftoff: it tells the airport which way it will fly, hour by hour, 48 hours ahead.

## 2 · The problem · 0:15–0:35
Frankfurt switches its operating direction about 156 times a year, three times a week, and six in ten departures use runway 18, which a strong north wind closes. Every switch moves ground staff, puts transfers at risk and shifts flights, and today that reaction starts when the decision is made.

## 3 · What we built · 0:35–1:00
For every hour of the next 48, Liftoff gives the direction, whether runway 18 is usable, how certain we are, and when the next change is likely. Watch the scene: the wind turns north-east, the airport flips to 07, and runway 18 greys out because its tailwind passes 15 knots. That's the moment we predict, a day or two ahead.

## 4 · Live dashboard · 1:00–1:35
This is the live dashboard, running inside the slide. The top line is the planning recommendation; below it the next 48 hours, hour by hour: direction, runway 18, certainty. Click an hour if there's time; otherwise just point at the next change.

## 5 · Replay · 1:35–2:05
To show it works, we replay a past day: first the forecast as it was issued, then what was actually flown. Click through the replay inside the frame.

## 6 · What we did · 2:05–2:25
Only public data: 76,588 hours of flown directions since 2018, 1,681 direction changes, archived forecasts from three weather models. We tested on 12 months the model never saw, ran 17 experiments, and Kai verified the data independently, down to hash-checking every raw weather file. We built it with Codex.

## 7 · How good is it · 2:25–3:00
Two days ahead, we get nine hours in ten right. That's about a third fewer mistakes than the official rules, and three times fewer than assuming today's direction holds, and the chance that this is luck is below one in a thousand. Then, verbatim: "Frankfurt changes operating direction about 156 times a year. 24 hours ahead, our model anticipates 82% of those changes, against 28% if you assume today's direction holds."

## 8 · Value · 3:00–3:20
Verbatim: "On EUROCONTROL unit costs that is worth an illustrative €0.13M to €3.2M a year at FRA, about €0.4M in our central case, plus a similar amount in passengers' time. These are estimates, not measured FRA savings."

## 9 · What's next · 3:20–3:40
Next, we want to test ensemble spread from the DWD's ICON-D2 model as a certainty feature, and take this to fleet-wide planning. Thank you.

## Numbers you can say out loud

All from `web/public/data/quality.json` (12-month walk-forward) and Kai's verification reports. They get a final check at 15:40; the deck re-reads `quality.json` on its own.

| Ahead | Model | 95% range | Official rules | Same as now |
|---|---|---|---|---|
| 6 h | 92.8% | 90.9–94.5 | 88.1% | 88.8% |
| 24 h | 91.7% | 89.7–93.5 | 87.7% | 75.1% |
| 48 h | 89.2% | 87.0–91.2 | 84.0% | 64.2% |

- Lead over the rules: +4.7, +4.0 and +5.2 points at 6, 24 and 48 h; the 95% range never touches zero.
- 1 h ahead all three tie at about 96%. Say so if asked: in the first hour, keeping the current direction is hard to beat.
- Changes seen 24 h ahead: model 82.1%, rules 80.2%, same as now 28.1%. The rules catch about as many changes; our edge is accuracy and sharper probabilities.
- Timing: 52.5% of changes timed within 3 hours, 12.8% false alarms. When you quote accuracy, give these too.
- FraAlliance's own numbers: 156 changes a year, about 3 a week; 6 of 10 departures on runway 18; westbound about 61% of the time.

Terms, if asked: "direction" = operating direction 25 (west) or 07 (east). "Same as now" = persistence, assuming today's direction holds. "Mistakes" = hours with the wrong direction. "95% range" = confidence interval from resampling whole days.

## Don't say

- Any comparison with the NASA study (Puranik et al.): its setup is not comparable to ours.
- A euro cost per runway switch, or any euro figure without the full sentence above.
- That ensemble spread already drives the certainty score: it is a next step, a candidate feature.
- A runway 18 accuracy figure: its labels are inferred from weather, not recorded.
