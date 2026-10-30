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


def test_hindcast_selects_only_an_earlier_fit(tmp_path, monkeypatch):
    import ml.predict as predictor

    final = tmp_path / "forecast.joblib"
    fold = tmp_path / "fold-2026-05.joblib"
    final.touch()
    fold.touch()
    monkeypatch.setattr(predictor, "MODEL_PATH", final)
    monkeypatch.setattr(predictor, "load_models", lambda path: {
        "trained_through": "2026-10-01T00:00Z" if path == final else "2026-04-30T22:00Z"})
    assert predictor.models_at_issue(pd.Timestamp("2026-05-01T00:00Z"))["trained_through"] == "2026-04-30T22:00Z"
    with pytest.raises(ValueError, match="trained before"):
        predictor.models_at_issue(pd.Timestamp("2026-04-01T00:00Z"))


def test_change_timing_counts_missed_changes():
    from ml.quality import next_change_timing

    issue = pd.Timestamp("2026-05-01T00:00Z")
    forecast = pd.DataFrame({"issue_time": issue, "time": pd.date_range(issue + pd.Timedelta(hours=1), periods=48, freq="h"),
                             "lead_h": range(1, 49), "od_at_issue": 1, "p_od25": 0.9})
    actual = pd.DataFrame({"time": pd.date_range(issue + pd.Timedelta(minutes=30), periods=96, freq="30min"),
                           "od": ["25"] * 11 + ["07"] * 85})
    result = next_change_timing(forecast, actual)
    assert result["n_actual_change_windows"] == 1
    assert result["within_1h"] == result["within_3h"] == 0
    forecast.loc[forecast.lead_h >= 6, "p_od25"] = 0.1
    assert next_change_timing(forecast, actual)["within_1h"] == 1


def test_blend_validation_purges_crossing_labels(monkeypatch):
    import ml.train as training

    class Constant:
        classes_ = [0, 1]

        def predict_proba(self, features):
            return np.full((len(features), 2), 0.5)

    issues = pd.date_range("2025-01-01", periods=100, freq="D", tz="UTC")
    frame = pd.DataFrame([{**{feature: 0 for feature in FEATURES}, "issue_time": issue,
                            "label_available_at": issue + pd.Timedelta(hours=lead + 1),
                            "lead_h": lead, "y_od": 1} for issue in issues for lead in (1, 6, 24, 48)])
    fits = []

    def capture_fit(rows):
        fits.append(rows)
        return {"od": Constant(), "r18": Constant()}

    monkeypatch.setattr(training, "fit_classifiers", capture_fit)
    models = training.fit(frame)
    validation_start = frame.issue_time.max() - pd.Timedelta(days=60)
    assert fits[0].label_available_at.max() < validation_start
    assert fits[1] is frame
    assert pd.Timestamp(models["od_blend_validation_period"]["start"]) >= validation_start
