# Demo script · 2 minutes · Hugo presents, Luca is backup

**Before you go on:** open the live URL in Chrome, zoom to 110%, and close other tabs. Have `MODEL_CARD.md` open in a second tab. If the venue Wi-Fi fails, run it locally: `cd web && npm install && npm run build && npx next start`, then open http://localhost:3000.

## 0:00 · The recommendation (20 s)
The page opens on the latest forecast.
> "This is what the shift supervisor sees first: one recommendation. Here it says prepare for a switch to 07 East, with the time window and how likely it is. It's a planning aid. DFS still decides."

Point at the issue line under the header: issue time, model version, rules version.

## 0:20 · The three answers (15 s)
> "Below it, three answers you can read from two metres away: the direction now, whether runway 18 is open, and when the next change comes."

## 0:35 · The 48 hours (25 s)
Pick **Wed 28 Oct (hindcast)** in the day picker (top right).
> "This is a past day, forecast exactly as it would have been at midnight, with only what was known then. Each column is one hour. Blue is west, magenta is east, green is runway 18 open. The bottom row is what was actually flown, from DFLD's records. Pale cells mean less sure."

Point at the yellow line: the predicted change, and where the recorded switch happened.

## 1:00 · Why (20 s)
Click the hour just before the change. Then click **Show evidence**.
> "Every forecast can explain itself: the wind for that hour, the tailwind on each runway against its limit, what the official rules say, and what the model says."

## 1:20 · Is it any good? (25 s)
Scroll to **Model quality**.
> "Tested on six months the model never saw. At 6 hours it beats the official rules by 4 points and keep-current by 2. At 24 hours it's 89.6% against 86.3% and 76.3%. When it says 85%, it happens 85% of the time." [update the numbers at 15:30]

## 1:45 · Close (15 s)
Click **iPad widget** (top right).
> "The same answers on an iPad for apron and ground staff. Built today on public data, and ready to pilot next to the shift supervisor."

## If something breaks
- The page is blank: open `/?day=2026-10-28` directly.
- No internet: use the local build above. All forecast files are in `web/public/forecasts/`.
- Asked about runway 18: "Its closures are rare, about 0.2% of hours, and there is no public record of weather closures, so its label is inferred from the official 15 kt rule. That's what a pilot with DFS data would fix."
