import json

import pandas as pd
import pytest

from ml import forecast, live


def test_offline_demo_uses_only_weather_and_never_requests_network(monkeypatch, tmp_path):
    issue = pd.Timestamp("2026-10-27T23:00Z")
    observations = pd.DataFrame({
        "time": pd.date_range(issue - pd.Timedelta(hours=4), issue, freq="30min"),
        "wind_dir_deg": 250.0, "wind_kt": 8.0, "gust_kt": 11.0,
    })
    observations.to_parquet(tmp_path / "eddf_metar.parquet")
    weather = pd.DataFrame({"time": live.target_hours(issue)})
    for day in (1, 2, 3):
        for name, value in (("wind_speed_10m", 8.0), ("wind_direction_10m", 70.0),
                            ("wind_gusts_10m", 11.0)):
            weather[f"{name}_previous_day{day}"] = value
    weather.to_parquet(tmp_path / "openmeteo_previous_runs.parquet")
    monkeypatch.setattr(live, "DATA", tmp_path)

    def forbidden(*args, **kwargs):
        pytest.fail("Offline demo tried to use network, labels or a fitted model")

    monkeypatch.setattr(live, "cached_get", forbidden)
    monkeypatch.setattr(live, "recorded_history", forbidden)
    monkeypatch.setattr(forecast, "predict", forbidden)

    result = forecast.build_demo()

    assert result["model_version"] == "rules-demo"
    assert result["issued_at"] == "2026-10-27T23:00Z"
    assert len(result["hours"]) == 48
    assert "observed" not in result and "evidence" not in result
    assert "uncalibrated" in result["note"]
    assert [row["lead_h"] for row in result["hours"]] == list(range(1, 49))
    json.dumps(result, allow_nan=False)


def test_offline_demo_missing_weather_fails_cleanly(monkeypatch, tmp_path):
    monkeypatch.setattr(live, "DATA", tmp_path)
    with pytest.raises(ValueError, match="bundled IEM METAR"):
        forecast.build_demo()
