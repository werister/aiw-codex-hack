"""Mean sea-level pressure about 200 km N, S, W and E of EDDF, for gradient features.

Run python -m ml.synoptic to cache archived day1/day2/day3 runs. No credentials needed.
"""

from __future__ import annotations

import json

import pandas as pd

from ml.live import DATA, cached_get, target_hours

POINTS = {"n": (51.83, 8.57), "s": (48.23, 8.57), "w": (50.03, 5.77), "e": (50.03, 11.37)}
PATH = DATA / "openmeteo_previous_runs_pressure.parquet"
YEARS = [("2024-01-01", "2024-12-31"), ("2025-01-01", "2025-12-31"), ("2026-01-01", "2026-10-30")]


def _hourly(payload):
    """Open-Meteo returns a list for several coordinates; keep request order."""
    data = json.loads(payload["text"])
    return [item["hourly"] for item in (data if isinstance(data, list) else [data])]


def _params(variables, **extra):
    return {"latitude": ",".join(str(lat) for lat, _ in POINTS.values()),
            "longitude": ",".join(str(lon) for _, lon in POINTS.values()),
            "hourly": ",".join(variables), "timezone": "UTC", **extra}


def fetch():
    variables = [f"pressure_msl_previous_day{day}" for day in (1, 2, 3)]
    chunks = []
    for start, end in YEARS:
        payload = cached_get("https://previous-runs-api.open-meteo.com/v1/forecast",
                             _params(variables, models="best_match", start_date=start, end_date=end))
        frame = None
        for name, hourly in zip(POINTS, _hourly(payload)):
            part = pd.DataFrame(hourly)
            part["time"] = pd.to_datetime(part.time, utc=True)
            part = part.set_index("time").rename(columns={
                variable: variable.replace("pressure_msl", f"pressure_{name}") for variable in variables})
            frame = part if frame is None else frame.join(part)
        chunks.append(frame)
    result = pd.concat(chunks).sort_index().reset_index()
    result = result.drop_duplicates("time", keep="last")
    PATH.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(PATH, index=False)
    return result


def live(issue, now):
    """Live snapshot for the forecast CLI; retrieved_at must not exceed issue time."""
    targets = target_hours(issue)
    payload = cached_get("https://api.open-meteo.com/v1/forecast",
                         _params(["pressure_msl"], start_date=str(targets[0].date()), end_date=str(targets[-1].date())),
                         namespace=pd.Timestamp(now).floor("h").isoformat())
    frame = None
    for name, hourly in zip(POINTS, _hourly(payload)):
        part = pd.DataFrame(hourly).rename(columns={"pressure_msl": f"pressure_{name}"})
        part["time"] = pd.to_datetime(part.time, utc=True)
        part = part.set_index("time")
        frame = part if frame is None else frame.join(part)
    frame = frame.reset_index()
    frame["retrieved_at"] = pd.Timestamp(payload["retrieved_at"])
    return frame.loc[frame.time.isin(targets)].reset_index(drop=True)


if __name__ == "__main__":
    result = fetch()
    print(f"{len(result):,} hours, {result.time.min()} to {result.time.max()} -> {PATH}")
    print(result.drop(columns="time").isna().mean().round(4).to_string())


def add_live_pressure(frame, issue, now):
    """Attach pressure boxes known by issue time: a pre-issue snapshot, else a dated run + 12 h."""
    import sys

    import requests

    targets = target_hours(issue)
    try:
        snapshot = live(issue, now)
        if len(snapshot) == len(targets) and (snapshot.retrieved_at <= issue).all():
            extra = snapshot.drop(columns="retrieved_at").assign(pressure__available_at=snapshot.retrieved_at)
        else:
            # HACK: same conservative 12 h publication proxy as the live wind fallback.
            run = (min(issue, now) - pd.Timedelta(hours=12)).floor("6h")
            payload = cached_get("https://single-runs-api.open-meteo.com/v1/forecast",
                                 _params(["pressure_msl"], models="icon_seamless",
                                         run=run.strftime("%Y-%m-%dT%H:%M"), forecast_days=7))
            extra = None
            for name, hourly in zip(POINTS, _hourly(payload)):
                part = pd.DataFrame(hourly).rename(columns={"pressure_msl": f"pressure_{name}"})
                part["time"] = pd.to_datetime(part.time, utc=True)
                extra = part if extra is None else extra.merge(part, on="time")
            extra = extra.loc[extra.time.isin(targets)].assign(pressure__available_at=run + pd.Timedelta(hours=12))
    except (requests.RequestException, ValueError, KeyError) as error:
        print(f"WARNING: live pressure boxes unavailable: {error}", file=sys.stderr)
        return frame
    return frame.merge(extra, on="time", how="left", validate="one_to_one")
