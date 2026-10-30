"""Deterministic CLI contract and issue-time checks without network access."""

from datetime import date
import json
from types import SimpleNamespace

import pandas as pd
import pytest

from ml import forecast, live


DAY = date(2026, 10, 2)
NOW = pd.Timestamp("2026-10-30T11:23Z")


@pytest.fixture
def hindcast_inputs(monkeypatch):
    issue, _, _ = forecast.issue_time(DAY, now=NOW)
    observations = pd.DataFrame({
        "time": pd.date_range(issue - pd.Timedelta(hours=4), issue, freq="30min"),
        "wind_dir_deg": 250.0, "wind_kt": 8.0, "gust_kt": 10.0,
    })
    history_times = pd.date_range(issue - pd.Timedelta(hours=8), periods=60, freq="h")
    history = pd.DataFrame({"time": history_times,
                            "available_at": history_times + pd.Timedelta(hours=1),
                            "od": ["25" if t < issue else "07" for t in history_times]})
    targets = live.target_hours(issue)
    weather = pd.DataFrame({"time": targets})
    for offset, speed in ((1, 12.0), (2, 22.0), (3, 32.0)):
        weather[f"wind_speed_10m_previous_day{offset}"] = speed
        weather[f"wind_gusts_10m_previous_day{offset}"] = speed + 2
        weather[f"wind_direction_10m_previous_day{offset}"] = (
            [250.0] * 6 + [90.0] * 18 + [330.0] * 24)
    weather["available_at"] = [t - pd.Timedelta(days=live.nwp_offset_days(lead)) + pd.Timedelta(hours=6)
                               for lead, t in enumerate(targets, 1)]
    captured = {}

    def capture_predict(issue_time, obs, nwp, current_od):
        captured.update(issue=issue_time, obs=obs.copy(), nwp=nwp.copy(), current_od=current_od)
        return forecast.fallback_predict(issue_time, obs, nwp, current_od), "rules-fallback"

    def overlay(issue_time, _history):
        assert captured["issue"] == issue_time
        return [{"time": forecast.utc_text(targets[0]), "od": "25", "r18_usable": True}]

    monkeypatch.setattr(live, "metar_until", lambda cutoff: observations.copy())
    monkeypatch.setattr(live, "recorded_history", lambda: history.copy())
    monkeypatch.setattr(live, "archived_weather", lambda cutoff: (weather.copy(), "archived wind"))
    monkeypatch.setattr(forecast, "predict", capture_predict)
    monkeypatch.setattr(forecast, "observed_overlay", overlay)
    return issue, observations, history, weather, captured


def test_fixed_hindcast_contract_and_no_future_inputs(hindcast_inputs):
    issue, _, _, _, captured = hindcast_inputs
    result = forecast.build_forecast(DAY, now=NOW)
    assert set(result) == {"issued_at", "issued_local", "mode", "current_od", "nwp",
                           "model_version", "rules_version", "hours", "next_change",
                           "closures_18", "observed"}
    assert result["issued_at"] == "2026-10-01T22:00Z"
    assert result["issued_local"] == "2026-10-02T00:00"
    assert result["mode"] == "hindcast"
    assert result["current_od"] == "25"
    assert len(result["hours"]) == 48
    assert captured["obs"].time.max() <= issue
    assert captured["obs"].available_at.dropna().max() <= issue
    assert captured["obs"].od_time.dropna().max() < issue
    assert captured["nwp"].available_at.max() <= issue
    assert list(captured["nwp"].available_at) == [
        t - pd.Timedelta(days=live.nwp_offset_days(lead)) + pd.Timedelta(hours=6)
        for lead, t in enumerate(live.target_hours(issue), 1)]
    expected_fields = {"time", "local", "lead_h", "wind_dir_deg", "wind_kt", "gust_kt",
                       "tailwind_25_kt", "tailwind_18_kt", "rule_od", "rule_18_usable",
                       "p_od25", "od", "p_18_usable", "certainty"}
    for lead, hour in enumerate(result["hours"], 1):
        assert set(hour) == expected_fields
        assert hour["time"] == forecast.utc_text(issue + pd.Timedelta(hours=lead))
        assert hour["lead_h"] == lead
        assert hour["wind_kt"] == (12.0 if lead <= 18 else 22.0 if lead <= 42 else 32.0)
        assert hour["od"] in ("25", "07")
        assert hour["rule_od"] in ("25", "07")
        assert type(hour["rule_18_usable"]) is bool
        assert 0 <= hour["p_od25"] <= 1
        assert 0 <= hour["p_18_usable"] <= 1
        assert hour["od"] == ("25" if hour["p_od25"] >= 0.5 else "07")
        assert hour["certainty"] == round(100 * min(
            abs(2 * hour["p_od25"] - 1), abs(2 * hour["p_18_usable"] - 1)))
    assert result["next_change"] is not None
    assert result["closures_18"]
    json.dumps(result, allow_nan=False)


