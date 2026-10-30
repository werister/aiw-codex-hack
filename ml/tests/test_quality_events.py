import numpy as np
import pandas as pd

from ml.quality import next_change_timing, od_change_events, r18_events, skill, suspect_od_runs


def issue_forecast(issue, initial="25", change_at=None, change_to="07"):
    times = pd.date_range(issue + pd.Timedelta(hours=1), periods=48, freq="h")
    initial_value = int(initial == "25")
    target_value = int(change_to == "25")
    prediction = np.full(48, initial_value, dtype=float)
    if change_at is not None:
        prediction[times >= change_at] = target_value
    return pd.DataFrame({"issue_time": issue, "time": times, "lead_h": np.arange(1, 49),
                         "od_at_issue": initial_value, "p_od25": prediction})


def truth_window(issue, initial="25", transitions=(), hours=48):
    times = pd.date_range(issue, periods=hours * 2 + 1, freq="30min")
    state = initial
    values = []
    transitions = dict(transitions)
    for time in times:
        if time in transitions:
            state = transitions[time]
        values.append(state)
    return pd.DataFrame({"time": times, "od": values})


def test_past_switch_does_not_become_a_future_hit():
    issue = pd.Timestamp("2026-10-30T12:00Z")
    forecast = issue_forecast(issue, initial="25", change_at=issue + pd.Timedelta(hours=1))
    truth = truth_window(issue, initial="07")

    window = next_change_timing(forecast, truth)
    events = od_change_events(forecast, truth)

    assert window["n_actual_change_windows"] == 0
    assert window["n_no_change_windows"] == 1
    assert window["false_alarm_rate"] == 1.0
    assert window["within_1h"] is None
    assert events["n_actual_events"] == 0
    assert events["n_matched_events"] == 0
    assert events["n_false_alarm_clusters"] == 1


def test_actual_state_at_issue_and_half_hour_transition_are_used():
    issue = pd.Timestamp("2026-10-30T12:00Z")
    change = issue + pd.Timedelta(minutes=30)
    forecast = issue_forecast(issue, initial="25", change_at=issue + pd.Timedelta(hours=1))
    truth = truth_window(issue, initial="25", transitions=[(change, "07")])

    result = next_change_timing(forecast, truth)
    events = od_change_events(forecast, truth)

    assert result["n_actual_change_windows"] == 1
    assert result["within_1h"] == 1.0
    assert result["mean_absolute_error_h_when_predicted"] == 0.5
    assert events["n_actual_events"] == 1
    assert events["n_matched_events"] == 1
    assert events["median_event_time_error_h"] == 0.5
    assert events["median_warning_lead_h"] == 0.5


def test_mixed_utc_timestamp_units_are_normalized_before_join_and_grid_checks():
    issue = pd.Timestamp("2026-10-30T12:00Z").as_unit("us")
    event = issue + pd.Timedelta(minutes=30)
    forecast = issue_forecast(issue, initial="25", change_at=issue + pd.Timedelta(hours=1))
    forecast["time"] = forecast.time.dt.as_unit("us")
    truth = truth_window(issue, initial="25", transitions=[(event, "07")])
    truth["time"] = truth.time.dt.as_unit("ns")

    timing = next_change_timing(forecast, truth)
    events = od_change_events(forecast, truth)

    assert timing["excluded_windows_by_reason"] == {}
    assert timing["within_1h"] == 1.0
    assert events["excluded_windows_by_reason"] == {}
    assert events["n_matched_events"] == 1

    wind_truth = pd.DataFrame({"time": pd.date_range(issue, periods=3, freq="h").as_unit("ns"),
                               "od": ["25", "25", "25"]})
    observations = pd.DataFrame({"time": pd.date_range(issue, periods=3, freq="h").as_unit("us"),
                                 "wind_kt": [0.0, 0.0, 0.0],
                                 "wind_dir_deg": [0.0, 0.0, 0.0]})
    flags = suspect_od_runs(wind_truth, observations, min_hours=1)
    assert len(flags) == 3
    assert not flags.any()


