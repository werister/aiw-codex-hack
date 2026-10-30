# OUR CHALLENGE: FraAlliance runway forecast

> Agents: read this whole file first, including **the full pitch transcript at the bottom**. Then read `briefing/README.md` for the event, the judges, the models and the team.

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

## FULL TRANSCRIPT of the FraAlliance pitch (verbatim, nothing cut)

> Verbatim machine transcript (Whisper large-v3-turbo) of the FraAlliance pitch at the 30 Oct kick-off, recorded on a phone. Nothing cut, nothing summarised. Known mishearings: "Fraalines" = FraAlliance, "Fraalbord" = Fraport, "Luska" = the speaker's name (uncertain), "1.8" / "1/8" / "1-8" = Runway 18, "Cadets 2." = unclear (likely "If the wind is too"), "flight library scheduling" = unclear (likely flight/delay rescheduling), "Runaways" = runways.

And next up we have something completely different from our friends at Fra Alliance. I would welcome you on stage now and describe your challenge. Big applause. take pictures, so you will be able to download everything, the presentation and what else. Just as FYI. Hi, guys.

Good morning. So just a little thinking example of what I want to do with you here. Imagine it's Friday morning. You're at Frankfurt Airport right here. You see a lot of aircraft taking off, departing, and landing. Imagine you're sitting in an aircraft right now.

Which would be your favorite destination to go to? How about you? Barcelona. Beautiful destination. I would only recommend that. San Francisco.

Amazing. So now you're sitting in the aircraft, and you're wondering, you're right before takeoff. Which way are you going to go? Is it eastbound or is it westbound? And that's a question that doesn't answer, isn't answered by the pilot or by flight planning, ground handling. It will be answered by the wind and by the wind only.

Hi, my name is Luska. I am from Fraalines, which is a joint venture between Lufthansa and Fraalbord. And that is the question I'm bringing for you guys today. So the task is to build a machine learning model that forecasts 48 hours ahead which way aircraft and landing, and whether or not Runway 18 will be closed or open for departures. So here at Frankfurt Airport, I don't know how many of you guys have taken off and landed here at Frankfurt? Raise of hands.

Many people. Okay, so you are a bunch of, in total, 63 million passengers that travel through Frankfurt Airport within a year. Those 63 million passengers are going through airports here in Frankfurt with 460,000 aircraft movements, that is departures and landings in total. That sums up to about 1,260 flight movements a day that have to go through four runways. You can see on the picture, behind you guys, or ahead, how many runways you have. We have three runways that can be operated into their own.

directions, this way, east way, or west way. And then we have another runway that is going in the direction of the south. So within those four runways, you have capacity of up to 110 movements in the peak hour. So that is departures and landings. On the side, for those of you that don't know, those runways are named by the compass direction that the wind determines. So which way they're going to take off and land.

So for example, for you guys to understand, the runway that is going to the south, that is called 1-8, because it's going on the compass direction 180 degrees to the south. Then we have the three center runaways. The one in the middle is called center, because it's in the center. And depending whether or not it's going to the east or to the west, it will be called 2-5 center or 0-7 center, because it's either going 7 degrees in the compass direction or 250 degrees in the compass direction. And the ones on the side of center are 2-5 right or 2-5 left. 0-7 left or 0-7 right.

depending on which way the wind goes. So what's important for you guys? Six out of ten departures will be taking off on the 1/8. The rest of them will be taking off on center, when there is wind coming from the north. Cadets 2. heavy, the 1/8 runway will be closed for departures, because aircraft can only take off against the wind.

So we need to know ahead of time whether or not all four runaways will be operating or not. To give you a few more numbers, 156 operational direction changes is what we're collecting within a year. So that's about three changes in operation direction per week. So those of you who guessed earlier that you're going to the West, you're right, and about 61% of the time. The other time, you're going to go to take off to the east. So why is this so important for Frankfurt Airport?

Depending on which way the wind is going to go, because that's what we need for aircraft to take off and land, it will be decided on how the airport is operated. And how does that work? they're going to decide, okay, wind's too heavy, we're going to take off to the other direction. And then what happens after that? We have our ground handling staff that needs to be repositioned. Ground handling properties, I would say, they have to be repositioned.

We have transfer passengers that might not be making their connecting flight. And we need to do a whole lot of flight library scheduling. And once that decision is made, everybody else has to react. And obviously, in an aircraft this big, this leads to a lot of planning and rescheduling and delays. So what we're trying to do with our model that you guys are going to build, please predict 48 hours in advance whether or not runway 18 will be open or closed. So you need to measure in the wind that's coming in from the north.

If it's too heavy, from the back and aircraft can't take off. We have one pager that will be uploaded and you can see the exact rule set on how far or how much wind we can take with the tailwind and when the wind direction will be changed and when 1-8 will be closed. So, First task is find out when 1.8 will be closed, and second task is find out when will the wind change. So for that, you can use all data available open source. There is a whole bunch of data to find out when the direction is changed for the operations, and which direction is operating, and of course, how the wind is behaving. So that is the task to help us-- yeah, for the passengers to make their connections, to predict staff and ground handling, and to make a better experience for the cooperation behind all of the partners that are making this airport work, obviously for the passengers to make their connecting flights.

And I think you will find the one pager, like I said, as well as the presentation online. And with that, best of luck, and I'm looking forward for your tasks. Yeah.
