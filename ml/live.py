"""Cached public weather inputs for issue-time forecasts. No credentials needed."""

from __future__ import annotations

import hashlib
import io
import json
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CACHE = DATA / "raw" / "forecast_cli"
VARIABLES = ["wind_speed_10m", "wind_direction_10m", "wind_gusts_10m",
             "pressure_msl", "temperature_2m", "wind_speed_80m", "wind_direction_80m"]
_last_request = 0.0


def cached_get(url, params, *, namespace="archive"):
    """Immutable archive requests; live requests use an hourly namespace."""
    global _last_request
    prepared = requests.Request("GET", url, params=params).prepare()
    key = hashlib.sha256((prepared.url + namespace).encode()).hexdigest()[:24]
    path = CACHE / (key + ".json")
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    time.sleep(max(0, 1.2 - (time.monotonic() - _last_request)))
    _last_request = time.monotonic()
    response = requests.get(url, params=params, timeout=(15, 60),
                            headers={"User-Agent": "EDDF-forecast/1.0"})
    response.raise_for_status()
    payload = {"text": response.text, "retrieved_at": pd.Timestamp.now(tz="UTC").isoformat(),
               "url": response.url}
    CACHE.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return payload


def normalize_metar(frame):
    frame = frame.rename(columns={"valid": "time", "drct": "wind_dir_deg",
                                  "sknt": "wind_kt", "gust": "gust_kt"}).copy()
    frame["time"] = pd.to_datetime(frame.time, utc=True)
    for column in ("wind_dir_deg", "wind_kt", "gust_kt"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["gust_kt"] = frame.gust_kt.fillna(frame.wind_kt)
    return frame.dropna(subset=["wind_kt"]).sort_values("time").drop_duplicates("time", keep="last")


def metar_until(cutoff):
    """At most 48h of METAR ending at cutoff, including a 3h trend history."""
    cutoff = pd.Timestamp(cutoff).tz_convert("UTC")
    start = cutoff - pd.Timedelta(hours=48)
    path = DATA / "eddf_metar.parquet"
    frame = normalize_metar(pd.read_parquet(path)) if path.exists() else pd.DataFrame()
    if len(frame):
        frame = frame.loc[frame.time.between(start, cutoff)].copy()
    if frame.empty or cutoff - frame.time.iloc[-1] > pd.Timedelta(hours=2):
        stop = cutoff + pd.Timedelta(days=1)
        params = {"station": "EDDF", "data": ["drct", "sknt", "gust", "metar"],
                  "year1": start.year, "month1": start.month, "day1": start.day,
                  "year2": stop.year, "month2": stop.month, "day2": stop.day,
                  "tz": "Etc/UTC", "format": "onlycomma", "latlon": "no",
                  "missing": "M", "report_type": [3, 4]}
        payload = cached_get("https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py", params,
                             namespace=cutoff.isoformat())
        frame = normalize_metar(pd.read_csv(io.StringIO(payload["text"]), na_values=["M"]))
        frame = frame.loc[frame.time.between(start, cutoff)].copy()
    if frame.empty or cutoff - frame.time.iloc[-1] > pd.Timedelta(hours=2):
        raise ValueError("No EDDF METAR within two hours before the input cutoff")
    return frame.reset_index(drop=True)


def target_hours(issue):
    return pd.date_range(issue + pd.Timedelta(hours=1), periods=48, freq="h")


def covers(frame, targets, archived=False):
    if frame.empty:
        return False
    source = frame.drop_duplicates("time", keep="last").set_index("time").reindex(targets)
    for lead, (_, row) in enumerate(source.iterrows(), 1):
        suffix = f"_previous_day{1 if lead <= 24 else 2}" if archived else ""
        if any(pd.isna(row.get(name + suffix)) for name in VARIABLES[:3]):
            return False
    return True


def archived_weather(issue):
    targets = target_hours(issue)
    path = DATA / "openmeteo_previous_runs.parquet"
    frame = pd.read_parquet(path) if path.exists() else pd.DataFrame()
    if len(frame):
        frame["time"] = pd.to_datetime(frame.time, utc=True)
    if not covers(frame, targets, archived=True):
        variables = [f"{name}_previous_day{day}" for day in (1, 2) for name in VARIABLES]
        params = {"latitude": 50.033, "longitude": 8.570, "hourly": ",".join(variables),
                  "wind_speed_unit": "kn", "timezone": "UTC", "models": "best_match",
                  "start_date": str(targets[0].date()), "end_date": str(targets[-1].date())}
        payload = cached_get("https://previous-runs-api.open-meteo.com/v1/forecast", params)
        frame = pd.DataFrame(json.loads(payload["text"])["hourly"])
        frame["time"] = pd.to_datetime(frame.time, utc=True)
    if not covers(frame, targets, archived=True):
        raise ValueError("Archived forecast does not cover all 48 hours; no observed-weather substitution")
    frame = frame.loc[frame.time.isin(targets)].copy().sort_values("time")
    # These are nominal offset availability proxies, not publication timestamps.
    frame["available_at"] = [t - pd.Timedelta(days=1 if i < 24 else 2)
                             for i, t in enumerate(frame.time)]
    return frame, "Open-Meteo previous runs (best_match; day1/day2 availability proxy)"


def live_weather(issue, now):
    """Use a pre-issue snapshot, otherwise a dated run with a publication buffer.

    API docs: https://open-meteo.com/en/docs/single-runs-api
    The 12h buffer is conservative, not a verified historical publication time.
    """
    targets = target_hours(issue)
    path = DATA / "live_forecast.parquet"
    def known_snapshot(frame):
        frame["time"] = pd.to_datetime(frame.time, utc=True)
        frame["retrieved_at"] = pd.to_datetime(frame.retrieved_at, utc=True)
        frame = frame.loc[frame.retrieved_at <= issue].copy()
        if covers(frame, targets):
            frame = frame.loc[frame.time.isin(targets)].sort_values("time")
            frame["available_at"] = frame.retrieved_at
            return frame
        return None

    if path.exists():
        frame = known_snapshot(pd.read_parquet(path))
        if frame is not None:
            return frame, "Open-Meteo Forecast API (snapshot retrieved before issue)"
    params = {"latitude": 50.033, "longitude": 8.570, "hourly": ",".join(VARIABLES),
              "wind_speed_unit": "kn", "timezone": "UTC",
              "start_date": str(targets[0].date()), "end_date": str(targets[-1].date())}
    payload = cached_get("https://api.open-meteo.com/v1/forecast", params,
                         namespace=now.floor("h").isoformat())
    snapshot = pd.DataFrame(json.loads(payload["text"])["hourly"])
    snapshot["retrieved_at"] = payload["retrieved_at"]
    frame = known_snapshot(snapshot)
    if frame is not None:
        return frame, "Open-Meteo Forecast API (snapshot retrieved before issue)"
    # HACK: allow 12h for publication when no pre-issue live snapshot exists.
    run = (min(issue, now) - pd.Timedelta(hours=12)).floor("6h")
    params = {"latitude": 50.033, "longitude": 8.570, "hourly": ",".join(VARIABLES),
              "wind_speed_unit": "kn", "timezone": "UTC", "models": "icon_global",
              "run": run.strftime("%Y-%m-%dT%H:%M"), "forecast_days": 7}
    payload = cached_get("https://single-runs-api.open-meteo.com/v1/forecast", params)
    frame = pd.DataFrame(json.loads(payload["text"])["hourly"])
    frame["time"] = pd.to_datetime(frame.time, utc=True)
    frame["issued_at"] = run
    frame["available_at"] = run + pd.Timedelta(hours=12)
    if not covers(frame, targets):
        raise ValueError("Requested day is outside the available live forecast horizon")
    return frame.loc[frame.time.isin(targets)].copy(), (
        f"Open-Meteo single run fallback (ICON; run {run.isoformat()}; 12h publication proxy)")


def recorded_history():
    path = DATA / "ground_truth" / "dfld_hourly.csv"
    if not path.exists():
        return pd.DataFrame(columns=["time", "od", "available_at"])
    frame = pd.read_csv(path, dtype={"od": str})
    frame["time"] = pd.to_datetime(frame.time, utc=True)
    # An hourly label describes the whole hour, so it cannot be an input at its start.
    frame["available_at"] = frame.time + pd.Timedelta(hours=1)
    return frame.sort_values("time")
