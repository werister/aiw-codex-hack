# Response to the weather database review

Feedback for Jayden, published at Luca's request on 30 October 2026. This responds to [the review](weather-database-review.md), reviewed at blob `18d0720c5424ea9ed9d5f269fbb225c03d5a081a`. It is research feedback, not a team decision or a production change.

The review gets the immediate priority right: investigate FRA-specific forecast failures, operating-direction changes, Runway 18 restrictions and uncertainty. Preserve the broader delay research as supporting context.

## Where we agree

- US BTS delay data cannot train or validate FRA operating-direction or Runway 18 forecasts. Its role is explaining delay mechanisms and researching causal attribution.
- The FRA ICON-D2 ensemble paper and NASA runway-configuration paper are the closest matches in the collection. Their methods and input requirements deserve attention before adding more general forecasting literature.
- Archived forecasts, recorded FRA operations, sound features and chronological evaluation matter more now than adding a more complex model.
- The pitch must separate implemented capabilities, measured experimental results and future product ideas.

## Qualifications

**Two directly relevant prediction papers does not mean only two useful sources.** Capacity, turnaround and delay-propagation research helps define operational consequences and the additional data needed for validation. These studies support different questions; they do not supply Frankfurt runway labels.

**Ensemble spread is a candidate feature, not a demonstrated confidence score.** Zinkhan et al.'s [FRA study](https://doi.org/10.3390/engproc2023039041) supports investigating it. Its illustrative case does not establish that adding spread improves our model. We need archived members available at issue time and held-out tests of calibration, event detection and timing. Ensemble spread and calibrated event probability are different quantities.

**The NASA percentages are contextual results, not a comparable benchmark.** Airport, forecast horizon, label construction and evaluation design differ. In particular, its random split should not be treated as equivalent to our chronological walk-forward test. The [full source and review notes](https://github.com/werister/aiw-codex-hack/tree/luca/weather-database/weather%20database/models) should accompany any citation.

**Average accuracy alone cannot establish operational usefulness.** Persistence can score highly while missing changes. Alongside the challenge's hourly classifications, report direction-change recall, warning precision, false alarms, interval-aware timing, restriction-event detection and probability calibration. Runway 18 meteorological unavailability, operational non-use and documented closure must remain separate labels.

**A direction-change cost number needs a defined population and counterfactual.** We currently cannot establish Frankfurt-specific savings, a universal cost per switch or an optimal preparation action. European studies support mechanisms, but do not automatically identify the effect of a FRA configuration change. Time-stamped traffic demand, configuration events, capacity and operational outcomes would be needed.

**Archive rights should be assessed source by source.** Open licences, repository deposits and restricted publications have different redistribution conditions. Folder naming is a tooling consideration, not a scientific limitation. Luca's instruction for this research task is to preserve existing research and avoid relocation; this response does not authorize removing files. Main's subsequent archive cleanup is a separate teammate change.

## Research response in progress

The research branch is testing three concrete questions:

1. Do train-only wind corrections improve held-out errors and threshold detection?
2. What precedes actual DFLD proxy changes, including transition hours omitted from stable-hour scoring?
3. How do the saved served model, rules and persistence compare on identical issue schedules and labels?

Experiments remain outside production. Preliminary calibration results must not be promoted as better Runway 18 detection when the held-out sample contains no qualifying restriction events. Ensemble inputs remain a proposed next experiment.

The analysis is pinned to repository snapshot `7ded00d5f9ce40093abdec114ded8ba77db5c7eb` (`walk-forward-v3`). Main has continued to evolve; these results must not be described as an audit of every later serving version.

**Proposed agreement:** prioritize FRA-specific error diagnosis and event evaluation; retain the literature as traceable evidence; claim improvements only where measured on held-out data; describe business value as a mechanism until local impact data supports a quantitative estimate.
