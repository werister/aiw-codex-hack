"""Regenerate the *.data.js files for the deck visualizations from repo data.

Run: python web/public/deck/viz/build_data.py
"""
import csv, json, base64, sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from collections import OrderedDict
import joblib, numpy as np

from pathlib import Path
R = str(Path(__file__).resolve().parents[4])
OUT = str(Path(__file__).resolve().parent)
BER = ZoneInfo("Europe/Berlin")

# Check the whole bundle before writing any generated chart file.
q = json.load(open(R + "/web/public/data/quality.json"))
m = joblib.load(R + "/ml/models/forecast.joblib")
m2 = json.load(open(R + "/ml/models/metadata.json"))
examples = {day: json.load(open(R + "/web/public/forecasts/" + day + ".json"))
            for day in ["2026-10-28", "2026-10-29"]}
assert m["version"] == m2["version"] == q["model_version"], "Model and quality versions differ"
assert all(d["model_version"] == q["model_version"] for d in examples.values()), "Example forecast is stale"

# ---------- barcode ----------
days = OrderedDict()
prev = None; changes = 0; n = 0; nw = 0; ne = 0
with open(R + "/data/ground_truth/dfld_hourly.csv", newline="") as f:
    for row in csv.DictReader(f):
        t = datetime.strptime(row["time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).astimezone(BER)
        od = row["od"]
        n += 1
        if od == "25": nw += 1
        else: ne += 1
        if prev is not None and od != prev: changes += 1
        prev = od
        key = t.date().isoformat()
        d = days.setdefault(key, [0] * 24)
        d[t.hour] = 1 if od == "25" else 2
# fill missing dates
from datetime import date, timedelta
first = date.fromisoformat(next(iter(days))); last = date.fromisoformat(list(days)[-1])
allbytes = bytearray(); ndays = 0
cur = first
while cur <= last:
    d = days.get(cur.isoformat(), [0] * 24)
    bits = 0
    for h in range(24): bits |= d[h] << (2 * h)
    allbytes += bits.to_bytes(6, "little")
    ndays += 1; cur += timedelta(days=1)
b64 = base64.b64encode(bytes(allbytes)).decode()
bar = {"start": first.isoformat(), "end": last.isoformat(), "days": ndays, "hours": n, "west_hours": nw, "east_hours": ne,
       "changes": changes, "source": "data/ground_truth/dfld_hourly.csv (DFLD recorded operating direction, hours in Europe/Berlin)",
       "encoding": "6 bytes per local day, 2 bits per hour (bit 2h), 0 = no record, 1 = west (25), 2 = east (07)"}
with open(OUT + "/barcode.data.js", "w", encoding="utf-8") as f:
    f.write("// Generated from data/ground_truth/dfld_hourly.csv. Do not edit by hand.\n")
    f.write("export const META = " + json.dumps(bar) + ";\n")
    f.write("export const BITS = \"" + b64 + "\";\n")
print("barcode", bar, len(b64))

# ---------- accuracy ----------
sig = {r["lead_h"]: r for r in q["significance"]["od"]}
acc = []
for r in q["out_of_sample"]["od"]:
    L = r["lead_h"]
    acc.append({"lead_h": L, "n": r["n"], "model": r["model_acc"], "rules": r["rule_acc"], "same": r["persistence_acc"],
                "model_ci": sig[L]["model_acc_ci"], "n_days": sig[L]["n_days"]})
accd = {"model_version": q["model_version"], "rows": acc, "test_period": q["folds"][0]["test_period"]["start"][:10] + " to " + q["folds"][-1]["test_period"]["end"][:10],
        "source": "web/public/data/quality.json out_of_sample.od + significance.od (95% issue-day bootstrap CI)"}
with open(OUT + "/accuracy.data.js", "w", encoding="utf-8") as f:
    f.write("// Generated from web/public/data/quality.json. Do not edit by hand.\n")
    f.write("export const DATA = " + json.dumps(accd, indent=1) + ";\n")
print("accuracy", json.dumps(accd)[:600])

# drivers too
with open(OUT + "/drivers.data.js", "w", encoding="utf-8") as f:
    f.write("// Generated from web/public/data/quality.json drivers. Do not edit by hand.\n")
    f.write("export const DRIVERS = " + json.dumps(q["drivers"], indent=1) + ";\n")

# ---------- tree ----------
od = m["od"]; feats = m["features"]
p = od._predictors[0][0]
nodes = p.nodes
def subtree_stats(i):
    nd = nodes[i]
    if nd["is_leaf"]: return float(nd["value"]) * nd["count"], int(nd["count"])
    a, c1 = subtree_stats(nd["left"]); b, c2 = subtree_stats(nd["right"]); return a + b, c1 + c2
def build(i, depth):
    nd = nodes[i]
    s, c = subtree_stats(i)
    out = {"count": int(nd["count"]), "lean": s / c}
    if nd["is_leaf"]:
        out["leaf"] = True; out["value"] = float(nd["value"])
        return out
    out["feature"] = feats[int(nd["feature_idx"])]
    out["threshold"] = float(nd["num_threshold"])
    out["missing_left"] = bool(nd["missing_go_to_left"])
    if depth < 3:
        out["left"] = build(int(nd["left"]), depth + 1)
        out["right"] = build(int(nd["right"]), depth + 1)
    else:
        out["more"] = True
    return out
tree = build(0, 0)
td = {"n_trees": int(od.n_iter_), "tree_index": 0, "n_leaves": int(sum(nodes["is_leaf"])), "n_nodes": len(nodes),
      "learning_rate": float(od.learning_rate), "max_leaf_nodes": od.max_leaf_nodes, "baseline": float(np.ravel(od._baseline_prediction)[0]),
      "version": m["version"], "trained_through": m["trained_through"], "class_1": "west (25)",
      "note": "left branch = value <= threshold; leaf value = log-odds push toward west (positive) or east (negative)",
      "root": tree, "source": "ml/models/forecast.joblib od model, boosting iteration 1"}
with open(OUT + "/tree.data.js", "w", encoding="utf-8") as f:
    f.write("// Generated from ml/models/forecast.joblib (first tree of the operating-direction model). Do not edit by hand.\n")
    f.write("export const TREE = " + json.dumps(td, indent=1) + ";\n")
print("tree", json.dumps(td)[:3000])

# ---------- example ----------
ex = {}
for day in ["2026-10-28", "2026-10-29"]:
    d = examples[day]
    obs = {o["time"]: o["od"] for o in d["observed"]}
    hrs = []
    for h in d["hours"]:
        hrs.append({"local": h["local"], "lead": h["lead_h"], "p_west": round(h["p_od25"], 4), "model": h["od"], "rules": h["rule_od"],
                    "actual": obs.get(h["time"])})
    ex[day] = {"issued_local": d["issued_local"], "current_od": d["current_od"], "mode": d["mode"], "model_version": d["model_version"],
               "next_change": d["next_change"], "hours": hrs, "source": "web/public/forecasts/%s.json" % day}
    print(day, [ (h['lead'], h['p_west'], h['actual']) for h in hrs])
with open(OUT + "/example.data.js", "w", encoding="utf-8") as f:
    f.write("// Generated from web/public/forecasts/*.json (hindcasts with recorded DFLD direction). Do not edit by hand.\n")
    f.write("export const DAYS = " + json.dumps(ex) + ";\n")

pm = {"n_features": len(m2["features"]), "n_rows": m2["n"], "trained_through": m2["trained_through"], "version": m2["version"], "source": "ml/models/metadata.json"}
with open(OUT + "/pipeline.data.js", "w", encoding="utf-8") as f:
    f.write("// Generated from ml/models/metadata.json. Do not edit by hand.\n")
    f.write("export const META = " + json.dumps(pm) + ";\n")
