"""Rebuild recorded EDDF direction and runway-18 display history from DFLD."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date, datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from ml.fetch import DATA, Downloads, intervals
from ml.rules import RULES, tailwind

BERLIN = ZoneInfo("Europe/Berlin")
OUTPUT = DATA / "ground_truth"
URL = "https://www.dfld.de/Mess/StatWetter.php"
HALF_COLUMNS = ["date_local", "hour_local", "minute_local", "od", "source"]


class DailyImages(HTMLParser):
    def __init__(self):
        super().__init__()
        self.lines = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag == "p":
            self.current = []
            self.lines.append(self.current)
        elif tag == "img" and self.current is not None:
            self.current.append(dict(attrs))

    def handle_endtag(self, tag):
        if tag == "p":
            self.current = None


def parse_month(html, source, start, stop):
    """Preserve the page's half-hour clock and separate unknown R18 symbols."""
    od, runway = [], []
    for row in re.findall(r"<tr\b[^>]*>.*?</tr>", html, re.I | re.S):
        match = re.search(r"(\d{2}\.\d{2}\.\d{4}):", row)
        if not match:
            continue
        day = datetime.strptime(match[1], "%d.%m.%Y").date()
        if not start <= day < stop:
            continue
        parser = DailyImages()
        parser.feed(row)
        for line in parser.lines:
            for image in line:
                title = re.fullmatch(r"(\d{2}):([03]0) - \d{2}:\d{2}: BR(07|25)", image.get("title", ""))
                if title:
                    od.append({"date_local": day.isoformat(), "hour_local": int(title[1]),
                               "minute_local": int(title[2]), "od": title[3], "source": source})
        if len(parser.lines) < 3:
            continue
        images = parser.lines[2]
        if len(images) != 48:
            raise ValueError(f"Expected 48 runway-18 bins on {day}, got {len(images)}")
        for index, image in enumerate(images):
            src = image.get("src", "").split("/")[-1]
            if src == "180.gif" and image.get("title", "").endswith("18 West in Betrieb"):
                value = True
            elif src == "000.gif":
                value = False
            elif src in ("Undef.gif", "Trans.gif"):
                value = None
            else:
                raise ValueError(f"Unknown runway-18 symbol on {day}: {image}")
            runway.append({"date_local": day.isoformat(), "hour_local": index // 2,
                           "minute_local": 30 * (index % 2), "r18_in_use": value, "source": source})
    return pd.DataFrame(od, columns=HALF_COLUMNS), pd.DataFrame(runway, columns=[
        "date_local", "hour_local", "minute_local", "r18_in_use", "source"])


def hourly(bins, value, change_reason):
    rows, excluded = [], []
    for (day, hour), group in bins.groupby(["date_local", "hour_local"], sort=True):
        local = datetime.fromisoformat(day).replace(hour=int(hour))
        reason = None
        if local.replace(tzinfo=BERLIN, fold=0).utcoffset() != local.replace(tzinfo=BERLIN, fold=1).utcoffset():
            reason = "DST ambiguous or nonexistent local hour"
        elif len(group) != 2 or set(group.minute_local) != {0, 30} or group[value].isna().any():
            reason = "missing half hour"
        elif group[value].nunique() != 1:
            reason = change_reason
        if reason:
            excluded.append({"date_local": day, "hour_local": hour, "reason": reason})
            continue
        stamp = local.replace(tzinfo=BERLIN).astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")
        rows.append({"time": stamp, value: group[value].iloc[0], "source": group.source.iloc[0]})
    return pd.DataFrame(rows, columns=["time", value, "source"]), pd.DataFrame(
        excluded, columns=["date_local", "hour_local", "reason"])


def retain_existing(path, frame, keys, *, dtype=None):
    """Append unseen keys while verifying that rebuilding never changes old labels."""
    if not path.exists():
        return frame
    old = pd.read_csv(path, dtype=dtype)
    overlap = old.merge(frame, on=keys, suffixes=("_old", "_new"))
    for column in frame.columns.difference(keys):
        if not overlap[f"{column}_old"].eq(overlap[f"{column}_new"]).all():
            raise ValueError(f"Rebuilt data disagrees with existing {path.name}: {column}")
    return pd.concat([old, frame], ignore_index=True).drop_duplicates(keys, keep="first").sort_values(keys)


