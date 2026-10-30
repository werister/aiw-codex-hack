#!/usr/bin/env python3
"""Audit raw IEM METAR wind groups against the shipped normalized CSV; stdlib only."""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

WIND = re.compile(r"(?<![A-Z0-9])(?P<dir>VRB|\d{3})(?P<speed>\d{2,3})(?:G(?P<gust_p>P)?(?P<gust>\d{2,3}))?(?P<unit>KT|MPS|KMH)(?![A-Z0-9])")
VARIATION = re.compile(r"(?<![A-Z0-9])(?P<from>\d{3})V(?P<to>\d{3})(?![A-Z0-9])")
OBSERVATION_TIME = re.compile(r"\d{6}Z\Z")
TREND_MARKERS = {"BECMG", "TEMPO", "NOSIG", "RMK", "INTER", "PROB30", "PROB40"}
def sha256(data: bytes) -> str:
    import hashlib
    return hashlib.sha256(data).hexdigest()


def numeric(value):
    if value in (None, "", "M", "T", "-999", "-999.0"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def iso_utc(value: str) -> str:
    return datetime.strptime(value, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_wind(raw: str) -> dict:
    tokens = raw.split()
    # Respect the coded report header. Never hunt later groups for a replacement:
    # a later wind can be a forecast trend, not the observation.
    cursor = 0
    if cursor < len(tokens) and tokens[cursor] in {"METAR", "SPECI"}:
        cursor += 1
    if cursor < len(tokens) and tokens[cursor] == "COR":
        cursor += 1
    if cursor < len(tokens) and tokens[cursor] == "EDDF":
        cursor += 1
    else:
        return {"state": "BAD_HEADER", "slash_tokens": [], "variation": None,
                "extra_wind_tokens": [], "any_variation": None}
    if cursor >= len(tokens) or not OBSERVATION_TIME.fullmatch(tokens[cursor]):
        return {"state": "BAD_HEADER", "slash_tokens": [], "variation": None,
                "extra_wind_tokens": [], "any_variation": None}
    cursor += 1
    while cursor < len(tokens) and tokens[cursor] in {"AUTO", "COR", "CCA", "CCB", "CCC"}:
        cursor += 1
    if cursor >= len(tokens):
        return {"state": "NO_MAIN_GROUP", "slash_tokens": [], "variation": None,
                "extra_wind_tokens": [], "any_variation": None}
    token = tokens[cursor]
    match = WIND.fullmatch(token)
    if not match:
        state = "SLASH_MISSING" if "/" in token and token.endswith(("KT", "MPS", "KMH")) else "NO_MAIN_GROUP"
        return {"state": state, "slash_tokens": [token] if "/" in token else [], "variation": None,
                "extra_wind_tokens": [], "any_variation": None}
    wind_index = cursor
    # The optional dddVddd range belongs to the observation only when it follows
    # the primary wind group; any later trend section remains separate.
    variability = VARIATION.fullmatch(tokens[wind_index + 1]) if wind_index + 1 < len(tokens) else None
    any_variation = next((VARIATION.fullmatch(t) for t in tokens if VARIATION.fullmatch(t)), None)
    trend_index = next((i for i in range(wind_index + 1, len(tokens)) if tokens[i] in TREND_MARKERS), len(tokens))
    later_wind_tokens = [t for t in tokens[trend_index:] if WIND.fullmatch(t)]
    direction = match.group("dir")
    speed = int(match.group("speed"))
    gust = int(match.group("gust")) if match.group("gust") else None
    gust_over_99 = match.group("gust_p") == "P"
    if direction == "VRB":
        direction_class = "VARIABLE_VRB"
        direction_deg = None
    elif direction == "000" and speed == 0:
        direction_class = "CALM"
        direction_deg = None
    elif variability:
        direction_class = "VARIABLE_RANGE"
        direction_deg = int(direction)
    else:
        direction_class = "DIRECTIONAL"
        direction_deg = int(direction)
    return {"state": "VALID", "token": token, "direction_token": direction,
            "direction_deg": direction_deg, "direction_class": direction_class,
            "speed": speed, "gust": gust, "gust_over_99": gust_over_99,
            "unit": match.group("unit"), "variation": variability,
            "any_variation": any_variation, "extra_wind_tokens": later_wind_tokens,
            "slash_tokens": []}


def parser_self_check():
    slash_then_trend = parse_wind("EDDF 301050Z AUTO /////KT 9999 BECMG 22010KT")
    if slash_then_trend["state"] != "SLASH_MISSING":
        raise AssertionError("trend wind was incorrectly accepted as the missing primary wind")
    two_winds = parse_wind("EDDF 220050Z AUTO 22027G37KT 9999 BECMG 23020G35KT")
    if (two_winds["state"] != "VALID" or two_winds["direction_token"] != "220"
            or two_winds["extra_wind_tokens"] != ["23020G35KT"]):
        raise AssertionError("trend wind changed the primary observed wind")


def clockwise_contains(start: int, end: int, direction: int) -> bool:
    width = (end - start) % 360
    return (direction - start) % 360 <= width


def max_tailwind_in_range(speed: float, start: int, end: int) -> float:
    if clockwise_contains(start, end, 0):
        return speed
    return max(speed * math.cos(math.radians(start)), speed * math.cos(math.radians(end)))


def load_normalized(path: Path):
    by_key = {}
    with path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            key = (row["observation_time_utc"], int(row["report_type"]))
            if key in by_key:
                raise ValueError(f"duplicate normalized key: {key}")
            by_key[key] = row
    return by_key


def iem_raw_audit(source: Path, rules: dict) -> dict:
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    normalized = load_normalized(source / "eddf_metar_observations.csv")
    stats = Counter()
    speeds = []
    encoded_gusts = []
    no_gust_speeds = []
    vrb_speeds = []
    vrb_gusts = []
    direction_ranges = []
    examples = {"vrb": [], "range_threshold": []}
    mismatches = Counter()
    normalized_seen = set()
    type_counts = Counter()
    direct_samples = []
    for request in manifest.get("requests", []):
        raw_path = source / "raw" / "iem" / request["file"]
        body = raw_path.read_bytes()
        digest = sha256(body)
        if digest != request["sha256"] or len(body) != request["bytes"]:
            raise ValueError(f"raw chunk integrity mismatch: {request['file']}")
        chunk_rows = 0
        report_type = int(re.search(r"type([34])", request["file"]).group(1))
        with raw_path.open(encoding="utf-8-sig", newline="") as stream:
            for raw_row in csv.DictReader(stream):
                chunk_rows += 1
                type_counts[str(report_type)] += 1
                stamp = iso_utc(raw_row["valid"])
                key = (stamp, report_type)
                if key not in normalized:
                    mismatches["normalized_key_missing"] += 1
                    continue
                normalized_seen.add(key)
                row = normalized[key]
                raw_metar = (raw_row.get("metar") or "").strip()
                if raw_metar != row.get("raw_metar", ""):
                    mismatches["raw_metar_differs"] += 1
                parsed = parse_wind(raw_metar)
                stats["reports"] += 1
                stats[f"report_type_{report_type}"] += 1
                if "AUTO" in raw_metar.split():
                    stats["auto_reports"] += 1
                if parsed["state"] == "VALID":
                    stats["main_wind_valid"] += 1
                    if parsed["extra_wind_tokens"]:
                        stats["later_trend_wind_groups_not_primary"] += len(parsed["extra_wind_tokens"])
                    speeds.append(parsed["speed"])
                    if parsed["unit"] != "KT":
                        stats[f"unit_{parsed['unit']}"] += 1
                    if parsed["gust"] is None:
                        stats["gust_group_absent"] += 1
                        no_gust_speeds.append(parsed["speed"])
                    else:
                        stats["gust_group_present"] += 1
                        encoded_gusts.append(parsed["gust"])
                    stats[f"direction_{parsed['direction_class']}"] += 1
                    if parsed["direction_class"] == "VARIABLE_VRB":
                        vrb_speeds.append(parsed["speed"])
                        if parsed["gust"] is not None:
                            vrb_gusts.append(parsed["gust"])
                        if len(examples["vrb"]) < 3:
                            examples["vrb"].append({"time_utc": stamp, "report": raw_metar,
                                                    "mean_speed_kt": parsed["speed"], "gust_kt": parsed["gust"]})
                    if parsed["variation"]:
                        stats["direction_range_present"] += 1
                        direction_ranges.append((stamp, raw_metar, parsed, int(parsed["variation"].group("from")), int(parsed["variation"].group("to"))))

                    expected_dir_status = parsed["direction_class"]
                    if row.get("wind_direction_status") != expected_dir_status:
                        mismatches["direction_status"] += 1
                    if numeric(row.get("wind_speed_kt")) != parsed["speed"]:
                        mismatches["speed_vs_raw_group"] += 1
                    if numeric(row.get("wind_gust_kt")) != parsed["gust"]:
                        mismatches["gust_vs_raw_group"] += 1
                    if parsed["gust"] is None and row.get("wind_gust_status") != "NOT_ENCODED":
                        mismatches["absent_gust_status"] += 1
                    if parsed["gust"] is not None and row.get("wind_gust_status") != "REPORTED":
                        mismatches["reported_gust_status"] += 1
                    if parsed["direction_class"] in ("VARIABLE_VRB", "CALM") and numeric(row.get("wind_direction_deg")) is not None:
                        mismatches["unknown_direction_has_value"] += 1
                    if parsed["direction_class"] in ("DIRECTIONAL", "VARIABLE_RANGE") and numeric(row.get("wind_direction_deg")) is None:
                        mismatches["coded_direction_lost"] += 1
                    # The old normalizer searches the entire report for dddVddd;
                    # compare that behavior with the group immediately after the
                    # primary wind token to detect trend-group contamination.
                    normalized_regex_saw_range = bool(parsed["any_variation"])
                    primary_group_has_range = bool(parsed["variation"])
                    if normalized_regex_saw_range != primary_group_has_range:
                        mismatches["variability_range_outside_primary_group"] += 1
                    if row.get("raw_gust") not in ("", "M", "T", None) and parsed["gust"] is None:
                        mismatches["iem_gust_value_without_raw_G"] += 1
                    if parsed["gust"] is not None and numeric(row.get("raw_gust")) != parsed["gust"]:
                        mismatches["iem_gust_vs_raw_G"] += 1
                else:
                    stats[f"main_wind_{parsed['state']}"] += 1
                    if len(direct_samples) < 5:
                        direct_samples.append({"time_utc": stamp, "state": parsed["state"], "report": raw_metar})

                if parsed["slash_tokens"]:
                    stats["slash_wind_token"] += 1

                if parsed["state"] == "VALID":
                    actual_gust = parsed["gust"]
                    if actual_gust is None:
                        # DWD's national rule only permits a G group at a reported
                        # peak >= mean + 10 kt; no G therefore bounds the max below it.
                        possible_peak_upper = parsed["speed"] + 10
                    else:
                        possible_peak_upper = actual_gust
                    if possible_peak_upper <= rules["crosswind_limit_kt_incl_gusts"]:
                        stats["decoded_crosswind_component_cannot_exceed_limit_by_wind_speed_bound"] += 1
                    else:
                        stats["crosswind_rule_not_proven_by_speed_bound"] += 1

    if len(normalized_seen) != len(normalized):
        mismatches["normalized_rows_without_raw_key"] += len(normalized) - len(normalized_seen)
    if len(manifest.get("requests", [])) != 46:
        raise ValueError(f"expected 46 raw chunks; found {len(manifest.get('requests', []))}")
    stats["all_raw_chunk_hashes_verified"] = len(manifest["requests"])
    stats["normalized_rows"] = len(normalized)
    stats["wind_speed_min_kt"] = min(speeds) if speeds else None
    stats["wind_speed_max_kt"] = max(speeds) if speeds else None
    stats["gust_max_reported_kt"] = max(encoded_gusts) if encoded_gusts else None
    stats["no_G_peak_bound_max_strictly_below_kt"] = max(no_gust_speeds) + 10 if no_gust_speeds else None
    stats["no_G_mean_speed_max_kt"] = max(no_gust_speeds) if no_gust_speeds else None
    stats["vrb_mean_speed_max_kt"] = max(vrb_speeds) if vrb_speeds else None
    stats["vrb_reported_gust_max_kt"] = max(vrb_gusts) if vrb_gusts else None

    tailwind_limit = rules["departure_tailwind_limit_kt"]
    prevailing_direction_range_disagreements = []
    variable_ge_15 = 0
    variable_potential_r18_closures = 0
    variable_mean_usable_but_range_reaches_limit = 0
    for stamp, report, parsed, direction_from, direction_to in direction_ranges:
        speed = parsed["speed"]
        mean_dir = int(parsed["direction_token"])
        mean_tailwind = speed * math.cos(math.radians(mean_dir))
        worst_range_tailwind = max_tailwind_in_range(speed, direction_from, direction_to)
        if speed >= tailwind_limit:
            variable_ge_15 += 1
        if worst_range_tailwind >= tailwind_limit:
            variable_potential_r18_closures += 1
        if mean_tailwind < tailwind_limit <= worst_range_tailwind:
            variable_mean_usable_but_range_reaches_limit += 1
            if len(examples["range_threshold"]) < 5:
                examples["range_threshold"].append({
                    "time_utc": stamp, "report": report, "mean_speed_kt": speed,
                    "prevailing_direction_deg": mean_dir,
                    "variable_range_deg": [direction_from, direction_to],
                    "mean_direction_tailwind_kt": round(mean_tailwind, 3),
                    "max_component_within_range_kt": round(worst_range_tailwind, 3),
                })
        if not clockwise_contains(direction_from, direction_to, mean_dir):
            prevailing_direction_range_disagreements.append(stamp)

    dwd = inspect_dwd(source)
    return {
        "dataset": {"period_utc": manifest.get("requested_period"), "raw_chunks": len(manifest.get("requests", [])),
                    "normalized_csv": "eddf_metar_observations.csv", "directly_reparsed_from_raw_metar_text": True},
        "raw_verification": {"counts": dict(sorted(stats.items())), "mismatches": dict(sorted(mismatches.items())),
                             "mismatch_total": sum(mismatches.values()), "report_type_counts": dict(sorted(type_counts.items())),
                             "sample_parse_failures": direct_samples},
        "direction_range_r18_review": {
            "rule_tailwind_threshold_kt": tailwind_limit,
            "variable_range_rows": len(direction_ranges),
            "variable_range_mean_speed_ge_15_rows": variable_ge_15,
            "rows_whose_direction_interval_has_possible_r18_tailwind_ge_15": variable_potential_r18_closures,
            "rows_mean_direction_says_below_15_but_interval_reaches_15": variable_mean_usable_but_range_reaches_limit,
            "rows_mean_direction_outside_encoded_clockwise_interval": len(prevailing_direction_range_disagreements),
            "example_rows": examples["range_threshold"],
            "caveat": "A direction range and a separate 10-minute mean speed do not establish that the directional extreme and the mean speed occurred simultaneously; these counts identify ambiguity, not a realized closure label.",
        },
        "vrb_review": {"rows": len(vrb_speeds), "mean_speed_max_kt": max(vrb_speeds) if vrb_speeds else None,
                       "tailwind_threshold_kt": tailwind_limit,
                       "all_vrb_mean_speeds_below_tailwind_threshold": bool(vrb_speeds and max(vrb_speeds) < tailwind_limit),
                       "rows_with_encoded_gust": len(vrb_gusts), "encoded_gust_max_kt": max(vrb_gusts) if vrb_gusts else None,
                       "example_rows": examples["vrb"],
                       "caveat": "Conditional rule-level reasoning under the DWD reporting rule and this dataset's complete valid main wind groups; it is not an operational runway clearance."},
        "dwd_review": dwd,
    }


def read_csv_from_zip(z: zipfile.ZipFile, suffix: str):
    member = next(name for name in z.namelist() if name.endswith(suffix))
    text = z.read(member).decode("latin-1")
    rows = []
    for row in csv.DictReader(text.splitlines(), delimiter=";"):
        rows.append({(k or "").strip(): (v or "").strip() for k, v in row.items()})
    return member, rows


def inspect_dwd(source: Path) -> dict:
    dwd_dir = source / "raw" / "dwd"
    wind_path = dwd_dir / "wind-01420-recent.zip"
    gust_path = dwd_dir / "gust-01420-recent.zip"
    if not wind_path.exists() or not gust_path.exists():
        return {"status": "DWD reference ZIPs absent"}
    with zipfile.ZipFile(wind_path) as zw, zipfile.ZipFile(gust_path) as zg:
        _, geo_rows = read_csv_from_zip(zw, "Metadaten_Geographie_01420.txt")
        _, wind_param = read_csv_from_zip(zw, "Metadaten_Parameter_ff_stunde_01420.txt")
        _, gust_param = read_csv_from_zip(zg, "Metadaten_Parameter_fx_stunde_01420.txt")
        _, wind_devices = read_csv_from_zip(zw, "Metadaten_Geraete_Windgeschwindigkeit_01420.txt")
        _, dir_devices = read_csv_from_zip(zw, "Metadaten_Geraete_Windrichtung_01420.txt")
        _, gust_devices = read_csv_from_zip(zg, "Metadaten_Geraete_Maxwind_01420.txt")
    period_start, period_end = "20250428", "20261029"

    def covering(rows, parameter_field="Parameter"):
        return [r for r in rows if r.get("Von_Datum", "") <= period_start and r.get("Bis_Datum", "99999999") >= period_end]

    geo_cover = covering(geo_rows, "")
    current_geo = geo_cover[-1] if geo_cover else {}
    def active_devices(rows):
        return [r for r in rows if r.get("Von_Datum", "") <= period_end and r.get("Bis_Datum", "99999999") >= period_start]

    wind_parameter_rows = [r for r in covering(wind_param) if r.get("Parameter") in {"F", "D"}]
    gust_parameter_rows = [r for r in covering(gust_param) if r.get("Parameter") == "FX_911"]
    dwd_time_rows = []
    for r in wind_parameter_rows + gust_parameter_rows:
        dwd_time_rows.append({"parameter": r.get("Parameter"), "from": r.get("Von_Datum"), "to": r.get("Bis_Datum"),
                              "time_text": r.get("Zusatz-Info"), "data_source": r.get("Datenquelle (Strukturversion=SV)"),
                              "description": r.get("Parameterbeschreibung")})
    lat, lon = numeric(current_geo.get("Geogr.Breite")), numeric(current_geo.get("Geogr.Laenge"))
    arp_lat, arp_lon = 50 + 1/60 + 59.90/3600, 8 + 34/60 + 13.64/3600
    distance = None
    if lat is not None and lon is not None:
        radius = 6371.0088
        p1, p2 = math.radians(arp_lat), math.radians(lat)
        dp, dl = math.radians(lat - arp_lat), math.radians(lon - arp_lon)
        a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
        distance = 2*radius*math.asin(math.sqrt(a))
    recent_note = "DWD's official dataset description says recent/ quality control is not complete."
    return {
        "station_id": "01420", "station_name": current_geo.get("Stationsname"),
        "geography_metadata_covering_2025_2026": current_geo,
        "wind_parameter_metadata_covering_interval": dwd_time_rows,
        "wind_speed_devices_over_interval": active_devices(wind_devices),
        "wind_direction_devices_over_interval": active_devices(dir_devices),
        "gust_devices_over_interval": active_devices(gust_devices),
        "airport_reference_point_from_Fraport": {"latitude": arp_lat, "longitude": arp_lon},
        "distance_station_to_airport_reference_point_km": round(distance, 3) if distance is not None else None,
        "product_caveats": ["F/D are a separate DWD CDC hourly-mean product; the official dataset description identifies hourly mean processing, not the airport METAR's 10-minute wind window.",
                            "FX_911 is described in the station metadata as the highest wind peak of the last hour; it is a coarser maximum window than METAR G, which uses a 10-minute (or shorter after a marked change) wind peak.",
                            recent_note,
                            "Station coordinates and sensor metadata do not prove that DWD 01420 is the designated airport METAR reference wind sensor; do not silently substitute or timestamp-align as if identical."],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path,
                        help="Read-only observations handoff folder containing manifest.json, raw/, and normalized CSVs")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("audit.json"))
    args = parser.parse_args()
    parser_self_check()
    repo = Path(__file__).resolve().parents[3]
    rules = json.loads((repo / "ml" / "rules.json").read_text(encoding="utf-8"))
    report = {"created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "rules_version": rules["version"],
              "r18_rule_limits": {"tailwind_ge_kt_closes": rules["departure_tailwind_limit_kt"],
                                  "crosswind_including_gust_gt_kt_closes": rules["crosswind_limit_kt_incl_gusts"]},
              "source_audit": iem_raw_audit(args.source.resolve(), rules)}
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    summary = report["source_audit"]["raw_verification"]
    print(json.dumps({"output": str(args.output), "rows": summary["counts"]["reports"],
                      "mismatch_total": summary["mismatch_total"],
                      "variable_range_r18": report["source_audit"]["direction_range_r18_review"],
                      "vrb": report["source_audit"]["vrb_review"],
                      "dwd_location_km_from_arp": report["source_audit"]["dwd_review"].get("distance_station_to_airport_reference_point_km")},
                     indent=2, ensure_ascii=False))
    if summary["mismatch_total"]:
        raise SystemExit("raw/normalized discrepancies found; inspect audit.json")


if __name__ == "__main__":
    main()
