import numpy as np
import pandas as pd
import pytest

from ml.features import FEATURES, build_features


@pytest.mark.parametrize("timestamp", ["2026-01-03T00:00Z", "2026-03-29T00:00Z", "2026-10-25T00:00Z"])
def test_issue_time_and_offsets(timestamp):
    issue = pd.Timestamp(timestamp)
    obs = pd.DataFrame({"time": pd.date_range(issue - pd.Timedelta(hours=4), periods=6, freq="h"),
                        "wind_dir_deg": [250] * 6, "wind_kt": [5, 6, 7, 8, 9, 999], "gust_kt": [10] * 6})
    nwp = pd.DataFrame({"time": pd.date_range(issue + pd.Timedelta(hours=1), periods=48, freq="h")})
    for day in (1, 2):
        for key, value in {"wind_speed_10m": day * 5, "wind_direction_10m": 250,
                           "wind_gusts_10m": day * 10}.items():
            nwp[f"{key}_previous_day{day}"] = value
    history = pd.DataFrame({"time": [issue - pd.Timedelta(hours=1), issue], "od": ["25", "07"],
                            "available_at": [issue, issue + pd.Timedelta(hours=1)]})
    frame = build_features(issue, obs, nwp, "25", history)
    assert frame.obs_time_max.le(issue).all()
    assert frame.od_available_max.le(issue).all()
    assert frame.nwp_available_proxy.le(issue).all()
    assert frame.nwp_offset_days.tolist() == [1] * 24 + [2] * 24
    assert frame.wind_kt.tolist() == [5] * 24 + [10] * 24
    assert frame.obs_wind_kt.eq(9).all()
    assert frame.hours_since_change.isna().all()
    # Alter all future observations and labels; every model input must be identical.
    obs.loc[obs.time > issue, "wind_kt"] = -1000
    history.loc[history.available_at > issue, "od"] = "25"
    changed = build_features(issue, obs, nwp, "25", history)
    pd.testing.assert_frame_equal(frame[FEATURES], changed[FEATURES])
    required = frame[FEATURES].drop(columns=["hours_since_change", "pressure_msl", "temperature_2m", "wind_speed_80m"])
    assert np.isfinite(required.to_numpy(dtype=float)).all()


def test_no_day0_fallback_and_future_publication():
    from ml.features import select_nwp

    issue = pd.Timestamp("2026-01-01T00:00Z")
    nwp = pd.DataFrame({"time": pd.date_range(issue, periods=49, freq="h"),
                        "wind_kt": 5, "wind_dir_deg": 250, "gust_kt": 10,
                        "issued_at": issue + pd.Timedelta(minutes=1)})
    with pytest.raises(ValueError, match="coverage"):
        select_nwp(issue, nwp)
    with pytest.raises(ValueError, match="issued_at"):
        select_nwp(issue, nwp.drop(columns="issued_at"))
