# Presenting at 17:00 · for Hugo (presenter) and Luca (backup)

Site: https://fraalliance-runway-forecast.statworx-par-2884.chatgpt.site (Jayden switches sharing on). Locally: `cd web && npm install && npm run build && npx next start`, then open http://localhost:3000.

| Path | What | Owner |
|---|---|---|
| `/deck` | Finals slides (about 9, animated 3D scene, live dashboard inside, numbers read from repo files). Presenter notes: `web/public/deck/NOTES.md` | deck lane |
| `/pitch` | Kai's guided pitch and historical replay | Kai, restyled by the design lane |
| `/` | The dashboard: plain-language forecast, 48 h bar, "For experts" at the bottom | design lane |
| `/widget` | iPad view for apron and ground staff | design lane |

## Words and numbers to use
- **Spoken pitch and demo:** `PITCH.md` and `DEMO_SCRIPT.md`. The demo clicks get updated after the dashboard is final at 15:45.
- **Numbers:** `MODEL_CARD.md`, from `web/public/data/quality.json`. Quote the margins with their 95% ranges, not p-values. On money, use only pitch line 2 of "Economic value (illustrative estimate)" in `RESULTS.md`, word for word.
- **Kai's pitch strategy (German):** `resources/hackathon-pitch-strategy.md`.
- **Backup video if the site fails:** `assets/airport/airport-demo.mp4` (60 s airport scene).

## Hard questions, short answers
- **Runway 18?** Closures are rare (about 0.2% of hours) and have no public record. Our label is inferred from the official 15 kt rule. In 12 test months the model caught 3 of 24 closure events a day ahead, with no false alarms. That is honest but weak. A pilot with DFS wind-sensor data is the fix.
- **Why not just the rules?** On the measured wind, the official rules match what was flown only about 90% of the time. From 6 h ahead the model beats them by 4 to 5 points, and it beats keeping the current direction by up to 25 points.
- **Is the test fair?**
  - Every test month is predicted only from earlier data.
  - Forecasts are used as they were published.
  - The jury command reproduces the backtest exactly.
  - We chose the features on these same months, so today's live forecasts are the clean test.
