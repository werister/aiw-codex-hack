#!/usr/bin/env python3
"""Download and validate EDDF Open-Meteo forecast archive data (stdlib only)."""
import argparse
import calendar
import csv
import hashlib
import json
import os
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
RUNS = RAW / "previous-runs"
SINGLES = RAW / "single-runs"
CSV_PATH = ROOT / "normalized" / "open-meteo-icon-global.csv"
MANIFEST_PATH = ROOT / "manifest.json"
QUALITY_PATH = ROOT / "quality.json"
PREVIOUS_API = "https://previous-runs-api.open-meteo.com/v1/forecast"
SINGLE_API = "https://single-runs-api.open-meteo.com/v1/forecast"
MODEL = "icon_global"
LAT, LON = 50.033, 8.570
OFFSETS = (1, 2, 3)
VARIABLES = ("wind_speed_10m", "wind_direction_10m", "wind_gusts_10m", "pressure_msl", "temperature_2m")
SUFFIX = {"wind_speed_10m": "kn", "wind_direction_10m": "deg", "wind_gusts_10m": "kn",
          "pressure_msl": "hpa", "temperature_2m": "c"}
UNITS = {"wind_speed_10m": "kn", "wind_direction_10m": "°", "wind_gusts_10m": "kn",
         "pressure_msl": "hPa", "temperature_2m": "°C"}
RANGES = {"wind_speed_10m": (0, 150), "wind_direction_10m": (0, 360), "wind_gusts_10m": (0, 180),
          "pressure_msl": (800, 1100), "temperature_2m": (-90, 60)}
AGENT = "aiw-forecast-data-handoff/1.0"


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(body):
    return hashlib.sha256(body).hexdigest()


