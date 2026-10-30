# What changed in v6

v6 keeps the same 45 input features and the same histogram gradient-boosting model family as v5. Its main changes concern starting state, information availability, runway-18 blending and evaluation. It is not a new model with more weather inputs.

The rule forecasts now remember how long positive tailwind has already been present at issue time. Previously, that timer effectively restarted at zero. This change applies to base-weather rules, ensemble-weather rules and the fallback forecast.

Historical forecasts now check every supplied issuance and retrieval timestamp. Each must be no later than the forecast issue time. Missing archive publication metadata remains a limitation: a six-hour proxy is still an assumption, not verified release history.

Runway-18 probabilities can now blend the classifier with the observed current state, using horizon-specific weights selected on earlier validation data. Sparse validation, no closure examples or unknown current state triggers a raw-classifier fallback. The committed final metadata has weights of 1.0 at every horizon because the validation blocks had no closure examples; the capability exists, but that fitted artifact does not gain a persistence contribution.

Primary training retains all recorded operating-direction labels. The full-run rule-disagreement flag is a sensitivity check, not proof that observations are wrong. On the team's current twelve-fold label-policy comparison, training labels were identical, so no alternative refits were required. This does not prove that the filtering mechanism would be safe at every possible boundary.

Direction-change evaluation now checks the predicted direction as well as time, requires warnings to precede the event, and distinguishes overlapping forecast windows from unique actual changes. Runway-18 event scoring requires complete observation and prediction windows. Missing data cannot silently become “no closure.” Seven-day blocks better acknowledge correlated forecasts in uncertainty estimates.

The interface also preserves recorded direction observations when only runway-18 labels are missing, and future-day requests retain the complete current 48-hour forecast with its actual issue time.

These changes improve correctness and make the report more faithful to what was tested. A general accuracy improvement over v5 has not been established. The current twelve-month report gives 95.7%, 92.7%, 91.8% and 88.9% OD accuracy at 1, 6, 24 and 48 hours. Those historical folds influenced development.

Independent Colab status at this document's creation: 31 source/reference files and six input-file hashes verified; 103 software tests passed in 3.98 seconds. Two fresh October fits and the daily-midnight January/April/July comparison have completed. Results are mixed, with no general v6 superiority established. See [completed results](v6-colab/RESULTS.md), including the failed full-schedule attempt and the clearly separated midnight sampling.

Source: [pinned v6 explanation](https://github.com/werister/aiw-codex-hack/blob/4c6c1143ee69cd131b1d4c1fe5593a18a0ffa756/ML_VERBESSERUNGEN.md), [model card](https://github.com/werister/aiw-codex-hack/blob/4c6c1143ee69cd131b1d4c1fe5593a18a0ffa756/MODEL_CARD.md), [metadata](https://github.com/werister/aiw-codex-hack/blob/4c6c1143ee69cd131b1d4c1fe5593a18a0ffa756/ml/models/metadata.json).
