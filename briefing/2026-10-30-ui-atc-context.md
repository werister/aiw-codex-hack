# UI and ATC context: browser evidence, 30 October 2026

This note records what was inspected and a proposed interface interpretation. WP7's `DATA_AND_DECISIONS.md` remains the home for operational decision and data research; this note supplies UI evidence to WP5. Sources were read on **2026-10-30**. No source code, challenge rules, or deployment configuration was changed.

## Application snapshot and runtime evidence

**Pinned source:** `428cd4c95d746ca26b84497789bb5c82063be606` (`docs: add team brainstorm transcript and bullet points`, 2026-10-30 11:46:10 +0100). Inspection worktree: `/private/tmp/aiw-ui-inspect`. The independent backend inspection subsequently checked `00365bb` and reported unchanged application code. Main was moving during this session; these findings are snapshots, not a claim about future commits.

| Check | Result | Evidence / reproduction |
| --- | --- | --- |
| Version | Package `fra-runway-forecast` version `0.1.0`; Next `16.4.3`, React `19.3.0` | [Pinned package.json](https://github.com/werister/aiw-codex-hack/blob/428cd4c95d746ca26b84497789bb5c82063be606/web/package.json) |
| Implemented page | A heading and a paragraph saying the timeline is being built; no controls or forecast requests | [Pinned page.tsx](https://github.com/werister/aiw-codex-hack/blob/428cd4c95d746ca26b84497789bb5c82063be606/web/src/app/page.tsx), independently checked by backend agent |
| Styling | Source defines warm cream background, navy text and Geist font; centered content | [Pinned globals.css](https://github.com/werister/aiw-codex-hack/blob/428cd4c95d746ca26b84497789bb5c82063be606/web/src/app/globals.css) and [layout.tsx](https://github.com/werister/aiw-codex-hack/blob/428cd4c95d746ca26b84497789bb5c82063be606/web/src/app/layout.tsx); source interpretation, not a rendered-app observation |
| Browser session | Chrome extension showed the private repository tab; README and AGENTS.md were read there | [Repository](https://github.com/werister/aiw-codex-hack) |
| Pull requests | GitHub UI showed Open (0), Closed (0), including after the README refresh | [PR listing](https://github.com/werister/aiw-codex-hack/pulls); no open PR could be reviewed |
| Deployment discovery | No repository homepage; deployments query returned no rows | `gh api repos/werister/aiw-codex-hack/deployments` with the projection shown below exited 0 with empty output |
| Local app | Browser navigation to documented `http://localhost:3000` returned connection refused | No application runtime was inspected |

Deployment query used: `gh api repos/werister/aiw-codex-hack/deployments --jq '.[] | {id,environment,sha,statuses_url}'`.

The app's text is: “FRA operating direction forecast” and “48 h hourly forecast of OD 25/07 and runway 18. The timeline UI is being built.” The README's complete demo sequence describes intended work, and explicitly notes that some commands are still landing during the day. No dependency installation or test suite was run: no reusable Next installation was found, and approximately 360 MiB disk space remained. An empty deployments response does not prove that no deployment exists elsewhere.

## Public operating-direction UI: observed through the browser extension

[Umwelthaus current operating direction and forecast](https://www.umwelthaus.org/fluglaerm/anwendungen-service/aktuelle-betriebsrichtung-und-prognose/) displayed BR07 east, active since 29 October 09:54, with current direction attributed to DFS. Upper wind showed 14 kn from east; surface wind showed 3 kn from east-northeast. These are a dated page observation.

The page combines a plane illustration, green BR25 and blue BR07 probability bands, a time slider and a date/time caption. The forecast spans five days in eight-hour blocks (06–14, 14–22, 22–06), updated three times daily. It credits GFS and an experienced contracted meteorologist.

**Interaction reproduced:** dragging the slider changed the displayed forecast from Friday 30 October 06–14 to Monday 2 November 06–14. No hourly grid, runway-18 probability, backtest panel or model card was visible. This is a public information service oriented toward residents and noise exposure; it is not evidence of the Frankfurt controller workstation.

Screenshots were emitted in the browser-tool conversation for the initial view and moved slider. No persistent image artifact was saved, so this file does not claim to bundle screenshots.

## Operational ATC product context

The official [DFS Aviation Services PHOENIX WebInnovation brochure, May 2026](https://dfs-as.aero/wp-content/uploads/dlm_uploads/2026/05/2026_das-portfolio_flyer_phoenixwebinnovation_en_web.pdf) describes three connected components:

| Component | What it does |
| --- | --- |
| ASD — Air Situation Display | Presents the current radar-based air situation to operational staff. |
| EFS — Electronic Flight Strip System | Handles flight data digitally, replacing paper flight strips. |
| IMS — Information Management System | Brings operational information into a shared view. |

The brochure describes role-based browser access, local or cloud deployment, and flight-plan exchange using industry interfaces such as OLDI/FMTP and ICAO/ADEXP formats. These are product capabilities. They do not establish Frankfurt's exact installed console, software version, screen layout, integration contract, or public API availability. Browser PDF navigation timed out; brochure text was read through web retrieval, and its product screenshots were not visually verified.

## Published operating guidance and the challenge rules differ

[Fraport's public operating-direction explanation](https://www.fraport.com/en/business-areas/operations/airside-and-terminal-operations/easterly-and-westerly-operations.html) says west operation is usually maintained until the tailwind component reaches 5 kn. It identifies DFS as the decision-maker and mentions upper winds and DWD forecasts. This describes a published west-operation preference; it does not establish a universal automatic switching rule. The public explanation is not a complete operational procedure or proof of current internal thresholds.

The [pinned challenge rules](https://github.com/werister/aiw-codex-hack/blob/428cd4c95d746ca26b84497789bb5c82063be606/ml/rules.json) specify immediate change at landing tailwind **>=10 kn**; positive tailwind below 10 kn is tolerated for **30 minutes**. Its version is `fraalliance-brief-2026-10-30`. These statements differ materially. Preserve the official hackathon baseline as specified; record the discrepancy for WP7 and organizer clarification. Do not silently replace 10 with 5 or present challenge-derived output as the exact DFS decision process.

## Ground truth and what the UI can honestly say

The [forecast contract](https://github.com/werister/aiw-codex-hack/blob/428cd4c95d746ca26b84497789bb5c82063be606/web/src/lib/forecast-types.ts) says `current_od` is inferred from METAR plus rules, and `observed[]` means what the rules say happened. They are synthetic rule labels. A model score against those labels measures agreement with that labeling process; it does not, by itself, establish accuracy against directions actually flown.

The separately sourced DFS-attributed current state on the public page is a candidate for independent spot validation. A current snapshot does not provide a historical ground-truth dataset, reliable archive, or confirmed integration permission. WP7 should establish historical coverage, timestamps, actual-direction provenance and terms before any evaluation claim or automated integration. The UI must retain the distinction between **rule-inferred state**, **model forecast**, and **confirmed operational observation**.

## Proposed WP5 layout, grounded in the contract

This is a design recommendation for the existing [WP5 scope](../openspec/changes/wp5-ui-timeline/proposal.md), not implemented functionality or a replacement specification.

| User question | Suggested view | Contract fields and handling |
| --- | --- | --- |
| What am I looking at, and how recent is it? | Top status strip: selected day, live/hindcast, issued time, current inferred direction | `mode`, `issued_local` / `issued_at`, `current_od`; explicitly label METAR-and-rules inference. Show freshness separately from certainty. |
| What changes next? | Prominent next-change card with earliest/latest window | `next_change.from`, `.to`, `.local`, `.window_local`, `.p`; `null` means no forecast change within the supplied horizon, not a rendering failure. |
| What happens each hour? | 48-hour timeline with synchronized OD, runway 18 and certainty rows; selected hour detail | `hours[].local`, `.od`, `.p_od25`, `.p_18_usable`, `.certainty`; text and percentages alongside color. Borrow the reference page's directional clarity, while retaining hourly resolution. |
| When might runway 18 be unavailable? | Highlight predicted intervals and show selected-hour probability | `closures_18` and `p_18_usable`; interval end is the first usable hour. Use “predicted unavailable” rather than implying an official runway closure. |
| Why this forecast? | Selected-hour detail with wind, gust, tailwind and rule comparison | `wind_dir_deg`, `wind_kt`, `gust_kt`, `tailwind_25_kt`, `tailwind_18_kt`, `rule_od`, `rule_18_usable`. Surface model/rule disagreement without inventing explanations. |
| How much should I trust it? | Backtest panel with model/rule/persistence comparison at 1/6/24 h | `BacktestResult.labels`, train/test periods, `od[]`, `r18[]`, accuracy/Brier score and `n`; prominently state whether labels were validated against actual operations. |
| Which source and baseline produced this? | Compact provenance details | `nwp`, `model_version`, `rules_version`; identify the challenge-rule version and unresolved operational discrepancy. |

Use the same priority order for an iPad widget: issued time, inferred current state, next change, a compact hourly timeline, and runway-18 probability. An hourly selector should have an accessible alternative to dragging. Loading, unavailable data, stale data and no predicted change are distinct states. The contract currently has no independent actual-direction provenance field; adding one requires agreement between ML and UI owners, rather than relabeling `observed`.

## Not verified

No live project UI, deployed preview, open PR, operational DFS integration, historical DFS ground-truth archive, or exact Frankfurt ATC installation was verified. Source inspection and public-page interaction are the evidence above. Follow-up ownership: WP5 for display behavior; WP7 (`hk-research`) for operational data and decision facts; ML owners for labels, calibration and the JSON contract.
