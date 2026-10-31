"""Walk-forward scores. Runway 18 targets are inferred from METAR wind rules."""

from collections import Counter

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

from ml.features import components
from ml.rules import RULES

LEADS = (1, 6, 24, 48)


def suspect_od_runs(truth, obs, min_hours=3):
    """Flag recorded OD runs for review when repeated METARs exceed a rules limit.

    This rule-derived inconsistency is a review signal, not independent evidence
    that the recorded feed is stuck or that a different direction was flown.
    """
    truth = truth.sort_values("time")
    truth_times = pd.to_datetime(truth.time, utc=True).dt.as_unit("ns")
    obs_for_join = obs[["time", "wind_kt", "wind_dir_deg"]].copy()
    obs_for_join["time"] = pd.to_datetime(obs_for_join.time, utc=True).dt.as_unit("ns")
    truth_for_join = pd.DataFrame({"time": truth_times}, index=truth.index).sort_values("time")
    wind = pd.merge_asof(truth_for_join, obs_for_join.sort_values("time"), on="time",
                         tolerance=pd.Timedelta(hours=1))
    heading = np.where(truth.od.eq("25"), RULES["runway_heading_deg"]["25"], RULES["runway_heading_deg"]["07"])
    tail = components(wind.wind_kt.to_numpy(float), wind.wind_dir_deg.to_numpy(float), heading)
    over = pd.Series(tail >= RULES["landing_tailwind_change_now_kt"], index=truth.index)
    run = truth.od.ne(truth.od.shift()).cumsum()
    return over.groupby(run).transform("sum") >= min_hours


def skill(frame, target):
    ycol, pcol, rcol, bcol = (("y_od", "p_od25", "rule_od25", "od_at_issue") if target == "od"
                            else ("y_r18", "p_18_usable", "rule_18_usable", "persistence_18"))
    result = []
    for lead in LEADS:
        rows = frame.loc[frame.lead_h.eq(lead)].dropna(subset=[ycol, pcol, rcol, bcol])
        record = {"lead_h": lead, "n": len(rows)}
        raw_col = ("p_od25_raw" if target == "od" and "p_od25_raw" in rows else
                   "p_18_usable_raw" if target == "r18" and "p_18_usable_raw" in rows else pcol)
        for name, col in (("model", pcol), ("raw_model", raw_col), ("blend", pcol), ("rule", rcol), ("persistence", bcol)):
            y, p = rows[ycol].to_numpy(float), rows[col].to_numpy(float)
            record[name + "_acc"] = float(np.mean((p >= 0.5) == y)) if len(y) else None
            record[name + "_brier"] = float(np.mean((p - y) ** 2)) if len(y) else None
            changed = rows.changed_within_lead.to_numpy(bool)
            record[name + "_change_acc"] = float(np.mean((p[changed] >= 0.5) == y[changed])) if changed.any() else None
        record["change_n"] = int(rows.changed_within_lead.sum())
        result.append(record)
    return result


def reliability(frame, target, confidence=False):
    if target in ("combined", "certainty"):
        rows = frame.dropna(subset=["y_od", "y_r18", "p_od25", "p_18_usable"])
        od, r18 = rows.p_od25.to_numpy(float), rows.p_18_usable.to_numpy(float)
        p = np.minimum(np.maximum(od, 1 - od), np.maximum(r18, 1 - r18))
        if target == "certainty":
            p = 2 * p - 1
        y = (((od >= 0.5) == rows.y_od) & ((r18 >= 0.5) == rows.y_r18)).to_numpy(float)
        return probability_bins(p, y)
    ycol, pcol = ("y_od", "p_od25") if target == "od" else ("y_r18", "p_18_usable")
    rows = frame.dropna(subset=[ycol, pcol])
    p, y = rows[pcol].to_numpy(float), rows[ycol].to_numpy(float)
    if confidence:
        y = ((p >= 0.5) == y).astype(float)
        p = np.maximum(p, 1 - p)
    return probability_bins(p, y)


def probability_bins(p, y):
    records = []
    for index in range(10):
        low, high = index / 10, (index + 1) / 10
        selected = (p >= low) & ((p < high) if high < 0.999 else (p <= 1))
        records.append({"lower": round(float(low), 1), "upper": round(float(high), 1),
                        "n": int(selected.sum()), "mean_predicted": float(p[selected].mean()) if selected.any() else None,
                        "observed_frequency": float(y[selected].mean()) if selected.any() else None})
    return records


