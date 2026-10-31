# Operating-direction research inputs

Direction/status datasets are intentionally absent. The source provides no open redistribution licence; see [data rights](../../docs/DATA_SOURCES.md). Do not redistribute copies or fitted weights without permission or an independent rights assessment.

The historical pipeline expects stable hourly directions and availability times in `dfld_hourly.csv`, a half-hour archive for event scoring, and optional exclusion/status tables. Its parser remains in `ml/dfld.py` for lawfully supplied inputs. Stable-hour filtering excludes hours containing changes; targets are a public proxy, not a certified operations log. Runway-18 not-in-use status is not a weather-closure label.

The public example infers issue-time direction from weather rules. It is explicitly labelled and never scored as independent ground truth.
