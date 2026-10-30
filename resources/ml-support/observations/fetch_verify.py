#!/usr/bin/env python3
"""Fetch and QA public EDDF IEM routine/special METARs; optionally add DWD overlap."""
from __future__ import annotations
import argparse, csv, hashlib, io, json, re, time, zipfile
from collections import Counter, defaultdict
from datetime import date, datetime, time as dt_time, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw" / "iem"
ENDPOINT = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py"
START = date(2024, 12, 29)
END_EXCLUSIVE = date(2026, 10, 30)
KT_PER_MS = 1.9438444924406
WIND_GROUP = re.compile(r"(?<![A-Z0-9])(VRB|\d{3})(\d{2,3})(?:G(\d{2,3}))?(KT|MPS|KMH)\b")
VAR_RANGE = re.compile(r"(?<!\d)(\d{3})V(\d{3})(?!\d)")
FIELDS = [
    "station", "observation_time_utc", "report_type", "report_type_name",
    "wind_direction_deg", "wind_speed_kt", "wind_gust_kt",
    "wind_direction_status", "wind_speed_status", "wind_gust_status",
    "variable_direction_from_deg", "variable_direction_to_deg",
    "raw_drct", "raw_sknt", "raw_gust", "raw_metar", "raw_chunk_file",
]

