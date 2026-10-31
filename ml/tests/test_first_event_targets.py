import numpy as np
import pandas as pd
import pytest

from ml.first_event_experiment import attach_first_event_targets


ISSUE = pd.Timestamp("2026-06-30T21:00:00Z")


def sample_windows(feature_unit="us", truth_unit="ns"):
    truth_times = pd.date_range(ISSUE - pd.Timedelta(minutes=30), periods=98,
                                freq="30min").as_unit(truth_unit)
    # The state changes exactly at T from 07 to 25, then changes twice later
    # and returns to 25. Only the two transitions strictly after T are events.
    directions = ["07"] + ["25"] * 97
    directions[13:25] = ["07"] * 12  # T+6 h
    directions[25:] = ["25"] * 73  # T+12 h; final direction equals direction at T
    truth = pd.DataFrame({"time": truth_times, "od": directions})
    feature_times = pd.date_range(ISSUE + pd.Timedelta(hours=1), periods=48,
                                  freq="h").as_unit(feature_unit)
    frame = pd.DataFrame({"issue_time": [ISSUE] * 48, "time": feature_times,
        "lead_h": np.arange(1, 49), "od_at_issue": [1] * 48})
    return frame, truth


@pytest.mark.parametrize(("feature_unit", "truth_unit"), [("us", "ns"), ("ns", "us")])
def test_first_event_uses_complete_grid_strict_future_and_t49_availability(feature_unit, truth_unit):
    frame, truth = sample_windows(feature_unit, truth_unit)

    labeled, coverage, audit = attach_first_event_targets(frame, truth)

    by_lead = labeled.set_index("lead_h")
    assert coverage["complete_97_bin_windows"] == 1
    assert by_lead.loc[1, "event_by_lead"] == 0  # the state change at T is not future
    assert by_lead.loc[6, "event_by_lead"] == 1
    assert by_lead.loc[48, "event_by_lead"] == 1
    assert by_lead.loc[48, "truth_change_count_48h"] == 2
    assert by_lead.loc[48, "truth_initial_od25"] == by_lead.loc[48, "truth_final_od25"] == 1
    assert audit["multiple_changes_returning_to_initial_state"] == 1
    assert audit["two_changes_same_final_remain_positive"]["event_by_lead_48"] is True

    available_at = ISSUE + pd.Timedelta(hours=49)
    assert (labeled.event_label_available_at == available_at).all()
    assert not (labeled.event_label_available_at < available_at).any()
    assert (labeled.event_label_available_at < available_at + pd.Timedelta(seconds=1)).all()


def test_missing_half_hour_bin_leaves_entire_issue_unlabelled():
    frame, truth = sample_windows()
    missing_time = ISSUE + pd.Timedelta(hours=10, minutes=30)
    truth = truth.loc[truth.time.ne(missing_time)].reset_index(drop=True)

    labeled, coverage, _ = attach_first_event_targets(frame, truth)

    assert coverage["incomplete_truth_windows"] == 1
    assert coverage["unlabelled_issue_windows"] == 1
    assert labeled.event_by_lead.isna().all()
    assert labeled.event_label_available_at.isna().all()
