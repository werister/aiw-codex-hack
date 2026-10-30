# Preparation and handover

The cockpit supports a proposed preparation workflow for tower coordination and airport partners. The official challenge asks for hourly direction, runway-18 weather usability, certainty and the next likely change over 48 hours. It requires separate held-out comparisons at 1, 6 and 24 hours. It does not establish an operational decision procedure.

## Use the forecast

1. Check the issuance, source and available coverage. Issue-time direction and a future runway-18 prediction refer to different times.
2. Review both direction changes and runway-18 restriction periods. Select an event to inspect its hour, wind inputs and rule comparison. Later transitions derived from hourly calls have no additional calibrated timing interval.
3. Select the beginning of the period to hand over. The guide summarizes up to six consecutive UTC hours and identifies incomplete coverage, restrictions and model/rule disagreements. Copy the briefing only after reviewing its timestamps and sources.

Hourly probabilities describe the named state at that hour. The lowest hourly support is not the probability of no change throughout the forecast. The certainty score is a probability-margin score, not measured joint correctness. No probability threshold establishes that a plan is operationally approved.

## Demonstrate preparation

In `/pitch`, enter a preparation duration for a saved historical case, inspect the conditional review time, then reveal the recorded outcome. The comparison uses recorded-state bounds; gaps and hourly bins prevent exact switch-time claims. An earlier review time alone does not prove adequate preparation or historical input availability.

The pitch opens with a saved historical forecast. It displays published forecast and evaluation values; missing evidence remains unavailable. No synthetic weather or restriction scenario is shown.

## Evidence and validation boundary

- [Official challenge](../frankfurt-airport-operating-direction-forecast.md) and [original pitch](../briefing/transcripts/FRAALLIANCE_PITCH_FULL.md) establish the deliverables and advance-planning motivation.
- [DFS tower operations](https://www.dfs.de/homepage/de/flugsicherung/betrieb/) and the [Frankfurt coordinator interview](https://karriere.dfs.de/de/storys/tim) describe adjacent operational roles.
- [Fraport operating-direction explanation](https://www.fraport.com/en/business-areas/operations/airside-and-terminal-operations/easterly-and-westerly-operations.html) identifies DFS decision authority. Its public threshold explanation differs from the challenge baseline; the application follows the challenge rules.
- [Frankfurt A-CDM](https://cdm.frankfurt-airport.com/content/fraport-company-cdm/en/local-a-cdm-procedure.html) already coordinates departure demand and capacity. This application does not change flight targets or clearances.

A practitioner walkthrough still needs to establish the receiving role, actionable preparation, required lead time, acceptable false alarms and handover procedure. Automated and local-browser checks verify software behavior; they do not establish operational suitability or delay savings.

## Local verification, 30 October 2026

- `node --test src/lib/forecast-events.test.mjs src/lib/forecast-explanation.test.mjs src/lib/forecast-handover.test.mjs src/lib/pitch-replay.test.mjs src/lib/runway18-demo.test.mjs` from `web/`: 46 passed, including simultaneous events, final closed samples, missing intervals, partial coverage and repeated Berlin hours. The synthetic fixtures only exercise development logic.
- `tsc --noEmit --incremental false` and targeted ESLint on changed components/helpers: passed.
- `npm run build -- --webpack`: production build passed for `/`, `/widget`, `/pitch` and `/approach`. The default Turbopack build hit a local CSS-worker port permission error after integration; no build or deployment configuration was changed.
- The documented forecast command ran using the existing Python environment, with `--day 2026-10-31 --out /private/tmp/shift-planning-forecast.json`: exit 0, 48 rows, `walk-forward-v6`. The shell has no unqualified `python` command; its system `python3` lacks a Parquet engine.
- Local browser: latest and saved historical data; event selection opens the detail section and synchronizes scene, timeline and guide; selected-hour reset; six-hour and three-hour partial briefings; separate rule disagreements; successful handover copy; historical late/indeterminate review times; separate 1/6/24-hour evaluation. Checked desktop/iPad widths and 320 px layout, including the mobile scene height and non-overlapping bar labels.

The shared main worktree has concurrent scene, copy, data and presentation changes. These are local software checks, not a deployed-release or practitioner acceptance claim. Clipboard rejection is handled with a selectable-text fallback but was not forced in the browser.