def write_json(path: Path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def next_month(d: date) -> date:
    return date(d.year + (d.month == 12), 1 if d.month == 12 else d.month + 1, 1)

def month_chunks():
    first = date(START.year, START.month, 1)
    while first < END_EXCLUSIVE:
        following = next_month(first)
        yield max(START, first), min(END_EXCLUSIVE, following)
        first = following

def build_url(begin: date, end: date, report_type: int) -> str:
    pairs = [
        ("station", "EDDF"), ("data", "drct"), ("data", "sknt"),
        ("data", "gust"), ("data", "metar"),
        ("year1", str(begin.year)), ("month1", str(begin.month)), ("day1", str(begin.day)),
        ("year2", str(end.year)), ("month2", str(end.month)), ("day2", str(end.day)),
        ("tz", "Etc/UTC"), ("format", "onlycomma"), ("latlon", "no"),
        ("elev", "no"), ("missing", "M"), ("trace", "T"), ("direct", "no"),
        ("report_type", str(report_type)),
    ]
    return ENDPOINT + "?" + urlencode(pairs)

def fetch_bytes(url: str) -> tuple[bytes, int]:
    req = Request(url, headers={"User-Agent": "AIW-EDDF-observation-handoff/1.0 (public data research)"})
    with urlopen(req, timeout=60) as response:
        return response.read(), response.status

def fetch_all(pause: float, force: bool):
    RAW.mkdir(parents=True, exist_ok=True)
    manifest_path = ROOT / "manifest.json"
    manifest = {
        "dataset": "EDDF METAR/ASOS observations from Iowa Environmental Mesonet",
        "endpoint": ENDPOINT,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "requested_period": {"start_inclusive_utc": START.isoformat(), "end_inclusive_utc": (END_EXCLUSIVE - timedelta(days=1)).isoformat(), "api_end_exclusive_utc": END_EXCLUSIVE.isoformat()},
        "request_policy": {"chunking": "calendar month; routine and special reports requested separately", "minimum_seconds_between_requests": max(2.0, pause), "report_types": {"3": "routine", "4": "special"}, "data_fields": ["drct", "sknt", "gust", "metar"]},
        "source_notes": ["IEM describes archive as an as-is collection with little quality control.", "Each response is retained byte-for-byte as CSV under raw/iem/.", "API date bounds are inclusive start and exclusive end."],
        "requests": [],
    }
    prior_manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else None
    old_requests = {(item["file"]): item for item in (prior_manifest or {}).get("requests", [])}
    last_request_at = None
    for begin, end in month_chunks():
        for report_type, name in ((3, "routine"), (4, "special")):
            filename = f"{begin:%Y-%m}-type{report_type}-{name}.csv"
            path = RAW / filename
            url = build_url(begin, end, report_type)
            if path.exists() and not force:
                content = path.read_bytes()
                info = old_requests.get(filename, {})
                info.update({"file": filename, "url": info.get("url", url), "sha256": sha256(content), "bytes": len(content), "reused_cached_file": True})
            else:
                if last_request_at is not None:
                    time.sleep(max(2.0, pause) - (time.monotonic() - last_request_at))
                last_request_at = time.monotonic()
                error = None
                for attempt in range(4):
                    try:
                        content, status = fetch_bytes(url)
                        if status != 200 or not content.startswith(b"station,"):
                            raise RuntimeError(f"unexpected response status/content: {status}; {content[:120]!r}")
                        path.write_bytes(content)
                        error = None
                        break
                    except (HTTPError, URLError, TimeoutError, RuntimeError) as exc:
                        error = str(exc)
                        if attempt < 3:
                            time.sleep(2 ** attempt * max(2.0, pause))
                if error is not None:
                    raise RuntimeError(f"Failed {url}: {error}")
                info = {"file": filename, "url": url, "retrieved_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "http_status": status, "sha256": sha256(content), "bytes": len(content), "reused_cached_file": False}
            rows = list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"))))
            info["rows"] = len(rows)
            info["fields"] = list(rows[0].keys()) if rows else ["station", "valid", "drct", "sknt", "gust", "metar"]
            manifest["requests"].append(info)
            write_json(manifest_path, manifest)
            if len(manifest["requests"]) % 8 == 0:
                print(f"requests processed: {len(manifest['requests'])}/46")
    manifest["normalized_output"] = "eddf_metar_observations.csv"
    write_json(manifest_path, manifest)

def number(value):
    if value is None or value.strip() in ("", "M", "-999", "-999.0", "///"):
        return None
    try:
        return float(value)
    except ValueError:
        return None

def verify_raw_manifest():
    manifest_path = ROOT / "manifest.json"
    if not manifest_path.exists():
        raise RuntimeError("manifest.json is missing; fetch raw chunks first")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    checked = 0
    for item in manifest.get("requests", []):
        path = RAW / item["file"]
        if not path.exists():
            raise RuntimeError(f"raw response is missing: {path.name}")
        content = path.read_bytes()
        if len(content) != item.get("bytes") or sha256(content) != item.get("sha256"):
            raise RuntimeError(f"raw response integrity check failed: {path.name}")
        checked += 1
    if checked != 46:
        raise RuntimeError(f"expected 46 monthly/type response files, found {checked}")
    return checked

def normalize():
    verify_raw_manifest()
    all_rows = []
    for path in sorted(RAW.glob("*.csv")):
        m = re.match(r"(\d{4}-\d{2})-type(\d)-", path.name)
        if not m:
            continue
        report_type = int(m.group(2))
        report_name = "routine" if report_type == 3 else "special" if report_type == 4 else "other"
        with path.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                raw = (row.get("metar") or "").strip()
                valid = (row.get("valid") or "").strip()
                try:
                    obs = datetime.strptime(valid, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
                if not (datetime.combine(START, dt_time.min, tzinfo=timezone.utc) <= obs < datetime.combine(END_EXCLUSIVE, dt_time.min, tzinfo=timezone.utc)):
                    continue
                parsed_speed = number(row.get("sknt"))
                parsed_dir = number(row.get("drct"))
                parsed_gust = number(row.get("gust"))
                wm = WIND_GROUP.search(raw)
                vr = VAR_RANGE.search(raw)
                raw_direction = wm.group(1) if wm else None
                raw_speed = int(wm.group(2)) if wm else None
                raw_gust = int(wm.group(3)) if wm and wm.group(3) else None
                raw_unit = wm.group(4) if wm else None
                if raw_direction == "VRB":
                    direction_status = "VARIABLE_VRB"
                    out_dir = None
                elif raw_direction == "000" and raw_speed == 0:
                    direction_status = "CALM"
                    out_dir = None
                elif raw_direction is not None:
                    direction_status = "VARIABLE_RANGE" if vr else "DIRECTIONAL"
                    out_dir = parsed_dir
                elif parsed_dir is not None:
                    direction_status = "PARSED_DIRECTION_ONLY"
                    out_dir = parsed_dir
                else:
                    direction_status = "MISSING"
                    out_dir = None
                if parsed_speed is None:
                    speed_status = "MISSING"
                elif parsed_speed == 0:
                    speed_status = "CALM"
                else:
                    speed_status = "OBSERVED"
                if parsed_gust is not None or raw_gust is not None:
                    gust_status = "REPORTED"
                elif wm is None:
                    gust_status = "WIND_GROUP_MISSING"
                else:
                    gust_status = "NOT_ENCODED"
                all_rows.append({
                    "station": row.get("station", "EDDF"),
                    "observation_time_utc": obs.isoformat(timespec="seconds").replace("+00:00", "Z"),
                    "report_type": report_type,
                    "report_type_name": report_name,
                    "wind_direction_deg": out_dir,
                    "wind_speed_kt": parsed_speed,
                    "wind_gust_kt": parsed_gust,
                    "wind_direction_status": direction_status,
                    "wind_speed_status": speed_status,
                    "wind_gust_status": gust_status,
                    "variable_direction_from_deg": int(vr.group(1)) if vr else None,
                    "variable_direction_to_deg": int(vr.group(2)) if vr else None,
                    "raw_drct": row.get("drct"),
                    "raw_sknt": row.get("sknt"),
                    "raw_gust": row.get("gust"),
                    "raw_metar": raw,
                    "raw_chunk_file": path.name,
                    "raw_wind_group": wm.group(0) if wm else None,
                    "raw_wind_group_unit": raw_unit,
                    "raw_wind_speed": raw_speed,
                    "raw_wind_gust": raw_gust,
                })
    all_rows.sort(key=lambda r: (r["observation_time_utc"], r["report_type"], r["raw_metar"]))
    path = ROOT / "eddf_metar_observations.csv"
    keys = FIELDS + ["raw_wind_group", "raw_wind_group_unit", "raw_wind_speed", "raw_wind_gust"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader(); writer.writerows(all_rows)
    return all_rows

def summarize(rows):
    times = sorted({datetime.fromisoformat(r["observation_time_utc"].replace("Z", "+00:00")) for r in rows})
    type_counts = Counter(r["report_type_name"] for r in rows)
    report_minutes = defaultdict(Counter)
    for r in rows:
        report_minutes[r["report_type_name"]][datetime.fromisoformat(r["observation_time_utc"].replace("Z", "+00:00")).strftime("%M")] += 1
    intervals = Counter(round((b-a).total_seconds()/60) for a,b in zip(times,times[1:]))
    routine_times = sorted({datetime.fromisoformat(r["observation_time_utc"].replace("Z", "+00:00")) for r in rows if r["report_type"]==3})
    routine_intervals = Counter(round((b-a).total_seconds()/60) for a,b in zip(routine_times,routine_times[1:]))
    routine_missing_hours = []
    if routine_times:
        cursor = routine_times[0].replace(minute=0,second=0,microsecond=0)
        end = routine_times[-1].replace(minute=0,second=0,microsecond=0)
        have = {t.replace(minute=0,second=0,microsecond=0) for t in routine_times}
        while cursor <= end:
            if cursor not in have: routine_missing_hours.append(cursor.isoformat().replace("+00:00","Z"))
            cursor += timedelta(hours=1)
    dup_key = Counter((r["station"],r["observation_time_utc"],r["report_type"],r["raw_metar"]) for r in rows)
    wind_status = Counter(r["wind_direction_status"] for r in rows)
    gust_status = Counter(r["wind_gust_status"] for r in rows)
    speed_vals = [r["wind_speed_kt"] for r in rows if r["wind_speed_kt"] is not None]
    gust_vals = [r["wind_gust_kt"] for r in rows if r["wind_gust_kt"] is not None]
    speeds_missing = sum(r["wind_speed_kt"] is None for r in rows)
    group_missing = sum(not r["raw_wind_group"] for r in rows)
    range_out = sum((x < 0 or x > 150) for x in speed_vals)
    gust_below = sum(r["wind_gust_kt"] is not None and r["wind_speed_kt"] is not None and r["wind_gust_kt"] < r["wind_speed_kt"] for r in rows)
    raw_speed_mismatch = sum(r["raw_wind_speed"] is not None and r["wind_speed_kt"] is not None and abs(r["raw_wind_speed"]-r["wind_speed_kt"]) > 1e-9 for r in rows)
    raw_gust_mismatch = sum(r["raw_wind_gust"] is not None and r["wind_gust_kt"] is not None and abs(r["raw_wind_gust"]-r["wind_gust_kt"]) > 1e-9 for r in rows)
    return {
        "dataset": "EDDF IEM METAR/ASOS observations",
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "requested_range_utc": {"start_inclusive": START.isoformat(), "end_inclusive": (END_EXCLUSIVE-timedelta(days=1)).isoformat()},
        "coverage": {"rows": len(rows), "first_observation_utc": times[0].isoformat().replace("+00:00","Z") if times else None, "last_observation_utc": times[-1].isoformat().replace("+00:00","Z") if times else None, "unique_observation_times": len(times), "routine_rows": type_counts["routine"], "special_rows": type_counts["special"], "report_minute_of_hour_counts_utc": {name: dict(sorted(counts.items())) for name, counts in sorted(report_minutes.items())}, "routine_interval_minutes": dict(sorted(routine_intervals.items())), "all_report_interval_minutes": dict(sorted(intervals.items())), "routine_missing_hour_count_between_first_and_last": len(routine_missing_hours), "routine_missing_hour_examples_utc": routine_missing_hours[:20]},
        "duplicates": {"exact_duplicate_rows": sum(n-1 for n in dup_key.values() if n>1), "observation_times_with_multiple_rows": sum(1 for t in Counter(r["observation_time_utc"] for r in rows).values() if t>1)},
        "wind_quality": {"direction_status_counts": dict(wind_status), "gust_status_counts": dict(gust_status), "missing_speed_count": speeds_missing, "missing_raw_wind_group_count": group_missing, "speed_kt_min": min(speed_vals) if speed_vals else None, "speed_kt_max": max(speed_vals) if speed_vals else None, "gust_kt_min": min(gust_vals) if gust_vals else None, "gust_kt_max": max(gust_vals) if gust_vals else None, "speed_outside_0_to_150_kt_count": range_out, "reported_gust_below_mean_speed_count": gust_below, "unknown_gust_count_not_encoded": gust_status["NOT_ENCODED"], "raw_group_field_mismatches": {"speed_group_vs_IEM_sknt": raw_speed_mismatch, "gust_group_vs_IEM_gust": raw_gust_mismatch}, "raw_wind_group_unit_counts": dict(Counter(r["raw_wind_group_unit"] or "MISSING" for r in rows))},
        "interpretation_limits": ["Missing gust is represented as null with status NOT_ENCODED; it is not zero. A METAR gust group reports qualifying gusts only, so the absence of the group does not establish absence of stronger instantaneous wind.", "VRB direction is kept as unknown direction; calm 00000KT is separate. Variable direction ranges are retained separately.", "IEM describes its archive as as-is with little quality control; raw responses are preserved for independent reprocessing.", "No runway labels or operating-direction labels are generated by this package."],
    }

def read_dwd_member(path: Path, token: str):
    with zipfile.ZipFile(path) as z:
        member = next(n for n in z.namelist() if n.endswith(".txt") and token in n)
        text = z.read(member).decode("latin-1")
    parsed = list(csv.DictReader(io.StringIO(text), delimiter=";"))
    # DWD fixed-width-aligned header/value cells contain leading spaces.
    cleaned = [{(k or "").strip(): (v or "").strip() for k, v in row.items()} for row in parsed]
    return member, cleaned

def read_dwd_parameter_metadata(path: Path, parameter_file: str, parameters: set[str]):
    with zipfile.ZipFile(path) as z:
        member = next(n for n in z.namelist() if n.endswith(parameter_file))
        content = z.read(member).decode("latin-1")
    rows = [{(k or "").strip(): (v or "").strip() for k, v in row.items()} for row in csv.DictReader(io.StringIO(content), delimiter=";")]
    start = START.strftime("%Y%m%d")
    end = (END_EXCLUSIVE - timedelta(days=1)).strftime("%Y%m%d")
    covering = [r for r in rows if r.get("Parameter") in parameters and r.get("Von_Datum", "") <= start and r.get("Bis_Datum", "") >= end]
    found = {r.get("Parameter") for r in covering}
    if found != parameters:
        raise RuntimeError(f"embedded DWD metadata does not cover requested interval for {parameters}; got {found}")
    if any("UTC" not in ((r.get("Zusatz-Info", "") + " " + r.get("Datenquelle (Strukturversion=SV)", ""))).upper() for r in covering):
        raise RuntimeError(f"embedded DWD metadata does not confirm UTC for {parameters}")
    return member, covering

def dwd_export(dwd_dir: Path | None, rows):
    if dwd_dir is None:
        print("DWD source not supplied; skipped")
        return None
    wind_zip = dwd_dir / "wind-01420-recent.zip"
    gust_zip = dwd_dir / "gust-01420-recent.zip"
    if not wind_zip.exists() or not gust_zip.exists():
        print("DWD source ZIPs missing; skipped")
        return None
    wind_member, wind_data = read_dwd_member(wind_zip, "produkt_ff_stunde")
    gust_member, gust_data = read_dwd_member(gust_zip, "produkt_fx_stunde")
    wind_meta_member, wind_meta = read_dwd_parameter_metadata(wind_zip, "Metadaten_Parameter_ff_stunde_01420.txt", {"F", "D"})
    gust_meta_member, gust_meta = read_dwd_parameter_metadata(gust_zip, "Metadaten_Parameter_fx_stunde_01420.txt", {"FX_911"})
    gust_by_time = {r["MESS_DATUM"]: r for r in gust_data}
    begin_dt = datetime.combine(START, dt_time.min, tzinfo=timezone.utc)
    end_dt = datetime.combine(END_EXCLUSIVE, dt_time.min, tzinfo=timezone.utc)
    out = []
    for w in wind_data:
        stamp = w.get("MESS_DATUM", "")
        try: dt = datetime.strptime(stamp, "%Y%m%d%H").replace(tzinfo=timezone.utc)
        except ValueError: continue
        if not begin_dt <= dt < end_dt: continue
        g = gust_by_time.get(stamp, {})
        mean_ms = number(w.get("F")); gust_ms = number(g.get("FX_911"))
        out.append({"timestamp_utc": dt.isoformat(timespec="seconds").replace("+00:00","Z"), "station_id": w.get("STATIONS_ID", ""), "station_name": "DWD station 01420 Frankfurt/Main (separate observation product)", "wind_quality_qn_3": w.get("QN_3", ""), "wind_mean_ms": mean_ms, "wind_mean_kt": mean_ms*KT_PER_MS if mean_ms is not None else None, "wind_direction_deg": number(w.get("D")), "gust_quality_qn_8": g.get("QN_8", ""), "wind_gust_hourly_max_ms": gust_ms, "wind_gust_hourly_max_kt": gust_ms*KT_PER_MS if gust_ms is not None else None})
    out.sort(key=lambda r:r["timestamp_utc"])
    path = ROOT / "dwd_01420_hourly_wind_gust_overlap.csv"
    keys = list(out[0].keys()) if out else ["timestamp_utc","station_id","station_name","wind_quality_qn_3","wind_mean_ms","wind_mean_kt","wind_direction_deg","gust_quality_qn_8","wind_gust_hourly_max_ms","wind_gust_hourly_max_kt"]
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(out)

    source_details = []
    known_urls = {
        wind_zip.name: "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/wind/recent/stundenwerte_FF_01420_akt.zip",
        gust_zip.name: "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/extreme_wind/recent/stundenwerte_FX_01420_akt.zip",
    }
    sources_index_candidates = [
        dwd_dir.parent.parent / "sources.json",
        ROOT.parent / "reference" / "project-sources.json",
    ]
    sources_index = next((candidate for candidate in sources_index_candidates if candidate.exists()), None)
    retrieved_by_path = {}
    if sources_index is not None:
        try:
            for item in json.loads(sources_index.read_text(encoding="utf-8")):
                retrieved_by_path[Path(item.get("path", "")).name] = item
        except (ValueError, OSError):
            pass
    existing_manifest = ROOT / "manifest.json"
    previous_sources = {}
    if existing_manifest.exists():
        try:
            old_manifest = json.loads(existing_manifest.read_text(encoding="utf-8"))
            previous_sources = {Path(item.get("path", "")).name: item for item in old_manifest.get("supplemental_sources", [])}
        except (ValueError, OSError):
            pass
    raw_target = ROOT / "raw" / "dwd"
    raw_target.mkdir(parents=True, exist_ok=True)
    for source_path, member in ((wind_zip, wind_member), (gust_zip, gust_member)):
        data = source_path.read_bytes()
        copy_path = raw_target / source_path.name
        if source_path.resolve() != copy_path.resolve():
            copy_path.write_bytes(data)
        indexed = retrieved_by_path.get(source_path.name) or previous_sources.get(source_path.name, {})
        expected_hash = indexed.get("sha256") or indexed.get("archive_sha256")
        if expected_hash and expected_hash != sha256(data):
            raise RuntimeError(f"DWD cache hash differs from source registry/manifest: {source_path.name}")
        source_details.append({"path": f"raw/dwd/{source_path.name}", "source_registry_path": indexed.get("path"), "url": indexed.get("url") or known_urls[source_path.name], "retrieved_at_utc": indexed.get("retrieved_at_utc"), "archive_bytes": len(data), "archive_sha256": sha256(data), "member_used": member})

    def count_missing(field): return sum(r[field] is None for r in out)
    times = [datetime.fromisoformat(r["timestamp_utc"].replace("Z", "+00:00")) for r in out]
    gaps = Counter(round((b-a).total_seconds()/3600) for a,b in zip(times,times[1:]))
    expected_hours = int((times[-1] - times[0]).total_seconds() / 3600) + 1 if len(times) > 1 else len(times)
    present_hours = set(times)
    missing_hours = []
    if times:
        cursor = times[0]
        while cursor <= times[-1]:
            if cursor not in present_hours:
                missing_hours.append(cursor.isoformat(timespec="seconds").replace("+00:00", "Z"))
            cursor += timedelta(hours=1)
    conversion_errors = []
    for record in out:
        if record["wind_mean_ms"] is not None: conversion_errors.append(abs(record["wind_mean_kt"] - record["wind_mean_ms"]*KT_PER_MS))
        if record["wind_gust_hourly_max_ms"] is not None: conversion_errors.append(abs(record["wind_gust_hourly_max_kt"] - record["wind_gust_hourly_max_ms"]*KT_PER_MS))
    q = {
        "output": path.name, "rows": len(out), "first_utc": out[0]["timestamp_utc"] if out else None, "last_utc": out[-1]["timestamp_utc"] if out else None,
        "expected_hourly_slots_between_first_and_last": expected_hours, "actual_hourly_slots": len(times), "missing_hour_slots_between_first_and_last": len(missing_hours), "missing_hour_examples_utc": missing_hours[:20],
        "observed_hour_interval_counts": dict(sorted(gaps.items())),
        "missing_counts": {"wind_mean_ms": count_missing("wind_mean_ms"), "wind_mean_kt": count_missing("wind_mean_kt"), "wind_direction_deg": count_missing("wind_direction_deg"), "wind_gust_hourly_max_ms": count_missing("wind_gust_hourly_max_ms"), "wind_gust_hourly_max_kt": count_missing("wind_gust_hourly_max_kt")},
        "quality_code_counts": {"wind_qn_3": dict(Counter(r["wind_quality_qn_3"] or "MISSING" for r in out)), "gust_qn_8": dict(Counter(r["gust_quality_qn_8"] or "MISSING" for r in out))},
        "wind_mean_ms_range": [min((r["wind_mean_ms"] for r in out if r["wind_mean_ms"] is not None), default=None), max((r["wind_mean_ms"] for r in out if r["wind_mean_ms"] is not None), default=None)],
        "wind_gust_hourly_max_ms_range": [min((r["wind_gust_hourly_max_ms"] for r in out if r["wind_gust_hourly_max_ms"] is not None), default=None), max((r["wind_gust_hourly_max_ms"] for r in out if r["wind_gust_hourly_max_ms"] is not None), default=None)],
        "unit_conversion_mps_to_kt": KT_PER_MS, "max_abs_conversion_error_kt": max(conversion_errors, default=0.0),
        "time_interpretation": "UTC is verified for this requested 2025-04-28 through 2026-10-29 interval from embedded DWD station parameter metadata.",
        "time_metadata": {"wind_member": wind_meta_member, "wind_parameter_rows_covering_interval": wind_meta, "gust_member": gust_meta_member, "gust_parameter_rows_covering_interval": gust_meta},
        "station_caveat": "A separate DWD station/product. Hourly aggregation and sensor equivalence to the IEM EDDF METAR stream are not established. Never silently substitute these values for METAR observations.",
        "sources": source_details,
    }
    return q

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--pause-seconds",type=float,default=2.0)
    ap.add_argument("--force",action="store_true")
    ap.add_argument("--skip-fetch",action="store_true")
    ap.add_argument("--dwd-dir",type=Path,default=ROOT / "raw" / "dwd",help="DWD ZIP cache directory (defaults to this package's raw/dwd)")
    args=ap.parse_args()
    if not args.skip_fetch: fetch_all(max(2.0,args.pause_seconds),args.force)
    rows=normalize()
    quality=summarize(rows)
    dwd=dwd_export(args.dwd_dir,rows)
    quality["dwd_backup"] = dwd
    manifest_path = ROOT / "manifest.json"
    if manifest_path.exists() and dwd:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["supplemental_sources"] = dwd.get("sources", [])
        write_json(manifest_path, manifest)
    quality_path = ROOT / "quality.json"
    write_json(quality_path, quality)
    manifest_path = ROOT / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["request_summary"] = {"requests": len(manifest.get("requests", [])), "rows": sum(item.get("rows", 0) for item in manifest.get("requests", [])), "raw_bytes": sum(item.get("bytes", 0) for item in manifest.get("requests", []))}
        outputs = [ROOT / "eddf_metar_observations.csv", quality_path]
        if dwd: outputs.append(ROOT / dwd["output"])
        manifest["outputs"] = [{"path": output.name, "bytes": output.stat().st_size, "sha256": sha256(output.read_bytes())} for output in outputs]
        write_json(manifest_path, manifest)
    print(json.dumps({"rows":quality["coverage"]["rows"],"first":quality["coverage"]["first_observation_utc"],"last":quality["coverage"]["last_observation_utc"],"report_types":{"routine":quality["coverage"]["routine_rows"],"special":quality["coverage"]["special_rows"]},"wind_quality":quality["wind_quality"],"dwd_rows":dwd["rows"] if dwd else 0,"dwd_missing":dwd["missing_counts"] if dwd else None,"dwd_missing_hours":dwd["missing_hour_slots_between_first_and_last"] if dwd else None},indent=2))

if __name__=="__main__": main()