def next_change_timing(frame, truth):
    """Score first next changes, counting missed changes as misses.

    Only complete 48-hour OOS trajectories with complete half-hour truth count.
    False alarms on windows without a change are reported separately.
    """
    _require_columns(frame, {"issue_time", "time", "lead_h", "od_at_issue", "p_od25"}, "forecast")
    _require_columns(truth, {"time", "od"}, "half-hour truth")
    truth = _prepare_truth(truth)
    actual_events = no_change = false_alarm = predicted_count = 0
    excluded = Counter()
    errors = []
    timing_hits_1h = timing_hits_3h = wrong_direction = 0
    for issue, rows in _forecast_windows(frame):
        reason = _forecast_grid_error(issue, rows)
        if reason:
            excluded[reason] += 1
            continue
        bins, reason = _truth_window(truth, issue, 48)
        if reason:
            excluded[reason] += 1
            continue
        try:
            initial = _od(rows.od_at_issue.iloc[0])
        except ValueError:
            excluded["invalid_issue_direction"] += 1
            continue
        predicted_change = _first_predicted_change(rows, initial)
        predicted = predicted_change["time"] if predicted_change is not None else None
        predicted_count += int(predicted is not None)

        # Truth at the issue timestamp establishes the ex-post starting state.
        # The forecast's transition detection still starts from OD known at issue.
        actual_od = bins.od.tolist()
        changes = [(bins.time.iloc[index], actual_od[index]) for index in range(1, len(bins))
                   if actual_od[index] != actual_od[index - 1]]
        if not changes:
            no_change += 1
            false_alarm += int(predicted is not None)
            continue
        actual_events += 1
        if predicted is not None:
            error = abs((predicted - changes[0][0]).total_seconds()) / 3600
            errors.append(error)
            if predicted_change["to"] == changes[0][1]:
                timing_hits_1h += int(error <= 1)
                timing_hits_3h += int(error <= 3)
            else:
                wrong_direction += 1

    return {"n_actual_change_windows": actual_events,
            "within_1h": timing_hits_1h / actual_events if actual_events else None,
            "within_3h": timing_hits_3h / actual_events if actual_events else None,
            "n_wrong_direction": wrong_direction,
            "n_no_change_windows": no_change,
            "false_alarm_rate": false_alarm / no_change if no_change else None,
            "n_predicted_changes": predicted_count,
            "excluded_incomplete_windows": sum(excluded.values()),
            "excluded_windows_by_reason": dict(sorted(excluded.items())),
            "mean_absolute_error_h_when_predicted": float(np.mean(errors)) if errors else None,
            "truth": "DFLD half-hour bins, including observed state at issue time; overlapping issue windows are not independent"}


def period(values):
    return {"start": values.min().isoformat(), "end": values.max().isoformat()}


def _require_columns(frame, names, description):
    missing = names - set(frame.columns)
    if missing:
        raise ValueError(f"{description} is missing columns: {', '.join(sorted(missing))}")


def _forecast_windows(frame):
    for issue, rows in frame.groupby("issue_time", sort=False, dropna=False):
        try:
            issue = pd.Timestamp(issue).as_unit("ns")
            if pd.isna(issue):
                yield pd.NaT, rows
                continue
            if issue.tzinfo is None:
                issue = issue.tz_localize("UTC")
            else:
                issue = issue.tz_convert("UTC")
        except (TypeError, ValueError):
            yield pd.NaT, rows
            continue
        yield issue, rows.sort_values("lead_h")


def _forecast_grid_error(issue, rows):
    if pd.isna(issue):
        return "invalid_issue_time"
    if len(rows) != 48:
        return "incomplete_forecast_grid"
    leads = pd.to_numeric(rows.lead_h, errors="coerce").to_numpy(float)
    if not np.array_equal(leads, np.arange(1, 49, dtype=float)):
        return "invalid_forecast_grid"
    times = pd.to_datetime(rows.time, utc=True, errors="coerce").dt.as_unit("ns")
    expected = pd.Series(pd.date_range(issue + pd.Timedelta(hours=1), periods=48, freq="h")).dt.as_unit("ns")
    if times.isna().any() or not times.reset_index(drop=True).equals(expected):
        return "invalid_forecast_times"
    probabilities = pd.to_numeric(rows.p_od25, errors="coerce").to_numpy(float)
    if not np.isfinite(probabilities).all() or ((probabilities < 0) | (probabilities > 1)).any():
        return "invalid_forecast_probabilities"
    return None


def _od(value):
    if value in ("25", 25, True, 1, 1.0):
        return "25"
    if value in ("07", "7", 7, False, 0, 0.0):
        return "07"
    raise ValueError("OD must be 07 or 25")


