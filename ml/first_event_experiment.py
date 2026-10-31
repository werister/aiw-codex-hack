"""Run a research-only walk-forward forecast for the first OD change by lead.

This experiment predicts P(any OD change after issue time T and by hour h).
That cumulative event probability is not the marginal probability of OD 25.
Results are written only to the requested research folder.
"""

import argparse
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

from ml.challengers import BASELINE_VERSION, safe_output
from ml.features import FEATURES
from ml.predict import od_probability, probability
from ml.quality import next_change_timing, od_change_events
from ml.train import cached_dataset


ROOT = Path(__file__).resolve().parents[1]
MONTHS = tuple(pd.Period(month, freq="M") for month in
               ("2026-07", "2026-08", "2026-09", "2026-10"))
LEADS = (1, 6, 24, 48)
OUTER_TRAINING_LAG_H = 49


def load_half_hour_truth(path=None):
    """Load the recorded half-hour runway direction on a UTC timeline."""
    path = Path(path) if path else ROOT / "data/ground_truth/dfld_half_hourly.csv.gz"
    truth = pd.read_csv(path, dtype={"od": str})
    local = (pd.to_datetime(truth.date_local) +
             pd.to_timedelta(truth.hour_local, unit="h") +
             pd.to_timedelta(truth.minute_local, unit="m"))
    truth["time"] = (local.dt.tz_localize("Europe/Berlin", ambiguous="NaT",
        nonexistent="NaT").dt.tz_convert("UTC").dt.as_unit("ns"))
    truth = truth.dropna(subset=["time"]).sort_values("time").reset_index(drop=True)
    duplicate = truth.time.duplicated(keep=False)
    duplicate_rows = int(duplicate.sum())
    if duplicate_rows:
        truth = truth.loc[~duplicate].reset_index(drop=True)
    return truth[["time", "od"]], duplicate_rows


