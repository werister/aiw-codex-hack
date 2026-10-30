# Liftoff — presentation script and cue sheet
Draft 1 • 30 October 2026 • Hugo presents; Luca backup.
Review draft beside the finals deck. Use the linked speaker cue sheet; reconcile final timing and figures before presenting.
Evidence frozen at [5ecf04e](https://github.com/werister/aiw-codex-hack/blob/5ecf04e3bf71996710f4ace5ed1a9f0628800c45/MODEL_CARD.md). Model: walk-forward-v5. Speaker assignments below are proposals, not messages sent to the team.

## Versions and running order

- **Two-minute opening:** story → illustrative value → demo → baseline/result → future. 205 spoken words, leaving room for clicks and pauses.
- **Five-minute full version:** use the same opening, then the proof section below. Assumed total duration until Hugo confirms.
- **Three-minute backup:** use the same opening, then the one-minute compressed proof. Jayden's existing finals notes target approximately three minutes.
- These are presentation lengths. They are separate from model versions and from implemented versus proposed features.
- Rehearse with a timer: time blocks are targets, not a measured speaking duration. Cut spare UI clicks first.

## A. Story and demo — hard stop at 2:00

### 0:00–0:20 | The story: one wind shift, an airport-wide consequence

**Show:** Airport diagram. Keep the opening visual simple.

**Say:** “Imagine your aircraft is ready to leave Frankfurt. The wind shifts. Across the airport, the operating direction may need to change. Handling teams reposition, departure plans change, and connections come under pressure. FraAlliance described roughly three direction changes a week. This is an airport-wide planning problem.”

### 0:20–0:35 | Why earlier notice has value

**Show:** 100 avoided aircraft-delay minutes × €45 = €4,500. Label: illustrative gross airline cost, 2022 prices.

**Say:** “Minutes matter. If better preparation avoided one hundred aircraft-delay minutes, EUROCONTROL’s short-delay benchmark puts that at about four thousand five hundred euros. That is an illustration, not a saving we have measured.”

### 0:35–1:15 | Show Liftoff

**Show:** Open the rehearsed forecast. Point to issue time, recommendation, timeline, then evidence. Use a labelled historical example if the live day is uneventful.

**Say:** “Here is Liftoff. It forecasts operating direction and runway-18 weather usability, hour by hour. Start with the next likely change and its uncertainty. Inspect an hour to see the weather inputs and available prediction evidence. The controller retains the decision; this gives the wider operation time to prepare.”

### 1:15–1:40 | The baseline and the measured gain

**Show:** 24 h: model 91.7% / challenge rules 87.7%. Small caption: historical walk-forward, stable-hour OD accuracy; v5.

**Say:** “The challenge baseline applies wind limits and persistence rules to the weather forecast. Our model adds patterns learned from recorded operations. At twenty-four hours, it gets the direction right in 91.7 percent of scored hours, compared with 87.7 percent for that baseline.”

### 1:40–2:00 | The future and the handoff to proof

**Show:** Now: runway-condition forecast → Next: demand, handling and connection planning. Clearly label the right-hand side as proposed.

**Say:** “The next step is to connect that forecast to demand, handling and connections, so teams can plan buffers together. That fleet-impact layer is future work. First, let us show the data, tests and limits behind the forecast.”

## B. Proof — extend to five minutes

Suggested delivery: Hugo narrates; Jayden/Kai supply the technical evidence; Luca owns the figures and backup. Avoid a speaker handover unless rehearsed.

### 2:00–2:35 | What went into the model

**Show:** DFLD + METAR + archived ECMWF/GFS/ICON + pressure → features → trees + persistence → hourly forecast.

**Say:** “We combined public records of the operating direction actually flown with Frankfurt METAR observations and archived forecasts from ECMWF, GFS and ICON. Pressure differences around Frankfurt add information about approaching weather. The direction archive reaches back to 2018, but the joined forecast training data starts in 2024. Flight schedules and US airline-delay data are not model inputs.”

### 2:35–3:10 | How it works and what changed

**Show:** Same 12 folds, 48 h: base feature set 84.9% → separate weather models 88.6% → v5 with pressure 89.2%.

**Say:** “Two gradient-boosted tree classifiers estimate operating direction and runway-18 usability. Near-term direction forecasts blend with the current state, with weights selected on earlier validation data. On the same twelve evaluation months, separate weather-model features improved forty-eight-hour accuracy from 84.9 to 88.6 percent. Adding pressure features brought it to 89.2. Deeper trees and doubling the issue frequency did not help, so we kept the simpler version.”

### 3:10–3:50 | How we tested it

**Show:** Train earlier months → test next month, repeated Nov 2025–Oct 2026. Show model/rules/persistence table at 1/6/24/48 h.

**Say:** “For each test month, we trained on earlier months and compared all methods on the same scored rows. We used archived forecasts with an assumed six-hour publication lag, rather than future observations. At one hour the methods effectively tie. At six, twenty-four and forty-eight hours, the model improves on both headline baselines. Day-resampled confidence intervals support those margins. Feature selection did look at these folds, however, so a later, frozen test is still needed.”

### 3:50–4:25 | What the score does not promise

**Show:** Timing ±3 h: 52.5% of change windows. False alarms: 12.8% of no-change windows. Runway 18: 3/24 positive issue windows detected at 24 h.

**Say:** “Direction accuracy is not exact switch-time accuracy. The next change falls within three hours in about half the evaluated change windows. False alarms occur in about thirteen percent of no-change windows. Runway-18 labels are inferred from weather, and positive cases are rare: at twenty-four hours the model detects only three of twenty-four positive issue windows. This is a planning prototype with clear limits.”

### 4:25–5:00 | The pilot we want

**Show:** Freeze model → collect timestamped forecasts → compare operational outcomes → measure net benefit.

**Say:** “A pilot needs the airport’s own timestamped direction and closure records, real flight demand and delay causes. We would freeze the model, record every prediction before its outcome, and measure whether earlier warnings improve preparation after accounting for false alarms and action costs. The ambition is shared planning across the airport. Today, we can demonstrate the forecast and the evidence behind its measured improvement.”

## C. Three-minute version: replace section B with this

**2:00–3:00 — show the results table, then close.**

“We trained gradient-boosted trees on recorded directions, METAR and archived weather forecasts. Twelve monthly walk-forward folds compare the model with the challenge rules and keeping the current direction. One hour is a tie; at twenty-four hours, accuracy is 91.7 percent versus 87.7 for the rules. But these folds informed feature selection, so we still need a frozen prospective test. Timing is within three hours in only about half of change windows, and runway-18 closure detection remains weak. Our next step is a pilot with airport records and demand data, measuring planning benefit rather than assuming savings.”

## Current numbers to put on screen

Stable-hour operating-direction accuracy. Historical monthly walk-forward; Nov 2025–Oct 2026. Feature selection used these folds, so this is not a completely untouched final holdout.

| Lead | Model | Challenge rules | Keep current direction | Scored rows |
|---|---:|---:|---:|---:|
| 1 h | 96.0% | 95.9% | 95.9% | 1416 |
| 6 h | 92.8% | 88.1% | 88.8% | 1416 |
| 24 h | 91.7% | 87.7% | 75.1% | 1383 |
| 48 h | 89.2% | 84.0% | 64.2% | 1338 |

Source: [quality.json](https://github.com/werister/aiw-codex-hack/blob/5ecf04e3bf71996710f4ace5ed1a9f0628800c45/web/public/data/quality.json), checked directly; [model card](https://github.com/werister/aiw-codex-hack/blob/5ecf04e3bf71996710f4ace5ed1a9f0628800c45/MODEL_CARD.md).
At 24 h, +4.0 percentage points versus the headline rules baseline; reported day-bootstrap 95% interval +2.4 to +5.6 points. At 48 h, +5.2 points (+3.2 to +7.1).
The stronger rule baseline using corrected ensemble wind achieves 89.2% at 24 h and 85.8% at 48 h; model margins are approximately +2.5 and +3.4 points. Include this in Q&A to avoid implying the only comparator is weak.
The 24 h Brier score is 0.0633 versus 0.1229 for the headline rules: lower average squared probability error. This alone does not prove “85% means 85%” or validate the UI's combined certainty number.

## What we tested: the credible development story

Source: [EXPERIMENTS.md](https://github.com/werister/aiw-codex-hack/blob/5ecf04e3bf71996710f4ace5ed1a9f0628800c45/EXPERIMENTS.md).

| Experiment | What to say |
|---|---|
| Correct publication lag | Earlier performance dropped when forecast availability was tightened. Do not compare old scores across changed protocols as if they were model improvements. |
| Persistence blend | Current direction is useful at short horizons. Weights were selected within earlier chronological validation blocks. |
| Separate ECMWF/GFS/ICON forecasts | On the same 12-fold comparison, 48 h accuracy rose 84.9% → 88.6%. |
| Regional pressure features | Final v5 reached 89.2% at 48 h. |
| Deeper trees, constraints, per-lead models | No consistent gain; not adopted. |
| Three-hour rather than six-hour issue stride | 48 h 89.1% versus 89.2%; no gain. Newly added E17. |
| Runway-18 operational non-use as closure truth | Rejected: not using a runway does not mean wind made it unusable. |
| Corrected-wind runway-18 rules | New comparison: one hit and 64 false alarms across 24 h issue windows, versus model three hits and zero false alarms. Only 24 positive windows; not independent closure events. |
| ICON-D2 ensemble archive | Not used in this model; distinguish it from the three-model forecast spread that is used. |

## Money: a defendable illustration, then a measurement plan

**Use on stage:** 100 assumed avoided aircraft-delay minutes × €45/min = **€4,500 illustrative gross airline cost avoided**, in 2022 prices.

- €45 is EUROCONTROL's indicative at-gate tactical delay cost for delays shorter than 30 minutes, including reactionary effects. It is not a FRA-specific price or a per-passenger cost.
- The 100 minutes are an explicit scenario, not inferred from classification accuracy or measured by this prototype. For example, 20 affected aircraft × 5 avoided minutes; both inputs are assumptions.
- Net benefit would deduct intervention, staffing, deployment and false-alarm costs. The saving is not automatically revenue or cost reduction for FraAlliance itself.
- Do not add misconnection or passenger costs without checking overlap with the delay-cost definition.
- [EUROCONTROL source](https://standard-inputs.netlify.app/chapters/cost_of_delay.html) advises high-level use; fleet and delay distributions matter.

**Jayden's new annual scenario:** [RESULTS.md](https://github.com/werister/aiw-codex-hack/blob/5ecf04e3bf71996710f4ace5ed1a9f0628800c45/RESULTS.md) contains roughly €0.1m/year versus rules and €0.6m/year versus persistence. Keep it as an unvalidated research scenario, not the headline. Its calculation converts a change-conditioned hourly score into additional distinct annual switches anticipated; those denominators are not established as equivalent. Combining hourly planning benefits and per-change benefits also needs a non-overlap check. The rule comparison must not be described as today's measured FRA operation.

**To estimate real savings:** jointly measure forecast-driven action, flight demand/capacity, delay cause, handling resources, connection outcomes and false alarms against an agreed current-workflow comparator. Classification accuracy alone cannot compute avoided delay minutes.

## Demo rehearsal: exact parts to do

1. Jayden confirms the working deployment and freezes one app commit plus forecast run/issue time. Main's README links [finals deck](https://fraalliance-runway-forecast.statworx-par-2884.chatgpt.site/deck/index.html); /pitch is the React app's pitch mode.
2. Pick one day with a visible change; October 28 is the documented historical option. Confirm the current file and UI before rehearsing; regenerated forecasts may have new evidence IDs.
3. Show recommendation → issue/model identity → 48 h timeline → one selected hour → available evidence. Read values that actually appear; do not memorise an invented 07:00/79% example.
4. Distinguish the recommendation's time from an independently inspected hour. Only demonstrate return-to-recommendation if implemented and verified on this build.
5. Move to results at 1:15; stop the opening at 2:00. The iPad widget is optional, not required in the time budget.
6. If evidence is absent, say so and continue to saved forecast/result evidence. If the app fails, use a previously captured screenshot of the same frozen run. Build and verify the offline fallback before presenting, not on stage.
7. Display future flight-demand/connection integration as proposed. Do not animate hypothetical traffic as measured fleet impact.
8. Runway 18: say weather usability forecast, not confirmed operational opening/closure. The classifier is not a clearance.

## Visual direction: matching the brief and website

Inspected the supplied one-page case PDF and [FraAlliance's website](https://www.fraalliance.de/) on 30 October 2026.

- White background, deep indigo headings, vivid violet accents, generous spacing, thin dividers and pale lavender panels.
- Website computed colours: **#1D1A78** text and **#3C36DA** primary accent. The cue sheet uses these, plus **#F2F1FB** as an approximate pale panel colour sampled visually from the brief.
- The website uses Söhne light/book. Use licensed Söhne if already available; otherwise Helvetica/Arial is a safe visual approximation. No downloaded proprietary font is required.
- One assertion per view: airport consequence; value illustration; demo; results; data/model; validation/limits; pilot.
- Keep the operational UI's semantic colours intact. Use the brand palette for presentation chrome and charts; do not make uncertain forecasts appear certain to fit a colour scheme.
- Team prototype for the FraAlliance challenge; not an official FraAlliance product or endorsement.
- Companion HTML is a printable speaker cue sheet, not a replacement for Jayden's running deck.

## What changed on Jayden's main during this check

- 13:04–13:10 UTC (14:04–14:10 Berlin): shared 3D scene, finals deck and notes, results/economic narrative, results-slide change metric; deck moved from /pitch to /deck.
- 13:11–13:12 UTC: corrected-wind runway-18 evaluation, regenerated forecast evidence, executed October notebook, E17 issue-stride experiment, explicit archived-availability filtering.
- Latest inspected commit: **5ecf04e3bf71996710f4ace5ed1a9f0628800c45**. Current headline OD accuracy is unchanged after those updates.
- Existing Jayden research/data branches were listed; this script uses integrated main evidence, not unmerged experiments.
- Repository notices are leads to verify, not an authoritative current status. For example, the old deck-route conflict notice was overtaken by the /deck move.
- No model was retrained and no deployed UI behavior was independently certified in this task.

## Before presenting: who confirms what

| Person | Specific item |
|---|---|
| Hugo | Total time; the story; 2-minute cutoff; one complete timed rehearsal. |
| Jayden | Working /deck and /pitch URLs, private-window access, exact demo run and feature availability; final screen values. |
| Kai | Metric definitions (especially the “changes” subset), model/evaluation version, availability safeguards and baseline hysteresis state; freeze before scoring prospective data. |
| Luca | Figure/source alignment, money assumptions and no double-counting; saved result screenshot and backup delivery. |

## Claim corrections for the current draft deck

- Replace “wind alone decides” with “wind is a central constraint; DFS decides the operating direction.”
- Replace “today everyone only reacts after the decision” with the challenge's concrete coordination problem. Current production practice was not audited.
- The official brief's rules are our challenge baseline, not a complete account of all DFS/FRA forecasting or decision support.
- DWD documented a Frankfurt probabilistic wind/AI decision-support prototype in 2019. [Primary abstract](https://meetingorganizer.copernicus.org/DACH2019/DACH2019-189.pdf). This establishes prior work, not its current deployment status.
- Say “each monthly model was trained on earlier data”; acknowledge feature selection used the evaluation folds.
- Say “52.5% within ±3 h across evaluated change windows”; do not convert it into independent event recall.
- Treat the reported 82.1% change-subset score as a separate hourly metric pending Kai's exact definition; do not multiply it by 156 switches/year.
- Explain certainty as a displayed score. A probability for OD25, runway-18 usability, correct classification and correct change timing are different quantities.
- Retain the one-hour tie, weaker six-hour change score, rare runway-18 positives, excluded transition hours and assumed availability lag in the proof/Q&A.

## Source map

- Case PDF: AI_Week_2026_Hackathon_-_FraAlliance_Case.pdf (supplied case brief), one page, sections 1–4.
- [Kick-off transcript](https://github.com/werister/aiw-codex-hack/blob/5ecf04e3bf71996710f4ace5ed1a9f0628800c45/briefing/transcripts/FRAALLIANCE_PITCH_FULL.md): approximately 156 annual changes and handling/connection consequences; machine transcript, not an independently verified traffic statistic.
- [Quality artifact](https://github.com/werister/aiw-codex-hack/blob/5ecf04e3bf71996710f4ace5ed1a9f0628800c45/web/public/data/quality.json): exact metrics, denominators, folds and limitations.
- [Model card](https://github.com/werister/aiw-codex-hack/blob/5ecf04e3bf71996710f4ace5ed1a9f0628800c45/MODEL_CARD.md) and [experiments](https://github.com/werister/aiw-codex-hack/blob/5ecf04e3bf71996710f4ace5ed1a9f0628800c45/EXPERIMENTS.md): inputs, model and development history.
- [Jayden's notes](https://github.com/werister/aiw-codex-hack/blob/5ecf04e3bf71996710f4ace5ed1a9f0628800c45/web/public/deck/NOTES.md), [demo script](https://github.com/werister/aiw-codex-hack/blob/5ecf04e3bf71996710f4ace5ed1a9f0628800c45/DEMO_SCRIPT.md), [results/economic scenario](https://github.com/werister/aiw-codex-hack/blob/5ecf04e3bf71996710f4ace5ed1a9f0628800c45/RESULTS.md): existing presentation material reviewed and tightened here.
- [FraAlliance](https://www.fraalliance.de/): passenger journey and operational collaboration context; website palette inspected directly.
- [Operational Intelligence @Hub FRA](https://www.fraalliance.de/projects/operational-intelligence-hub-fra): shared operational visibility and coordination. Relevant context, not evidence of integration with this prototype.
- [EUROCONTROL cost of delay](https://standard-inputs.netlify.app/chapters/cost_of_delay.html): unit cost and cautions.
- [DWD 2019 prior work](https://meetingorganizer.copernicus.org/DACH2019/DACH2019-189.pdf): avoid claiming FRA has no probabilistic decision-support research.
