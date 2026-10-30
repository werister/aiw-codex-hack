"""Pure adapter: new normalized ICON-Global CSV -> issue/target-keyed SUPPLEMENTAL
wind/gust/tailwind values + missingness, for Muse's v5 supplemental experiment.

Pinned source snapshot for the data package: 5aed997313b78678d11fa23b808c2a9835a1d91a
(verified byte-identical in round-2; package-manifest integrity_pass=true).

SCOPE AND NON-GOALS (read before using)
---------------------------------------
* This produces a SUPPLEMENTAL, comparison feature block keyed by (issue, target).
  It does NOT build or replace the production `select_nwp` baseframe. Muse must keep
  the baseline `openmeteo_previous_runs.parquet` inputs as arm A; this adapter only
  supplies the extra ICON-Global columns for the matched supplemental arm.
* The ICON CSV carries NO issued_at / retrieved_at / download timestamp. This adapter
  therefore does NOT fabricate an availability time and does NOT label the historical
  download time as availability. It exposes only `offset_available_proxy`, the same
  day-band proxy production already uses (target - offset_days + PUBLICATION_LAG_H),
  explicitly named a PROXY, not a verified publication time.
* Pure: no network, no file writes, no global state, no model, no training. Input is a
  DataFrame (or path); output is a new DataFrame. Deterministic.
* The ICON-Global supplemental columns are emitted **RAW (unscaled, native knots/degrees)**
  by default. This adapter does NOT auto-apply the best_match `WIND_SCALE` (1.684) — that
  factor was fitted for the best_match source and must not be silently reused for ICON-Global.
  If Muse wants a bias correction it must pass an explicit `scale=` fitted for ICON-Global
  (chronologically, in the experiment), and the output records which scale was used.

LEAD -> OFFSET MAPPING (uses production ml.features.nwp_offset_days; not hardcoded)
  lead 1..18 -> previous_day1 ; 19..42 -> previous_day2 ; 43..48 -> previous_day3.

UNITS: CSV speed/gust already in knots (_kn), direction in degrees (_deg). No conversion.
TAILWIND sign convention matches ml.features.components: tailwind>0 means a tail component
  along the runway heading. Emitted from the (optionally scaled) speed; with scale=1.0
  (default) the tailwinds are in native ICON knots.

AVAILABILITY (optional, opt-in only): see `icon_supplement(...)` docstring. The adapter
  distinguishes a VERIFIED per-offset *publication availability* (usable for the causal
  cutoff) from a *retrospective download time* (a fetch timestamp that must NEVER gate
  eligibility). The default is to make no availability claim at all.
"""
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from ml.features import PUBLICATION_LAG_H, WIND_SCALE, nwp_offset_days
from ml.rules import RULES

# Reference only; NOT applied automatically. Fitted for best_match, not ICON-Global.
BEST_MATCH_SCALE = WIND_SCALE["best_match"]
HEADINGS = {r: RULES["runway_heading_deg"][r] for r in ("25", "07", "18")}

# CSV column templates (unit-suffixed, offset-banded). day in {1,2,3}.
_SPEED = "wind_speed_10m_previous_day{d}_kn"
_DIR = "wind_direction_10m_previous_day{d}_deg"
_GUST = "wind_gusts_10m_previous_day{d}_kn"
REQUIRED_BASE = {"time_utc", "model"}


def _tailwind(speed, direction_deg, heading_deg):
    """Scalar tailwind; mirrors ml.features.components (speed*cos(dir-heading-180))."""
    if speed is None or direction_deg is None or pd.isna(speed) or pd.isna(direction_deg):
        return math.nan
    return float(speed) * math.cos(math.radians(float(direction_deg) - heading_deg - 180.0))


def load_icon_csv(source) -> pd.DataFrame:
    """Read + validate the normalized ICON CSV. Rejects wrong model, duplicate
    target times, and missing offset columns. Returns a frame indexed by target time."""
    frame = source if isinstance(source, pd.DataFrame) else pd.read_csv(source)
    missing = REQUIRED_BASE - set(frame.columns)
    for d in (1, 2, 3):
        for tmpl in (_SPEED, _DIR, _GUST):
            if tmpl.format(d=d) not in frame.columns:
                missing.add(tmpl.format(d=d))
    if missing:
        raise ValueError(f"ICON CSV missing columns: {sorted(missing)}")
    models = set(frame["model"].unique())
    if models != {"icon_global"}:
        raise ValueError(f"expected only icon_global rows, got {sorted(models)}")
    frame = frame.copy()
    frame["time_utc"] = pd.to_datetime(frame["time_utc"], utc=True)
    dup = frame["time_utc"].duplicated().sum()
    if dup:
        raise ValueError(f"duplicate target times in ICON CSV: {dup}")
    return frame.set_index("time_utc").sort_index()


