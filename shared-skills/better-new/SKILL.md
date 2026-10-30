---
name: better-new
description: Discover evidence-backed new product opportunities in an existing project when the user asks for new features, unexplored use cases, or new project directions. Use for opportunity discovery; use better-function to improve a named existing feature.
---

# Better New

Find new ways this project could serve its users. Ground opportunities in the
project's actual capabilities and gaps; novelty means new to this project.

## Invocation and scope

`$better-new` uses the current project. An accompanying audience, problem, or
area narrows discovery. Recognize `/better-new` as the same written request.
If no project or source material is available, ask for the missing context.

Discovery is a complete deliverable. Implement a selected opportunity when the
user has requested implementation; finding or recommending it alone does not
authorize changing the product. If implementation is already authorized and
the choice fits that brief, continue without another approval step.

## Find opportunities from primary material

1. Read applicable project instructions and the product's canonical context.
   Trace representative user journeys into source code, data contracts, and
   integrations. Form a compact picture of who the product serves, what they
   can accomplish, and where work leaves the product or remains manual.
2. Inspect relevant existing plans, open change proposals, and accessible user
   evidence. Use issues, feedback, or telemetry when available within existing
   access; otherwise mark demand and frequency as hypotheses. Distinguish a
   genuinely new opportunity from an existing capability, unfinished planned
   work, or a defect in an existing feature.
3. Look for valuable adjacent jobs, underserved users, unused combinations of
   existing capabilities, and workflows the current product cannot complete.
   A new topic may expand product scope: state that expansion explicitly.
   Favor a few concrete opportunities over a generic feature inventory.

For each promising opportunity, make the four depth questions concrete:

- **Professional move:** Which user outcome or unmet job would an expert
  investigate that the current brief overlooks?
- **Primary evidence:** Which exact workflow, source path, contract, or user
  observation supports the opportunity? Separate observation from inference.
- **Method:** Which specific analysis, interview, experiment, or prototype
  would resolve its main uncertainty, and what would it consume and produce?
- **Independent proof:** What observable result would support or disprove its
  value? Specify the baseline, target, and measurement when evidence permits;
  label proposed thresholds and unmeasured baselines honestly.

## Compare and recommend

Present a small set of materially different options. For each, show the user
and scenario, evidence with source references, smallest useful capability,
expected benefit, dependencies, rough effort, and strongest uncertainty.
Use qualitative estimates unless measurements support precision.

For each leading idea, name the strongest contrary observation or reason it
might fail. Check that observation when available; keep unmet assumptions visible.

Recommend one opportunity by weighing user value, evidence strength,
distinctiveness, fit with the product, and cost to learn. Explain why it outranks
the alternatives; do not manufacture scores. If evidence supports no credible
new opportunity, report that and name the observation needed next.

Turn the recommendation into a ready-to-use brief: problem, intended outcome,
scope boundary, starting material, concrete method, smallest useful delivery,
and success or rejection criteria. Include the cheapest useful next step.

If asked to implement, work within the selected brief and report the resulting
change with verification evidence. Follow project rules for tests and external
actions; a proposed measurement or check is not an executed result.

## Completion

Discovery is complete when the user has distinct grounded options, a justified
recommendation, an actionable brief, and visible uncertainties. Implementation
is complete only after the authorized change and permitted verification are
done, with any missing evidence or gated operation reported.

## Sources

Four-question depth framing by Felix Rieseberg, as packaged in
[Josh's better skill](https://gist.github.com/joshp123/a1443d30fa1b7c577e74882895cea61b)
and [Andre Burgstahler's deepen-prompt](https://github.com/r3dlex/deepen-prompt).
The latter also informs the evidence and method guidance; its MIT notice is
preserved in `LICENSE`.
The opportunity-discovery workflow is a local extension.