def test_archived_loader_and_fallback_share_buffered_offsets(hindcast_inputs, monkeypatch, tmp_path):
    from ml.features import select_nwp

    issue, _, _, weather, _ = hindcast_inputs
    weather.to_parquet(tmp_path / "openmeteo_previous_runs.parquet")
    monkeypatch.setattr(live, "DATA", tmp_path)
    archived, _ = live.archived_weather(issue)
    features = select_nwp(issue, archived)
    assert list(archived.available_at) == list(features.nwp_available_proxy)
    fallback = forecast.selected_wind(issue, archived)
    columns = ["time", "wind_kt", "wind_dir_deg", "gust_kt"]
    pd.testing.assert_frame_equal(fallback[columns], features[columns])
    assert live.covers(archived, live.target_hours(issue), archived=True)
    missing_day3 = archived.drop(columns=[name for name in archived if name.endswith("_previous_day3")])
    assert not live.covers(missing_day3, live.target_hours(issue), archived=True)


def test_future_recorded_labels_cannot_change_forecast(hindcast_inputs):
    issue, _, history, _, _ = hindcast_inputs
    before = forecast.build_forecast(DAY, now=NOW)
    history.loc[history.available_at > issue, "od"] = "25"
    after = forecast.build_forecast(DAY, now=NOW)
    assert after["current_od"] == before["current_od"]
    assert after["hours"] == before["hours"]
    assert after["next_change"] == before["next_change"]


def test_rejects_weather_available_after_issue(hindcast_inputs):
    issue, _, _, weather, _ = hindcast_inputs
    weather.loc[0, "available_at"] = issue + pd.Timedelta(minutes=1)
    with pytest.raises(ValueError, match="availability exceeds issue time"):
        forecast.build_forecast(DAY, now=NOW)