def attach_first_event_targets(frame, truth, duplicate_truth_timestamps_removed=0):
    """Label complete 97-bin windows; all labels become available at T+49 h.

    The target is positive by lead h if any transition occurs strictly after T
    and no later than T+h. Every row from an issue shares the conservative
    label-availability time T+49 h: 48 h of truth plus a one-hour lag.
    """
    required = {"issue_time", "time", "lead_h"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Feature frame is missing: {', '.join(sorted(missing))}")
    truth = truth[["time", "od"]].copy()
    truth["time"] = pd.to_datetime(truth.time, utc=True, errors="coerce").dt.as_unit("ns")
    truth = truth.dropna(subset=["time"]).sort_values("time").reset_index(drop=True)
    frame = frame.copy().reset_index(drop=True)
    frame["issue_time"] = pd.to_datetime(frame.issue_time, utc=True).dt.as_unit("ns")
    frame["time"] = pd.to_datetime(frame.time, utc=True).dt.as_unit("ns")

    truth_times = pd.DatetimeIndex(truth.time).asi8
    truth_state = truth.od.map({"07": 0, "25": 1}).to_numpy(dtype=float)
    valid_state = np.isfinite(truth_state)
    half_hour_ns = int(pd.Timedelta(minutes=30).value)
    availability_lag_ns = int(pd.Timedelta(hours=OUTER_TRAINING_LAG_H).value)

    n = len(frame)
    event_by_lead = np.full(n, np.nan)
    label_available_ns = np.full(n, np.iinfo(np.int64).min, dtype=np.int64)
    truth_initial = np.full(n, np.nan)
    change_count = np.full(n, np.nan)
    truth_final = np.full(n, np.nan)
    first_change_ns = np.full(n, np.iinfo(np.int64).min, dtype=np.int64)
    complete = unknown = incomplete = bad_feature_grids = 0
    double_change_same_final = 0
    double_change_example = None

    for issue, positions in frame.groupby("issue_time", sort=False).indices.items():
        issue = pd.Timestamp(issue).as_unit("ns")
        issue_ns = issue.value
        positions = np.asarray(positions, dtype=int)
        rows = frame.iloc[positions]
        leads = rows.lead_h.to_numpy(int)
        if len(rows) != 48 or not np.array_equal(np.sort(leads), np.arange(1, 49)):
            bad_feature_grids += 1
            continue
        target_times = pd.DatetimeIndex(rows.time).as_unit("ns").asi8
        expected_targets = issue_ns + leads.astype(np.int64) * int(pd.Timedelta(hours=1).value)
        if not np.array_equal(target_times, expected_targets):
            bad_feature_grids += 1
            continue

        start = int(np.searchsorted(truth_times, issue_ns, side="left"))
        expected_truth = issue_ns + np.arange(97, dtype=np.int64) * half_hour_ns
        observed_truth = truth_times[start:start + 97]
        if len(observed_truth) != 97 or not np.array_equal(observed_truth, expected_truth):
            incomplete += 1
            continue
        values = truth_state[start:start + 97]
        if not valid_state[start:start + 97].all():
            unknown += 1
            continue

        complete += 1
        change_indices = np.flatnonzero(values[1:] != values[:-1]) + 1
        change_times = expected_truth[change_indices]
        labels = (np.searchsorted(change_times, target_times, side="right") > 0).astype(float)
        event_by_lead[positions] = labels
        label_available_ns[positions] = issue_ns + availability_lag_ns
        truth_initial[positions] = values[0]
        change_count[positions] = len(change_indices)
        truth_final[positions] = values[-1]
        lead_48_position = int(np.flatnonzero(leads == 48)[0])
        if len(change_times):
            first_change_ns[positions] = change_times[0]

        if len(change_indices) >= 2 and values[-1] == values[0]:
            double_change_same_final += 1
            # Regression guard: two real changes are still an event at 48 h.
            assert labels[lead_48_position] == 1.0
            if double_change_example is None:
                double_change_example = {"issue_time": issue.isoformat(),
                    "initial_od": "25" if values[0] else "07",
                    "final_od": "25" if values[-1] else "07",
                    "change_count": int(len(change_indices)),
                    "first_change_time": pd.Timestamp(change_times[0], tz="UTC").isoformat(),
                    "event_by_lead_48": bool(labels[lead_48_position])}

    frame["event_by_lead"] = event_by_lead
    frame["event_label_available_at"] = pd.to_datetime(label_available_ns, unit="ns", utc=True)
    frame["truth_initial_od25"] = truth_initial
    frame["truth_change_count_48h"] = change_count
    frame["truth_final_od25"] = truth_final
    frame["truth_first_change_time"] = pd.to_datetime(first_change_ns, unit="ns", utc=True)
    coverage = {"total_issue_windows": int(frame.issue_time.nunique()),
        "complete_97_bin_windows": complete, "incomplete_truth_windows": incomplete,
        "unknown_direction_windows": unknown,
        "bad_feature_trajectories": bad_feature_grids,
        "unlabelled_issue_windows": incomplete + unknown + bad_feature_grids,
        "duplicate_truth_rows_removed": int(duplicate_truth_timestamps_removed)}
    at_48 = frame.loc[frame.lead_h.eq(48)]
    target_audit = {"multiple_change_windows": int(at_48.truth_change_count_48h.gt(1).sum()),
        "multiple_changes_returning_to_initial_state": double_change_same_final,
        "two_changes_same_final_remain_positive": double_change_example}
    return frame, coverage, target_audit


def _load_features(feature_cache=None):
    if feature_cache:
        loaded = joblib.load(Path(feature_cache).expanduser())
        frame = loaded if isinstance(loaded, pd.DataFrame) else loaded[0]
        verified = False
        description = "user-supplied feature cache; input provenance not verified"
    else:
        frame, _, _, _ = cached_dataset(6)
        verified = True
        description = "canonical cached_dataset(6) pipeline"
    required = set(FEATURES) | {"issue_time", "time", "lead_h", "od_at_issue"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Feature cache is missing: {', '.join(sorted(missing))}")
    frame = frame.copy()
    frame["issue_time"] = pd.to_datetime(frame.issue_time, utc=True).dt.as_unit("ns")
    frame["time"] = pd.to_datetime(frame.time, utc=True).dt.as_unit("ns")
    return frame, verified, description


def _fit(rows):
    labelled = rows.dropna(subset=["event_by_lead"])
    if labelled.empty or labelled.event_by_lead.nunique() < 2:
        raise ValueError("First-event training data must contain both target classes")
    estimator = HistGradientBoostingClassifier(max_iter=80, max_leaf_nodes=15,
        learning_rate=0.08, l2_regularization=10, min_samples_leaf=50,
        early_stopping=False, random_state=42)
    estimator.fit(labelled[FEATURES], labelled.event_by_lead.astype(int))
    return estimator


def predict_cumulative_event(estimator, rows):
    """Return HGB probabilities made nondecreasing by one fixed cumulative max."""
    raw = probability(estimator, rows[FEATURES])
    values = pd.DataFrame({"issue_time": rows.issue_time.to_numpy(),
        "lead_h": rows.lead_h.to_numpy(), "raw": raw}, index=rows.index)
    values["cumulative"] = np.nan
    for positions in values.groupby("issue_time", sort=False).indices.values():
        positions = np.asarray(positions, dtype=int)
        ordered = positions[np.argsort(values.lead_h.iloc[positions].to_numpy())]
        indices = values.index.to_numpy()[ordered]
        values.loc[indices, "cumulative"] = np.maximum.accumulate(values.raw.iloc[ordered].to_numpy())
    result = values.cumulative.to_numpy(float)
    if not np.isfinite(result).all() or ((result < 0) | (result > 1)).any():
        raise ValueError("First-event probabilities must be finite and within [0, 1]")
    return result


def _train_prevalence(rows):
    return {str(lead): float(rows.loc[rows.lead_h.eq(lead), "event_by_lead"].mean())
            for lead in range(1, 49)}


def _brier(rows, prevalence):
    results = []
    for lead in LEADS:
        selected = rows.loc[rows.lead_h.eq(lead)].dropna(
            subset=["event_by_lead", "p_event_by_h"])
        y = selected.event_by_lead.to_numpy(float)
        p = selected.p_event_by_h.to_numpy(float)
        prior = prevalence[str(lead)]
        results.append({"lead_h": lead, "n": len(selected),
            "positive_n": int(y.sum()), "event_rate": float(y.mean()) if len(y) else None,
            "model_brier": float(np.mean((p - y) ** 2)) if len(y) else None,
            "train_prevalence_brier": float(np.mean((prior - y) ** 2)) if len(y) else None})
    return results


def _event_scores(rows, truth):
    counts = rows.groupby("issue_time").size()
    complete_ids = counts.index[counts.eq(48)]
    complete = rows.loc[rows.issue_time.isin(complete_ids)].copy()
    issue_state = complete.groupby("issue_time").od_at_issue.apply(
        lambda values: pd.to_numeric(values, errors="coerce").isin([0, 1]).all())
    comparable_ids = issue_state.index[issue_state]
    complete = complete.loc[complete.issue_time.isin(comparable_ids)].copy()
    alignment = complete.groupby("issue_time").agg(
        known=("od_at_issue", "first"), truth_at_t=("truth_initial_od25", "first"))
    alignment["known"] = pd.to_numeric(alignment.known, errors="coerce")
    mismatches = alignment.known.ne(alignment.truth_at_t)

    # q=P(first change by h); convert to a directional path only for the
    # event-timing scorers, using the OD known at issue time, never truth at T.
    current = pd.to_numeric(complete.od_at_issue, errors="coerce").to_numpy(float)
    event_p = complete.p_event_by_h.to_numpy(float)
    complete["p_od25_first_event"] = np.where(current == 1, 1 - event_p,
        np.where(current == 0, event_p, np.nan))
    baseline = complete[["issue_time", "time", "lead_h", "od_at_issue", "p_od25_baseline"]].rename(
        columns={"p_od25_baseline": "p_od25"})
    first_event = complete[["issue_time", "time", "lead_h", "od_at_issue", "p_od25_first_event"]].rename(
        columns={"p_od25_first_event": "p_od25"}).dropna(subset=["p_od25"])
    return {"complete_comparable_issue_windows": int(len(comparable_ids)),
        "known_issue_od_differs_from_truth_at_t_windows": int(mismatches.sum()),
        "disagreement_share": float(mismatches.mean()) if len(mismatches) else None,
        "disagreements_retained": True,
        "baseline_v6": {"unique_events": od_change_events(baseline, truth),
                        "next_change_timing": next_change_timing(baseline, truth)},
        "first_event": {"unique_events": od_change_events(first_event, truth),
                        "next_change_timing": next_change_timing(first_event, truth)}}


def run(args):
    output = safe_output(args.out, ROOT)
    frame, cache_verified, cache_description = _load_features(args.feature_cache)
    truth_path = ROOT / "data/ground_truth/dfld_half_hourly.csv.gz"
    truth, duplicate_truth_rows = load_half_hour_truth(truth_path)
    labeled, coverage, target_audit = attach_first_event_targets(frame, truth, duplicate_truth_rows)
    fold_reports = []
    test_rows = []

    for month in MONTHS:
        start = month.start_time.tz_localize("UTC")
        end = (month + 1).start_time.tz_localize("UTC")
        train = labeled.loc[(labeled.issue_time < start) &
                            (labeled.event_label_available_at < start)].copy()
        validation_start = train.issue_time.max() - pd.Timedelta(days=60)
        inner_train = train.loc[train.event_label_available_at < validation_start].copy()
        validation = train.loc[(train.issue_time >= validation_start) &
                               (train.event_label_available_at < start)].copy()
        outer_test = labeled.loc[(labeled.issue_time >= start) & (labeled.issue_time < end) &
                                 labeled.event_by_lead.notna()].copy()
        if inner_train.empty or validation.empty or outer_test.empty:
            raise ValueError(f"Insufficient complete first-event windows in {month}")
        if inner_train.event_label_available_at.max() >= validation_start:
            raise ValueError(f"Inner training labels cross validation boundary in {month}")
        if validation.event_label_available_at.max() >= start or train.event_label_available_at.max() >= start:
            raise ValueError(f"Training or validation labels cross outer boundary in {month}")

        inner_model = _fit(inner_train)
        validation["p_event_by_h"] = predict_cumulative_event(inner_model, validation)
        inner_prevalence = _train_prevalence(inner_train)
        validation_brier = _brier(validation, inner_prevalence)

        model = _fit(train)
        prevalence = _train_prevalence(train)
        issue_ids = outer_test.issue_time.drop_duplicates()
        test_features = frame.loc[frame.issue_time.isin(issue_ids)].copy().sort_values(
            ["issue_time", "lead_h"]).reset_index(drop=True)
        scored = labeled.loc[labeled.issue_time.isin(issue_ids)].copy().sort_values(
            ["issue_time", "lead_h"]).reset_index(drop=True)
        if len(test_features) != len(scored) or len(scored) != len(issue_ids) * 48:
            raise ValueError(f"Test windows in {month} are not complete 48-hour trajectories")
        scored["p_event_raw"] = probability(model, test_features[FEATURES])
        scored["p_event_by_h"] = predict_cumulative_event(model, test_features)
        scored["p_event_train_prevalence"] = [prevalence[str(int(lead))] for lead in scored.lead_h]
        scored["p_od25_baseline"] = od_probability(
            _load_baseline(month, start), test_features)
        state = pd.to_numeric(scored.od_at_issue, errors="coerce").to_numpy(float)
        event_p = scored.p_event_by_h.to_numpy(float)
        scored["p_od25_first_event"] = np.where(state == 1, 1 - event_p,
            np.where(state == 0, event_p, np.nan))
        scored["outer_month"] = str(month)
        scored["event_label_available_before_month_end"] = (
            scored.event_label_available_at < end).to_numpy(bool)
        test_rows.append(scored)

        fold_reports.append({"month": str(month), "train_rows": len(train),
            "train_label_available_before": start.isoformat(),
            "validation_start": validation_start.isoformat(),
            "inner_train_rows": len(inner_train), "inner_validation_rows": len(validation),
            "inner_validation_brier_fixed_model": validation_brier,
            "test_issue_windows": int(len(issue_ids)), "test_rows": len(scored),
            "test_first_event_brier": _brier(scored, prevalence),
            "train_event_prevalence_by_lead": prevalence,
            "model": "HistGradientBoostingClassifier(max_iter=80,max_leaf_nodes=15,learning_rate=0.08,l2_regularization=10,min_samples_leaf=50,early_stopping=False,random_state=42)",
            "threshold": 0.5, "threshold_or_hyperparameters_selected_on_validation": False})
        print(f"Completed {month}: train={len(train)}, validation={len(validation)}, "
              f"test_windows={len(issue_ids)}", flush=True)

    predictions = pd.concat(test_rows, ignore_index=True)
    pooled_brier = []
    for lead in LEADS:
        rows = predictions.loc[predictions.lead_h.eq(lead)]
        positive = rows.event_by_lead.notna()
        selected = rows.loc[positive]
        if selected.empty:
            pooled_brier.append({"lead_h": lead, "n": 0})
            continue
        y = selected.event_by_lead.to_numpy(float)
        p = selected.p_event_by_h.to_numpy(float)
        prior = selected.p_event_train_prevalence.to_numpy(float)
        pooled_brier.append({"lead_h": lead, "n": len(selected),
            "positive_n": int(y.sum()), "event_rate": float(y.mean()),
            "model_brier": float(np.mean((p - y) ** 2)),
            "train_prevalence_brier": float(np.mean((prior - y) ** 2)),
            "model_minus_prevalence_brier": float(np.mean((p - y) ** 2) - np.mean((prior - y) ** 2))})

    event_scores = _event_scores(predictions, truth)
    predictions_path = output / "predictions.csv.gz"
    output.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(predictions_path, index=False, compression="gzip")
    source_files = [truth_path, Path(__file__), ROOT / "ml/features.py",
        ROOT / "ml/predict.py", ROOT / "ml/train.py", ROOT / "ml/quality.py"]
    report = {"experiment": "first future OD change by forecast hour",
        "candidate": "cumulative-first-event",
        "outer_months": [str(month) for month in MONTHS],
        "feature_cache": cache_description, "feature_cache_verified": cache_verified,
        "feature_count": len(FEATURES), "feature_names": FEATURES,
        "target": "any transition in half-hour recorded OD strictly after T and by T+h; later transitions do not cancel the event",
        "label_availability": "all labels for a complete issue window become available at T+49h (97 bins plus one-hour lag); strict purges apply at inner and outer boundaries",
        "inner_validation": "last 60 days of each outer training fold; fixed model and 0.5 event threshold are reported without selection",
        "probability_shape": "one fixed cumulative maximum enforces nondecreasing P(first event by h)",
        "direction_for_event_metrics": "convert using only issue-known OD; truth at T is used only to form labels and score outcomes",
        "outer_test_future_labels": "complete test issue windows may extend beyond the calendar month; those later truths are evaluation-only",
        "coverage": coverage, "target_audit": target_audit,
        "folds": fold_reports, "pooled_event_brier": pooled_brier,
        "event_metrics": event_scores,
        "baseline_model_version": BASELINE_VERSION,
        "row_predictions": {"file": predictions_path.name, "rows": len(predictions),
            "issue_windows": int(predictions.issue_time.nunique()),
            "complete_48h_issue_windows": event_scores["complete_comparable_issue_windows"]},
        "source_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                           for path in source_files},
        "limitations": [
            "Exploratory outer test months July-October 2026 were previously inspected in the broader forecast evaluation; this is not a fresh untouched confirmation period.",
            "The target is based on DFLD recorded directions, not certified flight movement logs.",
            "Half-hour truth cannot reveal two changes within the same half-hour bin.",
            "The predicted direction is the opposite of the issue-known OD; disagreements between that input and truth at T are retained as difficult cases.",
            "Cumulative event probability is not marginal P(OD25) and does not describe a second change after the first.",
            "The fixed 0.5 warning threshold creates more false alarms and lower timing hit rates than saved v6 in this experiment; no threshold search was performed.",
            "The constant training event prevalence is the Brier reference. Saved v6 marginal P(OD25) is not treated as an event probability.",
            "Issue windows overlap, so event windows and row counts are correlated."]}
    (output / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return report


def _load_baseline(month, start):
    path = ROOT / f"ml/models/fold-{month}.joblib"
    if not path.exists():
        raise FileNotFoundError(f"Missing saved v6 comparison fold: {path}")
    models = joblib.load(path)
    if models.get("version") != BASELINE_VERSION:
        raise ValueError(f"Expected {BASELINE_VERSION} in {path}")
    trained_through = pd.Timestamp(models["trained_through"])
    if trained_through.tzinfo is None:
        trained_through = trained_through.tz_localize("UTC")
    if trained_through >= start:
        raise ValueError(f"Baseline includes labels from test month {month}")
    return models


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--out", required=True, type=Path,
                        help="Research output folder; protected production paths are rejected")
    result.add_argument("--feature-cache", type=Path,
                        help="Optional joblib feature cache. Custom caches are marked unverified.")
    return result


def main():
    args = parser().parse_args()
    try:
        report = run(args)
    except (ValueError, FileNotFoundError) as error:
        raise SystemExit(str(error)) from error
    print(json.dumps({"candidate": report["candidate"],
        "out": str(args.out), "pooled_event_brier": report["pooled_event_brier"],
        "event_metrics": report["event_metrics"]}, indent=2))


if __name__ == "__main__":
    main()
