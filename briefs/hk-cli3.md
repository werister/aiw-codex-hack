# hk-cli3 · CLI fixes and regenerated forecasts (WP4)

Worktree `C:\olawt\aiw-wt-cli`, branch `jayden/cli`. **Push rule:** after each small commit run `git pull --rebase origin main && git push origin HEAD:main`. Never force, never merge. No AI assistant, model or vendor names in commits or files. Worker `hk-model2` is changing `ml/features.py`, `ml/train.py`, `ml/predict.py` and the model files right now (publication-lag fix and a persistence blend). Don't edit those files; pull them when they land.

Read first: `NOTICES.md` (open problems), `ml/forecast.py`, `ml/live.py`, `ml/predict.py`, `web/src/lib/forecast-types.ts`.

## Fix (in `ml/forecast.py` and `ml/live.py` only)
1. **Future `--day` (STOP in NOTICES):** today the CLI silently falls back to the rules because there is no METAR before a future midnight. For a day after the current hour, issue at the **current hour** with the latest METAR and the live forecast, then report that day's hours. Make the output say so: `issued_at` = now, and add a `note` line in the table header. Never silently fall back to the rules. If the model truly can't run, print a loud warning and set `model_version` to say so.
2. **Full OD history:** pass the full known recorded OD history (DFLD up to the issue time) to `predict_48h` through `obs.attrs["od_history"]`, as NOTICES describes, so long holds and changes are kept.
3. **Regenerate every published forecast with the trained model** once `hk-model2`'s blend lands on main: `web/public/forecasts/latest.json` (`--now`) and October hindcasts. Pick about 6 October days with at least one recorded OD change (from `data/ground_truth/dfld_hourly.csv`), including 2026-10-28 and 2026-10-29. Update `web/public/forecasts/index.json` (`{"latest": "latest.json", "days": [...]}`). Each file must show the trained model's `model_version`, not `rules-fallback`.
4. **Hit rate:** add `python -m ml.forecast --score --from 2026-10-01 --to 2026-10-29`. It hindcasts every day at 00:00 local and prints the hourly OD accuracy against DFLD for model, rules and persistence, at leads 1–6, 7–24 and 25–48. Write the summary to `web/public/data/october.json` as `{ "days": n, "rows": [{ "lead": "1-6", "model": acc, "rules": acc, "persistence": acc, "n": n }, ...] }`.
5. Re-run `python -m pytest ml/tests -q`, then report the October hit-rate table in one message and stop.
