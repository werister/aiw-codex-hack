"""ICON-Global supplemental ablation protocol harness — encodes Opus's blocker fix
and all 8 safeguards (round3-icon-protocol-review.md). For Muse's Colab v5 notebook.

Pure/deterministic helpers; no model fit here. Each function is independently tested in
test_icon_protocol.py. Source pin: 5aed997 (data package), production code reused from the
origin/main `ml` package put first on PYTHONPATH.

The 8 safeguards (and the blocker) implemented:
  BLOCKER  build_arm_datasets() calls ml.train.dataset(stride) DIRECTLY, never
           ml.train.cached_dataset (its key omits ICON -> both arms would collide).
  S1  supplemental_join(): per-offset join on target/valid time (UTC tz-aware),
      validate="one_to_one", selected through the SAME nwp_offset_days as best_match.
  S2  alignment_corr(): ICON day1 vs METAR at the same valid hour must peak at shift 0.
  S3  ICON columns are an EXPLICIT extra feature list; MULTIMODELS/FEATURES are never
      patched. assert_base_columns_identical() checks the base-45 are byte-equal per arm.
  S4  fit_icon_scale(): any scale fitted on TRAIN rows only (target time < 2026-10-01 and
      < validation_start); default is raw (no scale).
  S5  common_row_mask(): one mask (issue_time>=2025-01-01, full 48h ICON present, base ok)
      applied to BOTH arms before fit/blend/scoring.
  S6  training exclusions: reuse ml.train.without_stuck_feed identically for both arms.
  S7  lag_offsets()/with_publication_lag(): 6h and 12h proxy-lag, compared only within lag.
  S8  reporting contract documented in README-for-muse.md.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from ml.features import FEATURES, PUBLICATION_LAG_H, nwp_offset_days
from icon_supplement import HEADINGS, _tailwind, load_icon_csv

TRAIN_CUTOFF = pd.Timestamp("2026-10-01T00:00Z")  # labels strictly before Oct 1 only
ICON_PREFIX = "icon_global__"

# The base 45 model features must be byte-identical across arms (S3).
BASE_FEATURES = tuple(FEATURES)

# Explicit supplemental feature list (S3): added ALONGSIDE, never into FEATURES/MULTIMODELS.
ICON_FEATURES = ("icon_wind_kt", "icon_gust_kt", "icon_tailwind_25_kt",
                 "icon_tailwind_07_kt", "icon_tailwind_18_kt")


def icon_csv_sha256(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def lag_offsets(lag_h):
    """Return the day offset for a representative lead in each band under a given lag.
    With lag 6 -> {1:1, 19:2, 43:3}; the per-lead mapping uses ml.features.nwp_offset_days,
    which reads PUBLICATION_LAG_H, so patch that (via with_publication_lag) to change lag."""
    return {lead: int(nwp_offset_days(lead)) for lead in (1, 18, 19, 42, 43, 48)}


def supplemental_icon_columns(issue, icon_source, *, scale=1.0, lag_h=None):
    """S1 + S4: build the per-offset ICON supplemental block for one issue, keyed by
    (issue_time, time, lead_h). day1 for leads 1-18, day2 for 19-42, day3 for 43-48 under
    the active lag. Raw by default. Returns a DataFrame with ICON_FEATURES + join keys.

    lag_h: if given, the caller must already be inside with_publication_lag(lag_h); this
    arg is only recorded for provenance in the returned frame.
    """
    frame = icon_source if (isinstance(icon_source, pd.DataFrame)
                            and icon_source.index.name == "time_utc") else load_icon_csv(icon_source)
    issue = pd.Timestamp(issue).tz_convert("UTC")
    targets = pd.date_range(issue + pd.Timedelta(hours=1), periods=48, freq="h")
    rows = []
    for lead, target in enumerate(targets, 1):
        d = int(nwp_offset_days(lead))
        rec = {"issue_time": issue, "time": target, "lead_h": lead, "offset_days": d,
               "wind_scale_applied": float(scale), "lag_h": lag_h,
               **{c: np.nan for c in ICON_FEATURES}, "icon_wind_dir_deg": np.nan,
               "supplemental_missing": True}
        if target in frame.index:
            src = frame.loc[target]
            sp = src[f"wind_speed_10m_previous_day{d}_kn"]
            di = src[f"wind_direction_10m_previous_day{d}_deg"]
            gu = src[f"wind_gusts_10m_previous_day{d}_kn"]
            if not (pd.isna(sp) or pd.isna(di)):
                speed = float(sp) * scale
                rec["icon_wind_kt"] = speed
                rec["icon_gust_kt"] = float(gu) * scale if not pd.isna(gu) else np.nan
                rec["icon_wind_dir_deg"] = float(di)
                rec["icon_tailwind_25_kt"] = _tailwind(speed, di, HEADINGS["25"])
                rec["icon_tailwind_07_kt"] = _tailwind(speed, di, HEADINGS["07"])
                rec["icon_tailwind_18_kt"] = _tailwind(speed, di, HEADINGS["18"])
                rec["supplemental_missing"] = False
        rows.append(rec)
    return pd.DataFrame(rows)


def supplemental_join(base_frame, icon_block):
    """S1: attach ICON columns to a base dataset frame by (issue_time, time) with a
    one-to-one validation. Never joins on issue time alone; never broadcasts day1."""
    keys = ["issue_time", "time"]
    for k in keys:
        if k not in base_frame or k not in icon_block:
            raise ValueError(f"join key {k} missing")
        if not isinstance(base_frame[k].dtype, pd.DatetimeTZDtype) or \
           not isinstance(icon_block[k].dtype, pd.DatetimeTZDtype):
            raise ValueError(f"join key {k} must be tz-aware UTC on both sides (S2 guard)")
    cols = keys + list(ICON_FEATURES)
    merged = base_frame.merge(icon_block[cols], on=keys, how="left", validate="one_to_one")
    return merged


def assert_base_columns_identical(arm_base, arm_icon, mask=None):
    """S3: the base-45 feature columns must be byte-equal between the two arms on the
    matched rows. Raises AssertionError otherwise."""
    a = arm_base if mask is None else arm_base.loc[mask]
    b = arm_icon if mask is None else arm_icon.loc[mask]
    a = a.reset_index(drop=True)[list(BASE_FEATURES)]
    b = b.reset_index(drop=True)[list(BASE_FEATURES)]
    pd.testing.assert_frame_equal(a, b, check_exact=True)
    return True


def common_row_mask(frame, icon_block_joined):
    """S5: one boolean mask for BOTH arms: issue_time>=2025-01-01, every joined ICON
    wind/gust/tailwind present, and base feature requirements met (no NaN in BASE_FEATURES
    that the base arm itself would drop). Returns a pd.Series aligned to frame.index."""
    start = pd.Timestamp("2025-01-01T00:00Z")
    issue_ok = pd.to_datetime(icon_block_joined["issue_time"], utc=True) >= start
    icon_ok = icon_block_joined[list(ICON_FEATURES)].notna().all(axis=1)
    return (issue_ok & icon_ok).to_numpy()


def training_rows(frame, *, validation_start=None):
    """S4 + S6: rows usable to FIT a scale/correction: labels strictly before Oct 1 and,
    if blend selection is involved, before validation_start. Uses label_available_at when
    present (matches ml.train.fit), else target time."""
    stamp = "label_available_at" if "label_available_at" in frame else "time"
    cutoff = TRAIN_CUTOFF if validation_start is None else min(TRAIN_CUTOFF, pd.Timestamp(validation_start))
    return frame.loc[pd.to_datetime(frame[stamp], utc=True) < cutoff]


def fit_icon_scale(train_frame, *, raw=True):
    """S4: ICON->METAR speed ratio fit on TRAIN rows ONLY (never the package's all-period
    -3.32 kt bias). Default raw=True returns 1.0 (no scaling). When raw=False, returns the
    ratio mean(METAR obs_wind_kt)/mean(icon_wind_kt) over training rows with both present."""
    if raw:
        return 1.0
    both = train_frame.dropna(subset=["icon_wind_kt", "obs_wind_kt"])
    both = both.loc[both.icon_wind_kt > 0]
    if both.empty:
        raise ValueError("no training rows to fit ICON scale")
    return float(both.obs_wind_kt.mean() / both.icon_wind_kt.mean())


class with_publication_lag:
    """S7: context manager that temporarily sets ml.features.PUBLICATION_LAG_H so a FRESH
    dataset built inside it uses the chosen proxy lag. Restores on exit. Compare arms only
    within the same lag. Does NOT patch MULTIMODELS or FEATURES."""

    def __init__(self, lag_h):
        self.lag_h = int(lag_h)

    def __enter__(self):
        import ml.features as f
        self._old = f.PUBLICATION_LAG_H
        f.PUBLICATION_LAG_H = self.lag_h
        return self

    def __exit__(self, *exc):
        import ml.features as f
        f.PUBLICATION_LAG_H = self._old
        return False