def icon_supplement(issue, source, *, scale=1.0, publication_available_at=None,
                    download_time=None) -> pd.DataFrame:
    """Return 48 rows (leads 1..48) of supplemental ICON values for one issue time.

    issue : tz-aware issue timestamp (must have explicit tz).
    source: ICON CSV path or a pre-loaded DataFrame (or the index-keyed frame from
            load_icon_csv).
    scale : multiplicative wind/gust bias correction. DEFAULT 1.0 => RAW native ICON
            knots (no scaling). The best_match WIND_SCALE (1.684) is intentionally NOT
            applied automatically; pass a scale fitted for ICON-Global if desired. The
            value used is recorded in the output column `wind_scale_applied`.
    publication_available_at: OPTIONAL, opt-in causal-eligibility guard. A VERIFIED
            per-offset *publication availability* — i.e. when the day{N} forecast run for
            a target was actually published. Accepts either
              {offset_day:int(1|2|3) -> timestamp}  (per-offset, preferred), or
              {target_timestamp -> timestamp}        (per-target).
            Any target whose publication availability is AFTER `issue` is marked
            supplemental_missing=True with NaN values. When None (the default, and the
            case for this CSV which carries no such field) NO availability claim is made.
    download_time: OPTIONAL, a retrospective fetch/download timestamp. It is recorded for
            provenance ONLY (`download_time` column) and is NEVER used to gate eligibility.
            A download time is not a publication time; using it as availability would
            back-date knowledge. Passing it does not filter any row.

    `offset_available_proxy` is the production day-band proxy
    (target - offset_days + PUBLICATION_LAG_H). It is a labelled PROXY, not a verified
    publication time, and is never used here to drop rows.

    Output columns (per target hour): issue_time, time (target), lead_h, offset_days,
      offset_available_proxy, wind_scale_applied, download_time, supplemental_missing,
      icon_wind_kt, icon_gust_kt, icon_wind_dir_deg  (RAW unless scale!=1.0),
      icon_tailwind_25_kt, icon_tailwind_07_kt, icon_tailwind_18_kt.
    """
    issue = pd.Timestamp(issue)
    if issue.tzinfo is None:
        raise ValueError("issue must be timezone-aware")
    issue = issue.tz_convert("UTC")
    if scale <= 0:
        raise ValueError("scale must be positive")
    dl = pd.Timestamp(download_time).tz_convert("UTC") if download_time is not None else pd.NaT

    frame = source if (isinstance(source, pd.DataFrame) and source.index.name == "time_utc") \
        else load_icon_csv(source)

    def published_after_issue(target, offset_day):
        """True only if a VERIFIED publication availability exists and is after issue."""
        if publication_available_at is None:
            return False
        avail = publication_available_at.get(offset_day,
                                             publication_available_at.get(target))
        if avail is None:
            return False
        return pd.Timestamp(avail).tz_convert("UTC") > issue

    targets = pd.date_range(issue + pd.Timedelta(hours=1), periods=48, freq="h")
    out = []
    for lead, target in enumerate(targets, 1):
        d = int(nwp_offset_days(lead))  # 1 for 1..18, 2 for 19..42, 3 for 43..48
        proxy = target - pd.Timedelta(days=d) + pd.Timedelta(hours=PUBLICATION_LAG_H)
        row = {"issue_time": issue, "time": target, "lead_h": lead,
               "offset_days": d, "offset_available_proxy": proxy,
               "wind_scale_applied": float(scale), "download_time": dl,
               "supplemental_missing": False,
               "icon_wind_kt": math.nan, "icon_gust_kt": math.nan,
               "icon_wind_dir_deg": math.nan, "icon_tailwind_25_kt": math.nan,
               "icon_tailwind_07_kt": math.nan, "icon_tailwind_18_kt": math.nan}

        if target not in frame.index:
            row["supplemental_missing"] = True
            out.append(row); continue

        # Causal-eligibility guard: ONLY on a VERIFIED per-offset/target publication time.
        if published_after_issue(target, d):
            row["supplemental_missing"] = True
            out.append(row); continue

        src = frame.loc[target]
        raw_speed = src[_SPEED.format(d=d)]
        raw_dir = src[_DIR.format(d=d)]
        raw_gust = src[_GUST.format(d=d)]
        if pd.isna(raw_speed) or pd.isna(raw_dir):
            row["supplemental_missing"] = True
            out.append(row); continue

        speed = float(raw_speed) * scale
        gust = float(raw_gust) * scale if not pd.isna(raw_gust) else math.nan
        row["icon_wind_kt"] = speed
        row["icon_gust_kt"] = gust
        row["icon_wind_dir_deg"] = float(raw_dir)
        row["icon_tailwind_25_kt"] = _tailwind(speed, raw_dir, HEADINGS["25"])
        row["icon_tailwind_07_kt"] = _tailwind(speed, raw_dir, HEADINGS["07"])
        row["icon_tailwind_18_kt"] = _tailwind(speed, raw_dir, HEADINGS["18"])
        out.append(row)

    return pd.DataFrame(out)