def _truth_window(truth, issue, horizon_h):
    end = issue + pd.Timedelta(hours=horizon_h)
    start_index = int(truth.time.searchsorted(issue, side="left"))
    end_index = int(truth.time.searchsorted(end, side="right"))
    rows = truth.iloc[start_index:end_index]
    expected = pd.Series(pd.date_range(issue, issue + pd.Timedelta(hours=horizon_h), freq="30min")).dt.as_unit("ns")
    rows = rows.sort_values("time").reset_index(drop=True)
    rows["time"] = rows.time.dt.as_unit("ns")
    if rows.time.duplicated().any():
        return None, "duplicate_truth_timestamps"
    if len(rows) != len(expected):
        return None, "incomplete_truth_coverage"
    if not rows.time.equals(expected):
        return None, "invalid_truth_timeline"
    if not rows.od.isin(("07", "25")).all():
        return None, "unknown_truth_direction"
    return rows, None


def _prepare_truth(truth):
    """Sort and parse half-hour truth once; each forecast window then slices by time."""
    result = truth[["time", "od"]].copy()
    result["time"] = pd.to_datetime(result.time, utc=True, errors="coerce").dt.as_unit("ns")
    result = result.dropna(subset=["time"]).sort_values("time").reset_index(drop=True)
    return result


def _first_predicted_change(rows, initial_od):
    prediction = np.where(rows.p_od25.to_numpy(float) >= 0.5, "25", "07")
    changed = np.flatnonzero(prediction != np.array([initial_od, *prediction[:-1]]))
    if len(changed):
        index = int(changed[0])
        return {"time": pd.Timestamp(rows.time.iloc[index]).as_unit("ns"), "to": prediction[index]}
    return None


