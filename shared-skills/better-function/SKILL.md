---
name: better-function
description: Improve a named existing product feature or user workflow by tracing its behavior, comparing grounded improvement options, and carrying out the chosen bounded change. Use better-new for new project opportunities; use better for a general task or prompt rewrite.
---

# Better Function

Improve the outcome of an existing feature. Interpret "function" as a product
capability or user workflow unless the user names a code function or symbol.

## Invocation and execution

`$better-function upload` targets the upload feature; `/better-function` is
equivalent written intent. Use a feature named in the active conversation when
the invocation has no argument. Ask for a target only when it cannot be inferred.

Treat a request to improve the feature, including a bare skill invocation with
a clear target, as a request for a bounded local implementation. If the user asks
only for analysis, options, or a rewritten prompt, deliver that and stop there.
Honor narrower instructions and existing authorization boundaries.

## Establish the actual problem

1. Read applicable project instructions and the relevant owner context. Trace
   the feature's entry point through its state, contracts, persistence, and
   visible outcome as needed. Include important failure and recovery paths.
   Scope reads to this feature and its immediate dependencies.
2. Start from primary material: implementation, actual inputs and outputs,
   rendered behavior, existing tests as evidence, and available user reports
   or measurements. A prior summary is a lead to verify. Inspect the rendered
   surface for UI work using the project's prescribed workflow.
3. State the current user outcome, the desired improvement, and its supporting
   evidence. Separate confirmed behavior, inferred causes, and unknowns. Read
   relevant active plans before treating unfinished work as a missing feature.

Answer the depth questions for this particular feature:

- **Expert move:** Which overlooked behavior or bottleneck most affects the
  user's success within this feature?
- **Raw material:** Which exact source paths, representative inputs, observed
  interactions, or measurements will the work start from?
- **Method and tools:** Which concrete trace, comparison, profiling method,
  design exercise, or experiment will resolve the uncertainty, and why?
- **Independent proof:** Which observable behavior, contract, measurement,
  or rendered comparison would distinguish improvement from a plausible story?

Capture a baseline when feasible and permitted. Otherwise state what is missing;
do not present a proposed check as evidence that it passed.

## Choose the smallest valuable improvement

Where meaningful tradeoffs exist, compare a few distinct options within the
same feature. State the benefit, evidence, cost, risk, and proof for each, then
recommend one. A clear defect with one supported correction needs no artificial
menu. Match the method to the evidence rather than conducting unrelated audits.
Challenge the leading explanation against a competing cause or contrary
observation before committing to it when that could change the implementation.

Rewrite the brief around the recommendation: intended user outcome, concrete
behavior change, boundaries, primary inputs, method, and acceptance criteria.
Keep the existing feature's purpose and the user's requested scope explicit.

For an implementation request, state the brief concisely and carry it out when
the recommendation fits the authorized goal. Pause only for a material product
decision the user must make, a goal or scope change, or missing required access
or permission. Continue independent authorized work while a necessary answer is
pending. Present any scope-expanding option separately from the bounded fix.

## Implement and establish evidence

Change the complete necessary path through the feature and its affected callers.
Preserve unrelated work and the project's current contracts. Follow the
project's UI, schema, and test-authorization rules wherever they apply.

Perform the permitted checks identified in the brief. Record the observed
result against the baseline or acceptance criteria. When a check needs separate
authorization, report it as omitted and use available permitted evidence without
claiming an equivalent level of confidence.

## Completion

For analysis, return the supported problem, meaningful options, recommendation,
and actionable brief. For implementation, return the user-visible improvement,
changed files, evidence of what was checked, and remaining uncertainty or gated
operations. A rewritten prompt alone does not complete an implementation request.

## Sources

Four-question depth framing by Felix Rieseberg, as packaged in
[Josh's better skill](https://gist.github.com/joshp123/a1443d30fa1b7c577e74882895cea61b)
and [Andre Burgstahler's deepen-prompt](https://github.com/r3dlex/deepen-prompt).
The latter also informs the evidence and method guidance; its MIT notice is
preserved in `LICENSE`. Continuation behavior follows the original better skill.
The feature-improvement workflow is a local extension.
