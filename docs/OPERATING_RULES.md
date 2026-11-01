# Operating-direction baseline

`ml/rules.json` is the versioned rule specification used by this implementation. It is an experimental baseline, not a certified operating procedure or the complete current airport rulebook.

Parallel-runway direction is OD 25 toward the west or OD 07 toward the east. The state machine keeps the previous direction until wind limits require a change; it includes a sustained-tailwind timer. Runway 18 is departures-only and is checked separately against tailwind and crosswind limits. Wind direction is meteorological (where wind comes from), speeds are knots and timestamps are UTC internally. Berlin display time can repeat at daylight-saving transitions.

Canonical limits and headings live in `ml/rules.json`; `ml/rules.py` implements wind components, hysteresis and runway usability. Tests exercise threshold equality, variable wind, gusts and duration. Hourly aggregation cannot resolve a precise within-hour switch time.

Actual operations also depend on controller decisions, traffic, runway availability and constraints absent from this model. Public descriptions can differ from the experimental baseline. [Fraport explains easterly and westerly operations](https://www.fraport.com/en/business-areas/operations/airside-and-terminal-operations/easterly-and-westerly-operations.html); [DFS describes air-traffic operations](https://www.dfs.de/homepage/de/flugsicherung/betrieb/). These links provide context, not approval of this software.
