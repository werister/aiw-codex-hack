#!/usr/bin/env python3
"""Export the frozen weather inputs, deeper checks and current OD source data."""

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weather-package", type=Path, required=True)
    parser.add_argument("--truth-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    archive = output.with_suffix(".zip")
    if output.exists() or archive.exists():
        parser.error("Choose a new output path; existing evidence is never replaced")
    audit = Path(__file__).resolve().parent
    if any(output.is_relative_to(source.resolve()) for source in
           (audit, args.weather_package, args.truth_dir)):
        parser.error("Export outside the source directories to avoid recursive copying")
    subprocess.run([sys.executable, str(args.weather_package / "verify_package.py")], check=True)
    snapshot = json.loads((audit / "project-snapshot.json").read_text())
    shutil.copytree(args.weather_package, output / "weather",
                    ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"))
    shutil.copytree(audit, output / "audit",
                    ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"))
    shutil.copytree(args.truth_dir, output / "project-data" / "ground_truth")
    # Reuse the separately checked manifest verifier at the bundle root.
    shutil.copy2(args.weather_package / "verify_package.py", output / "verify_package.py")
    (output / "README.md").write_text(
        "# Daten-Zuarbeit: vertieft geprüft\n\n"
        "**Start: [aktuelle Übergabe und Entscheidungen](audit/README.md).**\n\n"
        f"Projektabgleich: `{snapshot['reviewed_commit'][:7]}`, 30.10.2026. "
        "Enthalten sind die unveränderten Wetter-Rohdaten, unabhängige Prüfungen "
        "und der inzwischen erweiterte DFLD-Bestand des Teams.\n\n"
        "Der Ordner `weather/` bewahrt das frühere Datenpaket unverändert. "
        "Seine älteren Berichte beschreiben damalige Suchergebnisse. "
        "Insbesondere die dortige fehlende OD-Historie, der damalige Stand ohne "
        "ML-Code und pauschale Aussagen zu unbekannten Böen sind durch "
        "`audit/README.md` und die vier vertieften Prüfberichte präzisiert oder überholt.\n\n"
        "## Offline prüfen\n\n"
        "Python 3.11 oder neuer mit Zeitzonendaten, aus diesem Verzeichnis:\n\n"
        "```bash\npython3 verify_package.py\npython3 weather/verify_package.py\n"
        "python3 audit/temporal/probe.py --verify\n"
        "python3 audit/observations/verify_raw_metar.py --source weather/observations "
        "--rules weather/reference/rules.json --truth project-data/ground_truth/dfld_hourly.csv "
        "--output /tmp/metar-audit-report.json\n"
        "python3 audit/comparability/analyze_comparability.py --support-package weather "
        "--output /tmp/wind-comparison-report.json\n"
        "python3 audit/labels/audit_labels.py --truth-dir project-data/ground_truth "
        "--output /tmp/dfld-audit-report.json\n```\n\n"
        "`weather/` ist das Wetterpaket. Für eine unveränderte Lieferung die "
        "Integrität vor allen Reproduktionen prüfen. Die Skripte schreiben "
        "sonst neue Prüfberichte.\n\n"
        "Dieses Paket ergänzt die Arbeit des ML-Kollegen. Es enthält keine "
        "neu trainierten Modelle, keine geänderte Anwendung und keine neue "
        "Modellgütebehauptung. Die bestehenden Trainingsdaten verwenden "
        "`best_match`; die zusätzliche Wetterreferenz verwendet `icon_global`.\n",
        encoding="utf-8")
    entries = []
    for path in sorted(output.rglob("*")):
        if not path.is_file():
            continue
        body = path.read_bytes()
        entry = {"path": path.relative_to(output).as_posix(), "bytes": len(body),
                 "sha256": hashlib.sha256(body).hexdigest()}
        if path.suffix == ".csv":
            with path.open(newline="") as stream:
                entry["csv_rows"] = sum(1 for _ in csv.DictReader(stream))
        entries.append(entry)
    manifest = {"created_at_utc": datetime.now(timezone.utc).isoformat(),
                "scope": "Independent data audit and colleague handoff; no new training or application edits",
                "reviewed_project_commit": snapshot["reviewed_commit"],
                "files": entries, "total_bytes_excluding_manifest": sum(e["bytes"] for e in entries)}
    (output / "package-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    subprocess.run([sys.executable, str(output / "verify_package.py")], check=True)
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as bundle:
        for path in sorted(output.rglob("*")):
            if path.is_file():
                bundle.write(path, Path(output.name) / path.relative_to(output))
    print(json.dumps({"output": str(output), "zip_bytes": archive.stat().st_size,
                      "zip_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                      "files": len(entries) + 1}, indent=2))


if __name__ == "__main__":
    main()
