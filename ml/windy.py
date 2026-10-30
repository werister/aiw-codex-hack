"""Windy Point Forecast connection check. Never supplies operational weather."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import shlex
import sys

import requests

ROOT = Path(__file__).resolve().parents[1]
KEY_NAME = "WINDY_POINT_FORECAST_API_KEY"
ENDPOINT = "https://api.windy.com/api/point-forecast/v2"
UNITS = {"wind_u-surface": "m*s-1", "wind_v-surface": "m*s-1",
         "gust-surface": "m*s-1", "pressure-surface": "Pa"}
WARNING = ("TEST ONLY: Windy's free Testing tier randomly shuffles and slightly modifies weather data. "
           "This check does not establish real weather, forecast accuracy or runway usability.")


class WindyError(ValueError):
    """An actionable error without provider bodies or credentials."""


def api_key():
    """Environment wins over the ignored, server-side project .env.local file."""
    if KEY_NAME in os.environ:
        return os.environ[KEY_NAME].strip()
    try:
        lines = (ROOT / ".env.local").read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return ""
    except OSError:
        raise WindyError("Cannot read the project .env.local file") from None
    key = ""
    for line in lines:
        name, separator, value = line.strip().removeprefix("export ").partition("=")
        if separator and name.strip() == KEY_NAME:
            try:
                parts = shlex.split(value, comments=True)
            except ValueError:
                raise WindyError(f"Invalid {KEY_NAME} entry in .env.local") from None
            if len(parts) > 1:
                raise WindyError(f"Invalid {KEY_NAME} entry in .env.local")
            key = parts[0].strip() if parts else ""
    return key


def numeric(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def response_summary(payload):
    """Validate the response, then discard every weather value."""
    if not isinstance(payload, dict):
        raise WindyError("Windy returned an invalid JSON object")
    timestamps = payload.get("ts")
    if (not isinstance(timestamps, list) or not timestamps
            or any(not numeric(t) or t <= 0 for t in timestamps)
            or any(right <= left for left, right in zip(timestamps, timestamps[1:]))):
        raise WindyError("Windy returned missing or unordered timestamps")
    units = payload.get("units")
    if not isinstance(units, dict):
        raise WindyError("Windy returned missing units")
    fields = {}
    for name, unit in UNITS.items():
        values = payload.get(name)
        if (not isinstance(values, list) or len(values) != len(timestamps)
                or any(value is not None and not numeric(value) for value in values)):
            raise WindyError(f"Windy returned an invalid {name} array")
        count = sum(value is not None for value in values)
        if count == 0 or units.get(name) != unit:
            raise WindyError(f"Windy returned no usable {name} values or unexpected units")
        fields[name] = {"unit": unit, "values": count, "missing": len(values) - count}
    try:
        first = datetime.fromtimestamp(timestamps[0] / 1000, timezone.utc).isoformat()
        last = datetime.fromtimestamp(timestamps[-1] / 1000, timezone.utc).isoformat()
    except (OverflowError, OSError, ValueError):
        raise WindyError("Windy returned timestamps outside the supported range") from None
    return {"time_steps": len(timestamps), "first_time_utc": first, "last_time_utc": last,
            "step_hours": sorted({(right - left) / 3_600_000
                                  for left, right in zip(timestamps, timestamps[1:])}),
            "fields": fields}


def check_connection(key, model="gfs"):
    if not key:
        raise WindyError(f"Set {KEY_NAME} in your environment or the project .env.local file")
    if model not in ("gfs", "iconEu"):
        raise WindyError("Choose gfs or iconEu for this connection check")
    body = {"lat": 50.03, "lon": 8.57, "model": model,
            "parameters": ["wind", "windGust", "pressure"], "levels": ["surface"], "key": key}
    try:
        response = requests.post(ENDPOINT, json=body, timeout=(10, 30), allow_redirects=False)
    except requests.Timeout:
        raise WindyError("Windy request timed out; try again later") from None
    except requests.RequestException:
        raise WindyError("Cannot connect to Windy; check the network and try again") from None
    if response.status_code in (400, 401, 403):
        raise WindyError(f"Windy rejected the request (HTTP {response.status_code}). "
                         "Use a Point Forecast key; Plugins and Map Forecast keys do not work here.")
    if response.status_code == 429:
        raise WindyError("Windy rate limit reached (HTTP 429); try again later")
    if response.status_code != 200:
        raise WindyError(f"Windy request failed (HTTP {response.status_code})")
    try:
        payload = response.json()
    except ValueError:
        raise WindyError("Windy returned invalid JSON") from None
    summary = response_summary(payload)
    return {"provider": "Windy Point Forecast", "purpose": "connection_test", "status": "ok",
            "http_status": 200, "operational_use": False, "warning": WARNING,
            "checked_at_utc": datetime.now(timezone.utc).isoformat(),
            "location": {"station": "EDDF", "latitude": 50.03, "longitude": 8.57},
            "model": model, **summary}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=("gfs", "iconEu"), default="gfs")
    parser.add_argument("--json", action="store_true", help="Print metadata only; no key or weather values")
    args = parser.parse_args(argv)
    try:
        result = check_connection(api_key(), args.model)
    except WindyError as error:
        print(f"Windy connection check failed: {error}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(WARNING)
        print(f"Connected: HTTP 200 | EDDF | {args.model} | {result['time_steps']} time steps")
        print(f"Response timestamps: {result['first_time_utc']} to {result['last_time_utc']}")
        print("Checked wind vectors, gusts and pressure. No forecast or training files were changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
