import json

import pandas as pd

from ml import fetch, live


def test_direction_disagreement_wraps_north_and_excludes_missing_pairs():
    frame = pd.DataFrame({"time": pd.date_range("2026-01-01", periods=2, tz="UTC", freq="h"),
                          "ecmwf_ifs025__wind_direction_10m_previous_day1": [350., None],
                          "gfs_seamless__wind_direction_10m_previous_day1": [10., 90.]})
    result = fetch.multimodel_summary(frame)
    assert result["day1_direction_pairs"][0]["n"] == 1
    assert result["pooled_mean_absolute_direction_difference_deg"] == 20


def test_model_columns_preserve_missing_gusts_and_utc():
    frame = fetch.model_frame({"hourly": {"time": ["2026-01-01T00:00"],
                                           "wind_speed_10m": [5.], "wind_direction_10m": [350.],
                                           "wind_gusts_10m": [None]}}, "ecmwf_ifs025")
    assert str(frame.time.dt.tz) == "UTC"
    assert frame["ecmwf_ifs025__wind_speed_10m"].iloc[0] == 5
    assert frame["ecmwf_ifs025__wind_gusts_10m"].isna().all()


def snapshot_frame(issue, retrieved):
    frame = pd.DataFrame({"time": live.target_hours(issue), "retrieved_at": retrieved})
    for model in fetch.MULTIMODELS:
        frame[f"{model}__wind_speed_10m"] = 99.
        frame[f"{model}__wind_direction_10m"] = 350.
        frame[f"{model}__wind_gusts_10m"] = float("nan")
    return frame


def test_live_uses_only_preissue_snapshot_and_accepts_missing_gusts(tmp_path, monkeypatch):
    issue = pd.Timestamp("2026-10-30T10:00Z")
    snapshot_frame(issue, issue - pd.Timedelta(minutes=1)).to_parquet(tmp_path / "live_forecast_multimodel.parquet")
    monkeypatch.setattr(live, "DATA", tmp_path)

    def unexpected_download(*args, **kwargs):
        raise AssertionError("Pre-issue snapshot already covers these model winds")

    monkeypatch.setattr(live, "cached_get", unexpected_download)
    result = live.add_live_models(pd.DataFrame({"time": live.target_hours(issue)}), issue, issue)
    for model in fetch.MULTIMODELS:
        assert result[f"{model}__wind_speed_10m"].eq(99.).all()
        assert result[f"{model}__available_at"].le(issue).all()


def test_live_rejects_postissue_snapshot_and_uses_buffered_dated_runs(tmp_path, monkeypatch):
    issue = pd.Timestamp("2026-10-30T10:00Z")
    snapshot_frame(issue, issue + pd.Timedelta(minutes=1)).to_parquet(tmp_path / "live_forecast_multimodel.parquet")
    monkeypatch.setattr(live, "DATA", tmp_path)
    calls = []

    def dated_run(url, params):
        calls.append(params)
        assert "single-runs-api" in url
        return {"text": json.dumps({"hourly": {"time": [str(t) for t in live.target_hours(issue)],
            "wind_speed_10m": [5.] * 48, "wind_direction_10m": [10.] * 48, "wind_gusts_10m": [None] * 48}})}

    monkeypatch.setattr(live, "cached_get", dated_run)
    result = live.add_live_models(pd.DataFrame({"time": live.target_hours(issue)}), issue, issue)
    assert [p["models"] for p in calls] == list(fetch.MULTIMODELS)
    for model in fetch.MULTIMODELS:
        assert result[f"{model}__wind_speed_10m"].eq(5.).all()
        assert result[f"{model}__available_at"].le(issue).all()
        assert (result[f"{model}__available_at"] - result[f"{model}__issued_at"]).eq(pd.Timedelta(hours=12)).all()
