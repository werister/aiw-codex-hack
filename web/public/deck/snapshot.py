"""Copy the deck's numbers from the repo into index.html, exactly as the source files state them.

Run from the repo root: python web/public/deck/snapshot.py
Sources: web/public/data/quality.json, EXPERIMENTS.md, RESULTS.md, ml/tests (pytest),
resources/ml-depth/*/report.json (independent data verification).
"""
import json
import pathlib
import re
import subprocess
import sys

here = pathlib.Path(__file__).resolve().parent
repo = here.parents[2]


def read_json(path):
    return json.loads((repo / path).read_text(encoding="utf-8"))


# Model quality (the deck re-reads this file at runtime when served).
q = read_json("web/public/data/quality.json")
folds = q.get("folds") or []
od = (q.get("significance") or {}).get("od") or q["out_of_sample"]["od"]
keys = ("lead_h", "n", "n_days", "model_acc", "model_acc_ci", "rule_acc", "persistence_acc",
        "model_change_acc", "rule_change_acc", "persistence_change_acc",
        "mcnemar_p_vs_rule", "dm_p_vs_rule", "mcnemar_p_vs_persistence", "dm_p_vs_persistence")
quality = {
    "test": {"start": folds[0]["test_period"]["start"], "end": folds[-1]["test_period"]["end"], "months": len(folds)} if folds else None,
    "od": [{k: r[k] for k in keys if k in r} for r in od],
    "next_change": {k: q["next_change"][k] for k in ("within_3h", "false_alarm_rate")},
}

# What we did.
experiments = (repo / "EXPERIMENTS.md").read_text(encoding="utf-8")
n_experiments = len(set(re.findall(r"^\| E(\d+) \|", experiments, flags=re.M)))
e10 = re.search(r"^\| E10 \|[^(]*\(([^)]*)\)", experiments, flags=re.M).group(1)
models = [m.strip() for m in re.sub(r"\s*previous runs", "", e10).split(",")]
tests = subprocess.run([sys.executable, "-m", "pytest", "ml/tests", "-q"], cwd=repo, capture_output=True, text=True)
passed = re.search(r"(\d+) passed", tests.stdout)
assert passed and " failed" not in tests.stdout, tests.stdout[-500:]
labels = read_json("resources/ml-depth/labels/report.json")
metar = read_json("resources/ml-depth/observations/audit.json")["source_audit"]
comparability = read_json("resources/ml-depth/comparability/report.json")
did = {
    "labels_since": "2018",  # EXPERIMENTS.md E7: labels and METAR extended back to 2018
    "weather_models": len(models),
    "weather_model_names": ", ".join(m.replace("ECMWF IFS", "ECMWF") for m in models),
    "experiments": n_experiments,
    "tests_passed": int(passed.group(1)),
    "hours_verified": labels["hourly_rows"],
    "half_hours": labels["half_hour_rows"],
    "changes": labels["contiguous_half_hour_direction_changes"],
    "raw_files_ok": metar["raw_verification"]["counts"]["all_raw_chunk_hashes_verified"],
    "raw_files": metar["dataset"]["raw_chunks"],
    "winds_rechecked": comparability["raw_source_integrity"]["open_meteo"]["raw_wind_values_compared"],
}

# Economic value: pitch line 2 of RESULTS.md, verbatim.
results = (repo / "RESULTS.md").read_text(encoding="utf-8")
sentence = re.search(r'^2\. "(On EUROCONTROL.*?)"\s*$', results, flags=re.M).group(1)
low, high = re.search(r"€([\d.]+)M to €([\d.]+)M a year", sentence).groups()
central = re.search(r"about €([\d.]+)M in our central case", sentence).group(1)
value = {"sentence": sentence, "low": low, "high": high, "central": central}

snap = {"quality": quality, "did": did, "value": value}
page = here / "index.html"
html = page.read_text(encoding="utf-8")
block = "/* SNAPSHOT:BEGIN */\n  var SNAPSHOT = " + json.dumps(snap, ensure_ascii=False) + ";\n  /* SNAPSHOT:END */"
html, n = re.subn(r"/\* SNAPSHOT:BEGIN \*/.*?/\* SNAPSHOT:END \*/", lambda m: block, html, flags=re.S)
assert n == 1, "snapshot markers not found"
page.write_text(html, encoding="utf-8", newline="\n")
print("quality:", [(r["lead_h"], round(r["model_acc"], 4)) for r in od], quality["next_change"])
print("did:", did)
print("value:", value["central"], value["low"], value["high"])
