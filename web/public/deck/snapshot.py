"""Copy the deck's numbers from the repo into index.html, exactly as the source files state them.

Run after viz/build_data.py, from the repo root: python web/public/deck/snapshot.py
Sources: web/public/data/quality.json (+ ml/models/metadata.json for the version check), viz/accuracy.data.js,
EXPERIMENTS.md, ml/tests (pytest), resources/ml-depth/*/report.json (independent data verification).
The deck needs every block below (quality, did); dropping one breaks a slide.
"""
import hashlib
import json
import pathlib
import re
import subprocess
import sys

here = pathlib.Path(__file__).resolve().parent
repo = here.parents[2]


def read(path):
    return (repo / path).read_text(encoding="utf-8")


# Model quality (the deck re-reads this file at runtime when served). Version must match the saved model.
source = repo / "web/public/data/quality.json"
q = json.loads(source.read_text(encoding="utf-8"))
meta = json.loads(read("ml/models/metadata.json"))
assert q["model_version"] == meta["version"], "Publish a coherent model/quality bundle first"
folds = q.get("folds") or []
od = (q.get("significance") or {}).get("od") or q["out_of_sample"]["od"]
keys = ("lead_h", "n", "n_days", "model_acc", "model_acc_ci", "rule_acc", "persistence_acc",
        "model_change_acc", "rule_change_acc", "persistence_change_acc",
        "mcnemar_p_vs_rule", "dm_p_vs_rule", "mcnemar_p_vs_persistence", "dm_p_vs_persistence")
quality = {
    "model_version": q["model_version"],
    "test": {"start": folds[0]["test_period"]["start"], "end": folds[-1]["test_period"]["end"], "months": len(folds)} if folds else None,
    "od": [{k: r[k] for k in keys if k in r} for r in od],
    "next_change": {k: q["next_change"][k] for k in ("within_1h", "within_3h", "false_alarm_rate")},
    "od_change_events": {k: q["od_change_events"][k] for k in ("n_actual_events", "n_matched_events", "tolerance_h", "n_false_alarm_clusters", "n_exposure_days")},
    "r18_events": q["r18_events"],
}

# The accuracy chart must come from the same model version and rows: no mixed bundles.
chart = json.loads((here / "viz/accuracy.data.js").read_text(encoding="utf-8").split("export const DATA = ")[1].rstrip(";\n"))
assert chart["model_version"] == q["model_version"], "Rerun viz/build_data.py first"
for row in quality["od"]:
    match = next(r for r in chart["rows"] if r["lead_h"] == row["lead_h"])
    assert (match["model"], match["rules"], match["same"]) == (row["model_acc"], row["rule_acc"], row["persistence_acc"])

# What we did.
experiments = read("EXPERIMENTS.md")
n_experiments = len(set(re.findall(r"^\| E(\d+) \|", experiments, flags=re.M)))
e10 = re.search(r"^\| E10 \|[^(]*\(([^)]*)\)", experiments, flags=re.M).group(1)
models = [m.strip() for m in re.sub(r"\s*previous runs", "", e10).split(",")]
tests = subprocess.run([sys.executable, "-m", "pytest", "ml/tests", "-q"], cwd=repo, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
passed = re.search(r"(\d+) passed", tests.stdout)
assert passed and " failed" not in tests.stdout, tests.stdout[-500:]
labels = json.loads(read("resources/ml-depth/labels/report.json"))
metar = json.loads(read("resources/ml-depth/observations/audit.json"))["source_audit"]
comparability = json.loads(read("resources/ml-depth/comparability/report.json"))
did = {
    "labels_since": "2018",  # EXPERIMENTS.md E7: labels and METAR extended back to 2018
    "weather_models": len(models),
    "weather_model_names": ", ".join(m.replace("ECMWF IFS", "ECMWF") for m in models),
    "experiments": n_experiments,
    "tests_passed": int(passed.group(1)),
    "hours_verified": labels["hourly_rows"],
    "half_hours": labels["half_hour_rows"],
    "raw_files_ok": metar["raw_verification"]["counts"]["all_raw_chunk_hashes_verified"],
    "raw_files": metar["dataset"]["raw_chunks"],
    "winds_rechecked": comparability["raw_source_integrity"]["open_meteo"]["raw_wind_values_compared"],
}

snap = {"source": "web/public/data/quality.json", "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "quality": quality, "did": did}
page = here / "index.html"
html = page.read_text(encoding="utf-8")
block = "/* SNAPSHOT:BEGIN */\n  var SNAPSHOT = " + json.dumps(snap, ensure_ascii=False) + ";\n  /* SNAPSHOT:END */"
html, n = re.subn(r"/\* SNAPSHOT:BEGIN \*/.*?/\* SNAPSHOT:END \*/", lambda m: block, html, flags=re.S)
assert n == 1, "snapshot markers not found"
page.write_text(html, encoding="utf-8", newline="\n")
print(q["model_version"], snap["sha256"][:12])
print("quality:", [(r["lead_h"], round(r["model_acc"], 4)) for r in od], quality["next_change"], quality["od_change_events"])
print("did:", did)
