# Live demo · 60 to 90 seconds inside the finals talk

The talk itself runs on the slides at `/deck/` (script and timings: `web/public/deck/NOTES.md`). This is only the live part, on the dashboard at `/`.

**Before you go on:**
- Open the site in Chrome and zoom to 110%.
- Have `/deck/` in a second tab.
- If the venue Wi-Fi fails, run it locally: `python -m http.server 8000 -d web/public` gives the slides, or `cd web && npm install && npm run build && npx next start` gives the full app.
- Backup video: `assets/airport/previews/airport-demo.mp4`.

## 1 · Today (20 s)
The page opens on the latest forecast.
> "This is what someone in the tower sees. One sentence: which way planes are landing right now and how sure we are. Below it, whether runway 18 is open, and when the next change is likely."

Point at the 3D airport: the arrows show arrivals and departures in the forecast direction.

## 2 · A real past day (30 s)
Top right, open the day picker and choose **Wed 28 Oct (past day)**.
> "This is a day that already happened, forecast at midnight with only what we knew then. The bar shows the next two days: blue is west, magenta is east. The change to east came early the next morning, and the forecast saw it coming, at 51%. It said it wasn't sure, and when it isn't sure, it tells you."

Click **Replay** on the 3D view to show the switch.

## 3 · How good is it (20 s)
Scroll down to the large numbers.
> "Tested on twelve months it never saw. From six hours ahead it beats FraAlliance's own rules by four to five points, and keeping the current direction by up to twenty-five."

## 4 · For the experts, if asked (10 s)
Open **For experts** at the bottom: the inputs for any hour, the official rules next to the model, and the held-out test results.

## If something breaks
- **Blank page:** reload, or open `/?day=2026-10-28`.
- **No internet:** use the local options above. Every forecast file is in `web/public/forecasts/`.
- **"What about runway 18?":** "It closes in about 0.2% of hours, and there's no public record of closures. With public data it isn't predictable beyond keeping the current state, and we say so on the model card. A pilot with DFS wind-sensor data is the next step."
