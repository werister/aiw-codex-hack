# OUR CHALLENGE: FraAlliance runway forecast

**This is the challenge our team is building for today.** The other two cases, KfW IPEX-Bank process intelligence and Condor complaint handling, are not ours. Condor is only our plan B.

Source: FraAlliance's pitch at the kick-off on 30 Oct 2026, transcribed from a recording. The official one-pager and slides are on the **team dashboard**. Download them and treat the one-pager as the source of truth for the rules.

## What FraAlliance wants from us, exactly

1. **A machine learning model, not just a rule lookup.** In their words: "build a machine learning model that forecasts 48 hours ahead".
2. **Two predictions, for the next 48 hours:**
   - **A. Runway 18 closed for departures?** (yes/no). This is their first task.
   - **B. Will the operating direction change?** BR25 west vs BR07 east. This is their second task.
3. **Input: open source data only.** Wind and weather forecasts plus the historical operating direction. "You can use all data available open source."
4. **The labels follow their rule set.** The one-pager defines the tailwind limits for runway 18 and when the direction is changed. Our model has to reproduce **their** rules, not physics we invent.
5. **The value is planning ahead:**
   - repositioning ground handling staff and equipment in time
   - protecting transfer passengers' connections
   - fewer reschedules and delays for all airport partners

**What we show at 17:00:**
- the live 48 h forecast for FRA, starting from now
- a backtest that proves accuracy against persistence ("same as now") and against the plain rule-on-forecast baseline
- the ops view: what changes, when, and how sure we are

## WAITING FOR: the FraAlliance slides and one-pager

werister commits them to this repo. As soon as they land:
- Copy the **exact thresholds** into the "Rules" section below: tailwind limit for 18, crosswind and tailwind limits for 07/25, any hysteresis or minimum duration, and gust handling.
- Check everything above against them. If anything differs, **the slides win**.

## The task

FraAlliance is a joint venture of Lufthansa and Fraport. They want a model that forecasts **48 hours ahead**:

1. **The operating direction.** Do aircraft take off and land **westbound (BR25)** or **eastbound (BR07)**? Only the wind decides this, not pilots, flight planning or ground handling.
2. **Runway 18 (Startbahn West).** Is it **open or closed for departures**? Runway 18 only takes departures to the south. When the wind comes from the north and is too strong, departing aircraft would have a tailwind, so 18 closes. Aircraft can only take off against the wind.

In their words: first, find out when 18 will be closed. Second, find out when the wind direction will change.

## Why it matters

When the direction changes or 18 closes, everybody has to react:
- Ground handling staff and equipment get repositioned.
- Transfer passengers may miss their connections.
- Flights are rescheduled and delayed.

Knowing 48 h in advance lets the airport and its partners plan instead of react.

## Numbers from the pitch

- 63 million passengers a year at FRA
- 460,000 aircraft movements a year, about 1,260 a day
- capacity of up to **110 movements in the peak hour**
- 4 runways: three parallel east and west (07L/25R, 07C/25C, 07R/25L) and 18 to the south
- **6 out of 10 departures use runway 18**
- **156 operating direction changes a year**, about 3 a week
- westbound operation about **61%** of the time, eastbound the rest

## Rules and data

- The **exact rule set** is in the one-pager on the team dashboard: tailwind limits, when the direction changes, and when 18 closes. It defines our labels.
- **All open source data is allowed.** That includes wind and weather, and the historical operating direction.
- FraAlliance people are on the floor all day for scope questions.

## Data leads (to verify, not confirmed)

- **Weather forecasts:**
  - Open-Meteo **Historical Forecast API** has archived past model forecasts. It's ideal for an honest 48 h backtest.
  - Open-Meteo **Historical Weather API** and the **Forecast API** (ICON, ECMWF) give the live 48 h.
- **Observed wind at EDDF:** the METAR and TAF archive from Iowa Environmental Mesonet (IEM ASOS download), or ogimet.
- **Historical operating direction:** possibly from:
  - Fraport and the UNH (Umwelt und Nachbarschaftshaus) statistics, plus a public operating direction forecast if one exists. That would be a good benchmark.
  - DFLD.de
  - derived from METAR wind using the one-pager rules
  - derived from OpenSky ADS-B departure headings

## Suggested approach

1. **Labels:** apply the one-pager rules to the historical data.
2. **Baseline:** apply the rules to the forecast wind.
3. **Model:** gradient boosting on forecast features: u and v wind at several heights, gusts, pressure, hour and season. It predicts hourly probabilities for t+1 to t+48:
   - P(BR25 vs BR07)
   - P(runway 18 closed)
4. **Evaluation:** show the skill against persistence and against the rule baseline on a held-out period.
5. **UI:** a 48 h timeline per hour showing:
   - the operating direction
   - runway 18 open or closed
   - the probability
   - the ops impact
   
   One idea from the team is an iPad widget for ops staff or pilots.

## Kick-off logistics

- Teams have 2 to 4 people. Register with the form (code "Let's Hack AI Week") and choose this case.
- After registering, OpenAI invites the team to a ChatGPT workspace. Choose the statworx partner workspace. Credits are free, and an API key is provided. Never commit it; see `.env.example`.
