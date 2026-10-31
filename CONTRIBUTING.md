# Contributing

Start with the offline demo and model card. Keep changes focused, explain behavior and include relevant checks:

```sh
python -m pytest ml/tests -q
cd web
npm ci
npm test
npm run lint
npm run build
```

Keep timestamps and availability explicit. Never replace missing data with invented measurements. Distinguish hourly state accuracy, event detection, calibrated probabilities and heuristic display scores. Model improvements need chronological validation and comparisons with both rules and persistence.

Do not contribute credentials, personal contact details, private paths, restricted direction records or models derived from unclear data rights. Include source and licence information with datasets. MIT is proposed for code, subject to approval by all original authors; this remains a release candidate until then.
