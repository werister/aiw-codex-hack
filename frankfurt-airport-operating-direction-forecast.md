# Frankfurt Airport Operating Direction Forecast

**Venue:** AI Week 2026, Frankfurt  
**Date:** 30 October 2026  
**Format:** One day, approximately six hours of build time

## Challenge

Build a machine-learning model that forecasts:

1. Whether departures are possible from Runway 18.
2. Which airport-wide operating direction is in use: 25 or 07.

At Frankfurt Airport, wind drives changes in operating direction. Strong northerly winds can close Runway 18, which is used only for departures.

## Runway system

- **07L/25R (northwest)** and **07R/25L (south)** are primarily landing runways.
- **07C/25C (centre)** is a departure runway.
- **Runway 18 (west)** is used for departures to the south.
- The 07/25 runways can operate in either direction, but direction is airport-wide: all switch together, and mixed directions are not used.
- **OD 25** means operations toward 250°T; **OD 07** means operations toward 070°T.
- Runway 18 departures are toward 180°T and can be used in either operating direction.

## Decision rules

### Wind and runway limits

- Only the wind component directly from behind counts as tailwind.
- Tailwind must remain below **15 kt for departures** and below **10 kt for landings**.
- Crosswinds above **40 kt**, including gusts, close the runway.
- Example: with 20 kt wind, a direction 30° off straight behind gives about 17.3 kt tailwind and is not permitted; 45° off gives about 14.1 kt and is permitted.

### Operating direction (07/25)

- Headwind is preferred.
- Landings determine the operating direction.
- A tailwind component of **10 kt or more** on the landing runways requires an immediate direction change.
- A smaller tailwind (under 10 kt) may be accepted for up to 30 minutes to avoid frequent changes. If it persists longer, the direction switches to the headwind direction.
- Example: wind from 090° at 20 kt gives about 19 kt tailwind on direction 25, so operations use OD 07.

### Runway 18

- Runway 18 is for departures only, toward the south.
- Tailwind of **15 kt or more** (wind from the north) closes it. Departures then use only the centre runway (07C/25C).
- Example: wind from 330° at 20 kt gives about 17.3 kt tailwind, so Runway 18 is closed.

## Deliverables

1. **Forecast model:** For each hour up to 48 hours ahead, predict the probability that Runway 18 is usable and the operating direction (25 or 07), with a certainty score and the next likely change time. The rules above are a baseline; teams are expected to improve on them.
2. **Self-sourced data:** Find and combine suitable public data. No dataset is provided. Possible sources include EDDF METAR, weather-model forecasts, and historical operating directions. Cite every source.
3. **Model evaluation:** Test on data not used for training, using only information available at each forecast time. Report quality at 1, 6, and 24 hours ahead.
4. **Submission:** Provide a code repository, a one-page model card (data sources, model quality, and key forecast drivers), and forecasts for the jury test days. The forecasts will be compared with the operating directions actually flown.

*Source: FraAlliance, “AI Week 2026 Hackathon — Frankfurt Airport Operating Direction Forecast” (PDF provided for this task).*