def test_invalid_issue_time_is_excluded_instead_of_breaking_grid_arithmetic():
    issue = pd.Timestamp("2026-10-30T12:00Z")
    truth = truth_window(issue)
    forecast = issue_forecast(issue)
    forecast["issue_time"] = "not-a-timestamp"

    timing = next_change_timing(forecast, truth)
    events = od_change_events(forecast, truth)
    runway = r18_forecast(issue)
    runway["issue_time"] = "not-a-timestamp"
    (r18,) = r18_events(runway, horizons=(6,))

    assert timing["excluded_windows_by_reason"] == {"invalid_issue_time": 1}
    assert events["excluded_windows_by_reason"] == {"invalid_issue_time": 1}
    assert r18["excluded_issues_by_reason"] == {"invalid_issue_time": 1}
    assert r18["n_issues"] == 0


def test_missing_or_invalid_forecast_and_truth_windows_are_excluded():
    issue = pd.Timestamp("2026-10-30T12:00Z")
    forecast = issue_forecast(issue)
    forecast = forecast.drop(index=10)
    missing_truth = truth_window(issue).drop(index=20)

    result = next_change_timing(forecast, missing_truth)
    events = od_change_events(forecast, missing_truth)

    assert result["excluded_incomplete_windows"] == 1
    assert result["excluded_windows_by_reason"] == {"incomplete_forecast_grid": 1}
    assert events["excluded_windows_by_reason"] == {"incomplete_forecast_grid": 1}

    complete_forecast = issue_forecast(issue)
    duplicate_truth = pd.concat([truth_window(issue), truth_window(issue).iloc[[10]]], ignore_index=True)
    duplicate = next_change_timing(complete_forecast, duplicate_truth)
    assert duplicate["excluded_windows_by_reason"] == {"duplicate_truth_timestamps": 1}

    missing_truth = truth_window(issue).drop(index=20)
    missing = next_change_timing(complete_forecast, missing_truth)
    assert missing["excluded_windows_by_reason"] == {"incomplete_truth_coverage": 1}

    invalid_truth = truth_window(issue)
    invalid_truth.loc[40, "od"] = "unknown"
    invalid = od_change_events(complete_forecast, invalid_truth)
    assert invalid["excluded_windows_by_reason"] == {"unknown_truth_direction": 1}


def test_unique_event_matching_suppresses_overlapping_duplicate_warnings():
    first_issue = pd.Timestamp("2026-10-30T00:00Z")
    event = first_issue + pd.Timedelta(hours=24)
    forecasts, truths = [], []
    for offset in (0, 6, 12, 18, 24):
        issue = first_issue + pd.Timedelta(hours=offset)
        state = "25" if issue < event else "07"
        change_at = event if issue < event else None
        forecasts.append(issue_forecast(issue, initial=state, change_at=change_at))
        truths.append(truth_window(issue, initial=state, transitions=[(event, "07")] if issue < event else ()))

    result = od_change_events(pd.concat(forecasts, ignore_index=True),
                              pd.concat(truths, ignore_index=True).drop_duplicates("time", keep="first"),
                              tolerance_h=3)

    assert result["n_actual_events"] == 1
    assert result["n_forecast_warnings"] == 4
    assert result["n_matched_events"] == 1
    assert result["n_duplicate_warnings_suppressed"] == 3
    assert result["n_false_alarm_clusters"] == 0
    assert result["event_recall"] == 1.0
    assert result["n_exposure_days"] == 3.0


def test_event_matching_maximizes_matches_before_minimizing_time_error():
    first_issue = pd.Timestamp("2026-10-30T00:00Z")
    second_issue = first_issue + pd.Timedelta(hours=1)
    event_1 = first_issue + pd.Timedelta(hours=10)
    event_2 = first_issue + pd.Timedelta(hours=11)
    event_3 = first_issue + pd.Timedelta(hours=12)
    first = issue_forecast(first_issue, initial="25", change_at=event_1)
    second = issue_forecast(second_issue, initial="25", change_at=first_issue + pd.Timedelta(hours=7))
    truth = truth_window(first_issue, initial="25", transitions=[(event_1, "07"),
                             (event_2, "25"), (event_3, "07")], hours=49)

    result = od_change_events(pd.concat([first, second], ignore_index=True), truth, tolerance_h=3)

    assert result["n_actual_events"] == 3
    assert result["n_forecast_warnings"] == 2
    assert result["n_matched_events"] == 2
    assert result["event_recall"] == 2 / 3
    assert result["median_event_time_error_h"] == 2.5


