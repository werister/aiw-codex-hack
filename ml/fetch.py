"""Download public EDDF weather archives into data/, with a reusable raw cache."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
IEM = "https://mesonet.agron.iastate.edu/cgi-bin/request/"
DWD = "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/"
VARIABLES = ["wind_speed_10m", "wind_direction_10m", "wind_gusts_10m",
             "pressure_msl", "temperature_2m", "wind_speed_80m", "wind_direction_80m"]
SOURCES = ["metar", "taf", "previous", "historical", "dwd", "live"]
TERMS = {
    "IEM": "Public domain; attribution appreciated. https://mesonet.agron.iastate.edu/disclaimer.php",
    "Open-Meteo": "CC BY 4.0; https://open-meteo.com/en/licence and https://open-meteo.com/en/terms",
    "DWD": "CDC terms, May 2024: CC BY 4.0. https://opendata.dwd.de/climate_environment/CDC/Terms_of_use.txt ; https://www.dwd.de/copyright . Older descriptions refer to GeoNutzV.",
    "NOAA": "US government weather data; https://www.weather.gov/disclaimer ; https://aviationweather.gov/data/api/",
}


def utcnow():
    return datetime.now(timezone.utc)


class Downloads:
    def __init__(self, refresh=False):
        RAW.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "EDDF-weather-research/1.0 (public-data-download)"
        self.refresh = refresh
        self.last_request = 0.0
        self.used = []

    def get(self, url, params=None, suffix=".txt", max_age=None, cache_tag=""):
        request = requests.Request("GET", url, params=params).prepare()
        key = hashlib.sha256((request.url + cache_tag).encode()).hexdigest()[:24]
        path = RAW / (key + suffix)
        meta_path = RAW / (key + ".meta.json")
        if path.exists() and meta_path.exists() and not self.refresh:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            age = (utcnow() - datetime.fromisoformat(meta["retrieved_at"])).total_seconds()
            if max_age is None or age < max_age:
                self.used.append(meta)
                return path
        for attempt in range(4):
            time.sleep(max(0, 1.2 - (time.monotonic() - self.last_request)))
            dates = (params or {}).get("start_date", "")
            print(f"GET {url} {dates}", flush=True)
            try:
                self.last_request = time.monotonic()
                with self.session.get(url, params=params, stream=True, timeout=(20, 180)) as response:
                    if response.status_code in (429, 500, 502, 503, 504):
                        if attempt < 3:
                            time.sleep(min(30, 5 * (attempt + 1)))
                            continue
                    response.raise_for_status()
                    temporary = path.with_suffix(path.suffix + ".part")
                    with temporary.open("wb") as output:
                        for chunk in response.iter_content(64 * 1024):
                            output.write(chunk)
                    temporary.replace(path)
                    meta = {"url": response.url, "retrieved_at": utcnow().isoformat(),
                            "bytes": path.stat().st_size, "cache_file": path.relative_to(DATA).as_posix()}
                    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
                    self.used.append(meta)
                    return path
            except requests.RequestException:
                if attempt == 3:
                    raise
                time.sleep(min(30, 5 * (attempt + 1)))
        raise RuntimeError(f"Download failed: {request.url}")


def intervals(start, stop, monthly=False):
    """Half-open calendar chunks, so the last cached chunk grows with the date."""
    while start < stop:
        if monthly:
            end = date(start.year + (start.month == 12), start.month % 12 + 1, 1)
        else:
            end = date(start.year + 1, 1, 1)
        yield start, min(end, stop)
        start = min(end, stop)


def iem_params(start, stop):
    return {"station": "EDDF", "year1": start.year, "month1": start.month,
            "day1": start.day, "year2": stop.year, "month2": stop.month,
            "day2": stop.day, "tz": "Etc/UTC"}


def save(frame, name, provider, downloads, time_column, notes=""):
    frame = frame.reset_index(drop=True)
    path = DATA / (name + ".parquet")
    frame.to_parquet(path, index=False, compression="zstd")
    values = frame[time_column].dropna()
    stats = {"file": path.name, "provider": provider, "rows": len(frame),
             "bytes": path.stat().st_size, "time_column": time_column,
             "start": str(values.min()) if len(values) else None,
             "end": str(values.max()) if len(values) else None,
             "columns": {c: str(frame[c].dtype) for c in frame.columns},
             "downloads": list(downloads.used), "notes": notes}
    manifest_path = DATA / "inventory.json"
    inventory = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    inventory[name] = stats
    manifest_path.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    print(f"SAVED {path.name}: {len(frame):,} rows, {stats['bytes']:,} bytes", flush=True)


def fetch_metar(dl, since, stop):
    frames = []
    existing = DATA / "eddf_metar.parquet"
    if existing.exists():
        frames.append(pd.read_parquet(existing))
    for start, end in intervals(since, stop):
        params = iem_params(start, end) | {"data": ["drct", "sknt", "gust", "metar"],
            "format": "onlycomma", "latlon": "no", "missing": "M", "report_type": [3, 4]}
        path = dl.get(IEM + "asos.py", params, ".csv", max_age=3600 if end > utcnow().date() else None)
        frame = pd.read_csv(path, na_values=["M"], dtype={"station": "string", "metar": "string"})
        frame["valid"] = pd.to_datetime(frame["valid"], utc=True)
        for col in ["drct", "sknt", "gust"]:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
        frames.append(frame)
    frame = pd.concat(frames, ignore_index=True).drop_duplicates(["valid", "metar"]).sort_values("valid")
    # A backfill must retain existing reports and their download provenance.
    inventory_path = DATA / "inventory.json"
    if existing.exists() and inventory_path.exists():
        previous = json.loads(inventory_path.read_text(encoding="utf-8")).get("eddf_metar", {})
        downloads = previous.get("downloads", []) + dl.used
        dl.used = list({item["url"]: item for item in downloads}.values())
    save(frame, "eddf_metar", "IEM", dl, "valid",
         "Types 3 and 4 retain routine and additional METARs, including half-hour reports. Missing direction includes VRB; missing gust means no gust reported, not zero.")


def fetch_taf(dl, since, stop):
    frames = []
    for start, end in intervals(since, stop):
        path = dl.get(IEM + "taf.py", iem_params(start, end) | {"fmt": "csv"}, ".csv",
                      max_age=3600 if end > utcnow().date() else None)
        frame = pd.read_csv(path)
        for col in ["valid", "fx_valid", "fx_valid_end"]:
            frame[col] = pd.to_datetime(frame[col], utc=True)
        frames.append(frame)
    frame = pd.concat(frames, ignore_index=True).drop_duplicates().sort_values("valid")
    note = "TAF issuance and forecast valid times are separate."
    if frame.empty:
        note = "IEM returned no EDDF TAF records for the requested archive. Empty parquet preserves the returned schema; it is not training data. Live NOAA TAF is saved separately."
    save(frame, "eddf_taf", "IEM", dl, "valid", note)


def fetch_openmeteo(dl, since, stop, previous=False):
    kind = "previous_runs" if previous else "historical_forecast"
    host = "previous-runs" if previous else "historical-forecast"
    variables = VARIABLES + ([f"{v}_previous_day{day}" for day in (1, 2, 3) for v in VARIABLES] if previous else [])
    # Offset fields are not archived before 2024; day 0 is the stitched forecast.
    start_date = max(since, date(2024, 1, 1)) if previous else since
    frames = []
    for start, end in intervals(start_date, stop, monthly=True):
        params = {"latitude": 50.033, "longitude": 8.570, "hourly": ",".join(variables),
                  "wind_speed_unit": "kn", "timezone": "UTC", "models": "best_match",
                  "start_date": str(start), "end_date": str(end - timedelta(days=1))}
        path = dl.get(f"https://{host}-api.open-meteo.com/v1/forecast", params, ".json",
                      max_age=3600 if end > utcnow().date() else None)
        payload = json.loads(path.read_text(encoding="utf-8"))
        if "hourly" not in payload:
            raise ValueError(f"Missing hourly data: {payload}")
        frame = pd.DataFrame(payload["hourly"])
        frame["time"] = pd.to_datetime(frame["time"], utc=True)
        frame[variables] = frame[variables].astype("float64")
        frames.append(frame)
    if not frames:
        raise ValueError("No dates in requested Open-Meteo archive range")
    frame = pd.concat(frames, ignore_index=True).drop_duplicates("time").sort_values("time")
    notes = "Day 0 is a stitched series of short forecast leads, not a fixed archived issuance."
    if previous:
        notes += " Offsets denote 24/48/72 hours before valid time, not explicit run initialization timestamps. Evaluation adds a six-hour publication lag. Early archive offsets can be null; inspect non-null coverage before backtesting."
    save(frame, "openmeteo_" + kind, "Open-Meteo", dl, "time", notes)


def fetch_dwd(dl, since, stop):
    for frequency, folders, name in [("hourly", ["historical", "recent"], "hourly"),
                                      ("10_minutes", ["recent"], "10min")]:
        dl.used = []
        frames = []
        for folder in folders:
            url = f"{DWD}{frequency}/wind/{folder}/"
            listing = dl.get(url, max_age=21600).read_text(encoding="utf-8")
            names = sorted(set(re.findall(r'href="([^"/]*01420[^"/]*\.zip)"', listing)))
            if not names:
                raise ValueError(f"Station 01420 missing from {url}")
            for filename in names:
                path = dl.get(urljoin(url, filename), suffix=".zip",
                              max_age=21600 if folder == "recent" else None)
                with zipfile.ZipFile(path) as archive:
                    member = next(n for n in archive.namelist() if n.startswith("produkt"))
                    with archive.open(member) as stream:
                        for chunk in pd.read_csv(stream, sep=";", chunksize=50000, na_values=[-999, -999.0]):
                            chunk.columns = chunk.columns.str.strip()
                            fmt = "%Y%m%d%H" if name == "hourly" else "%Y%m%d%H%M"
                            chunk["time"] = pd.to_datetime(chunk["MESS_DATUM"].astype(str), format=fmt, utc=True)
                            chunk = chunk[(chunk.time >= pd.Timestamp(since, tz="UTC")) & (chunk.time < pd.Timestamp(stop, tz="UTC"))].copy()
                            if chunk.empty:
                                continue
                            speed, direction = ("F", "D") if name == "hourly" else ("FF_10", "DD_10")
                            chunk["wind_speed_kn"] = chunk[speed] * (3600 / 1852)
                            chunk["wind_direction_deg"] = chunk[direction].where(chunk[direction].between(0, 360))
                            frames.append(chunk.drop(columns=["eor"], errors="ignore"))
        frame = pd.concat(frames, ignore_index=True).drop_duplicates("time", keep="last").sort_values("time")
        save(frame, "dwd_01420_wind_" + name, "DWD", dl, "time",
             "Original source columns and quality codes retained. F/FF_10 is m/s; D/DD_10 is degrees true. Recent wins on historical/recent overlap. Missing sentinel -999 is null. These products contain mean wind, not gusts.")


def fetch_live(dl, since, stop):
    snapshot = utcnow().replace(minute=0, second=0, microsecond=0)
    # Explicit hour makes a snapshot reproducible and prevents indefinitely stale live cache hits.
    params = {"latitude": 50.033, "longitude": 8.570, "hourly": ",".join(VARIABLES),
              "wind_speed_unit": "kn", "timezone": "UTC",
              "start_hour": snapshot.strftime("%Y-%m-%dT%H:%M"),
              "end_hour": (snapshot + timedelta(hours=71)).strftime("%Y-%m-%dT%H:%M")}
    path = dl.get("https://api.open-meteo.com/v1/forecast", params, ".json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    frame = pd.DataFrame(payload["hourly"])
    frame["time"] = pd.to_datetime(frame["time"], utc=True)
    retrieved = pd.Timestamp(dl.used[-1]["retrieved_at"])
    frame["retrieved_at"] = retrieved
    save(frame, "live_forecast", "Open-Meteo", dl, "time", "72 hourly values from the current UTC hour; retrieval timestamp retained.")
    for product in ["metar", "taf"]:
        dl.used = []
        params = {"ids": "EDDF", "format": "json"}
        path = dl.get(f"https://aviationweather.gov/api/data/{product}", params, ".json",
                      cache_tag=snapshot.isoformat())
        reports = json.loads(path.read_text(encoding="utf-8"))
        if not reports:
            raise ValueError(f"NOAA returned no live {product.upper()} for EDDF")
        if product == "metar":
            frame = pd.DataFrame([{ "station": r["icaoId"], "valid": pd.to_datetime(r["obsTime"], unit="s", utc=True),
                "drct": pd.to_numeric(r.get("wdir"), errors="coerce"), "sknt": r.get("wspd"),
                "gust": r.get("wgst"), "metar": r["rawOb"]} for r in reports])
        else:
            frame = pd.DataFrame([{ "station": r["icaoId"], "valid": pd.to_datetime(r["issueTime"], utc=True),
                "fx_valid": pd.to_datetime(r["validTimeFrom"], unit="s", utc=True),
                "fx_valid_end": pd.to_datetime(r["validTimeTo"], unit="s", utc=True), "raw": r["rawTAF"]} for r in reports])
        frame["retrieved_at"] = pd.Timestamp(dl.used[-1]["retrieved_at"])
        save(frame, "live_" + product, "NOAA", dl, "valid", "Latest report available at the snapshot hour; raw report retained.")


def write_readme(since, stop, failures):
    inventory = json.loads((DATA / "inventory.json").read_text(encoding="utf-8"))
    lines = ["# EDDF weather data", "", f"Most recent requested observation range: {since} through {stop - timedelta(days=1)}. METAR backfills append to existing reports; the inventory gives each file's full retained period. All timestamps are UTC. Data retrieval times and exact request URLs are recorded per file in [inventory.json](inventory.json).", "",
        "Rebuild METAR history with `python -m ml.fetch --since 2018-01-01 --sources metar`. Backfill only the older years with `python -m ml.fetch --since 2018-01-01 --until 2022-12-31 --sources metar`; existing reports win on duplicate observation timestamp and raw METAR. Other weather sources can be fetched with `python -m ml.fetch --since 2023-01-01`. Raw responses and retrieval metadata are cached in ignored `data/raw/`. Completed calendar chunks are reused; current chunks expire after one hour and DWD recent archives/listings after six hours. `--refresh` explicitly redownloads. Use `--sources metar previous` to select sources, or `--until YYYY-MM-DD` for an inclusive end date. Live snapshots reuse the current UTC hour. No credentials or accounts are used.", "",
        "## Inventory", "", "| File | Source | Rows | UTC period | Size MB | Retrieved UTC | Columns and units | Terms |", "|---|---|---:|---|---:|---|---|---|"]
    for info in inventory.values():
        dates = [d["retrieved_at"] for d in info["downloads"]]
        period = f"{info['start']} to {info['end']}" if info["rows"] else "No records returned"
        if info["provider"] == "Open-Meteo":
            units = "time UTC; 10/80 m speed and 10 m gust kn; direction degrees; MSL hPa; 2 m temperature Celsius"
        elif info["provider"] == "DWD":
            units = "station ID; UTC time; quality code; mean speed m/s and kn; direction degrees"
        elif "metar" in info["file"]:
            units = "station; valid UTC; drct degrees; sknt/gust kn; raw METAR"
        else:
            units = "station; issuance/validity UTC; raw TAF; IEM schema detailed below"
        terms = {"Open-Meteo": "CC BY 4.0", "DWD": "CDC CC BY 4.0", "IEM": "Public domain", "NOAA": "US government data"}[info["provider"]]
        lines.append(f"| [{info['file']}]({info['file']}) | {info['provider']} | {info['rows']:,} | {period} | {info['bytes']/1_000_000:.3f} | {min(dates)} to {max(dates)} | {units} | {terms} |")
    lines += ["", "## Exact URL patterns", "",
        "- IEM METAR: `https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=EDDF&data=drct&data=sknt&data=gust&data=metar&year1={Y1}&month1={M1}&day1={D1}&year2={Y2}&month2={M2}&day2={D2}&tz=Etc/UTC&format=onlycomma&latlon=no&missing=M&report_type=3&report_type=4`. Year chunks; end exclusive. Type 3 alone omits half-hour reports.",
        "- IEM TAF: `https://mesonet.agron.iastate.edu/cgi-bin/request/taf.py?station=EDDF&year1={Y1}&month1={M1}&day1={D1}&year2={Y2}&month2={M2}&day2={D2}&tz=Etc/UTC&fmt=csv`. Year chunks; limits issuance time.",
        "- Open-Meteo: `https://{previous-runs|historical-forecast}-api.open-meteo.com/v1/forecast?latitude=50.033&longitude=8.570&hourly={variables}&wind_speed_unit=kn&timezone=UTC&models=best_match&start_date={YYYY-MM-DD}&end_date={YYYY-MM-DD}`. Month chunks, both dates inclusive. Previous runs start 2024-01-01; historical forecast starts at the requested date. Variables listed below; previous runs request each unsuffixed, `_previous_day1`, `_previous_day2`, and `_previous_day3`.",
        f"- DWD hourly historical directory: `{DWD}hourly/wind/historical/`, station file `stundenwerte_FF_01420_{{start}}_{{end}}_hist.zip`.",
        f"- DWD hourly recent: `{DWD}hourly/wind/recent/stundenwerte_FF_01420_akt.zip`.",
        f"- DWD 10-minute recent: `{DWD}10_minutes/wind/recent/10minutenwerte_wind_01420_akt.zip`.",
        "- Live forecast: `https://api.open-meteo.com/v1/forecast?latitude=50.033&longitude=8.570&hourly={variables}&wind_speed_unit=kn&timezone=UTC&start_hour={UTC-hour}&end_hour={UTC-hour+71h}`.",
        "- Live observations/TAF: `https://aviationweather.gov/api/data/{metar|taf}?ids=EDDF&format=json`. Retrieved in a local hourly cache namespace, without limiting observations to the start of that hour.", "",
        "## Columns and units", "",
        "- METAR: `station` ICAO, `valid` observation timestamp, `drct` wind from degrees true, `sknt` mean wind knots, `gust` reported gust knots, `metar` original text. Missing direction can mean variable wind. Missing gust is unreported, not zero.",
        "- IEM TAF: `station`, `valid` issuance UTC, `fx_valid`/`fx_valid_end` forecast interval UTC, `raw` text, `is_tempo` and `is_amendment` flags, `sknt`/`gust` knots, `drct` degrees true, `visibility` statute miles, `presentwx` weather codes, `skyc` cloud codes, `skyl` cloud heights feet, `ws_level` feet, `ws_drct` degrees, `ws_sknt` knots, `product_id` identifier, `ftype` forecast type. Empty EDDF response is retained honestly.",
        "- Open-Meteo: `time` forecast valid UTC; `wind_speed_10m`, `wind_gusts_10m`, `wind_speed_80m` in knots; `wind_direction_10m`, `wind_direction_80m` in degrees true; `pressure_msl` hPa; `temperature_2m` degrees Celsius. Suffixes keep these units. Day 0 uses no suffix. Latitude 50.033, longitude 8.570; the API selects the surrounding land grid cell.",
        "- DWD hourly: `STATIONS_ID` station 1420, `MESS_DATUM` original UTC YYYYMMDDHH, `QN_3` quality flag, `F` m/s, `D` degrees true, plus parsed `time`, converted `wind_speed_kn` knots and `wind_direction_deg` degrees true. Ten-minute uses `MESS_DATUM` YYYYMMDDHHMM, `QN`, `FF_10` m/s and `DD_10` degrees. Sentinel -999 becomes null; direction codes outside 0 to 360 become null in the normalized field.",
        "- Live files also include `retrieved_at` UTC. Live METAR uses the METAR schema. Live TAF retains station, issuance, validity start/end and full raw text.", "", "## Coverage and sanity", ""]
    if "eddf_metar" in inventory:
        frame = pd.read_parquet(DATA / "eddf_metar.parquet")
        cutoff = min(pd.Timestamp(stop, tz="UTC"), pd.Timestamp(utcnow()).floor("h"))
        expected = pd.date_range(pd.Timestamp(since, tz="UTC"), cutoff, freq="h", inclusive="left")
        observed = pd.DatetimeIndex(frame.valid.dt.floor("h").unique())
        missing = expected.difference(observed)
        directional = frame.drct.notna() & frame.sknt.gt(0)
        angles = frame.loc[directional, "drct"]
        west = (angles > 180) & (angles < 360)
        east = (angles > 0) & (angles < 180)
        lines += [f"METAR has {len(frame):,} reports across {len(observed):,} UTC hours. Missing complete hours in the requested period: {len(missing):,}/{len(expected):,}. Current incomplete hour is excluded. First missing hours: {', '.join(str(t) for t in missing[:12]) or 'none'}.", "",
                  f"Among {len(angles):,} reports with known direction and nonzero speed, wind from a westerly component, 180 < direction < 360 degrees: {west.mean():.2%}; easterly component, 0 < direction < 180: {east.mean():.2%}. Exactly north/south directions are neither. Missing/variable directions: {frame.drct.isna().sum():,}. Max reported gust: {frame.gust.max():g} knots; max mean wind: {frame.sknt.max():g} knots. Gusts are only populated when reported.", ""]
    for name, info in inventory.items():
        lines += [f"- `{info['file']}`: {info['notes']}"]
        if name.startswith("openmeteo_"):
            frame = pd.read_parquet(DATA / info["file"])
            for col in frame.columns:
                if col == "time":
                    continue
                valid = frame.loc[frame[col].notna(), "time"]
                lines.append(f"  - `{col}`: {len(valid):,} non-null hours; {valid.min() if len(valid) else 'none'} through {valid.max() if len(valid) else 'none'}; maximum {frame[col].max():g}.")
    lines += ["", "Historical forecast day 0 stitches recent forecast leads and must not be used as an archived 24/48-hour forecast. Previous-day fields are lead offsets relative to valid time; preserve them separately and check availability at the evaluation issue time. Raw retrieval time is not a forecast initialization time.", "",
              "## Licences and attribution", ""]
    lines += [f"- {provider}: {terms}" for provider, terms in TERMS.items()]
    truth = DATA / "ground_truth"
    if (truth / "dfld_hourly.csv").exists():
        directions = pd.read_csv(truth / "dfld_hourly.csv", dtype={"od": str})
        lines += ["", "## Recorded operational history", "",
                  f"[DFLD recorded history](ground_truth/README.md) has {len(directions):,} stable OD hours, from {directions.time.min()} through {directions.time.max()}. Rebuild with `python -m ml.dfld --since 2018-01-01 --until 2026-10-29`. Labels describe whole hours and are available only after hour end; the original 2024+ rows are retained.", ""]
        if (truth / "dfld_r18_hourly.csv").exists():
            runway = pd.read_csv(truth / "dfld_r18_hourly.csv")
            lines += [f"Runway-18 display history has {len(runway):,} known hours from {runway.time.min()} through {runway.time.max()}, with gaps. `r18_in_use` describes the published operational display, not weather closure. Transparent and unknown bins are excluded, not classified as non-use. All requested monthly pages were inspected, including later months without known status.", ""]
    lines += ["", "## Needs an account", "", "None of the requested endpoints needs an account or key. No sign-up was attempted.", "", "## Retrieval failures", ""]
    lines += failures or ["None. Source coverage gaps are recorded above."]
    (DATA / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", type=date.fromisoformat, default=date(2023, 1, 1))
    parser.add_argument("--until", type=date.fromisoformat, default=utcnow().date())
    parser.add_argument("--sources", nargs="+", choices=SOURCES, default=SOURCES)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    if args.since > args.until:
        parser.error("--since must be on or before --until")
    DATA.mkdir(exist_ok=True)
    stop = args.until + timedelta(days=1)
    functions = {"metar": fetch_metar, "taf": fetch_taf, "previous": lambda d, s, e: fetch_openmeteo(d, s, e, True),
                 "historical": fetch_openmeteo, "dwd": fetch_dwd, "live": fetch_live}
    failures = []
    for source in args.sources:
        dl = Downloads(refresh=args.refresh)
        try:
            functions[source](dl, args.since, stop)
        except (requests.RequestException, ValueError, KeyError, pd.errors.ParserError) as error:
            message = f"{source}: {error}"
            print(f"FAILED {message}", flush=True)
            failures.append(message)
    if (DATA / "inventory.json").exists():
        write_readme(args.since, stop, failures)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
