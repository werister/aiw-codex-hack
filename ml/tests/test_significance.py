import numpy as np
import pandas as pd

from ml.significance import compare


def synthetic(model_right=True):
    issues = pd.date_range("2026-01-01", periods=60, freq="D", tz="UTC")
    frame = pd.DataFrame([{"issue_time": issue, "time": issue + pd.Timedelta(hours=6), "lead_h": 6,
                           "y_od": number % 2} for number, issue in enumerate(issues)])
    wrong_half = np.where(np.arange(60) % 4 < 2, frame.y_od, 1 - frame.y_od)
    frame["p_od25"] = frame.y_od.astype(float) if model_right else wrong_half.astype(float)
    frame["rule_od25"] = wrong_half
    frame["od_at_issue"] = wrong_half
    frame["changed_within_lead"] = np.arange(60) % 3 == 0
    return frame


def test_perfect_model_is_significant():
    (row,) = compare(synthetic(), leads=(6,), n_boot=200)
    assert row["model_acc"] == 1.0 and row["n_days"] == 60
    assert 0 <= row["model_acc_ci"][0] <= row["model_acc_ci"][1] <= 1
    assert row["mcnemar_p_vs_rule"] < 0.01 and row["dm_p_vs_persistence"] < 0.01
    assert row["acc_diff_vs_rule_ci"][0] > 0


def test_identical_predictions_are_not_significant():
    (row,) = compare(synthetic(model_right=False), leads=(6,), n_boot=200)
    assert row["mcnemar_p_vs_rule"] == 1.0 and row["dm_p_vs_rule"] == 1.0
    low, high = row["acc_diff_vs_rule_ci"]
    assert low <= 0 <= high