def test_json_stdout_matches_written_file(hindcast_inputs, monkeypatch, tmp_path, capsys):
    result = forecast.build_forecast(DAY, now=NOW)
    monkeypatch.setattr(forecast, "build_forecast", lambda day: result)
    destination = tmp_path / "forecasts" / "day.json"
    assert forecast.main(["--day", DAY.isoformat(), "--json", "--out", str(destination)]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == result
    assert captured.out == destination.read_text(encoding="utf-8")


def test_now_and_table_output(hindcast_inputs, monkeypatch, capsys):
    result = forecast.build_forecast(DAY, now=NOW)
    calls = []

    def build(day):
        calls.append(day)
        return result

    monkeypatch.setattr(forecast, "build_forecast", build)
    assert forecast.main(["--now"]) == 0
    captured = capsys.readouterr()
    assert calls == [None]
    assert captured.err == ""
    assert sum(line.startswith("2026-") for line in captured.out.splitlines()) == 48
    assert "Next change:" in captured.out
    assert "Runway 18 closures (inferred weather usability):" in captured.out


@pytest.mark.parametrize(("day", "expected"), [
    (date(2026, 10, 25), "2026-10-24T22:00Z"),
    (date(2026, 10, 26), "2026-10-25T23:00Z"),
])
def test_issue_midnight_and_dst(day, expected):
    issue, mode, _ = forecast.issue_time(day, now=NOW)
    assert forecast.utc_text(issue) == expected
    assert mode == "hindcast"
    assert len(live.target_hours(issue)) == 48
    assert live.target_hours(issue)[-1] - issue == pd.Timedelta(hours=48)


def test_now_rounds_to_current_full_hour():
    issue, mode, _ = forecast.issue_time(now=NOW)
    assert forecast.utc_text(issue) == "2026-10-30T11:00Z"
    assert mode == "live"


def test_next_change_window_and_closure_runs():
    start = pd.Timestamp("2026-10-02T00:00Z")
    hours = []
    for index, (p_od, p_18) in enumerate(zip([0.8, 0.6, 0.45, 0.3, 0.8], [0.8, 0.4, 0.2, 0.5, 0.3])):
        time = start + pd.Timedelta(hours=index)
        hours.append({"time": forecast.utc_text(time), "local": forecast.local_text(time),
                      "od": "25" if p_od >= 0.5 else "07", "p_od25": p_od,
                      "p_18_usable": p_18})
    change = forecast.next_change(hours, "25")
    assert change == {"time": hours[2]["time"], "local": hours[2]["local"],
                      "from": "25", "to": "07", "p": 0.55,
                      "window_local": [hours[1]["local"], hours[2]["local"]]}
    runs = forecast.closures(hours)
    assert len(runs) == 2
    assert runs[0]["start"] == hours[1]["time"]
    assert runs[0]["end"] == hours[3]["time"]
    assert runs[0]["min_p_usable"] == 0.2
    assert runs[1]["start"] == hours[4]["time"]
    assert runs[1]["end"] == forecast.utc_text(start + pd.Timedelta(hours=5))
    assert forecast.next_change([hours[0]], "25") is None
    assert forecast.closures([hours[0]]) == []


def test_metar_loader_excludes_reports_after_cutoff(monkeypatch, tmp_path):
    cutoff = pd.Timestamp("2026-10-01T22:00Z")
    pd.DataFrame({"valid": [cutoff - pd.Timedelta(minutes=10), cutoff + pd.Timedelta(minutes=20)],
                  "drct": [250, 90], "sknt": [8, 30], "gust": [None, 35]}).to_parquet(
                      tmp_path / "eddf_metar.parquet")
    monkeypatch.setattr(live, "DATA", tmp_path)
    reports = live.metar_until(cutoff)
    assert len(reports) == 1
    assert reports.time.max() <= cutoff
    assert reports.wind_kt.iloc[-1] == 8
    assert reports.gust_kt.iloc[-1] == 8


@pytest.mark.parametrize("error", [
    FileNotFoundError("No fitted forecast file"),
    ValueError("No model trained before this issue time; choose a later hindcast date"),
])
def test_predict_adapter_uses_fallback_when_fit_is_unavailable(monkeypatch, error):
    issue = pd.Timestamp("2026-10-02T00:00Z")
    obs, nwp = pd.DataFrame(), pd.DataFrame()
    expected = pd.DataFrame({"p_od25": [0.7], "p_18_usable": [0.9]})
    calls = []

    def unavailable(*args):
        raise error

    def fallback(*args):
        calls.append(args)
        return expected

    module = SimpleNamespace(predict_48h=unavailable)
    monkeypatch.setattr(forecast, "importlib", SimpleNamespace(import_module=lambda name: module))
    monkeypatch.setattr(forecast, "fallback_predict", fallback)
    actual, version = forecast.predict(issue, obs, nwp, "25")
    assert actual is expected
    assert version == "rules-fallback"
    assert len(calls) == 1
    assert calls[0][0] == issue
    assert calls[0][1] is obs
    assert calls[0][2] is nwp
    assert calls[0][3] == "25"


def test_predict_adapter_propagates_other_validation_errors(monkeypatch):
    error = ValueError("Incomplete 48-hour archived wind coverage")

    def invalid(*args):
        raise error

    module = SimpleNamespace(predict_48h=invalid)
    monkeypatch.setattr(forecast, "importlib", SimpleNamespace(import_module=lambda name: module))
    with pytest.raises(ValueError, match="Incomplete 48-hour archived wind coverage") as caught:
        forecast.predict(pd.Timestamp("2026-10-02T00:00Z"), pd.DataFrame(), pd.DataFrame(), "25")
    assert caught.value is error


def test_predict_adapter_preserves_fitted_output_and_version(monkeypatch):
    issue = pd.Timestamp("2026-10-02T00:00Z")
    obs, nwp = pd.DataFrame(), pd.DataFrame()
    expected = pd.DataFrame({"p_od25": [0.123, 0.987], "p_18_usable": [0.82, 0.35]})
    expected.attrs["model_version"] = "forecast-v2"
    calls = []

    def fitted(*args):
        calls.append(args)
        return expected

    module = SimpleNamespace(predict_48h=fitted)
    monkeypatch.setattr(forecast, "importlib", SimpleNamespace(import_module=lambda name: module))
    actual, version = forecast.predict(issue, obs, nwp, "07")
    assert actual is expected
    assert list(actual.p_od25) == [0.123, 0.987]
    assert list(actual.p_18_usable) == [0.82, 0.35]
    assert version == "forecast-v2"
    assert calls[0][0] == issue
    assert calls[0][1] is obs
    assert calls[0][2] is nwp
    assert calls[0][3] == "07"


@pytest.mark.parametrize("hours_ahead", [-1, 0, 1])
def test_predict_adapter_stale_metar_fallback_requires_future_issue(monkeypatch, hours_ahead):
    issue = NOW.floor("h") + pd.Timedelta(hours=hours_ahead)
    obs, nwp = pd.DataFrame(), pd.DataFrame()
    expected = pd.DataFrame({"p_od25": [0.8]})

    def stale(*args):
        raise ValueError("No METAR within two hours before issue")

    module = SimpleNamespace(predict_48h=stale)
    monkeypatch.setattr(forecast, "importlib", SimpleNamespace(import_module=lambda name: module))
    monkeypatch.setattr(forecast, "pd", SimpleNamespace(Timestamp=SimpleNamespace(now=lambda tz: NOW)))
    monkeypatch.setattr(forecast, "fallback_predict", lambda *args: expected)
    if hours_ahead > 0:
        actual, version = forecast.predict(issue, obs, nwp, "25")
        assert actual is expected
        assert version == "rules-fallback"
    else:
        with pytest.raises(ValueError, match="No METAR within two hours before issue"):
            forecast.predict(issue, obs, nwp, "25")
