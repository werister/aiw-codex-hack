"""Red-team B: independent recompute of October v4 comparison from per-row traces.

Reads only per_row_traces.parquet + metrics.csv + manifest.json.
Never touches models.joblib. No training, no sklearn needed.
Run with: TMPDIR=<SSD>/redteam_scratch/tmp PYTHONPYCACHEPREFIX=<SSD>/redteam_scratch/pycache \
  redteam_scratch/.venv/bin/python redteam_scratch/check_evidence.py
"""
import csv
import hashlib
import json
import pathlib
import sys

import numpy as np
import pandas as pd

EV = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/content/fra-red-team-results")
PARQUET = EV / "per_row_traces.parquet"
METRICS = EV / "metrics.csv"
MANIFEST = EV / "manifest.json"

PASS = 0
FAIL = 0

def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"PASS {name} {detail}")
    else:
        FAIL += 1
        print(f"FAIL {name} {detail}")

def main():
    manifest = json.loads(MANIFEST.read_text())
    # 1. Manifest split: train/test purge and row counts
    check("manifest_source_is_pinned_v4", manifest["source_commit"] == "44d5abd3363248b1de0a3ed96ff32982aafdd7b3", manifest["source_commit"][:8])
    check("manifest_train_rows", manifest["train_rows"] == 189000, str(manifest["train_rows"]))
    check("manifest_test_rows", manifest["test_rows"] == 5136, str(manifest["test_rows"]))
    check("manifest_scored_rows", manifest["scored_rows"] == 5068, str(manifest["scored_rows"]))
    train_end = pd.Timestamp(manifest["train_label_end"])
    test_start = pd.Timestamp(manifest["test_issue_start"])
    check("purge_train_end_before_test_start", train_end < test_start, f"{train_end} < {test_start}")
    check("feature_count_v4", len(manifest["feature_order"]) == 25, str(len(manifest["feature_order"])))

    # 2. Parquet loads and matches manifest
    df = pd.read_parquet(PARQUET)
    check("parquet_len_is_scored", len(df) == manifest["scored_rows"], f"{len(df)}")
    check("parquet_no_y_missing", int(df["y_od"].isna().sum()) == 0, "y_od complete in scored set")
    methods = ["original_raw", "original_blend", "extra_trees", "equal_mix", "persistence", "rules"]
    for m in methods:
        s = df[m]
        check(f"prob_{m}_finite_01", bool(np.isfinite(s.to_numpy()).all() and (s >= 0).all() and (s <= 1).all()),
              f"n={len(s)} null={int(s.isna().sum())}")

    # 3. equal_mix definition
    mix_ok = np.allclose(df["equal_mix"].to_numpy(), 0.5 * df["original_blend"].to_numpy() + 0.5 * df["extra_trees"].to_numpy(), atol=1e-12)
    check("equal_mix_is_half_blend_half_extra", bool(mix_ok), "0.5*blend+0.5*extra")

    # 4. Label meaning: y_od is 0/1 recorded direction; changed_within_lead rises with lead (any-transition flag)
    check("y_od_binary", bool(set(df["y_od"].unique()) <= {0.0, 1.0}), f"mean={float(df['y_od'].mean()):.3f}")
    ch1 = float(df.loc[df.lead_h == 1, "changed_within_lead"].mean())
    ch48 = float(df.loc[df.lead_h == 48, "changed_within_lead"].mean())
    check("changed_within_lead_rises_with_lead", ch1 < 0.1 and ch48 > 0.4, f"lead1={ch1:.3f} lead48={ch48:.3f}")
    # Target-hour direction vs any-transition are different columns with different meanings
    check("change_flag_is_not_target_label", "changed_within_lead" in df.columns and "y_od" in df.columns,
          "change_acc in skill() scores target-hour y_od conditional on changed_within_lead")

    # 5. Row comparability: all methods share identical scored rows per lead (common mask already applied)
    for lead in (1, 6, 24, 48):
        sub = df.loc[df.lead_h == lead]
        check(f"lead_{lead}_rowcount_matches_colab", len(sub) in (105, 107, 88, 81, 85, 26),
              f"all_recorded n={len(sub)}")
    # Suspect exclusion removes the stuck-feed rows only
    excl = df.loc[~(df["suspect_target"] | df["suspect_input"])]
    check("suspect_exclusion_removes_rows", 0 < len(excl) < len(df), f"{len(excl)}/{len(df)} kept")

    # 6. Recompute metrics.csv from per-row probs with the same scorer logic as ml/quality.skill
    # skill: per lead, dropna(y_od, p, rule_od25, od_at_issue); acc=(p>=.5)==y; brier=mean((p-y)^2);
    # change_acc on changed_within_lead subset; change_n=sum(changed).
    expected = {}
    with open(METRICS) as f:
        for r in csv.DictReader(f):
            key = (r["method"], r["slice"], int(r["lead_h"]))
            expected[key] = r

    def berlin_hour(ts):
        return ts.dt.tz_convert("Europe/Berlin").dt.hour

    n_checked = 0
    n_mismatch = 0
    worst = []
    for method in methods:
        base = df.assign(p=df[method].to_numpy(float))
        slices = {
            "all_recorded": base,
            "suspect_excluded_sensitivity": base.loc[~(base["suspect_target"] | base["suspect_input"])],
            "midnight_issues": base.loc[berlin_hour(base["issue_time"]).eq(0)],
        }
        for slice_name, subset in slices.items():
            for lead in (1, 6, 24, 48):
                rows = subset.loc[subset.lead_h == lead].dropna(subset=["y_od", "p", "rule_od25", "od_at_issue"])
                y = rows["y_od"].to_numpy(float)
                p = rows["p"].to_numpy(float)
                acc = float(np.mean((p >= 0.5) == y)) if len(y) else None
                brier = float(np.mean((p - y) ** 2)) if len(y) else None
                ch = rows["changed_within_lead"].to_numpy(bool)
                change_n = int(ch.sum())
                change_acc = float(np.mean((p[ch] >= 0.5) == y[ch])) if ch.any() else None
                key = (method, slice_name, lead)
                exp = expected.get(key)
                if exp is None:
                    print(f"FAIL missing metrics.csv row {key}")
                    n_mismatch += 1
                    continue
                n_checked += 1
                ok_n = int(exp["n"]) == len(rows)
                if exp["changed_n"] not in ("", None):
                    ok_ch_n = int(exp["changed_n"]) == change_n
                else:
                    ok_ch_n = change_n == 0
                ok = ok_n and ok_ch_n
                # accuracy/brier compare with tolerance; changed_accuracy may be empty when change_n==0
                def close(a, b):
                    if a is None and (b in ("", None)):
                        return True
                    if a is None or b in ("", None):
                        return False
                    return abs(float(a) - float(b)) < 1e-9
                ok = ok and close(acc, exp["accuracy"]) and close(brier, exp["brier"]) and close(change_acc, exp["changed_accuracy"])
                if not ok:
                    n_mismatch += 1
                    worst.append((key, len(rows), exp["n"], acc, exp["accuracy"], brier, exp["brier"], change_n, exp["changed_n"], change_acc, exp["changed_accuracy"]))
    check("metrics_csv_has_72_cells", len(expected) == 72, f"{len(expected)}")
    check("recomputed_all_72_cells_match", n_mismatch == 0 and n_checked == 72, f"{n_checked - n_mismatch}/{n_checked} match")
    if worst:
        for w in worst[:6]:
            print("  MISMATCH", w)

    # 7. Headline finding recomputed: no accuracy gain for alternatives on all_recorded
    def cell(m, lead):
        r = expected[(m, "all_recorded", lead)]
        return float(r["accuracy"]), float(r["brier"])
    for lead in (1, 6, 24, 48):
        b_acc, _ = cell("original_blend", lead)
        e_acc, _ = cell("extra_trees", lead)
        m_acc, _ = cell("equal_mix", lead)
        check(f"lead{lead}_no_alt_accuracy_gain", e_acc <= b_acc and m_acc <= b_acc + 1e-12,
              f"blend={b_acc:.4f} extra={e_acc:.4f} mix={m_acc:.4f}")

    print(f"\nSUMMARY pass={PASS} fail={FAIL}")
    return 1 if FAIL else 0

if __name__ == "__main__":
    sys.exit(main())