def save(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_bytes(body)
    os.replace(temp, path)


def save_json(path, value):
    save(path, (json.dumps(value, indent=2, sort_keys=True) + "\n").encode())


def load_manifest():
    if MANIFEST_PATH.exists():
        try:
            data = json.loads(MANIFEST_PATH.read_text())
            if data.get("manifest_version") == 1:
                return data
        except (OSError, json.JSONDecodeError):
            pass
    return {"manifest_version": 1, "model": MODEL, "requested_location": {"latitude": LAT, "longitude": LON},
            "timezone": "UTC", "wind_speed_unit": "kn", "chunks": {}, "single_runs_probe": None}


def write_manifest(manifest):
    manifest["updated_at_utc"] = now()
    save_json(MANIFEST_PATH, manifest)


def months(start, end):
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        first = date(year, month, 1)
        last = date(year, month, calendar.monthrange(year, month)[1])
        yield max(start, first), min(end, last)
        if month == 12:
            year, month = year + 1, 1
        else:
            month += 1


def fields():
    return [f"{v}_previous_day{n}" for n in OFFSETS for v in VARIABLES]


def get(url, retries):
    headers = {"User-Agent": AGENT, "Accept": "application/json"}
    last_error = None
    for attempt in range(retries + 1):
        try:
            with urlopen(Request(url, headers=headers), timeout=120) as response:
                body = response.read()
                return response.status, body, {
                    k.lower(): v for k, v in response.headers.items()
                    if k.lower() in {"content-type", "date", "etag", "last-modified"}
                }
        except HTTPError as error:
            last_error = f"HTTP {error.code}: {error.reason}"
            if error.code not in {408, 425, 429, 500, 502, 503, 504}:
                raise RuntimeError(last_error) from error
        except (URLError, TimeoutError, OSError) as error:
            last_error = str(error)
        if attempt < retries:
            time.sleep(min(2 ** attempt, 20))
    raise RuntimeError(f"Request failed after {retries + 1} attempts: {last_error}")


def request_url(start, end):
    params = {
        "latitude": f"{LAT:.3f}", "longitude": f"{LON:.3f}",
        "start_date": start.isoformat(), "end_date": end.isoformat(),
        "hourly": ",".join(fields()), "wind_speed_unit": "kn",
        "timezone": "UTC", "models": MODEL,
    }
    return f"{PREVIOUS_API}?{urlencode(params)}", params


def fetch(start, end, delay, retries, force):
    manifest = load_manifest()
    manifest["requested_period_utc"] = {"start_inclusive": start.isoformat(), "end_inclusive": end.isoformat()}
    manifest["fetch_policy"] = {
        "monthly_chunks": True, "delay_between_requests_seconds": delay, "retries": retries,
        "historical_publication_time_proven": False,
    }
    write_manifest(manifest)
    last_request = None
    for first, last in months(start, end):
        key = first.strftime("%Y-%m")
        path = RUNS / f"{key}.json"
        url, params = request_url(first, last)
        entry = manifest["chunks"].get(key)
        if not force and path.exists() and entry and entry.get("url") == url and digest(path.read_bytes()) == entry.get("sha256"):
            try:
                cached = json.loads(path.read_bytes())
                if all(f in cached.get("hourly", {}) for f in fields()):
                    print(f"cache {key}: {len(cached['hourly']['time'])} rows")
                    continue
            except (json.JSONDecodeError, KeyError):
                pass
        if last_request is not None:
            wait = delay - (time.monotonic() - last_request)
            if wait > 0:
                time.sleep(wait)
        print(f"fetch {key} {first}..{last}", flush=True)
        requested = now()
        last_request = time.monotonic()
        status, body, headers = get(url, retries)
        data = json.loads(body)
        save(path, body)
        manifest["chunks"][key] = {
            "requested_start_inclusive_utc": first.isoformat(), "requested_end_inclusive_utc": last.isoformat(),
            "requested_at_utc": requested, "retrieved_at_utc": now(), "http_status": status,
            "url": url, "parameters": params, "response_headers": headers,
            "raw_file": str(path.relative_to(ROOT)), "raw_bytes": len(body),
            "sha256": digest(body), "rows": len(data.get("hourly", {}).get("time", [])),
        }
        write_manifest(manifest)
        print(f"saved {key}: {manifest['chunks'][key]['rows']} rows sha256={manifest['chunks'][key]['sha256']}", flush=True)


def normalize(start, end):
    manifest = load_manifest()
    expected = []
    cursor = datetime(start.year, start.month, start.day, tzinfo=timezone.utc)
    stop = datetime(end.year, end.month, end.day, tzinfo=timezone.utc) + timedelta(days=1)
    while cursor < stop:
        expected.append(cursor)
        cursor += timedelta(hours=1)
    expected_set = set(expected)
    by_time, grids, schema_errors, missing_chunks = {}, set(), [], []
    nulls, values, violations, api_units = {}, {}, {}, {}
    all_fields = fields()
    for field in all_fields:
        nulls[field], values[field], violations[field] = 0, [], 0
    chunk_stats = []

    for first, last in months(start, end):
        key = first.strftime("%Y-%m")
        path = RUNS / f"{key}.json"
        entry = manifest.get("chunks", {}).get(key)
        if not entry or not path.exists():
            missing_chunks.append(key)
            continue
        body = path.read_bytes()
        if digest(body) != entry.get("sha256"):
            schema_errors.append(f"{key}: raw SHA-256 mismatch")
            continue
        try:
            data = json.loads(body)
        except json.JSONDecodeError as error:
            schema_errors.append(f"{key}: invalid JSON ({error})")
            continue
        hourly, hourly_units = data.get("hourly", {}), data.get("hourly_units", {})
        times = hourly.get("time", [])
        absent = [f for f in all_fields if f not in hourly]
        if absent:
            schema_errors.append(f"{key}: missing fields {absent}")
            continue
        if data.get("utc_offset_seconds") != 0:
            schema_errors.append(f"{key}: response timezone offset is not UTC")
        grid = (data.get("latitude"), data.get("longitude"))
        try:
            grid = (float(grid[0]), float(grid[1]))
            grids.add(grid)
        except (TypeError, ValueError):
            schema_errors.append(f"{key}: missing grid coordinates")
        for field in all_fields:
            if len(hourly[field]) != len(times):
                schema_errors.append(f"{key}: {field} length mismatch")
            base = field.rsplit("_previous_day", 1)[0]
            api_units.setdefault(base, set()).add(str(hourly_units.get(field)))

        chunk_times = []
        for i, text in enumerate(times):
            stamp = datetime.fromisoformat(text.replace("Z", "+00:00"))
            if stamp.tzinfo is None:
                stamp = stamp.replace(tzinfo=timezone.utc)
            stamp = stamp.astimezone(timezone.utc)
            chunk_times.append(stamp)
            if stamp in by_time:
                continue
            row = {"time_utc": stamp, "model": MODEL, "requested_latitude_deg": LAT,
                   "requested_longitude_deg": LON, "grid_latitude_deg": grid[0], "grid_longitude_deg": grid[1]}
            for field in all_fields:
                base = field.rsplit("_previous_day", 1)[0]
                value = hourly[field][i]
                row[f"{field}_{SUFFIX[base]}"] = value
                if value is None:
                    nulls[field] += 1
                else:
                    try:
                        numeric = float(value)
                    except (TypeError, ValueError):
                        schema_errors.append(f"{key}: nonnumeric {field} at {text}")
                        continue
                    values[field].append(numeric)
                    low, high = RANGES[base]
                    violations[field] += not low <= numeric <= high
            by_time[stamp] = row
        chunk_expected = []
        t = datetime(first.year, first.month, first.day, tzinfo=timezone.utc)
        chunk_stop = datetime(last.year, last.month, last.day, tzinfo=timezone.utc) + timedelta(days=1)
        while t < chunk_stop:
            chunk_expected.append(t)
            t += timedelta(hours=1)
        chunk_stats.append({
            "month": key, "rows_expected": len(chunk_expected), "rows_returned": len(times),
            "missing_hours": len(set(chunk_expected) - set(chunk_times)),
            "extra_hours": len(set(chunk_times) - set(chunk_expected)),
            "first_utc": min(chunk_times).strftime("%Y-%m-%dT%H:%M:%SZ") if chunk_times else None,
            "last_utc": max(chunk_times).strftime("%Y-%m-%dT%H:%M:%SZ") if chunk_times else None,
            "returned_grid": grid,
        })

    actual, sorted_times = set(by_time), sorted(by_time)
    missing = sorted(expected_set - actual)
    extra = sorted(actual - expected_set)
    duplicates = sum(stat["rows_returned"] for stat in chunk_stats) - len(by_time)
    gaps = [
        {"from": a.isoformat(), "to": b.isoformat(), "hours": (b-a).total_seconds()/3600}
        for a, b in zip(sorted_times, sorted_times[1:]) if b-a != timedelta(hours=1)
    ]
    unit_pass = all(api_units.get(v) == {u} for v, u in UNITS.items())
    structural_pass = (
        not missing_chunks and not schema_errors and not duplicates and not missing and not extra and not gaps
        and len(grids) == 1 and unit_pass
    )
    wind_fields = [f"{v}_previous_day{n}" for n in OFFSETS
                   for v in ("wind_speed_10m", "wind_direction_10m", "wind_gusts_10m")]
    wind_complete = all(nulls[f] == 0 for f in wind_fields)
    all_complete = all(n == 0 for n in nulls.values())
    ranges_pass = all(n == 0 for n in violations.values())
    field_stats = {}
    for field in all_fields:
        base = field.rsplit("_previous_day", 1)[0]
        field_stats[field] = {
            "null_count": nulls[field], "numeric_count": len(values[field]),
            "min": min(values[field]) if values[field] else None,
            "max": max(values[field]) if values[field] else None,
            "out_of_range_count": violations[field], "sanity_range": RANGES[base],
            "unit": UNITS[base], "api_units_observed": sorted(api_units.get(base, set())),
        }
    columns = ["time_utc", "model", "requested_latitude_deg", "requested_longitude_deg",
               "grid_latitude_deg", "grid_longitude_deg"]
    columns += [f"{f}_{SUFFIX[f.rsplit('_previous_day', 1)[0]]}" for f in all_fields]
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for stamp in sorted_times:
            row = dict(by_time[stamp])
            row["time_utc"] = stamp.strftime("%Y-%m-%dT%H:%M:%SZ")
            writer.writerow(row)
    csv_hash = digest(CSV_PATH.read_bytes())
    quality = {
        "generated_at_utc": now(), "source": "Open-Meteo Previous Runs API", "model": MODEL,
        "period_utc": {"start_inclusive": start.isoformat()+"T00:00:00Z",
                       "end_inclusive": end.isoformat()+"T23:00:00Z"},
        "expected_hourly_rows": len(expected), "actual_unique_rows": len(by_time),
        "duplicate_timestamp_count": duplicates, "missing_expected_hour_count": len(missing),
        "extra_timestamp_count": len(extra), "non_hourly_gap_count": len(gaps),
        "missing_month_chunks": missing_chunks, "grid_points_observed": [
            {"latitude": lat, "longitude": lon} for lat, lon in sorted(grids)],
        "grid_point_consistent": len(grids) == 1, "chunk_quality": chunk_stats,
        "fields": field_stats, "schema_errors": schema_errors,
        "structural_validation_pass": structural_pass,
        "wind_features_complete": wind_complete, "all_fields_complete": all_complete,
        "value_ranges_pass": ranges_pass,
        "validation_pass": structural_pass and all_complete and ranges_pass,
        "normalized_csv": str(CSV_PATH.relative_to(ROOT)), "normalized_csv_rows": len(by_time),
        "normalized_csv_sha256": csv_hash,
        "interpretation_limits": [
            "Archive retrieval does not prove public availability at historical issue times.",
            "Previous-day values are lead-time series and do not identify a single source run per hour.",
            "Missing hourly values remain blank and are never imputed.",
            "Returned coordinates identify the model grid cell, which may differ from the requested coordinates.",
        ],
    }
    save_json(QUALITY_PATH, quality)
    manifest["normalized_output"] = {"path": str(CSV_PATH.relative_to(ROOT)), "rows": len(by_time),
                                     "columns": columns, "sha256": csv_hash}
    manifest["quality_report"] = str(QUALITY_PATH.relative_to(ROOT))
    write_manifest(manifest)
    print(json.dumps({
        "structural_validation_pass": structural_pass, "wind_features_complete": wind_complete,
        "all_fields_complete": all_complete, "value_ranges_pass": ranges_pass,
        "expected_rows": len(expected), "actual_rows": len(by_time), "missing": len(missing),
        "duplicates": duplicates, "extra": len(extra), "schema_errors": schema_errors[:5],
        "output": str(CSV_PATH), "quality": str(QUALITY_PATH),
    }, indent=2))
    nonnull_warnings = {name: stat["null_count"] for name, stat in field_stats.items() if stat["null_count"]}
    if nonnull_warnings:
        print("WARNING: missing optional fields are retained as blanks: " + json.dumps(nonnull_warnings))
    if not structural_pass or not wind_complete or not ranges_pass:
        raise RuntimeError("Structural, wind-feature or value-range validation failed; inspect quality.json")


def probe(run, retries):
    init = datetime.strptime(run, "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc)
    params = {"latitude": f"{LAT:.3f}", "longitude": f"{LON:.3f}",
              "hourly": ",".join(VARIABLES), "wind_speed_unit": "kn", "timezone": "UTC",
              "models": MODEL, "run": run, "forecast_days": "3"}
    url = f"{SINGLE_API}?{urlencode(params)}"
    print(f"probe Single Runs {run} UTC", flush=True)
    requested = now()
    status, body, headers = get(url, retries)
    data = json.loads(body)
    path = SINGLES / f"{run.replace(':', '-')}.json"
    save(path, body)
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    stats = {}
    for variable in VARIABLES:
        vals = [float(v) for v in hourly.get(variable, []) if v is not None]
        count = len(hourly.get(variable, []))
        stats[variable] = {"count": count, "null_count": count-len(vals),
                           "min": min(vals) if vals else None, "max": max(vals) if vals else None,
                           "unit": data.get("hourly_units", {}).get(variable)}
    result = {
        "requested_at_utc": requested, "retrieved_at_utc": now(), "http_status": status, "url": url,
        "parameters": params, "response_headers": headers, "raw_file": str(path.relative_to(ROOT)),
        "raw_bytes": len(body), "sha256": digest(body), "requested_run_initialization_utc": init.isoformat(),
        "model": MODEL, "returned_grid": {"latitude": data.get("latitude"), "longitude": data.get("longitude"),
                                           "elevation_m": data.get("elevation")},
        "timezone": data.get("timezone"), "utc_offset_seconds": data.get("utc_offset_seconds"),
        "rows": len(times), "first_valid_time_utc": times[0] if times else None,
        "last_valid_time_utc": times[-1] if times else None,
        "missing_fields": [v for v in VARIABLES if v not in hourly], "variables": stats,
        "interpretation": ["This proves the run is retrievable now, not when it was first published.",
                           "The run parameter is initialization time, not publication time."],
    }
    save_json(ROOT / "single-runs-probe.json", result)
    manifest = load_manifest()
    manifest["single_runs_probe"] = result
    write_manifest(manifest)
    print(json.dumps({"http_status": status, "run": run, "rows": len(times),
                      "first": result["first_valid_time_utc"], "last": result["last_valid_time_utc"],
                      "missing_fields": result["missing_fields"], "output": str(ROOT / "single-runs-probe.json")},
                     indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("fetch", "verify"):
        p = sub.add_parser(name)
        p.add_argument("--start", default="2025-01-01")
        p.add_argument("--end", default="2026-10-29")
    p = sub.choices["fetch"]
    p.add_argument("--delay", type=float, default=1.25)
    p.add_argument("--retries", type=int, default=4)
    p.add_argument("--force", action="store_true")
    p = sub.add_parser("probe-single-run")
    p.add_argument("--run", default="2026-10-29T00:00")
    p.add_argument("--retries", type=int, default=4)
    args = parser.parse_args()
    if args.command == "probe-single-run":
        probe(args.run, args.retries)
    else:
        start, end = date.fromisoformat(args.start), date.fromisoformat(args.end)
        if end < start:
            parser.error("--end must be on or after --start")
        if args.command == "fetch":
            fetch(start, end, args.delay, args.retries, args.force)
        else:
            normalize(start, end)


if __name__ == "__main__":
    main()