def od_change_events(frame, truth, tolerance_h=3):
    """Match unique DFLD transitions to first-change forecasts, one to one.

    An issue contributes its first predicted transition only. Warnings whose
    predicted time and direction agree with a DFLD change within the tolerance
    are candidate duplicates; a one-to-one assignment maximizes the number of
    matches, then minimizes total timing error. Remaining false warnings are clustered
    by direction and predicted time to avoid counting the same alert at every issue.
    """
    if tolerance_h <= 0:
        raise ValueError("tolerance_h must be positive")
    _require_columns(frame, {"issue_time", "time", "lead_h", "od_at_issue", "p_od25"}, "forecast")
    _require_columns(truth, {"time", "od"}, "half-hour truth")
    truth = _prepare_truth(truth)
    excluded = Counter()
    issues, warnings = [], []
    for issue, rows in _forecast_windows(frame):
        reason = _forecast_grid_error(issue, rows)
        if reason:
            excluded[reason] += 1
            continue
        bins, reason = _truth_window(truth, issue, 48)
        if reason:
            excluded[reason] += 1
            continue
        try:
            initial = _od(rows.od_at_issue.iloc[0])
        except ValueError:
            excluded["invalid_issue_direction"] += 1
            continue
        issues.append(issue)
        predicted = _first_predicted_change(rows, initial)
        if predicted is not None:
            warnings.append({"issue_time": issue, **predicted})

    # Reconstruct each half-hour event once from the union of complete windows.
    events = {}
    for issue in issues:
        bins, _ = _truth_window(truth, issue, 48)
        for index in range(1, len(bins)):
            before, after = bins.od.iloc[index - 1], bins.od.iloc[index]
            if before != after:
                moment = pd.Timestamp(bins.time.iloc[index])
                events[(moment, after)] = {"time": moment, "to": after}
    events = list(events.values())

    edges = []
    tolerance = pd.Timedelta(hours=tolerance_h)
    for warning_index, warning in enumerate(warnings):
        for event_index, event in enumerate(events):
            delta = abs(warning["time"] - event["time"])
            if (warning["to"] == event["to"] and delta <= tolerance
                    and warning["issue_time"] < event["time"]
                    and event["time"] <= warning["issue_time"] + pd.Timedelta(hours=48)):
                edges.append((delta, warning["issue_time"], warning_index, event_index))
    matched_warnings, matched_events, matches = set(), set(), []
    if warnings and events:
        # The dummy columns represent unmatched warnings. A penalty larger than
        # every possible total ETA error makes the assignment maximize match
        # count first, then minimize timing error across those matches.
        max_matches = min(len(warnings), len(events))
        unmatched_cost = tolerance_h * (max_matches + 1) + 1
        invalid_cost = unmatched_cost * 2
        costs = np.full((len(warnings), len(events) + len(warnings)), unmatched_cost, dtype=float)
        costs[:, :len(events)] = invalid_cost
        for delta, _issue, warning_index, event_index in edges:
            error_h = delta.total_seconds() / 3600
            costs[warning_index, event_index] = error_h + (warning_index * len(events) + event_index) * 1e-9
        assigned_warnings, assigned_events = linear_sum_assignment(costs)
        for warning_index, event_index in zip(assigned_warnings, assigned_events):
            if event_index >= len(events) or costs[warning_index, event_index] >= invalid_cost:
                continue
            matched_warnings.add(int(warning_index))
            matched_events.add(int(event_index))
            warning, event = warnings[warning_index], events[event_index]
            matches.append({"event_time_error_h": abs((warning["time"] - event["time"]).total_seconds()) / 3600,
                            "warning_lead_h": (event["time"] - warning["issue_time"]).total_seconds() / 3600})

    # A forecast near a real event is a duplicate alert even if another issue's
    # forecast won that event's one-to-one assignment.
    event_near_warning = {index for _error, _issue, index, _event in edges}
    false_warnings = [warning for index, warning in enumerate(warnings) if index not in event_near_warning]
    false_warnings.sort(key=lambda warning: (warning["to"], warning["time"], warning["issue_time"]))
    false_clusters = []
    for warning in false_warnings:
        cluster = next((item for item in reversed(false_clusters)
                        if item["to"] == warning["to"]
                        and warning["time"] - item["anchor_time"] <= tolerance), None)
        if cluster is None:
            false_clusters.append({"to": warning["to"], "anchor_time": warning["time"]})

    n_events = len(events)
    n_issue_days = len({issue.tz_convert("Europe/Berlin").date() for issue in issues})
    exposure_days = _exposure_days(issues, horizon_h=48)
    n_matched = len(matches)
    n_false = len(false_clusters)
    event_errors = [row["event_time_error_h"] for row in matches]
    warning_leads = [row["warning_lead_h"] for row in matches]
    return {"n_actual_events": n_events,
            "n_matched_events": n_matched,
            "event_recall": n_matched / n_events if n_events else None,
            "n_forecast_warnings": len(warnings),
            "n_false_alarm_clusters": n_false,
            "precision": n_matched / (n_matched + n_false) if n_matched + n_false else None,
            "false_alarms_per_exposure_day": n_false / exposure_days if exposure_days else None,
            "n_exposure_days": exposure_days,
            "false_alarms_per_issue_day": n_false / n_issue_days if n_issue_days else None,
            "n_issue_days": n_issue_days,
            "n_duplicate_warnings_suppressed": len(warnings) - n_matched - n_false,
            "mean_event_time_error_h": float(np.mean(event_errors)) if event_errors else None,
            "median_event_time_error_h": float(np.median(event_errors)) if event_errors else None,
            "median_warning_lead_h": float(np.median(warning_leads)) if warning_leads else None,
            "tolerance_h": tolerance_h,
            "excluded_incomplete_windows": sum(excluded.values()),
            "excluded_windows_by_reason": dict(sorted(excluded.items())),
            "truth": "Unique transitions in complete half-hour DFLD windows; overlapping forecast warnings matched one to one"}


def _exposure_days(issues, horizon_h):
    """Measure the union of valid issue-to-horizon windows, without overlap inflation."""
    intervals = sorted((issue, issue + pd.Timedelta(hours=horizon_h)) for issue in issues)
    if not intervals:
        return 0.0
    start, end = intervals[0]
    total = pd.Timedelta(0)
    for next_start, next_end in intervals[1:]:
        if next_start <= end:
            end = max(end, next_end)
        else:
            total += end - start
            start, end = next_start, next_end
    total += end - start
    return total.total_seconds() / 86400


