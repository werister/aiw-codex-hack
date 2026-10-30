"""Small regressions for observed OD hysteresis and forecast availability."""

from datetime import date

import numpy as np
import pandas as pd
import pytest

from ml import forecast, live
from ml.features import build_features, select_nwp, tailwind_since_issue
from ml.forecast import fallback_predict, hour_inputs, input_sources, selected_wind
from ml.rules import od_state_machine


ISSUE = pd.Timestamp("2026-10-30T12:00:00Z")


def winds(issue=ISSUE, times=(-20, 0), direction=70, speed=5):
    return pd.DataFrame({
        "time": [issue + pd.Timedelta(minutes=minute) for minute in times],
        "wind_dir_deg": direction, "wind_kt": speed, "gust_kt": speed,
    })


def archived(issue=ISSUE, **metadata):
    frame = pd.DataFrame({"time": pd.date_range(issue + pd.Timedelta(hours=1), periods=48, freq="h")})
    for name, value in metadata.items():
        frame[name] = value
    for day in (1, 2, 3):
        frame[f"wind_speed_10m_previous_day{day}"] = 5.0
        frame[f"wind_direction_10m_previous_day{day}"] = 70.0
        frame[f"wind_gusts_10m_previous_day{day}"] = 5.0
        frame[f"pressure_msl_previous_day{day}"] = 1013.0
        frame[f"temperature_2m_previous_day{day}"] = 10.0
        frame[f"wind_speed_80m_previous_day{day}"] = 7.0
    return frame


def live_forecast(issue=ISSUE, **metadata):
    frame = pd.DataFrame({
        "time": pd.date_range(issue + pd.Timedelta(hours=1), periods=48, freq="h"),
        "wind_dir_deg": 70.0, "wind_kt": 5.0, "gust_kt": 5.0,
    })
    for name, value in metadata.items():
        frame[name] = value
    return frame


def test_known_mild_tailwind_starts_both_rule_paths_at_lead_one():
    obs = winds()
    nwp = archived()

    frame = build_features(ISSUE, obs, nwp, "25")

    assert tailwind_since_issue(ISSUE, obs, "25") == ISSUE - pd.Timedelta(minutes=20)
    assert frame.rule_od.iloc[:3].tolist() == ["07", "07", "07"]
    assert frame.rule_od25_ens.iloc[:3].tolist() == [0, 0, 0]


@pytest.mark.parametrize("speeds,directions", [
    ([5, 0, 5], [70, 70, 70]),       # calm resets the run
    ([5, 5, 5], [70, 250, 70]),     # headwind resets the run
    ([5, 5, 5], [70, None, 70]),    # unknown direction resets the run
])
def test_calm_and_headwind_reset_observed_timer(speeds, directions):
    obs = pd.DataFrame({
        "time": [ISSUE - pd.Timedelta(minutes=20), ISSUE - pd.Timedelta(minutes=10), ISSUE],
        "wind_dir_deg": directions, "wind_kt": speeds, "gust_kt": speeds,
    })

    assert tailwind_since_issue(ISSUE, obs, "25") == ISSUE


def test_stale_observations_and_strong_tailwind_are_handled_without_backdating():
    stale = winds(times=(-31,))
    strong = winds(times=(-20, 0), speed=10)

    assert tailwind_since_issue(ISSUE, stale, "25") is None
    assert tailwind_since_issue(ISSUE, strong, "25") == ISSUE - pd.Timedelta(minutes=20)


def test_long_gap_resets_timer_and_last_known_direction_caps_it():
    obs = winds(times=(-50, -10, 0), direction=250)
    history = pd.DataFrame({
        "time": [ISSUE - pd.Timedelta(hours=1), ISSUE - pd.Timedelta(minutes=20)],
        "available_at": [ISSUE - pd.Timedelta(minutes=45), ISSUE - pd.Timedelta(minutes=20)],
        "od": ["25", "07"],
    })

    assert tailwind_since_issue(ISSUE, obs, "07", history) == ISSUE - pd.Timedelta(minutes=10)
    assert tailwind_since_issue(ISSUE, winds(times=(-50, 0)), "25") == ISSUE
    assert tailwind_since_issue(ISSUE, winds(times=(-50, 0)), "25").hour == ISSUE.hour


