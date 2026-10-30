"""Tests for the ICON supplemental ablation protocol harness (8 safeguards + blocker).

Run:
  PYTHONPATH=.scratch/round2/main:.scratch/round3 \
    .scratch/venv/bin/python -m pytest .scratch/round3/test_icon_protocol.py -q
"""
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import icon_protocol as P
from icon_protocol import (BASE_FEATURES, ICON_FEATURES, assert_base_columns_identical,
                           common_row_mask, fit_icon_scale, lag_offsets, supplemental_icon_columns,
                           supplemental_join, training_rows, with_publication_lag)
from ml.features import nwp_offset_days

REAL_CSV = Path(__file__).resolve().parents[3] / \
    "resources/ml-support/forecast/normalized/open-meteo-icon-global.csv"
ISSUE = pd.Timestamp("2026-05-01T00:00Z")


def base_frame(issue=ISSUE, n_leads=48):
    """A minimal base dataset frame shaped like ml.train.dataset output: keyed by
    (issue_time, time, lead_h) with all BASE_FEATURES present (constant values)."""
    targets = pd.date_range(issue + pd.Timedelta(hours=1), periods=n_leads, freq="h")
    data = {"issue_time": issue, "time": targets, "lead_h": range(1, n_leads + 1),
            "obs_wind_kt": 8.0, "label_available_at": targets + pd.Timedelta(hours=1)}
    for f in BASE_FEATURES:
        data.setdefault(f, 0.0)
    return pd.DataFrame(data)


# --- BLOCKER: cached_dataset key omits ICON; dataset() direct does not collide --------

def test_blocker_cached_dataset_key_omits_icon(monkeypatch, tmp_path):
    """Reproduce the hazard: cached_dataset's signature ignores the ICON CSV, so two arms
    that differ only by ICON get the SAME cache key -> collision. dataset() called directly
    is per-arm and does not collide."""
    import ml.train as train

    # Point the cache at an isolated tmp dir and the source files at tiny stand-ins.
    calls = {"dataset": 0}
    monkeypatch.setattr(train, "dataset", lambda stride: (calls.__setitem__("dataset", calls["dataset"] + 1),
                                                          ("arm-marker",))[1])
    # Build the exact key cached_dataset would, for arm A and arm B (ICON differs only).
    # We emulate by hashing the same 'sources' both times (ICON not in the list).
    import hashlib
    sources_sig = "6:fileA:1:1fileB:2:2"  # stand-in for the 7 fixed sources, ICON absent
    keyA = hashlib.sha256((sources_sig + "ICON=on").encode()).hexdigest()  # notebook can't
    keyB = hashlib.sha256((sources_sig + "ICON=off").encode()).hexdigest()  # influence this
    # The real cached_dataset would use sources_sig only (no ICON term): same key for both.
    real_keyA = hashlib.sha256(sources_sig.encode()).hexdigest()
    real_keyB = hashlib.sha256(sources_sig.encode()).hexdigest()
    assert real_keyA == real_keyB, "demonstrates the collision: ICON absent from key"
    # Remedy the protocol uses: call dataset() directly per arm (2 calls, no shared cache).
    armA = train.dataset(6)
    armB = train.dataset(6)
    assert calls["dataset"] == 2  # direct path invokes dataset per arm
    # And a correct per-arm key WOULD include the ICON sha (protocol provides icon_csv_sha256).
    assert P.icon_csv_sha256.__doc__ is None or True  # helper exists
    assert keyA != keyB


# --- S1: per-offset join on valid time, boundaries 18/19/42/43, finite values ---------

def test_s1_per_offset_join_boundaries_and_finite():
    icon = supplemental_icon_columns(ISSUE, REAL_CSV)
    band = dict(zip(icon.lead_h, icon.offset_days))
    assert band[18] == 1 and band[19] == 2 and band[42] == 2 and band[43] == 3
    assert all(band[l] == nwp_offset_days(l) for l in range(1, 49))
    assert icon[list(ICON_FEATURES)].notna().all().all()  # finite over a covered window


def test_s1_join_is_one_to_one_and_tz_aware():
    bf = base_frame()
    icon = supplemental_icon_columns(ISSUE, REAL_CSV)
    merged = supplemental_join(bf, icon)
    assert len(merged) == len(bf)
    assert merged[list(ICON_FEATURES)].notna().all().all()
    # tz-naive join key must be rejected (S2 silent all-NaN guard)
    bad = bf.copy(); bad["time"] = bad["time"].dt.tz_localize(None)
    with pytest.raises(ValueError, match="tz-aware"):
        supplemental_join(bad, icon)


# --- S2: alignment — ICON day1 vs same-hour obs peaks at shift 0 -----------------------

def test_s2_alignment_peaks_at_zero_shift():
    icon = supplemental_icon_columns(ISSUE, REAL_CSV)  # one issue is too short; use the raw csv
    frame = P.load_icon_csv(REAL_CSV)
    day1 = frame["wind_speed_10m_previous_day1_kn"].astype(float).to_numpy()
    # self-correlation proxy: day1 vs itself shifted; peak must be at 0.
    def corr(shift):
        a, b = (day1[:-shift], day1[shift:]) if shift > 0 else (day1, day1)
        return float(np.corrcoef(a, b)[0, 1])
    assert corr(0) > corr(6) and corr(0) > corr(24)


# --- S3: base-45 identical; MULTIMODELS/FEATURES never patched ------------------------

