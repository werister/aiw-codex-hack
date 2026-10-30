# Independent v6 Colab check
Source frozen at `4c6c1143ee69cd131b1d4c1fe5593a18a0ffa756`. Runs executed in Google Colab on 30 October 2026. No local model training.

## Completed
31 source/reference files and six data hashes verified. **103 ML tests passed in 3.98 seconds**, one date-format inference warning. Two fresh October fits completed in **406.5 seconds**, exit 0.

| Fit | Training rows | 1 h accuracy | 6 h | 24 h | 48 h |
|---|---:|---:|---:|---:|---:|
| v6 full earlier history | 189000 | 90.48% | 82.24% | 81.31% | 79.44% |
| v6 restricted 2025+ | 122280 | 91.43% | 82.24% | 80.37% | 77.57% |
| Prior paired v5 restricted 2025+ | 122280 | 91.43% | 82.24% | 80.37% | 76.64% |

All fits predict 5,136 October rows across 107 issue times. Scored OD lead counts are 105/107/107/107 at 1/6/24/48 h. The restricted comparison exactly verifies all 5,068 prior scored test keys and OD labels. Earlier training keys were not exported; the restricted training match is reconstructed from fixed data, date bounds, complete-issue counts and label-filter equivalence, rather than verified against an old key hash.

Restricted v6-minus-v5 Brier differences at 1/6/24/48 h are **−.000196 / +.000136 / −.000965 / −.002409**. Negative is better. The exploratory circular seven-day paired bootstrap interval at 48 h is [−.004724, −.000154]; other leads include zero. This is not an across-horizon or untouched-test superiority result. No promotion is made.

The fresh full-history v6 October accuracies match the committed October fold. Strict 1e−9 Brier parity does not pass: observed differences are at most about **3.35e−8**, below displayed precision. Do not call it bit-for-bit reproduction; the cause of those tiny numerical differences has not been isolated.

## Additional-month checks
January, April and July were selected before seeing new seasonal scores. The initial six-hourly experiment stopped at a harness assertion requiring every month-end issue to retain all 48 target rows. The production monthly split intentionally excludes targets beyond the month, so that assertion was too strict. No seasonal score from that attempt is claimed.

A separate, clearly labelled **24-hour issue-stride (daily midnight)** comparison is now running to fit the deadline. It preserves matched v5/v6 training/test rows and labels and uses the v6 event scorer for both. Its results must not be mixed with the team's six-hourly monthly metrics. Completion and output evidence will be added separately.

## Interpretation
These are historical development months, not untouched forward validation. Input release timing still uses a six-hour proxy. Runway-18 targets are inferred weather usability, not confirmed closures. Complete 48-hour prediction traces are retained for timing and event evaluation; month-end incomplete windows are excluded by the common scorer.

- [Exact paired October CSV](paired_october.csv)
- [Executed October notebook](october-executed.ipynb)
- [Software test output](pytest.txt)
- [What changed in v6](../V6_EXPLAINED.md)
- [Version explanation](../MODELS_EXPLAINED_SIMPLY.md)

Review: independent reviewer checked script boundaries and API contracts, notebook results, and the seasonal matched-row audit. It did not independently rerun model fitting.