def test_late_retrieved_duplicate_does_not_hide_earlier_observation():
    obs = winds(times=(-20, 0))
    obs["retrieved_at"] = [ISSUE - pd.Timedelta(minutes=19), ISSUE + pd.Timedelta(minutes=5)]

    assert tailwind_since_issue(ISSUE, obs, "25") == ISSUE - pd.Timedelta(minutes=20)


@pytest.mark.parametrize("stamp", ["issued_at", "retrieved_at"])
def test_archived_inputs_obey_explicit_availability(stamp):
    nwp = archived(**{stamp: ISSUE + pd.Timedelta(hours=2)})

    with pytest.raises(ValueError, match="coverage"):
        select_nwp(ISSUE, nwp)


def test_all_explicit_availability_fields_must_be_valid_and_preissue():
    nwp = archived(issued_at=ISSUE - pd.Timedelta(hours=1),
                   retrieved_at=ISSUE + pd.Timedelta(minutes=1))
    with pytest.raises(ValueError, match="coverage"):
        select_nwp(ISSUE, nwp)
    nwp["issued_at"] = "not-a-time"
    with pytest.raises(ValueError, match="issued_at"):
        select_nwp(ISSUE, nwp)


@pytest.mark.parametrize("stamp", ["issued_at", "retrieved_at"])
def test_live_inputs_obey_each_explicit_availability_column(stamp):
    nwp = live_forecast(issued_at=ISSUE - pd.Timedelta(hours=1),
                        retrieved_at=ISSUE - pd.Timedelta(minutes=1))
    nwp.loc[0, stamp] = ISSUE + pd.Timedelta(minutes=1)

    with pytest.raises(ValueError, match="coverage"):
        select_nwp(ISSUE, nwp)


def test_explicit_availability_is_reported_and_latest_eligible_duplicate_wins():
    older = archived(issued_at=ISSUE - pd.Timedelta(hours=2))
    newer = archived(issued_at=ISSUE - pd.Timedelta(hours=1))
    newer[[f"wind_speed_10m_previous_day{day}" for day in (1, 2, 3)]] = 7.0
    selected = select_nwp(ISSUE, pd.concat([older, newer], ignore_index=True))

    assert selected.wind_kt.eq(7.0).all()
    assert selected.nwp_available_proxy.eq(ISSUE - pd.Timedelta(hours=1)).all()


def test_metar_retrieval_timestamp_must_be_valid():
    obs = winds()
    obs["retrieved_at"] = [ISSUE - pd.Timedelta(minutes=19), "invalid"]

    with pytest.raises(ValueError, match="retrieved_at"):
        tailwind_since_issue(ISSUE, obs, "25")


def test_duplicate_archived_targets_select_latest_eligible_row():
    older = archived(issued_at=ISSUE - pd.Timedelta(hours=2))
    newer_but_late = older.copy()
    newer_but_late["issued_at"] = ISSUE + pd.Timedelta(hours=2)
    newer_but_late[[f"wind_speed_10m_previous_day{day}" for day in (1, 2, 3)]] = 99.0
    selected = select_nwp(ISSUE, pd.concat([older, newer_but_late], ignore_index=True))
    assert selected.wind_kt.eq(5.0).all()
    assert selected.nwp_available_proxy.le(ISSUE).all()


def test_cli_fallback_uses_shared_availability_and_hysteresis():
    obs = winds()
    nwp = archived()

    fallback = fallback_predict(ISSUE, obs, nwp, "25")
    shared = selected_wind(ISSUE, nwp)
    direct = od_state_machine(
        [(r.time, r.wind_dir_deg, r.wind_kt, r.gust_kt) for r in shared.itertuples(index=False)],
        initial_od="25", tailwind_since=tailwind_since_issue(ISSUE, obs, "25"),
    )

    assert fallback.rule_od.tolist() == direct
    assert fallback.rule_od.iloc[0] == "07"
    assert np.isfinite(fallback.p_od25.to_numpy()).all()


