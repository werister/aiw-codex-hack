#!/usr/bin/env python3
"""Narrow Previous Runs vs Single Runs timing probe (stdlib only).

Run `python3 resources/ml-depth/temporal/probe.py --fetch` to save raw public
responses and a comparison for TARGET_DATE. `--verify` compares saved bodies
without network access. This probes icon_global only; it does not establish
availability times or map best_match's changing model mix.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
TARGET_DATE = "2026-10-28"
LAT, LON = 50.033, 8.570
PREVIOUS_URL = "https://previous-runs-api.open-meteo.com/v1/forecast"
SINGLE_URL = "https://single-runs-api.open-meteo.com/v1/forecast"
VARIABLES = ("wind_speed_10m", "wind_direction_10m", "wind_gusts_10m")


def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def query_url(base, params):
    return base + "?" + urllib.parse.urlencode(params)


def get_saved_or_fetch(name, base, params, receipts, fetch):
    path = RAW / f"{name}.json"
    url = query_url(base, params)
    if path.exists():
        body = path.read_bytes()
        old = next((r for r in receipts if r.get("file") == path.name), None)
        digest = hashlib.sha256(body).hexdigest()
        if (old and old.get("http_status") == 200 and old.get("url") == url
                and old.get("sha256") == digest):
            return json.loads(body), old
        if not fetch:
            raise RuntimeError(f"Saved response/receipt mismatch for {path.name}")
        if old:
            receipts.remove(old)
        path.unlink()
    if not fetch:
        raise RuntimeError(f"Missing saved response: {path.name}; run with --fetch")

    last_error = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "EDDF-temporal-audit/1.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                body = response.read()
                receipt = {"file": path.name, "url": response.geturl(),
                           "retrieved_at_utc": utc_now(), "http_status": response.status,
                           "content_type": response.headers.get("Content-Type"),
                           "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}
            path.write_bytes(body)
            receipts.append(receipt)
            time.sleep(1.2)
            return json.loads(body), receipt
        except urllib.error.HTTPError as exc:
            body = exc.read()
            receipt = {"file": path.name, "url": url, "retrieved_at_utc": utc_now(),
                       "http_status": exc.code, "bytes": len(body),
                       "sha256": hashlib.sha256(body).hexdigest(),
                       "error_body": body.decode("utf-8", "replace")[:1000]}
            path.write_bytes(body)
            receipts.append(receipt)
            last_error = RuntimeError(f"HTTP {exc.code} for {name}: {receipt['error_body']}")
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 3:
                raise last_error
            time.sleep(min(30, 5 * (attempt + 1)))
        except Exception as exc:
            last_error = exc
            if attempt == 3:
                raise
            time.sleep(min(30, 5 * (attempt + 1)))
    raise last_error or RuntimeError("request failed")


def save_receipts(receipts):
    (ROOT / "receipts.json").write_text(json.dumps(receipts, indent=2) + "\n", encoding="utf-8")


def parse_hourly(payload, field):
    hourly = payload.get("hourly") or {}
    times = hourly.get("time") or []
    vals = hourly.get(field) or []
    return {t: v for t, v in zip(times, vals)}


def main():
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--fetch", action="store_true", help="retrieve/cache narrow public responses")
    mode.add_argument("--verify", action="store_true", help="compare cached responses only")
    args = ap.parse_args()
    RAW.mkdir(exist_ok=True)
    receipts_path = ROOT / "receipts.json"
    receipts = json.loads(receipts_path.read_text()) if receipts_path.exists() else []
    fetch = args.fetch

    best_fields = [f"{variable}_previous_day{n}" for variable in VARIABLES for n in (1, 2, 3)]
    best_params = {"latitude": LAT, "longitude": LON, "hourly": ",".join(best_fields),
                   "wind_speed_unit": "kn", "timezone": "UTC", "models": "best_match",
                   "start_date": TARGET_DATE, "end_date": TARGET_DATE}
    best_payload, _ = get_saved_or_fetch("previous-best_match", PREVIOUS_URL, best_params, receipts, fetch)
    # Direct ICON global is a model-specific control; the handoff package uses best_match.
    icon_params = best_params | {"models": "icon_global"}
    icon_payload, _ = get_saved_or_fetch("previous-icon_global", PREVIOUS_URL, icon_params, receipts, fetch)

    day_values = {n: {v: parse_hourly(icon_payload, f"{v}_previous_day{n}") for v in VARIABLES}
                  for n in (1, 2, 3)}
    best_values = {n: {v: parse_hourly(best_payload, f"{v}_previous_day{n}") for v in VARIABLES}
                   for n in (1, 2, 3)}
    target_hours = sorted(day_values[1][VARIABLES[0]])
    if len(target_hours) != 24:
        raise RuntimeError(f"Expected 24 UTC hours for {TARGET_DATE}, got {len(target_hours)}")

    runs = {}
    date0 = dt.date.fromisoformat(TARGET_DATE)
    for n in (1, 2, 3):
        for cycle in (0, 6, 12, 18):
            run = dt.datetime.combine(date0 - dt.timedelta(days=n), dt.time(cycle), tzinfo=dt.timezone.utc)
            run_text = run.strftime("%Y-%m-%dT%H:%M")
            params = {"latitude": LAT, "longitude": LON, "hourly": ",".join(VARIABLES),
                      "wind_speed_unit": "kn", "timezone": "UTC", "models": "icon_global",
                      "run": run_text, "forecast_days": 5}
            name = "single-icon_global-" + run.strftime("%Y%m%dT%H")
            payload, receipt = get_saved_or_fetch(name, SINGLE_URL, params, receipts, fetch)
            if receipt.get("http_status") != 200 or not payload.get("hourly"):
                runs[run_text] = {"error": receipt.get("error_body", "non-200 or no hourly payload")}
            else:
                runs[run_text] = {v: parse_hourly(payload, v) for v in VARIABLES}
    save_receipts(receipts)

    results = []
    for n in (1, 2, 3):
        matches = mismatches = missing = 0
        variable_counts = {v: {"matches": 0, "mismatches": 0, "missing": 0} for v in VARIABLES}
        details = []
        all_valid_times = sorted(day_values[n][VARIABLES[0]])
        for valid_time in all_valid_times:
            hour = int(valid_time[11:13])
            run = dt.datetime.combine(date0 - dt.timedelta(days=n), dt.time((hour // 6) * 6),
                                      tzinfo=dt.timezone.utc).strftime("%Y-%m-%dT%H:%M")
            run_values = runs.get(run, {})
            previous_values = {v: day_values[n][v].get(valid_time) for v in VARIABLES}
            single_values = {v: run_values.get(v, {}).get(valid_time) for v in VARIABLES}
            statuses = {}
            for v in VARIABLES:
                p, s = previous_values[v], single_values[v]
                if p is None or s is None:
                    variable_counts[v]["missing"] += 1
                    statuses[v] = "missing"
                elif abs(float(p) - float(s)) <= 1e-8:
                    variable_counts[v]["matches"] += 1
                    statuses[v] = "exact_match"
                else:
                    variable_counts[v]["mismatches"] += 1
                    statuses[v] = "value_mismatch"
            if any(s == "missing" for s in statuses.values()):
                missing += 1
                status = "missing"
            elif all(s == "exact_match" for s in statuses.values()):
                matches += 1
                status = "exact_match"
            else:
                mismatches += 1
                status = "value_mismatch"
            details.append({"valid_time_utc": valid_time, "previous_values": previous_values,
                            "expected_run_utc": run, "single_run_values": single_values,
                            "per_variable_status": statuses, "all_variables_status": status})
        best_vs_icon = {v: [] for v in VARIABLES}
        for v in VARIABLES:
            for t, b in best_values[n][v].items():
                i = day_values[n][v].get(t)
                if b is not None and i is not None:
                    best_vs_icon[v].append({"valid_time_utc": t, "best_match": b,
                                            "icon_global": i, "equal": abs(float(b)-float(i)) <= 1e-8})
        results.append({"previous_day": n, "hours": len(all_valid_times), "matches": matches,
                        "mismatches": mismatches, "missing": missing,
                        "per_variable": variable_counts,
                        "distinct_expected_cycle_boundaries": sorted({d["expected_run_utc"] for d in details}),
                        "best_match_vs_icon_global_equal_hours_per_variable": {
                            v: sum(x["equal"] for x in best_vs_icon[v]) for v in VARIABLES},
                        "best_match_vs_icon_global_compared_hours_per_variable": {
                            v: len(best_vs_icon[v]) for v in VARIABLES},
                        "details": details, "best_match_vs_icon_global": best_vs_icon})

    out = {"target_date_utc": TARGET_DATE, "coordinates": {"latitude": LAT, "longitude": LON},
           "probe_model": "icon_global", "variables": list(VARIABLES),
           "units_from_api_hourly_units": True,
           "mapping_hypothesis": "run_date = valid_date - N days; for 6-hour cycle model run hour = floor(valid_hour/6)*6",
           "interpretation_limit": "This compares forecast values; it does not observe historical publication time and does not establish best_match source model/run semantics.",
           "results": results}
    (ROOT / "comparison.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"target_date_utc": TARGET_DATE, "results": [
        {k: r[k] for k in ("previous_day", "hours", "matches", "mismatches", "missing", "per_variable", "distinct_expected_cycle_boundaries", "best_match_vs_icon_global_equal_hours_per_variable", "best_match_vs_icon_global_compared_hours_per_variable")}
        for r in results]}, indent=2))
    if any(r["mismatches"] or r["missing"] for r in results):
        raise SystemExit(2)

if __name__ == "__main__":
    main()