def extract(start, stop, refresh=False):
    dl = Downloads(refresh=refresh)
    od_parts, runway_parts, manifest = [], [], []
    month_start = start.replace(day=1)
    for first, last in intervals(month_start, stop, monthly=True):
        path = dl.get(URL, {"R": 1, "D": first.strftime("01.%m.%Y")}, ".html")
        metadata = dl.used[-1]
        # Keep the canonical query order used by the original recorded labels.
        source = f"{URL}?R=1&D={first.strftime('01.%m.%Y')}"
        od, runway = parse_month(path.read_text(encoding="utf-8"), source, start, stop)
        if od.empty:
            raise ValueError(f"No recorded OD bins returned for {first:%Y-%m}")
        od_parts.append(od)
        runway_parts.append(runway)
        manifest.append({"url": source, "retrieved_at": metadata["retrieved_at"],
                         "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size,
                         "half_hour_records": len(od), "r18_half_hour_records": len(runway),
                         "r18_known_half_hours": int(runway.r18_in_use.notna().sum())})
        print(f"{first:%Y-%m}: {len(od)} OD bins, {len(runway)} runway-18 bins", flush=True)
    bins = pd.concat(od_parts, ignore_index=True)
    runway_bins = pd.concat(runway_parts, ignore_index=True)
    directions, excluded = hourly(bins, "od", "direction differs between half hours")
    runway, runway_excluded = hourly(runway_bins, "r18_in_use", "runway-18 status differs between half hours")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    files = [("dfld_hourly.csv", directions, ["time"], {"od": str}),
             ("dfld_half_hourly.csv.gz", bins, ["date_local", "hour_local", "minute_local"], {"od": str}),
             ("dfld_excluded_hours.csv", excluded, ["date_local", "hour_local"], None),
             ("dfld_r18_hourly.csv", runway, ["time"], None),
             ("dfld_r18_excluded_hours.csv", runway_excluded, ["date_local", "hour_local"], None)]
    # Validate every overlap before replacing any output.
    merged = [(name, retain_existing(OUTPUT / name, frame, keys, dtype=dtype))
              for name, frame, keys, dtype in files]
    for name, frame in merged:
        frame.to_csv(OUTPUT / name, index=False)
        print(f"SAVED {name}: {len(frame):,} rows", flush=True)
    manifest_path = OUTPUT / "dfld_manifest.json"
    previous = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else []
    entries = {row["url"]: row for row in previous}
    entries.update({row["url"]: row for row in manifest})
    manifest_path.write_text(json.dumps(sorted(entries.values(), key=lambda row: datetime.strptime(
        row["url"].split("D=")[1], "%d.%m.%Y")), indent=2) + "\n", encoding="utf-8")


def compare_metar():
    """Use the same hour-start observation alignment as the training labels."""
    runway = pd.read_csv(OUTPUT / "dfld_r18_hourly.csv")
    runway["time"] = pd.to_datetime(runway.time, utc=True)
    reports = pd.read_parquet(DATA / "eddf_metar.parquet")
    weather = reports.rename(columns={"valid": "time", "sknt": "wind_kt", "drct": "wind_dir_deg"})
    weather = weather.dropna(subset=["wind_kt"]).sort_values("time").drop_duplicates("time", keep="last")
    joined = pd.merge_asof(runway, weather[["time", "wind_kt", "wind_dir_deg"]],
                           on="time", tolerance=pd.Timedelta(hours=1))
    known = joined.wind_kt.notna() & (joined.wind_dir_deg.notna() | joined.wind_kt.eq(0))
    closed = pd.Series([tailwind(speed, direction, RULES["runway_heading_deg"]["18"])
                        >= RULES["departure_tailwind_limit_kt"]
                        for speed, direction in zip(joined.wind_kt, joined.wind_dir_deg)], index=joined.index)
    not_in_use = ~joined.r18_in_use
    result = {"alignment": "latest METAR at or before UTC hour start, maximum age 1 hour",
              "tailwind_threshold_kt": RULES["departure_tailwind_limit_kt"],
              "r18_known_status_hours": len(runway), "r18_not_in_use_hours": int(not_in_use.sum()),
              "matched_known_wind_hours": int(known.sum()),
              "not_in_use_with_known_wind": int((not_in_use & known).sum()),
              "tailwind_closure_hours_on_status_overlap": int((closed & known).sum()),
              "not_in_use_and_tailwind_closure_hours": int((not_in_use & closed & known).sum()),
              "metar_rows": len(reports), "metar_start": str(reports.valid.min()),
              "metar_end": str(reports.valid.max())}
    payload = json.dumps(result, indent=2) + "\n"
    (OUTPUT / "dfld_r18_tailwind_overlap.json").write_text(payload, encoding="utf-8")
    print(payload, end="")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", type=date.fromisoformat, default=date(2018, 1, 1))
    parser.add_argument("--until", type=date.fromisoformat,
                        default=datetime.now(tz=BERLIN).date() - timedelta(days=1))
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--permission-confirmed", action="store_true",
                        help="Confirm you have permission for this processing; see docs/DATA_SOURCES.md")
    parser.add_argument("--compare-metar", action="store_true",
                        help="Compare saved runway-18 display hours with METAR tailwind, without downloading")
    args = parser.parse_args()
    if args.compare_metar:
        compare_metar()
        return
    if not args.permission_confirmed:
        parser.error("DFLD processing requires permission; see https://www.dfld.de/DFLDimprint.php?L=G "
                     "and docs/DATA_SOURCES.md. Only pass --permission-confirmed when authorized.")
    if args.since > args.until or args.until >= datetime.now(tz=BERLIN).date():
        parser.error("Use a nonempty range of completed local days")
    extract(args.since, args.until + timedelta(days=1), args.refresh)


if __name__ == "__main__":
    main()
