"""Run isolated walk-forward challenger experiments without touching forecasts."""

import argparse
import hashlib
import json
import platform
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingClassifier

from ml.features import FEATURES
from ml.predict import HORIZONS, REGIMES, blend_keys, od_probability, probability
from ml.quality import next_change_timing, od_change_events
from ml.train import cached_dataset

ROOT = Path(__file__).resolve().parents[1]
BASELINE_VERSION = "walk-forward-v6"
LEADS = (1, 6, 24, 48)
GRID = np.round(np.linspace(0, 1, 11), 1)


def safe_output(path, root=ROOT, allow_existing=False):
    """Resolve symlinks before rejecting production artifact destinations."""
    requested = Path(path).expanduser().absolute()
    output = requested.resolve()
    root = root.resolve()
    if output == root:
        raise ValueError("Research output cannot target the repository root")
    if root in output.parents and root not in requested.parents:
        raise ValueError("Research output cannot reach the repository through a symlink")
    protected = ((root / "ml/models").resolve(), (root / "web/public").resolve())
    if any(output == item or item in output.parents for item in protected):
        raise ValueError("Research output must be outside ml/models and web/public")
    if root in output.parents:
        allowed = ((root / "resources/raw").resolve(), (root / "verification").resolve())
        if not any(base in output.parents and output != base for base in allowed):
            raise ValueError("In-repository research output is limited to a new subfolder of resources/raw or verification")
    if output.exists() and not allow_existing:
        if not output.is_dir() or any(output.iterdir()):
            raise ValueError("Research output already exists; use --rescore to update it")
    return output


def opposite_to_p25(p_switch, current_od):
    """Map P(target OD differs from issue OD) back to P(OD 25)."""
    p_switch = np.asarray(p_switch, dtype=float)
    current_od = np.asarray(current_od, dtype=float)
    if np.any(~np.isin(current_od, (0, 1))):
        raise ValueError("od_at_issue must contain only 0 (07) or 1 (25)")
    return np.where(current_od == 1, 1 - p_switch, p_switch)


def physical_blend(baseline, rule, weight):
    """Mix v6 with its ensemble rule; unavailable rules retain v6 exactly."""
    baseline = np.asarray(baseline, dtype=float)
    rule = np.asarray(rule, dtype=float)
    weight = np.asarray(weight, dtype=float)
    return np.where(np.isfinite(rule), weight * baseline + (1 - weight) * rule, baseline)


def split_fold(frame, month):
    """Return label-purged training rows and all issue rows for one test month."""
    period = pd.Period(month, freq="M")
    start, end = period.start_time.tz_localize("UTC"), (period + 1).start_time.tz_localize("UTC")
    train = frame.loc[frame.label_available_at < start].copy()
    test = frame.loc[(frame.issue_time >= start) & (frame.issue_time < end)].copy()
    if train.empty or test.empty or train.label_available_at.max() >= test.issue_time.min():
        raise ValueError(f"Invalid or empty purged fold: {period}")
    test["point_in_outer_fold"] = (test.label_available_at < end).to_numpy(bool)
    return period, start, end, train, test


def _classifier(rows, target):
    labelled = rows.dropna(subset=[target])
    if labelled.empty:
        raise ValueError(f"No training labels for {target}")
    model = HistGradientBoostingClassifier(
        max_iter=80, max_leaf_nodes=15, learning_rate=0.08,
        l2_regularization=10, min_samples_leaf=50,
        early_stopping=False, random_state=42,
    )
    model.fit(labelled[FEATURES], labelled[target].astype(int))
    return model


def _fit_validation_od(earlier):
    return _classifier(earlier, "y_od")


def _brier_alpha(rows, baseline, rule, mask):
    selected = rows.loc[mask]
    if len(selected) < 30:
        return {"lambda_baseline": 1.0, "validation_n": int(len(selected)),
                "reason": "fewer_than_30_validation_rows"}
    p_base = baseline[mask.to_numpy()]
    p_rule = rule[mask.to_numpy()]
    y = selected.y_od.to_numpy(float)
    scores = [(float(np.mean((weight * p_base + (1 - weight) * p_rule - y) ** 2)),
               -float(weight)) for weight in GRID]
    score, negative_weight = min(scores)
    return {"lambda_baseline": -negative_weight, "validation_n": int(len(selected)),
            "validation_brier": score,
            "validation_start": selected.issue_time.min().isoformat(),
            "validation_end": selected.issue_time.max().isoformat()}


