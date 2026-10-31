"""Counterexamples documenting why whole-run flags are sensitivity-only."""

import numpy as np
import pandas as pd

from ml.quality import suspect_od_runs
from ml.train import without_stuck_feed


def runs_across_boundary():
    # 07 run spans a fold boundary at 2026-06-01T00Z. Westerly 12 kt = 12 kt tailwind on 07.
    times = pd.date_range("2026-05-31T20:00Z", periods=10, freq="h")
    truth = pd.DataFrame({"time": times, "od": ["25"] + ["07"] * 9})
    wind = [0.0] * 5 + [12.0] * 5  # over-limit hours only from 01:00Z, after the boundary
    obs = pd.DataFrame({"time": times, "wind_kt": wind, "wind_dir_deg": 250.0})
    return truth, obs, pd.Timestamp("2026-06-01T00:00Z")


def test_whole_run_flag_uses_post_boundary_metar():
    truth, obs, boundary = runs_across_boundary()
    flag = suspect_od_runs(truth, obs)
    before = truth.time < boundary
    # Pre-boundary 07 hours (21:00-23:00Z) carry no over-limit METAR, yet are flagged.
    assert flag[before & truth.od.eq("07")].all()
    # Causal version: data truncated at the boundary leaves them unflagged.
    causal = suspect_od_runs(truth[before], obs[obs.time < boundary])
    assert not causal.any()


def test_train_row_unlabelled_by_test_period_info():
    truth, obs, boundary = runs_across_boundary()
    truth["suspect"] = suspect_od_runs(truth, obs)
    # One training row: issue 21:00Z, target 22:00Z (07 run), label available 23:00Z.
    issue = boundary - pd.Timedelta(hours=3)
    frame = pd.DataFrame({"issue_time": [issue], "time": [issue + pd.Timedelta(hours=1)],
                          "label_available_at": [issue + pd.Timedelta(hours=2)], "y_od": [0.0]})
    # Same expressions as ml/train.py:92-93.
    known = truth.loc[truth.time + pd.Timedelta(hours=1) <= issue]
    frame["suspect_target"] = truth.set_index("time").suspect.reindex(frame.time).to_numpy(bool)
    frame["suspect_input"] = bool(known.suspect.iloc[-1])
    assert frame.label_available_at.max() < boundary  # passes the purge in train.evaluate
    cleaned = without_stuck_feed(frame)
    # Row selection for the fit before `boundary` changed because of METAR after `boundary`.
    assert cleaned.y_od.isna().all()

