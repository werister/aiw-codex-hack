#!/usr/bin/env python3
"""Rebuild DFLD hourly labels independently; compare two fresh HTML samples."""

import argparse
import csv
import gzip
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo

BERLIN = ZoneInfo("Europe/Berlin")
DATE = re.compile(r"\b(\d{2}\.\d{2}\.\d{4}):")
BIN = re.compile(r"^(\d{2}):(00|30) - \d{2}:\d{2}: BR(07|25)$")


class MonthlyPage(HTMLParser):
    def __init__(self):
        super().__init__()
        self.date = None
        self.records = []

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.date = None
        if tag == "img":
            match = BIN.fullmatch(dict(attrs).get("title", ""))
            if match:
                if self.date is None:
                    raise ValueError("OD image has no table-row date")
                hour, minute, od = match.groups()
                self.records.append((self.date, int(hour), int(minute), od))

    def handle_data(self, data):
        match = DATE.search(data)
        if match:
            self.date = datetime.strptime(match[1], "%d.%m.%Y").date().isoformat()


def read_csv(path):
    with (gzip.open(path, "rt", newline="") if path.suffix == ".gz"
          else path.open(newline="")) as stream:
        return list(csv.DictReader(stream))


def local_time(row):
    return datetime.fromisoformat(row["date_local"]).replace(hour=int(row["hour_local"]),
                                                           minute=int(row["minute_local"]))


def unique_utc(local):
    # A spring gap and a repeated autumn hour both lack a unique UTC mapping.
    first, second = (local.replace(tzinfo=BERLIN, fold=fold) for fold in (0, 1))
    return None if first.utcoffset() != second.utcoffset() else first.astimezone(timezone.utc)


def audit(truth_dir, raw_dir):
    half = read_csv(truth_dir / "dfld_half_hourly.csv.gz")
    hourly = read_csv(truth_dir / "dfld_hourly.csv")
    excluded = read_csv(truth_dir / "dfld_excluded_hours.csv")
    groups = defaultdict(list)
    full_keys = [(r["date_local"], int(r["hour_local"]), int(r["minute_local"])) for r in half]
    if len(set(full_keys)) != len(full_keys):
        raise ValueError("Duplicate local half-hour source bins")
    for row in half:
        if row["od"] not in ("07", "25"):
            raise ValueError("Unknown direction in retained half-hour data")
        groups[(row["date_local"], int(row["hour_local"]))].append(row)
    rebuilt, omitted = [], []
    for (date, hour), rows in sorted(groups.items()):
        reason = None
        if sorted(int(r["minute_local"]) for r in rows) != [0, 30]:
            reason = "missing half-hour bin"
        moment = unique_utc(datetime.fromisoformat(date).replace(hour=hour))
        if moment is None:
            reason = "ambiguous or nonexistent local hour"
        elif len({r["od"] for r in rows}) != 1:
            reason = "direction differs between half hours"
        if reason:
            omitted.append((date, hour, reason))
        else:
            if len({r["source"] for r in rows}) != 1:
                raise ValueError("Conflicting source URLs within hour")
            rebuilt.append((moment.isoformat().replace("+00:00", "Z"), rows[0]["od"], rows[0]["source"]))
    actual = [(r["time"], r["od"], r["source"]) for r in hourly]
    expected_omitted = {(r["date_local"], int(r["hour_local"])) for r in excluded}
    omission_match = {(d, h) for d, h, _ in omitted} == expected_omitted
    sequence = sorted((unique_utc(local_time(r)), r["od"]) for r in half if unique_utc(local_time(r)))
    transitions = []
    for (before, od_before), (after, od_after) in zip(sequence, sequence[1:]):
        if after - before == timedelta(minutes=30) and od_before != od_after:
            transitions.append(after)
    samples = []
    receipts = json.loads((raw_dir / "receipts.json").read_text())
    for receipt in receipts:
        path = raw_dir / receipt["file"]
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != receipt["sha256"]:
            raise ValueError(f"Receipt hash mismatch: {path.name}")
        parser = MonthlyPage()
        parser.feed(raw.decode("utf-8", errors="strict"))
        actual_sample = {(r["date_local"], int(r["hour_local"]), int(r["minute_local"]), r["od"])
                         for r in half if r["source"] == receipt["url"]}
        # The ongoing October page can contain a newer day than the frozen file.
        last_date = max(key[0] for key in actual_sample)
        fresh_sample = [r for r in parser.records if r[0] <= last_date]
        samples.append({"file": path.name, "retained_bins": len(actual_sample),
                        "fresh_bins_in_frozen_period": len(fresh_sample),
                        "unique_fresh_bins": len(set(fresh_sample)),
                        "exact_match": set(fresh_sample) == actual_sample and len(set(fresh_sample)) == len(fresh_sample),
                        "sha256": receipt["sha256"]})
    return {
        "source_files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in sorted(truth_dir.iterdir()) if p.is_file()},
        "half_hour_rows": len(half), "hourly_rows": len(hourly),
        "hourly_rebuild_exact_match_including_order_and_source": rebuilt == actual,
        "excluded_hours": len(omitted), "excluded_hour_keys_match": omission_match,
        "exclusion_reasons": dict(Counter(reason for _, _, reason in omitted)),
        "contiguous_half_hour_direction_changes": len(transitions),
        "change_bin_start_minutes": dict(Counter(str(t.minute) for t in transitions)),
        "warning": "Half-hour bin starts are not exact movement-event times. DST-ambiguous bins are excluded from transition counts.",
        "raw_html_samples": samples,
        "passed": rebuilt == actual and omission_match and all(s["exact_match"] for s in samples),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--truth-dir", type=Path, required=True)
    parser.add_argument("--raw-dir", type=Path, default=Path(__file__).parent / "raw")
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "report.json")
    args = parser.parse_args()
    report = audit(args.truth_dir, args.raw_dir)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