def _physical_weights(validation, baseline):
    weights = {}
    for lead, lower, upper in ((1, 1, 1), (6, 2, 6), (24, 7, 24), (48, 25, 48)):
        mask = validation.lead_h.between(lower, upper) & validation.y_od.notna()
        mask &= validation.rule_od25_ens.notna()
        weights[str(lead)] = _brier_alpha(validation, baseline,
                                         validation.rule_od25_ens.to_numpy(float), mask)
    return weights


def _regime_weights(validation, raw):
    y = validation.y_od.to_numpy(float)
    prior = validation.od_at_issue.to_numpy(float)
    keys = blend_keys(validation)
    horizons = np.select([validation.lead_h <= 1, validation.lead_h <= 6,
                          validation.lead_h <= 24], HORIZONS[:3], default=HORIZONS[3])

    def best(mask):
        selected = mask & np.isfinite(y) & np.isfinite(raw) & np.isfinite(prior)
        if not selected.any():
            return 1.0
        errors = [np.mean((weight * raw[selected] + (1 - weight) * prior[selected] - y[selected]) ** 2)
                  for weight in GRID]
        return float(GRID[int(np.argmin(errors))])

    result = {}
    for horizon in HORIZONS:
        period_rows = (horizons == horizon) & np.isfinite(y) & np.isfinite(raw) & np.isfinite(prior)
        fallback = best(period_rows)
        for regime in REGIMES:
            selected = period_rows & (keys == f"{horizon}:{regime}")
            result[f"{horizon}:{regime}"] = best(selected) if selected.sum() >= 50 else fallback
    return result


def _horizon_alpha(rows, weights):
    buckets = np.select([rows.lead_h.eq(1), rows.lead_h.between(2, 6),
                         rows.lead_h.between(7, 24)], (1, 6, 24), default=48)
    return np.asarray([weights[str(lead)]["lambda_baseline"] for lead in buckets])


def _transition_alpha(rows, weights):
    return np.asarray([weights[key] for key in blend_keys(rows)])


def _metrics(rows, candidate_name, rule_cohort=False):
    result = {}
    for lead in LEADS:
        mask = rows.lead_h.eq(lead) & rows.point_in_outer_fold & rows.y_od.notna()
        if rule_cohort:
            mask &= rows.rule_od25_ens.notna()
        selected = rows.loc[mask]
        y = selected.y_od.to_numpy(float)
        changed = selected.changed_within_lead.fillna(False).to_numpy(bool)
        record = {"n": int(len(selected)), "change_n": int(changed.sum())}
        for label, column in (("baseline", "p_baseline"), (candidate_name, "p_candidate")):
            prediction = selected[column].to_numpy(float)
            right = (prediction >= 0.5) == y
            record[label] = {"accuracy": float(right.mean()) if len(y) else None,
                             "brier": float(np.mean((prediction - y) ** 2)) if len(y) else None,
                             "change_accuracy": float(right[changed].mean()) if changed.any() else None}
        record["candidate_minus_baseline"] = {
            name: (record[candidate_name][name] - record["baseline"][name]
                   if record[candidate_name][name] is not None and record["baseline"][name] is not None else None)
            for name in ("accuracy", "brier", "change_accuracy")}
        result[str(lead)] = record
    return result


