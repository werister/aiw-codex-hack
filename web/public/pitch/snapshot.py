"""Copy the deck's results snapshot from web/public/data/quality.json into index.html.

Run from the repo root: python web/public/pitch/snapshot.py
"""
import json
import pathlib
import re

here = pathlib.Path(__file__).resolve().parent
q = json.loads((here.parent / "data" / "quality.json").read_text(encoding="utf-8"))
folds = q.get("folds") or []
od = (q.get("significance") or {}).get("od") or q["out_of_sample"]["od"]
keys = ("lead_h", "n", "model_acc", "model_acc_ci", "rule_acc", "persistence_acc", "acc_diff_vs_rule", "acc_diff_vs_rule_ci")
snap = {
    "test": {"start": folds[0]["test_period"]["start"], "end": folds[-1]["test_period"]["end"], "months": len(folds)} if folds else None,
    "od": [{k: r[k] for k in keys if k in r} for r in od],
    "next_change": {k: q["next_change"][k] for k in ("within_3h", "false_alarm_rate")},
}
page = here / "index.html"
html = page.read_text(encoding="utf-8")
block = "/* SNAPSHOT:BEGIN */\n  var SNAPSHOT = " + json.dumps(snap) + ";\n  /* SNAPSHOT:END */"
html, n = re.subn(r"/\* SNAPSHOT:BEGIN \*/.*?/\* SNAPSHOT:END \*/", lambda m: block, html, flags=re.S)
assert n == 1, "snapshot markers not found"
page.write_text(html, encoding="utf-8", newline="\n")
print("snapshot:", [(r["lead_h"], round(r["model_acc"], 4)) for r in snap["od"]], snap["next_change"])
