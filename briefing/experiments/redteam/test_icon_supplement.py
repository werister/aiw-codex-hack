"""Tests for the ICON supplemental adapter. Pure, offline, stdlib+pandas.

Run:
  PYTHONPATH=.scratch/round2/main:.scratch/round3 \
    .scratch/venv/bin/python -m pytest .scratch/round3/test_icon_supplement.py -q
"""
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from icon_supplement import (BEST_MATCH_SCALE, HEADINGS, icon_supplement, load_icon_csv,
                             _tailwind)
from ml.features import nwp_offset_days

REAL_CSV = Path(__file__).resolve().parents[3] / \
    "resources/ml-support/forecast/normalized/open-meteo-icon-global.csv"

ISSUE = pd.Timestamp("2026-05-01T00:00Z")  # a window fully inside ICON coverage


def synthetic_csv(tmp_path, *, dup=False, extra_model=False, drop_target=None):
    """Build a tiny valid ICON-shaped CSV covering ISSUE+1h .. +48h."""
    targets = pd.date_range(ISSUE + pd.Timedelta(hours=1), periods=48, freq="h")
    rows = []
    for i, t in enumerate(targets):
        if drop_target is not None and i == drop_target:
            continue
        row = {"time_utc": t.strftime("%Y-%m-%dT%H:%M:%SZ"), "model": "icon_global",
               "requested_latitude_deg": 50.033, "requested_longitude_deg": 8.57,
               "grid_latitude_deg": 50.0, "grid_longitude_deg": 8.625}
        for d in (1, 2, 3):
            # distinct per-day values so we can prove the correct band is selected
            row[f"wind_speed_10m_previous_day{d}_kn"] = 10.0 * d
            row[f"wind_direction_10m_previous_day{d}_deg"] = 250.0
            row[f"wind_gusts_10m_previous_day{d}_kn"] = 10.0 * d + 5
            row[f"pressure_msl_previous_day{d}_hpa"] = 1013.0
            row[f"temperature_2m_previous_day{d}_c"] = 10.0
        rows.append(row)
    frame = pd.DataFrame(rows)
    if dup:
        frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    if extra_model:
        bad = frame.iloc[[0]].copy(); bad["model"] = "icon_seamless"
        frame = pd.concat([frame, bad], ignore_index=True)
    path = tmp_path / "icon.csv"
    frame.to_csv(path, index=False)
    return path


# --- offset boundary 18/19 and 42/43 -------------------------------------------------

def test_offset_boundaries_18_19_42_43(tmp_path):
    out = icon_supplement(ISSUE, synthetic_csv(tmp_path))
    assert len(out) == 48
    band = dict(zip(out.lead_h, out.offset_days))
    assert band[18] == 1 and band[19] == 2
    assert band[42] == 2 and band[43] == 3
    # matches production mapping exactly for every lead
    assert all(band[l] == nwp_offset_days(l) for l in range(1, 49))
    # RAW by default: raw 10/20/30 come through unscaled.
    assert out.loc[out.lead_h == 1, "icon_wind_kt"].iloc[0] == pytest.approx(10.0)
    assert out.loc[out.lead_h == 19, "icon_wind_kt"].iloc[0] == pytest.approx(20.0)
    assert out.loc[out.lead_h == 43, "icon_wind_kt"].iloc[0] == pytest.approx(30.0)


# --- units: raw by default; best_match scale NEVER auto-applied -----------------------

def test_units_raw_by_default_no_autoscale(tmp_path):
    out = icon_supplement(ISSUE, synthetic_csv(tmp_path))
    r1 = out[out.lead_h == 1].iloc[0]
    assert r1.icon_wind_kt == pytest.approx(10.0)   # NOT 10*1.684
    assert r1.icon_gust_kt == pytest.approx(15.0)
    assert r1.icon_wind_dir_deg == 250.0            # direction never scaled
    assert r1.wind_scale_applied == pytest.approx(1.0)


def test_explicit_scale_is_opt_in_and_recorded(tmp_path):
    out = icon_supplement(ISSUE, synthetic_csv(tmp_path), scale=1.5)
    r1 = out[out.lead_h == 1].iloc[0]
    assert r1.icon_wind_kt == pytest.approx(15.0)
    assert r1.icon_gust_kt == pytest.approx(22.5)
    assert r1.wind_scale_applied == pytest.approx(1.5)
    # best_match value exists for reference but is not the default.
    assert BEST_MATCH_SCALE == pytest.approx(1.684)


# --- tailwind sign convention matches ml.features.components -------------------------

def test_tailwind_matches_components_convention(tmp_path):
    from ml.features import components
    out = icon_supplement(ISSUE, synthetic_csv(tmp_path))  # raw, scale=1.0
    r = out[out.lead_h == 1].iloc[0]
    speed = 10.0
    for runway, col in (("25", "icon_tailwind_25_kt"), ("07", "icon_tailwind_07_kt"),
                        ("18", "icon_tailwind_18_kt")):
        expected = float(components(np.array([speed]), np.array([250.0]), HEADINGS[runway])[0])
        assert r[col] == pytest.approx(expected)
    # Convention check: wind FROM 250 deg on a 250-heading runway is a pure HEADWIND,
    # so components() returns -speed (tail component is negative). The opposite runway
    # (heading 70) sees the same wind as a pure TAILWIND, +speed.
    assert r.icon_tailwind_25_kt == pytest.approx(-speed, abs=1e-6)
    assert r.icon_tailwind_07_kt == pytest.approx(+speed, abs=1e-6)


