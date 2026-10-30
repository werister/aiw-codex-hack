"""Offline integrity and CSV/JSON readability check for the exported handoff."""
import csv
import hashlib
import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent
    manifest_path = root / 'package-manifest.json'
    manifest = json.loads(manifest_path.read_text())
    problems = []
    checked = 0
    for item in manifest['files']:
        path = root / item['path']
        if not path.resolve().is_relative_to(root):
            problems.append(f"Invalid path: {item['path']}")
            continue
        if not path.is_file():
            problems.append(f"Missing: {item['path']}")
            continue
        body = path.read_bytes()
        if len(body) != item['bytes'] or hashlib.sha256(body).hexdigest() != item['sha256']:
            problems.append(f"Changed: {item['path']}")
        if path.suffix == '.json':
            try:
                json.loads(body)
            except (UnicodeDecodeError, json.JSONDecodeError):
                problems.append(f"Invalid JSON: {item['path']}")
        if 'csv_rows' in item:
            try:
                with path.open(newline='') as stream:
                    reader = csv.DictReader(stream)
                    count = sum(1 for _ in reader)
                if count != item['csv_rows']:
                    problems.append(f"CSV count differs: {item['path']}: {count}")
            except (UnicodeDecodeError, csv.Error):
                problems.append(f"Unreadable CSV: {item['path']}")
        checked += 1
    result = {'files_checked': checked, 'integrity_pass': not problems, 'problems': problems}
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if not problems else 1)


if __name__ == '__main__':
    main()