def _provenance(cache_path, frame, cache_reference=None):
    source_files = ("data/ground_truth/dfld_hourly.csv", "data/eddf_metar.parquet",
                    "data/ground_truth/dfld_half_hourly.csv.gz",
                    "data/openmeteo_previous_runs.parquet",
                    "data/openmeteo_previous_runs_multimodel.parquet",
                    "data/openmeteo_previous_runs_pressure.parquet", "ml/features.py",
                    "ml/rules.py", "ml/rules.json", "ml/train.py", "ml/predict.py",
                    "ml/quality.py", "ml/challengers.py")
    sources = {}
    for relative in source_files:
        path = ROOT / relative
        if path.exists():
            sources[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    values = pd.util.hash_pandas_object(frame[FEATURES], index=False).to_numpy().tobytes()
    reference = json.loads(Path(cache_reference).read_text()) if cache_reference else {}
    expected_cache_sha = reference.get("file_sha256", reference.get("sha256"))
    return {"feature_cache": str(cache_path) if cache_path else "cached_dataset(stride=6)",
            "feature_cache_sha256": hashlib.sha256(Path(cache_path).read_bytes()).hexdigest()
            if cache_path else None,
            "feature_cache_sha256_reference": expected_cache_sha,
            "feature_values_sha256": hashlib.sha256(values).hexdigest(),
            "feature_names": FEATURES,
            "feature_names_sha256": hashlib.sha256(json.dumps(FEATURES).encode()).hexdigest(),
            "source_sha256": sources,
            "cache_input_link_verified": bool(cache_reference),
            "cache_input_note": ("source hashes checked; cache binary hash anchored by reference" if expected_cache_sha else
                                 "source hashes checked when referenced; loaded cache and feature values hashed, no trusted binary digest supplied" if cache_reference else
                                 "cache bytes and feature values hashed; source relationship not independently verified"),
            "feature_cache_reference": str(cache_reference) if cache_reference else None,
            "python": platform.python_version(), "pandas": pd.__version__, "scikit_learn": sklearn.__version__}


def _load_frame(cache_path=None, reference_path=None):
    if reference_path:
        reference = json.loads(Path(reference_path).read_text())
        referenced_cache = Path(reference["file"]).expanduser().resolve()
        if cache_path and Path(cache_path).expanduser().resolve() != referenced_cache:
            raise ValueError("--feature-cache does not match the cache reference")
        cache_path = referenced_cache
        input_hashes = reference.get("input_hashes", {})
        if not input_hashes:
            raise ValueError("Feature cache reference has no source input hashes")
        expected_cache_sha = reference.get("file_sha256", reference.get("sha256"))
        if expected_cache_sha and hashlib.sha256(cache_path.read_bytes()).hexdigest() != expected_cache_sha:
            raise ValueError("Feature cache binary hash mismatch")
        for relative, expected in input_hashes.items():
            source = ROOT / relative
            if not source.exists() or hashlib.sha256(source.read_bytes()).hexdigest() != expected:
                raise ValueError(f"Feature cache input hash mismatch: {relative}")
    if cache_path:
        loaded = joblib.load(cache_path)
        frame = loaded if isinstance(loaded, pd.DataFrame) else loaded[0]
    else:
        frame, _, _, _ = cached_dataset(6)
    missing = (set(FEATURES) | {"issue_time", "time", "lead_h", "label_available_at",
                               "od_at_issue", "y_od", "changed_within_lead", "rule_od25_ens"}) - set(frame.columns)
    if missing:
        raise ValueError(f"Feature cache is missing columns: {', '.join(sorted(missing))}")
    frame = frame.copy()
    frame["issue_time"] = pd.to_datetime(frame.issue_time, utc=True)
    frame["time"] = pd.to_datetime(frame.time, utc=True)
    frame["label_available_at"] = pd.to_datetime(frame.label_available_at, utc=True)
    return frame, cache_path


def _check_model(models, path, start):
    if models.get("version") != BASELINE_VERSION:
        raise ValueError(f"Expected {BASELINE_VERSION} at {path}")
    trained = pd.Timestamp(models["trained_through"])
    if trained.tzinfo is None:
        trained = trained.tz_localize("UTC")
    if trained >= start:
        raise ValueError(f"Saved baseline contains labels at or after test start: {path}")
    estimator = models["od"]
    if estimator.n_features_in_ != len(FEATURES):
        raise ValueError(f"Baseline feature count changed: {path}")
    if hasattr(estimator, "feature_names_in_") and list(estimator.feature_names_in_) != list(FEATURES):
        raise ValueError(f"Baseline feature names/order changed: {path}")


def _report_events(rows, candidate):
    # The physical-mixture benchmark was originally scored on complete point
    # test trajectories; the direction-transition probe retained full windows.
    if candidate == "physical-blend":
        rows = rows.loc[rows.point_in_outer_fold]
    issue_counts = rows.groupby("issue_time").size()
    complete_ids = issue_counts.index[issue_counts.eq(48)]
    complete = rows.loc[rows.issue_time.isin(complete_ids)]
    if not len(complete):
        return {"complete_48h_issue_windows": 0, "baseline": None, "candidate": None}
    truth = pd.read_csv(ROOT / "data/ground_truth/dfld_half_hourly.csv.gz", dtype={"od": str})
    local = (pd.to_datetime(truth.date_local) + pd.to_timedelta(truth.hour_local, unit="h")
             + pd.to_timedelta(truth.minute_local, unit="m"))
    truth["time"] = local.dt.tz_localize("Europe/Berlin", ambiguous="NaT", nonexistent="NaT").dt.tz_convert("UTC")
    truth = truth.dropna(subset=["time"])
    events = {}
    for name, column in (("baseline", "p_baseline"), ("candidate", "p_candidate")):
        forecast = complete[["issue_time", "time", "lead_h", "od_at_issue", column]].rename(
            columns={column: "p_od25"})
        events[name] = {"unique_events": od_change_events(forecast, truth),
                        "first_change_windows": next_change_timing(forecast, truth)}
    return {"complete_48h_issue_windows": int(len(complete_ids)), "cohort": events}


def _read_report_predictions(output, candidate):
    report_path = output / "report.json"
    predictions_path = output / "predictions.csv.gz"
    if not report_path.exists() or not predictions_path.exists():
        raise FileNotFoundError("--rescore needs report.json and predictions.csv.gz in --out")
    report = json.loads(report_path.read_text())
    if report.get("candidate") != candidate:
        raise ValueError("--candidate does not match the saved research report")
    return report, pd.read_csv(predictions_path, compression="gzip")


def _rescore(output, report, rows, candidate):
    rule_cohort = candidate == "physical-blend"
    report["point_metrics"] = _metrics(rows, candidate, rule_cohort=rule_cohort)
    report["event_metrics"] = _report_events(rows, candidate)
    event_cohort = ("complete 48h issue trajectories whose labels were available before the test-month boundary"
                    if candidate == "physical-blend" else
                    "complete 48h issue trajectories for test-month issue times, retaining unlabelled overhang hours")
    report["row_predictions"] = {"file": "predictions.csv.gz", "rows": int(len(rows)),
        "point_cohort": "label available before outer test-month end; exact leads 1,6,24,48",
        "event_cohort": event_cohort}
    (output / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return report


def run(args):
    output = safe_output(args.out, allow_existing=args.rescore)
    if args.rescore:
        report, rows = _read_report_predictions(output, args.candidate)
        report = _rescore(output, report, rows, args.candidate)
        return report

    frame, cache_path = _load_frame(args.feature_cache, args.feature_cache_reference)
    provenance = _provenance(cache_path, frame, args.feature_cache_reference)
    months = pd.period_range(args.start_month, args.end_month, freq="M")
    rows_by_fold, fold_reports = [], []
    for month in months:
        period, start, end, train, test = split_fold(frame, month)
        model_path = ROOT / f"ml/models/fold-{period}.joblib"
        if not model_path.exists():
            raise FileNotFoundError(f"Missing saved v6 comparison fold: {model_path}")
        baseline_model = joblib.load(model_path)
        _check_model(baseline_model, model_path, start)
        baseline = od_probability(baseline_model, test)
        validation_start = train.issue_time.max() - pd.Timedelta(days=60)
        earlier = train.loc[train.label_available_at < validation_start].copy()
        validation = train.loc[(train.issue_time >= validation_start)
                               & (train.label_available_at < start)].copy()
        weights = {}

        if args.candidate == "physical-blend":
            early_model = _fit_validation_od(earlier)
            validation_baseline = od_probability(
                {"od": early_model, "od_model_weight": baseline_model["od_model_weight"]}, validation)
            weights = _physical_weights(validation, validation_baseline)
            lead_weights = _horizon_alpha(test, weights)
            candidate = physical_blend(baseline, test.rule_od25_ens.to_numpy(float), lead_weights)
            validation_candidate = physical_blend(
                validation_baseline, validation.rule_od25_ens.to_numpy(float),
                _horizon_alpha(validation, weights))
            validation_mask = validation.y_od.notna() & validation.rule_od25_ens.notna()
            validation_prediction = validation_candidate[validation_mask.to_numpy()]
            validation_target = validation.loc[validation_mask, "y_od"].to_numpy(float)
        else:
            early = earlier.dropna(subset=["y_od", "od_at_issue"]).copy()
            valid = validation.dropna(subset=["y_od", "od_at_issue"]).copy()
            early["y_switch"] = (early.y_od.to_numpy(int) != early.od_at_issue.to_numpy(int)).astype(int)
            early_model = _classifier(early, "y_switch")
            validation_raw = opposite_to_p25(probability(early_model, valid[FEATURES]),
                                             valid.od_at_issue.to_numpy(float))
            weights = _regime_weights(valid, validation_raw)
            lead_weights = _transition_alpha(test, weights)
            final_train = train.dropna(subset=["y_od", "od_at_issue"]).copy()
            final_train["y_switch"] = (final_train.y_od.to_numpy(int)
                                        != final_train.od_at_issue.to_numpy(int)).astype(int)
            final_model = _classifier(final_train, "y_switch")
            raw = opposite_to_p25(probability(final_model, test[FEATURES]), test.od_at_issue.to_numpy(float))
            candidate = lead_weights * raw + (1 - lead_weights) * test.od_at_issue.to_numpy(float)
            validation_candidate = np.asarray([weights[key] for key in blend_keys(valid)]) * validation_raw + \
                (1 - np.asarray([weights[key] for key in blend_keys(valid)])) * valid.od_at_issue.to_numpy(float)
            validation_prediction = validation_candidate
            validation_target = valid.y_od.to_numpy(float)

        scored = test.loc[test.point_in_outer_fold & test.y_od.notna()]
        validation_brier = float(np.mean((validation_prediction - validation_target) ** 2)) \
            if len(validation_target) else None
        fold_reports.append({"month": str(period), "train_rows": int(len(train)),
            "train_label_boundary": train.label_available_at.max().isoformat(),
            "validation_start": validation_start.isoformat(),
            "validation_rows": int(len(validation_target)), "validation_candidate_brier": validation_brier,
            "test_issue_rows": int(len(test)), "point_test_rows": int(len(scored)),
            "saved_baseline": str(model_path.relative_to(ROOT)),
            "baseline_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
            "baseline_trained_through": baseline_model["trained_through"],
            "baseline_version": baseline_model["version"],
            "feature_count": int(baseline_model["od"].n_features_in_),
            "weights_selected_on_validation_only": weights})

        local = test[["issue_time", "time", "lead_h", "od_at_issue", "y_od",
                      "label_available_at", "changed_within_lead", "rule_od25_ens",
                      "point_in_outer_fold"]].copy()
        local["p_baseline"] = baseline
        local["p_candidate"] = candidate
        local["outer_month"] = str(period)
        rows_by_fold.append(local)

    predictions = pd.concat(rows_by_fold, ignore_index=True)
    candidate_definition = ("lambda[h] * p_v6 + (1-lambda[h]) * rule_od25_ens; missing rule falls back to p_v6"
                            if args.candidate == "physical-blend" else
                            "HGB P(target OD differs from issue OD), mapped to P(OD25), blended with issue OD by v6 horizon/regime weights")
    report = {"candidate": args.candidate, "candidate_definition": candidate_definition,
        "baseline_version": BASELINE_VERSION,
        "months": [str(x) for x in months],
        "limits": ["Exploratory Jul-Oct months overlap previous v6 development; not a fresh confirmation set.",
                   "OD change-label candidate predicts endpoint direction differs from issue direction; it is not a first-event hazard.",
                   "Overlapping issue windows are correlated; row counts are not independent samples."],
        "provenance": provenance, "folds": fold_reports}
    output.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(output / "predictions.csv.gz", index=False, compression="gzip")
    return _rescore(output, report, predictions, args.candidate)


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--candidate", required=True, choices=("opposite-direction", "physical-blend"))
    result.add_argument("--feature-cache", type=Path, help="Optional joblib cache; default uses cached_dataset(6)")
    result.add_argument("--feature-cache-reference", type=Path,
                        help="Optional JSON with source hashes to verify against this checkout")
    result.add_argument("--start-month", default="2026-07")
    result.add_argument("--end-month", default="2026-10")
    result.add_argument("--out", required=True, type=Path, help="Research report folder, outside protected production paths")
    result.add_argument("--rescore", action="store_true", help="Recompute metrics from saved predictions without training")
    return result


def main():
    args = parser().parse_args()
    try:
        report = run(args)
    except (ValueError, FileNotFoundError) as error:
        raise SystemExit(str(error)) from error
    print(json.dumps({"candidate": report["candidate"], "out": str(args.out),
                      "point_metrics": report["point_metrics"], "event_metrics": report["event_metrics"]}, indent=2))


if __name__ == "__main__":
    main()