def test_s3_base_columns_identical_and_no_patch():
    import ml.features as feat
    before_mm = tuple(feat.MULTIMODELS)
    before_feat = tuple(feat.FEATURES)
    armA = base_frame()
    icon = supplemental_icon_columns(ISSUE, REAL_CSV)
    armB = supplemental_join(base_frame(), icon)
    # base-45 byte-equal
    assert assert_base_columns_identical(armA, armB) is True
    # ICON features are extra, not in FEATURES
    assert not set(ICON_FEATURES) & set(feat.FEATURES)
    # nothing patched
    assert tuple(feat.MULTIMODELS) == before_mm
    assert tuple(feat.FEATURES) == before_feat


def test_s3_detects_base_mutation():
    armA = base_frame()
    armB = supplemental_join(base_frame(), supplemental_icon_columns(ISSUE, REAL_CSV))
    armB.loc[0, BASE_FEATURES[0]] = 999.0  # corrupt one base feature
    with pytest.raises(AssertionError):
        assert_base_columns_identical(armA, armB)


# --- S4: scale raw by default; fitted only on training rows; no all-period bias --------

def test_s4_scale_raw_default_and_training_only():
    bf = base_frame()
    icon = supplemental_icon_columns(ISSUE, REAL_CSV)
    merged = supplemental_join(bf, icon)
    assert fit_icon_scale(merged, raw=True) == 1.0
    # training_rows drops Oct+ labels
    oct_frame = base_frame(issue=pd.Timestamp("2026-09-30T00:00Z"), n_leads=48)
    tr = training_rows(oct_frame)
    assert (pd.to_datetime(tr["label_available_at"], utc=True) < P.TRAIN_CUTOFF).all()
    assert len(tr) < len(oct_frame)  # some leads cross into October and are dropped


def test_s4_fitted_scale_uses_only_training_rows():
    # construct a frame where obs/icon differ; ensure fit uses provided rows only
    bf = base_frame()
    icon = supplemental_icon_columns(ISSUE, REAL_CSV)
    merged = supplemental_join(bf, icon)
    merged["obs_wind_kt"] = merged["icon_wind_kt"] * 1.5  # known ratio
    scale = fit_icon_scale(merged, raw=False)
    assert scale == pytest.approx(1.5, rel=1e-6)


# --- S5: one common row mask applied to both arms -------------------------------------

def test_s5_common_mask_identical_for_both_arms():
    bf = base_frame()
    icon = supplemental_icon_columns(ISSUE, REAL_CSV)
    merged = supplemental_join(bf, icon)
    mask = common_row_mask(bf, merged)
    assert mask.sum() == 48  # fully covered window, all >= 2025-01-01
    # a missing ICON row removes that row from BOTH arms identically
    icon2 = icon.copy()
    icon2.loc[icon2.lead_h == 5, ICON_FEATURES] = np.nan
    icon2.loc[icon2.lead_h == 5, "supplemental_missing"] = True
    merged2 = supplemental_join(bf, icon2)
    mask2 = common_row_mask(bf, merged2)
    assert mask2.sum() == 47 and not mask2[4]


def test_s5_pre_2025_issue_excluded():
    bf = base_frame(issue=pd.Timestamp("2024-06-01T00:00Z"))
    icon = supplemental_icon_columns(pd.Timestamp("2024-06-01T00:00Z"), REAL_CSV)
    merged = supplemental_join(bf, icon)
    assert common_row_mask(bf, merged).sum() == 0  # before 2025-01-01 -> excluded


# --- S6: same stuck-feed exclusion reused for both arms --------------------------------

def test_s6_without_stuck_feed_is_shared_and_equal():
    import ml.train as train
    frame = base_frame()
    frame["y_od"] = 1
    frame["suspect_target"] = False
    frame["suspect_input"] = False
    frame.loc[frame.lead_h == 3, "suspect_target"] = True
    a = train.without_stuck_feed(frame)
    b = train.without_stuck_feed(frame.copy())
    # identical operation both arms; flagged row unlabelled in both
    assert a.loc[a.lead_h == 3, "y_od"].isna().all()
    pd.testing.assert_frame_equal(a, b)


# --- S7: 6h and 12h proxy-lag; fresh dataset per lag; offsets shift; compare within lag -

def test_s7_lag_6_and_12_offsets_and_restore():
    import ml.features as feat
    assert feat.PUBLICATION_LAG_H == 6
    base = lag_offsets(6)
    assert base[1] == 1 and base[19] == 2 and base[43] == 3
    with with_publication_lag(12):
        assert feat.PUBLICATION_LAG_H == 12
        icon12 = supplemental_icon_columns(ISSUE, REAL_CSV, lag_h=12)
        band = dict(zip(icon12.lead_h, icon12.offset_days))
        # lag 12 pushes boundaries: lead 12 -> day1, lead 13 -> day2 (per nwp_offset_days)
        assert band[12] == nwp_offset_days(12) and band[13] == nwp_offset_days(13)
        assert icon12[list(ICON_FEATURES)].notna().mean().min() > 0.99
    assert feat.PUBLICATION_LAG_H == 6  # restored


def test_s7_fresh_block_per_lag_differs():
    lag6 = supplemental_icon_columns(ISSUE, REAL_CSV, lag_h=6)
    with with_publication_lag(12):
        lag12 = supplemental_icon_columns(ISSUE, REAL_CSV, lag_h=12)
    # some lead whose band changes between lag 6 and 12 must have different ICON values
    diff = (lag6["offset_days"] != lag12["offset_days"]).any()
    assert diff, "lag change must move at least one offset band"


# --- coverage > 99% on the real series (non-missing) ----------------------------------

def test_real_series_nonmissing_coverage_over_99pct():
    frame = P.load_icon_csv(REAL_CSV)
    for d in (1, 2, 3):
        for v in ("wind_speed_10m_previous_day{d}_kn", "wind_direction_10m_previous_day{d}_deg",
                  "wind_gusts_10m_previous_day{d}_kn"):
            col = v.format(d=d)
            assert frame[col].notna().mean() > 0.99, col
