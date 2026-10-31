import numpy as np
import pandas as pd

from ml.significance import compare
from ml.significance import _calendar_blocks


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


def test_calendar_blocks_never_bridge_missing_days():
    dates = pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03",
                            "2026-01-06", "2026-01-07", "2026-01-08"]).date
    assert _calendar_blocks(dates, 3) == [(0, 1, 2), (3, 4, 5)]
    assert _calendar_blocks(dates, 7) == []


def test_contiguous_block_intervals_are_seeded_and_keep_pairs():
    first, = compare(synthetic(), leads=(6,), n_boot=80, seed=31)
    second, = compare(synthetic(), leads=(6,), n_boot=80, seed=31)
    for metric in ("model_acc_ci_3d", "model_acc_ci_7d",
                   "acc_diff_vs_rule_ci_3d", "acc_diff_vs_rule_ci_7d"):
        assert first[metric] == second[metric]
        assert first[metric] is not None
    assert first["acc_diff_vs_rule_ci_7d"][0] > 0


def test_ensemble_rule_uses_its_own_shared_cohort():
    frame = synthetic()
    frame["rule_od25_ens"] = np.where(np.arange(len(frame)) % 3, frame.y_od, 1 - frame.y_od)
    frame.loc[frame.index[:4], "rule_od25_ens"] = np.nan
    row, = compare(frame, leads=(6,), n_boot=40, seed=12)
    assert row["n"] == len(frame)
    assert row["rule_ensemble_n"] == len(frame) - 4
    assert row["model_acc_on_rule_ensemble_cohort"] == 1.0
    assert row["rule_ensemble_coverage"] == (len(frame) - 4) / len(frame)
    assert row["acc_diff_model_vs_rule_ensemble_ci"][0] > 0
    assert row["brier_diff_model_vs_rule_ensemble_ci"][1] < 0


def test_missing_calendar_days_can_make_long_block_ci_unavailable():
    frame = synthetic()
    frame["issue_time"] = pd.date_range("2026-01-01", periods=60, freq="2D", tz="UTC")
    row, = compare(frame, leads=(6,), n_boot=20, seed=9)
    assert row["model_acc_ci_7d"] is None
    assert row["model_acc_ci_3d"] is None


def test_block_ci_is_unavailable_when_a_scored_day_has_no_full_block():
    frame = synthetic().iloc[:4].copy()
    frame["issue_time"] = pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-10"], utc=True)
    row, = compare(frame, leads=(6,), n_boot=20, seed=9)
    assert row["model_acc_ci"] is not None
    assert row["model_acc_ci_3d"] is None
    assert row["model_acc_ci_7d"] is None


def test_empty_ensemble_cohort_has_zero_coverage_and_null_metrics():
    frame = synthetic()
    frame["rule_od25_ens"] = np.nan
    row, = compare(frame, leads=(6,), n_boot=20, seed=9)
    assert row["rule_ensemble_n"] == 0
    assert row["rule_ensemble_coverage"] == 0
    assert row["model_acc_on_rule_ensemble_cohort"] is None
    assert row["rule_ensemble_brier"] is None
    assert row["mcnemar_p_vs_rule_ensemble"] is None
    assert row["acc_diff_model_vs_rule_ensemble_ci"] == [None, None]
    assert row["acc_diff_model_vs_rule_ensemble_ci_3d"] is None