# --- join: issue/target keyed, exactly 48 target hours -------------------------------

def test_join_is_issue_target_keyed(tmp_path):
    out = icon_supplement(ISSUE, synthetic_csv(tmp_path))
    targets = pd.date_range(ISSUE + pd.Timedelta(hours=1), periods=48, freq="h")
    assert list(out.time) == list(targets)
    assert (out.issue_time == ISSUE).all()
    assert out.lead_h.tolist() == list(range(1, 49))


# --- missingness: a target absent from the CSV -> missing row, not a crash -----------

def test_missing_target_marked_not_dropped(tmp_path):
    out = icon_supplement(ISSUE, synthetic_csv(tmp_path, drop_target=5))  # lead 6 missing
    assert len(out) == 48
    miss = out[out.lead_h == 6].iloc[0]
    assert bool(miss.supplemental_missing) is True
    assert math.isnan(miss.icon_wind_kt) and math.isnan(miss.icon_tailwind_18_kt)
    assert not out[out.lead_h != 6].supplemental_missing.any()


# --- duplicate rejection -------------------------------------------------------------

def test_duplicate_target_times_rejected(tmp_path):
    with pytest.raises(ValueError, match="duplicate target"):
        icon_supplement(ISSUE, synthetic_csv(tmp_path, dup=True))


def test_wrong_model_rejected(tmp_path):
    with pytest.raises(ValueError, match="icon_global"):
        icon_supplement(ISSUE, synthetic_csv(tmp_path, extra_model=True))


def test_missing_columns_rejected(tmp_path):
    path = synthetic_csv(tmp_path)
    frame = pd.read_csv(path).drop(columns=["wind_speed_10m_previous_day2_kn"])
    with pytest.raises(ValueError, match="missing columns"):
        icon_supplement(ISSUE, frame)


# --- FUTURE-STAMP NEGATIVE CONTROL ---------------------------------------------------

def test_future_publication_availability_marks_missing(tmp_path):
    """FUTURE-STAMP NEGATIVE CONTROL. A target whose VERIFIED publication availability is
    after the issue is excluded (NaN, missing=True). Keyed per-TARGET here."""
    path = synthetic_csv(tmp_path)
    targets = pd.date_range(ISSUE + pd.Timedelta(hours=1), periods=48, freq="h")
    avail = {targets[0]: ISSUE + pd.Timedelta(hours=1),   # published AFTER issue -> drop
             targets[1]: ISSUE - pd.Timedelta(hours=3)}   # before issue -> keep
    out = icon_supplement(ISSUE, path, publication_available_at=avail)
    r1 = out[out.lead_h == 1].iloc[0]
    r2 = out[out.lead_h == 2].iloc[0]
    assert bool(r1.supplemental_missing) is True and math.isnan(r1.icon_wind_kt)
    assert bool(r2.supplemental_missing) is False and not math.isnan(r2.icon_wind_kt)
    # Without any availability claim, no row is dropped on that basis.
    out_noclaim = icon_supplement(ISSUE, path)
    assert not out_noclaim[out_noclaim.lead_h == 1].iloc[0].supplemental_missing


def test_future_publication_availability_keyed_per_offset(tmp_path):
    """Per-OFFSET keying: {offset_day -> time}. If day3's run publishes after issue, all
    day3 leads (43..48) drop while day1/day2 stay."""
    path = synthetic_csv(tmp_path)
    avail = {1: ISSUE - pd.Timedelta(days=1),
             2: ISSUE - pd.Timedelta(hours=6),
             3: ISSUE + pd.Timedelta(hours=2)}   # day3 run not yet published at issue
    out = icon_supplement(ISSUE, path, publication_available_at=avail)
    day3 = out[out.offset_days == 3]
    others = out[out.offset_days != 3]
    assert day3.supplemental_missing.all() and day3.lead_h.min() == 43
    assert not others.supplemental_missing.any()


def test_download_time_never_gates_eligibility(tmp_path):
    """A retrospective download time (even far AFTER issue) must NOT drop any row; it is
    recorded for provenance only. Download time != publication availability."""
    path = synthetic_csv(tmp_path)
    dl = ISSUE + pd.Timedelta(days=400)  # fetched long after issue (retrospective export)
    out = icon_supplement(ISSUE, path, download_time=dl)
    assert not out.supplemental_missing.any()          # nothing dropped
    assert (out.download_time == pd.Timestamp(dl).tz_convert("UTC")).all()  # recorded only


# --- real CSV smoke: loads, 48 rows, no crash, deterministic -------------------------

@pytest.mark.skipif(not REAL_CSV.exists(), reason="real ICON CSV not extracted")
def test_real_csv_smoke_and_determinism():
    frame = load_icon_csv(REAL_CSV)
    assert frame.index.is_monotonic_increasing and not frame.index.has_duplicates
    a = icon_supplement(ISSUE, frame)
    b = icon_supplement(ISSUE, frame)
    assert len(a) == 48
    pd.testing.assert_frame_equal(a, b)  # pure/deterministic
    assert not a.supplemental_missing.any()  # window fully covered
    assert a.icon_wind_kt.between(0, 200).all()