def test_wrong_direction_warning_is_a_miss_and_a_false_alert():
    issue = pd.Timestamp("2026-10-30T12:00Z")
    event = issue + pd.Timedelta(hours=3)
    forecast = issue_forecast(issue, initial="25", change_at=event, change_to="07")
    truth = truth_window(issue, initial="07", transitions=[(event, "25")])

    result = od_change_events(forecast, truth)
    timing = next_change_timing(forecast, truth)

    assert result["n_actual_events"] == 1
    assert result["n_matched_events"] == 0
    assert result["event_recall"] == 0.0
    assert result["n_false_alarm_clusters"] == 1
    assert timing["within_1h"] == 0.0
    assert timing["n_wrong_direction"] == 1


def r18_forecast(issue, closure_lead=None):
    rows = []
    for lead in range(1, 7):
        closed = closure_lead == lead
        rows.append({"issue_time": issue, "time": issue + pd.Timedelta(hours=lead), "lead_h": lead,
                     "y_r18": 0.0 if closed else 1.0,
                     "p_18_usable": 0.3 if closed else 0.9,
                     "rule_18_usable": 0 if closed else 1,
                     "rule_18_ens": 0 if closed else 1,
                     "persistence_18": 1})
    return pd.DataFrame(rows)


def test_r18_event_windows_exclude_unknown_incomplete_truth_and_predictions():
    issues = pd.date_range("2026-10-01", periods=3, freq="D", tz="UTC")
    first = r18_forecast(issues[0], closure_lead=3)
    second = r18_forecast(issues[1])
    second.loc[5, "y_r18"] = np.nan  # The six-hour outcome window is no longer fully observed.
    second.loc[0, "p_18_usable"] = np.nan
    third = r18_forecast(issues[2])
    frame = pd.concat([first, second, third], ignore_index=True)

    one_hour, six_hour = r18_events(frame, horizons=(1, 6))

    assert one_hour["n_issues"] == 2  # A missing hour beyond H does not censor a 1 h outcome.
    assert one_hour["n_positive_issue_windows"] == 0
    assert one_hour["excluded_issues_by_reason"] == {"unknown_prediction_window": 1}
    assert six_hour["n_issues"] == 2
    assert six_hour["n_positive_issue_windows"] == 1
    assert six_hour["model"]["hits"] == 1
    assert six_hour["rule"]["hits"] == 1
    assert six_hour["rule_ensemble"]["hits"] == 1
    assert six_hour["rule_corrected"] == six_hour["rule_ensemble"]
    assert six_hour["persistence"]["misses"] == 1
    assert six_hour["excluded_issues_by_reason"] == {"unknown_truth_window": 1}


def test_r18_empty_cohort_reports_unknown_positive_count():
    frame = r18_forecast(pd.Timestamp("2026-10-01T00:00Z"))
    frame["y_r18"] = np.nan

    (result,) = r18_events(frame, horizons=(6,))

    assert result["n_issues"] == 0
    assert result["n_positive_issue_windows"] is None
    assert result["model"]["recall"] is None


def test_skill_reports_raw_r18_scores_separately_from_served_blend():
    frame = pd.DataFrame({"lead_h": [1, 1], "y_r18": [1, 0],
                          "p_18_usable": [0.9, 0.3], "p_18_usable_raw": [0.2, 0.3],
                          "rule_18_usable": [1, 0], "persistence_18": [1, 1],
                          "changed_within_lead": [False, True]})

    (row,) = skill(frame, "r18")[:1]

    assert row["blend_acc"] == 1.0
    assert row["model_acc"] == 1.0
    assert row["raw_model_acc"] == 0.5
    assert row["rule_acc"] == 1.0
