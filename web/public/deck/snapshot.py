"""Refresh the deck snapshot from published model quality; run after viz/build_data.py."""
import hashlib
import json
from pathlib import Path
import re

here = Path(__file__).resolve().parent
repo = here.parents[2]
source = repo / "web/public/data/quality.json"
q = json.loads(source.read_text())
meta = json.loads((repo / "ml/models/metadata.json").read_text())
assert q["model_version"] == meta["version"], "Publish a coherent model/quality bundle first"
folds = q["folds"]
keys = ("lead_h", "n", "n_days", "model_acc", "model_acc_ci", "rule_acc", "persistence_acc")
quality = {
    "model_version": q["model_version"],
    "test": {"start": folds[0]["test_period"]["start"], "end": folds[-1]["test_period"]["end"], "months": len(folds)},
    "od": [{k: r[k] for k in keys} for r in q["significance"]["od"]],
    "next_change": q["next_change"],
    "od_change_events": q["od_change_events"],
    "r18_events": q["r18_events"],
}
snapshot = {"source": "web/public/data/quality.json", "sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "quality": quality}
# Require the chart bundle to have been refreshed too: avoid mixing model versions.
chart = json.loads((here / "viz/accuracy.data.js").read_text().split("export const DATA = ")[1].rstrip(";\n"))
assert chart["model_version"] == q["model_version"]
for row in quality["od"]:
    match = next(r for r in chart["rows"] if r["lead_h"] == row["lead_h"])
    assert (match["model"], match["rules"], match["same"]) == (row["model_acc"], row["rule_acc"], row["persistence_acc"])
page = here / "index.html"
block = "/* SNAPSHOT:BEGIN */\n  var SNAPSHOT = " + json.dumps(snapshot, ensure_ascii=False) + ";\n  /* SNAPSHOT:END */"
html, n = re.subn(r"/\* SNAPSHOT:BEGIN \*/.*?/\* SNAPSHOT:END \*/", lambda _: block, page.read_text(), flags=re.S)
assert n == 1
page.write_text(html)
print(q["model_version"], snapshot["sha256"])