def r18_events(frame, horizons=(1, 6, 24)):
    """Issue-level runway 18 closure detection within the next H hours.

    An issue counts as an actual event when any labelled target hour within H is
    inferred closed, and as predicted when the forecast calls any hour closed.
    Model calls use p_18_usable < 0.5; rules and persistence use their 0/1 states.
    Every method uses the same complete issue cohort, including optional
    ``rule_ensemble`` when that comparator is present.
    """
    required = {"issue_time", "time", "lead_h", "y_r18", "p_18_usable", "rule_18_usable", "persistence_18"}
    _require_columns(frame, required, "runway 18 backtest")
    if any(horizon < 1 for horizon in horizons):
        raise ValueError("horizons must be positive")
    result = []
    for horizon in horizons:
        expected = np.arange(1, horizon + 1, dtype=float)
        cohorts, excluded = [], Counter()
        for issue, rows in _forecast_windows(frame):
            if pd.isna(issue):
                excluded["invalid_issue_time"] += 1
                continue
            leads = pd.to_numeric(rows.lead_h, errors="coerce").to_numpy(float)
            selected = rows.loc[np.isfinite(leads) & (leads <= horizon)].copy()
            selected_leads = pd.to_numeric(selected.lead_h, errors="coerce").to_numpy(float)
            if len(selected) != horizon or not np.array_equal(selected_leads, expected):
                excluded["incomplete_lead_window"] += 1
                continue
            selected_times = pd.to_datetime(selected.time, utc=True, errors="coerce").dt.as_unit("ns").reset_index(drop=True)
            expected_times = pd.Series(pd.date_range(issue + pd.Timedelta(hours=1), periods=horizon, freq="h")).dt.as_unit("ns")
            if selected_times.isna().any() or not selected_times.equals(expected_times):
                excluded["invalid_forecast_times"] += 1
                continue
            labels = pd.to_numeric(selected.y_r18, errors="coerce").to_numpy(float)
            if not np.isfinite(labels).all() or not np.isin(labels, (0.0, 1.0)).all():
                excluded["unknown_truth_window"] += 1
                continue
            model = pd.to_numeric(selected.p_18_usable, errors="coerce").to_numpy(float)
            rule = pd.to_numeric(selected.rule_18_usable, errors="coerce").to_numpy(float)
            persistence = pd.to_numeric(selected.persistence_18, errors="coerce").to_numpy(float)
            predictions = [model, rule, persistence]
            ensemble_col = next((name for name in ("rule_ensemble", "rule_18_ens", "rule_18_usable_ens")
                                 if name in frame.columns), None)
            if ensemble_col is not None:
                ensemble = pd.to_numeric(selected[ensemble_col], errors="coerce").to_numpy(float)
                predictions.append(ensemble)
            if any(not np.isfinite(values).all() for values in predictions):
                excluded["unknown_prediction_window"] += 1
                continue
            if ((model < 0) | (model > 1)).any() or not np.isin(rule, (0, 1)).all() or not np.isin(persistence, (0, 1)).all():
                excluded["invalid_prediction_window"] += 1
                continue
            if len(predictions) == 4 and not np.isin(predictions[3], (0, 1)).all():
                excluded["invalid_prediction_window"] += 1
                continue
            cohorts.append((issue, labels, *predictions))

        record = {"horizon_h": horizon, "n_issues": len(cohorts),
                  "n_actual": None if not cohorts else 0,
                  "n_positive_issue_windows": None if not cohorts else 0,
                  "excluded_issues": sum(excluded.values()),
                  "excluded_issues_by_reason": dict(sorted(excluded.items()))}
        actual_values = []
        for _issue, labels, _model, _rule, _persistence, *_optional in cohorts:
            actual_values.append(bool(np.any(labels == 0)))
        actual = np.asarray(actual_values, dtype=bool)
        if cohorts:
            record["n_actual"] = int(actual.sum())  # Kept for existing output readers.
            record["n_positive_issue_windows"] = int(actual.sum())
        methods = [("model", 2, 0.5), ("rule", 3, 0.5), ("persistence", 4, 0.5)]
        if any(name in frame.columns for name in ("rule_ensemble", "rule_18_ens", "rule_18_usable_ens")):
            methods.append(("rule_ensemble", 5, 0.5))
        for name, index, threshold in methods:
            predictions = [values[index] for values in cohorts]
            predicted = np.asarray([bool(np.any(values < threshold if name == "model" else values == 0))
                                    for values in predictions], dtype=bool)
            hits = int((actual & predicted).sum())
            misses = int((actual & ~predicted).sum())
            false_alarms = int((~actual & predicted).sum())
            record[name] = {"hits": hits, "misses": misses, "false_alarms": false_alarms,
                            "recall": hits / (hits + misses) if hits + misses else None,
                            "precision": hits / (hits + false_alarms) if hits + false_alarms else None,
                            "false_alarm_rate": false_alarms / int((~actual).sum()) if (~actual).any() else None}
        if "rule_ensemble" in record:
            record["rule_corrected"] = record["rule_ensemble"].copy()
        all_labels = np.concatenate([values[1] for values in cohorts]) if cohorts else np.array([])
        all_probabilities = np.concatenate([values[2] for values in cohorts]) if cohorts else np.array([])
        record["model_brier"] = float(np.mean((all_probabilities - all_labels) ** 2)) if len(all_labels) else None
        result.append(record)
    return result
