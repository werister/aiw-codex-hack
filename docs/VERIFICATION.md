# Verified release candidate

Verified on 31 October 2026 using Python 3.12.10, Node.js 24.21.0 and npm 11.19.0. Python 3.13 is configured in the proposed CI workflow but was not available for local execution. The workflow file has not been triggered from this environment.

## Fresh checkout

A new single-branch clone was created in an empty directory. Because the cleaned repository is not yet published, only the README's clone transport was substituted with a local repository path; the destination remains `https://github.com/werister/aiw-codex-hack`. The clone used the pinned package lock and a newly created Python environment, with no existing project environment or API credentials.

The README commands `npm ci`, `npm run dev`, `python -m venv .venv`, environment activation, `python -m pip install -r ml/requirements.txt`, `python -m ml.forecast --demo`, and the JSON-output variant all completed successfully. The generated JSON matched the committed forecast: 48 hours, `rules-demo`, no recorded outcomes.

Fresh-checkout browser navigation passed for the dashboard, all 48 selectable hours, historical model quality, return navigation and tablet view, with no page exceptions. That run intentionally disabled WebGL to exercise the 2D fallback after a combined development/3D attempt exhausted the host's commit memory. The running production export separately passed the full software-WebGL scene checks and supplied the real screenshots.

## Results

| Check | Result |
|---|---|
| `python -m pytest -q` in fresh environment | 97 passed, 7 intentionally skipped fitted-artifact checks; one malformed-timestamp parsing warning |
| Original fitted-model checks before withholding artifacts | Full ML suite: 104 passed |
| `npm test` | 40 passed |
| `npm run typecheck` | Passed |
| `npm run lint` | Passed |
| `npm run build` in fresh clone | Passed |
| `STATIC_EXPORT=1 npm run build` | Passed; dashboard, widget, quality, method and model-card routes generated |
| Production headless browser | Hour selection, six-hour summary, source/model pages, static navigation, missing-day retry, tablet and mobile layout passed |
| Historical fit replay | All accuracy estimates, accuracy intervals and event counts reproduced; small probability-score differences documented in the evaluation report |
| Dependency audit | 0 production advisories; 16 moderate development-tool advisories recorded for maintenance |

## Test repairs

Three stale trace checks asserted an old model revision or fixed artifact cutoff. They now check the current model contract and derive paths from the repository. Two experimental collection errors depended on supplementary-model adapters and external research data; those optional research fixtures were removed. Useful fitted-model contract and temporal-causality checks were retained under `ml/tests/`. The causality counterexamples still demonstrate why whole-run sensitivity flags cannot filter primary labels.

Optional generated-summary and connection-only API tools were removed with their tests and dependencies. The public forecast, dashboard and deterministic guide need no provider key. No model was retrained or tuned during cleanup.