def test_hour_evidence_keeps_new_r18_fields_optional_for_old_rows():
    row = {
        "nwp_offset_days": 1, "wind_kt_metar_scaled": 5.0,
        "ens_tailwind_25_mean": 0.0, "ens_tailwind_25_std": 0.0,
        "ens_tailwind_18_mean": 0.0, "ens_dir_spread": 0.0, "ens_votes_25": 0.5,
        "rule_od25_ens": 1, "dp_ns": 0.0, "dp_ew": 0.0, "blend_key": "global",
        "blend_weight": 1.0, "p_od25_raw": 0.7,
    }

    older = hour_inputs(row)
    newer = hour_inputs({**row, "p_18_usable_raw": 0.8, "r18_blend_weight": 0.6})

    assert older["p_18_usable_raw"] is None
    assert older["r18_blend_weight"] is None
    assert newer["p_18_usable_raw"] == 0.8
    assert newer["r18_blend_weight"] == 0.6


def test_evidence_sources_report_both_explicit_availability_stamps():
    nwp = pd.DataFrame({
        "available_at": [ISSUE - pd.Timedelta(hours=2)],
        "issued_at": [ISSUE - pd.Timedelta(hours=3)],
        "retrieved_at": [ISSUE - pd.Timedelta(hours=1)],
    })
    nwp = pd.concat([nwp, pd.DataFrame({
        "available_at": [ISSUE - pd.Timedelta(minutes=1)],
        "issued_at": [ISSUE + pd.Timedelta(minutes=1)],
        "retrieved_at": [ISSUE + pd.Timedelta(minutes=2)],
    })], ignore_index=True)
    obs = winds(times=(0,))

    source = input_sources(nwp, obs, pd.DataFrame(), ISSUE)[0]

    assert source["issued_at"] == "2026-10-30T09:00Z"
    assert source["retrieved_at"] == "2026-10-30T11:00Z"


def test_future_requested_day_keeps_full_horizon_and_change_timing(monkeypatch):
    now = pd.Timestamp("2026-10-30T11:23:00Z")
    issue = now.floor("h")
    target_times = pd.date_range(issue + pd.Timedelta(hours=1), periods=48, freq="h")
    observations = pd.DataFrame({"time": [issue], "wind_dir_deg": [250.0],
                                 "wind_kt": [0.0], "gust_kt": [0.0]})
    history = pd.DataFrame({
        "time": pd.Series(dtype="datetime64[ns, UTC]"),
        "od": pd.Series(dtype=str),
        "available_at": pd.Series(dtype="datetime64[ns, UTC]"),
    })
    nwp = pd.DataFrame({"time": target_times,
                        "available_at": issue - pd.Timedelta(hours=1)})
    probability = [0.9] * 5 + [0.1] * 43
    prediction = pd.DataFrame({
        "time": target_times,
        "wind_dir_deg": 250.0,
        "wind_kt": 5.0,
        "gust_kt": 5.0,
        "tailwind_25_kt": 0.0,
        "tailwind_18_kt": 0.0,
        "rule_od": ["25"] * 5 + ["07"] * 43,
        "rule_18_usable": True,
        "p_od25": probability,
        "p_18_usable": 0.9,
    })
    monkeypatch.setattr(live, "metar_until", lambda cutoff: observations.copy())
    monkeypatch.setattr(live, "recorded_history", lambda: history.copy())
    monkeypatch.setattr(live, "live_weather", lambda at, current: (nwp.copy(), "fixture live data"))
    monkeypatch.setattr(forecast, "predict", lambda *args: (prediction.copy(), "fixture-model"))

    result = forecast.build_forecast(date(2026, 10, 31), now=now, include_briefing=False)

    assert len(result["hours"]) == 48
    assert [hour["time"] for hour in result["hours"]] == [forecast.utc_text(t) for t in target_times]
    assert result["issued_at"] == forecast.utc_text(issue)
    assert "full 48-hour horizon" in result["note"]
    assert result["next_change"]["time"] == forecast.utc_text(target_times[5])
    assert pd.Timestamp(result["next_change"]["time"]).tz_convert(forecast.BERLIN).date() < date(2026, 10, 31)

    with pytest.raises(ValueError, match="does not intersect"):
        forecast.build_forecast(date(2026, 11, 2), now=now, include_briefing=False)
