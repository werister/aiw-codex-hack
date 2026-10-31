# Release boundary and verification

This source distribution is a release candidate for the existing project repository. Publication still requires all four authors to approve the proposed MIT licence. Recorded direction data and fitted weights remain withheld pending source permission. The historical evaluation cannot be independently reproduced from the weather-only distribution.

The public source tree contains no event deck, personal contacts, research-PDF archive or working-process instructions. Historical aggregates and their limits remain, together with a real offline rule computation and a separate model-quality view. The chart was generated from the replayed historical aggregate, not estimated from prose.

## Checks

- Python: `python -m pytest -q`. Seven fitted-artifact checks are deliberately skipped after weights are withheld; those checks also ran against the original fits before their removal.
- Forecast: `python -m ml.forecast --demo`, and the JSON-output variant. No key or network is required.
- Web: `npm ci`, `npm test`, `npm run typecheck`, `npm run lint`, `npm run build`. `STATIC_EXPORT=1` enables a static build. Ordinary document links and trailing-slash routes work on a plain static file server.
- Headless browser: real forecast loading, selected-hour synchronization, six-hour summary, model quality, method/card pages, tablet layout, missing-day retry and mobile overflow. Screenshot method is [documented separately](images/README.md).
- Privacy: `python tools/audit_release.py --out scan.json`; use `--git-history` only on the clean one-commit export. It checks tracked bytes and reachable Git object contents for credentials, email addresses, phone numbers, home paths, private hosts and private links without printing matched values. Pattern scanning cannot prove the absence of every possible credential or personal detail; decoded weather fields and original geometry metadata were also inspected.

## Explained generic matches

- A matrix-multiplication expression in `verify_assets.py` resembles an email address. It is geometry code. The requested public no-reply commit identity is intentional Git metadata.
- The scanner includes definitions of the patterns it checks; these are explained by the scanner itself. No unexplained match is acceptable in the clean export.

## Dependencies and history

The dependency audit found no production advisories. Development tooling has 16 moderate advisories through a minimatch glob-amplification issue. The package manager proposes incompatible downgrades; no forced downgrade or unvalidated override is applied. Recheck advisories and the lint toolchain before a maintained release.

The existing repository history is outside the clean distribution. Deleting files in a later commit does not erase old Git objects, branches, tags, pull-request refs, forks, caches or clones. The owner must replace the old history and inspect all remote refs and hosting-retained objects before changing visibility. The locally supplied history has been inventoried separately for the owner; it is intentionally absent from this public tree.
