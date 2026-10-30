"""Controlled v5 + supplemental ICON-Global experiment (October exploratory).

Standalone script: runs in a FRESH subprocess per lag so no earlier notebook
imports leak in. v5 model source is NEVER modified; the candidate appends 7 raw
ICON columns (adapter default scale=1.0, asserted). Identical full-48h issue
masks in both arms. Core paired comparison first; then a case-by-case selector
exploration learned ONLY on pre-October out-of-fit predictions (never on Oct).

Exact CLI (after extracting the pinned archive to /content/fra-v5-icon and the
colab bundle to the same root), once per lag -- 6 and 12, compared only
within the same lag:

    python3 /content/fra-v5-icon/experiment_v5_icon.py \
        --repo /content/fra-v5-icon \
        --out /content/fra-v5-icon-results/lag6 --lag 6 \
        --archive-sha <sha256 of fra-v5-icon-source.zip> \
        --adapter-sha <sha256 of icon_supplement.py>

Pinned values are recorded in the notebook; the script asserts them.
"""
import argparse
import hashlib
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

EXPECTED_OFFSETS = {6: {1: 18, 2: 24, 3: 6}, 12: {1: 12, 2: 24, 3: 12}}
KEY_COLS = ["issue_time", "time", "lead_h"]


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="extracted source archive root")
    parser.add_argument("--out", required=True, help="results directory (created)")
    parser.add_argument("--lag", type=int, choices=(6, 12), default=6,
                        help="publication-lag proxy hours; separate fresh dataset per lag")
    parser.add_argument("--rev", default="5aed997313b78678d11fa23b808c2a9835a1d91a")
    parser.add_argument("--archive-sha", required=True)
    parser.add_argument("--adapter-sha", required=True)
    return parser.parse_args(argv)


def base_block_hash(frame, features):
    """Index-safe hash of the baseline feature block on canonical key order."""
    ordered = frame.sort_values(KEY_COLS).reset_index(drop=True)
    return hashlib.sha256(
        pd.util.hash_pandas_object(ordered[features], index=False).to_numpy().tobytes()
    ).hexdigest()


def main(argv=None):
    args = parse_args(argv)
    ROOT = Path(args.repo)
    OUT = Path(args.out)
    OUT.mkdir(parents=True, exist_ok=True)

    import sklearn
    import joblib
    from sklearn.ensemble import HistGradientBoostingClassifier
    from threadpoolctl import threadpool_limits
    sys.path.insert(0, str(ROOT))
    import ml.features as feat
    feat.PUBLICATION_LAG_H = args.lag  # local run parameter, before any consumer import
    from ml import train as training
    from ml.features import FEATURES, MULTIMODELS, WIND_SCALE, nwp_offset_days
    from ml.predict import HORIZONS, REGIMES, blend_keys, probability
    from ml.quality import r18_events, skill
    from ml.rules import RULES
    import icon_supplement as icon
    assert icon.PUBLICATION_LAG_H == args.lag, "adapter must see the run lag"
    started = time.time()
    threadpool_limits(limits=2)
    RUN_ID = f"v5icon-{args.rev[:8]}-lag{args.lag}"

    # ---- frozen identity: feature count/order DERIVED from metadata, not literal ----
    assert args.rev == "5aed997313b78678d11fa23b808c2a9835a1d91a", args.rev
    assert RULES["version"] == "fraalliance-brief-2026-10-30", RULES["version"]
    meta = json.loads((ROOT / "ml/models/metadata.json").read_text())
    assert meta["version"] == "walk-forward-v5", meta["version"]
    BASE_FEATURES = list(meta["features"])
    assert list(FEATURES) == BASE_FEATURES, "imported FEATURES must equal metadata order"
    print(f"BASE features from metadata: {len(BASE_FEATURES)} (order-verified)", flush=True)
    assert set(BASE_FEATURES) & {"y_od", "y_r18", "suspect_target", "suspect_input",
                                 "changed_within_lead"} == set()
    assert MULTIMODELS == ("ecmwf_ifs025", "gfs_seamless", "icon_seamless"), MULTIMODELS
    assert "icon_global" not in WIND_SCALE, "ICON must stay out of MULTIMODELS (S3)"
    import inspect as _inspect
    _fit_src = _inspect.getsource(training.fit_classifiers)
    for _needle in ("max_iter=80", "max_leaf_nodes=15", "learning_rate=0.08",
                    "l2_regularization=10", "min_samples_leaf=50, early_stopping=False",
                    "random_state=42"):
        assert _needle in _fit_src, _needle  # baseline model family unchanged
    ADAPTER_PATH = ROOT / "icon_supplement.py"
    assert ADAPTER_PATH.exists(), f"missing adapter: {ADAPTER_PATH}"
    assert hashlib.sha256(ADAPTER_PATH.read_bytes()).hexdigest() == args.adapter_sha, \
        "adapter bytes differ from review"
    ICON_COLS = ["icon_wind_kt", "icon_gust_kt", "icon_wind_dir_deg", "icon_tailwind_25_kt",
                 "icon_tailwind_07_kt", "icon_tailwind_18_kt", "supplemental_missing"]
    assert set(ICON_COLS) & set(BASE_FEATURES) == set(), "supplemental must not overwrite baseline"
    CAND_FEATURES = list(BASE_FEATURES) + ICON_COLS
    print(f"BASELINE {len(BASE_FEATURES)} + SUPPLEMENTAL 7 = {len(CAND_FEATURES)} at lag {args.lag}", flush=True)

    # ---- supplemental source contract (S1/S2) ----
    ICON_CSV = ROOT / "resources/ml-support/forecast/normalized/open-meteo-icon-global.csv"
    icon_frame = icon.load_icon_csv(ICON_CSV)  # rejects wrong model, dupes, missing offset cols
    assert len(icon_frame) == 16008, len(icon_frame)
    assert icon_frame.index.min() == pd.Timestamp("2025-01-01T00:00Z"), icon_frame.index.min()
    assert icon_frame.index.max() == pd.Timestamp("2026-10-29T23:00Z"), icon_frame.index.max()
    assert (icon_frame.index[1:] - icon_frame.index[:-1] == pd.Timedelta(hours=1)).all(), "hourly grid"
    probe = icon_frame.iloc[:24]
    assert (probe["requested_latitude_deg"] == 50.033).all()
    assert (probe["requested_longitude_deg"] == 8.57).all()
    assert (probe["grid_latitude_deg"] == 50.0).all() and (probe["grid_longitude_deg"] == 8.625).all()
    for day in (1, 2, 3):
        speed = icon_frame[f"wind_speed_10m_previous_day{day}_kn"]
        direction = icon_frame[f"wind_direction_10m_previous_day{day}_deg"]
        gust = icon_frame[f"wind_gusts_10m_previous_day{day}_kn"]
        assert speed.notna().all() and direction.notna().all() and gust.notna().all(), f"day{day} wind complete"
        assert ((speed >= 0) & (speed <= 200)).all(), f"day{day} speed range"
        assert ((direction >= 0) & (direction <= 360)).all(), f"day{day} direction range"
        assert (gust >= 0).all(), f"day{day} gust range"
    print("ICON source contract OK: 16008 hourly UTC targets, kn/deg columns, icon_global", flush=True)

    # ---- S2 alignment: ICON day1 vs METAR at the same valid hour (train window) ----
    met = pd.read_parquet(ROOT / "data/eddf_metar.parquet")
    met = met.rename(columns={"valid": "time", "drct": "wind_dir_deg", "sknt": "wind_kt"})
    met["time"] = pd.to_datetime(met["time"], utc=True)
    met["wind_kt"] = pd.to_numeric(met["wind_kt"], errors="coerce")
    met = met.dropna(subset=["wind_kt"]).sort_values("time").drop_duplicates("time", keep="last")
    grid = pd.DataFrame({"time": pd.date_range("2025-01-01", "2026-10-01", freq="h", tz="UTC", inclusive="left")})
    grid = grid.merge(icon_frame[["wind_speed_10m_previous_day1_kn"]].rename_axis("time").reset_index(),
                      on="time", how="left", validate="one_to_one")
    grid = pd.merge_asof(grid.sort_values("time"), met[["time", "wind_kt"]].rename(
        columns={"time": "met_time"}), left_on="time", right_on="met_time",
        direction="backward", tolerance=pd.Timedelta(hours=1))
    grid = grid.dropna(subset=["wind_speed_10m_previous_day1_kn", "wind_kt"]).reset_index(drop=True)
    assert len(grid) > 14000, len(grid)
    assert ((grid["time"] - grid["met_time"]) >= pd.Timedelta(0)).all(), "no future obs"
    hourly_met = grid.set_index("time")["wind_kt"].asfreq("h")
    hourly_icon = grid.set_index("time")["wind_speed_10m_previous_day1_kn"].asfreq("h")
    r0 = float(hourly_icon.corr(hourly_met))
    rm = float(hourly_icon.corr(hourly_met.shift(24)))
    rp = float(hourly_icon.corr(hourly_met.shift(-24)))
    print(f"ALIGNMENT day1-vs-METAR r: shift-24h={rm:.3f} shift0={r0:.3f} shift+24h={rp:.3f} n={len(grid)}", flush=True)
    assert r0 > 0.6 and r0 > rm and r0 > rp, "day1 must align at shift 0 (S2)"

    # ---- v5 dataset via the DIRECT builder (never the fixed-key cache: its key
    # omits supplemental inputs, so reuse across arms would collide) ----
    frame, truth, obs, skipped = training.dataset(stride=6)
    print(f"FULL v5 build rows: {len(frame)} issues skipped: {skipped}", flush=True)
    assert str(frame["time"].dt.tz) == "UTC" and str(frame["issue_time"].dt.tz) == "UTC"

    # ---- S5 identical full-48h issue mask, both arms ----
    COVERAGE_START = pd.Timestamp("2025-01-01", tz="UTC")
    candidate_issues = sorted(set(frame.issue_time[frame.issue_time >= COVERAGE_START]))
    assert len(candidate_issues) > 1500, len(candidate_issues)
    parts = [icon.icon_supplement(issue, icon_frame) for issue in candidate_issues]
    supp = pd.concat(parts, ignore_index=True)
    assert (supp.groupby("issue_time").size() == 48).all(), "adapter must return 48 rows per issue"
    assert str(supp["time"].dt.tz) == "UTC" and str(supp["issue_time"].dt.tz) == "UTC"
    assert (supp["offset_available_proxy"] <= supp["issue_time"]).all(), "proxy must not exceed issue"
    assert (supp["wind_scale_applied"] == 1.0).all(), "raw ICON default (S4)"
    expected = EXPECTED_OFFSETS[args.lag]
    mid_issue = candidate_issues[len(candidate_issues) // 2]
    got = supp.loc[supp.issue_time == mid_issue].groupby("offset_days").size().to_dict()
    assert got == expected, f"offset distribution {got} != {expected} at lag {args.lag}"
    assert (supp["offset_days"].to_numpy() == np.array(
        [nwp_offset_days(lead) for lead in supp["lead_h"]])).all(), "band must equal production mapping (S1)"
    spot = supp.loc[(supp.issue_time == mid_issue) & (supp.lead_h == 1)].iloc[0]
    assert spot["icon_wind_kt"] == icon_frame.loc[spot["time"], "wind_speed_10m_previous_day1_kn"], \
        "raw values must equal CSV day-band values"
    coverage = 1.0 - float(supp["supplemental_missing"].mean())
    print(f"SUPPLEMENTAL coverage over 2025+ issues: {coverage:.4f}", flush=True)
    assert coverage > 0.99, "non-missing coverage must exceed 99% (S5)"
    complete_issues = set(supp.loc[~supp["supplemental_missing"]].groupby("issue_time").filter(
        lambda g: len(g) == 48)["issue_time"].unique())
    print(f"ISSUES candidate {len(candidate_issues)} complete-48h {len(complete_issues)}", flush=True)
    eligible = frame.loc[frame.issue_time.isin(complete_issues)].copy()
    assert (eligible.groupby("issue_time").size() == 48).all(), "every kept issue needs all 48 rows"
    _pre_hash = base_block_hash(eligible, BASE_FEATURES)
    joined = eligible.merge(supp, on=["issue_time", "time", "lead_h"], how="left",
                            validate="one_to_one", indicator="_merge")
    assert (joined["_merge"] == "both").all(), "every eligible row needs a supplemental row"
    joined = joined.drop(columns=["_merge", "offset_days", "offset_available_proxy",
                                  "wind_scale_applied", "download_time"])
    joined["supplemental_missing"] = joined["supplemental_missing"].astype(int)
    assert base_block_hash(joined, BASE_FEATURES) == _pre_hash, \
        "base columns must be byte-identical between arms (S3)"
    assert not joined["supplemental_missing"].any(), "kept issues must be fully covered"
    for col in ICON_COLS[:-1]:
        assert np.isfinite(joined[col].to_numpy()).all() and joined[col].std() > 0, col
    assert (joined[ICON_COLS[:-1]].notna().mean() > 0.99).all(), "matched supplemental non-missing > 99%"
    print("JOIN OK: base block byte-identical, 7 raw supplemental cols finite with variance", flush=True)

    start, end = pd.Timestamp("2026-10-01", tz="UTC"), pd.Timestamp("2026-11-01", tz="UTC")
    train_rows = joined.loc[joined.label_available_at < start].copy()
    test_rows = joined.loc[(joined.issue_time >= start) & (joined.issue_time < end)
                           & (joined.label_available_at < end)].copy()
    assert len(train_rows) and len(test_rows)
    assert train_rows.label_available_at.max() < test_rows.issue_time.min(), "purge violated"
    assert train_rows.issue_time.max() < start, "blend validation must stay pre-October"
    assert (test_rows.groupby("issue_time").size() == 48).all(), "October issues must be intact"
    print(f"ROWS train {len(train_rows)} test {len(test_rows)}", flush=True)
    fit_rows = training.without_stuck_feed(train_rows)  # same inherited exclusion, both arms (S6)
    assert fit_rows.label_available_at.max() < test_rows.issue_time.min()

    # ---- shared fit/blend primitives (identical math for core + selector study) ----
    def fit_classifier(rows, features, label="y_od"):
        labelled = rows.dropna(subset=[label])
        model = HistGradientBoostingClassifier(max_iter=80, max_leaf_nodes=15, learning_rate=0.08,
            l2_regularization=10, min_samples_leaf=50, early_stopping=False, random_state=42)
        model.fit(labelled[features], labelled[label].astype(int))
        return model

    def select_blend_weights(validation, features, model):
        raw = probability(model, validation[features])
        y = validation.y_od.to_numpy(float)
        prior = validation.od_at_issue.to_numpy(float)
        keys = blend_keys(validation)

        def best_alpha(sel):
            losses = [(float(np.mean((a * raw[sel] + (1 - a) * prior[sel] - y[sel]) ** 2)), a)
                      for a in np.round(np.linspace(0, 1, 11), 1)]
            return float(min(losses)[1])

        weights = {}
        for horizon in HORIZONS:
            fallback = best_alpha(np.char.startswith(keys, horizon + ":"))
            for regime in REGIMES:
                sel = keys == f"{horizon}:{regime}"
                weights[f"{horizon}:{regime}"] = best_alpha(sel) if sel.sum() >= 50 else fallback
        return weights

    def fit_with_features(frame, features):
        validation_start = frame.issue_time.max() - pd.Timedelta(days=60)
        earlier = frame.loc[frame.label_available_at < validation_start]
        validation = frame.loc[frame.issue_time >= validation_start].dropna(subset=["y_od"])
        cand = fit_classifier(earlier, features)
        weights = select_blend_weights(validation, features, cand)
        models = {"od": fit_classifier(frame.dropna(subset=["y_od"]), features, "y_od")}
        r18_rows = frame.dropna(subset=["y_r18"])
        r18_model = HistGradientBoostingClassifier(max_iter=80, max_leaf_nodes=15, learning_rate=0.08,
            l2_regularization=10, min_samples_leaf=50, early_stopping=False, random_state=42)
        r18_model.fit(r18_rows[features], r18_rows["y_r18"].astype(int))
        models["r18"] = r18_model
        models["od_model_weight"] = weights
        models["od_blend_validation_start"] = validation_start.isoformat()
        return models

    def blended(models, features, rows):
        p_raw = probability(models["od"], rows[features])
        alpha = np.array([models["od_model_weight"][k] for k in blend_keys(rows)])
        return p_raw, alpha * p_raw + (1 - alpha) * rows.od_at_issue.to_numpy(float)

    # ---- CORE paired experiment (primary): full pre-Oct fit, Oct scoring ----
    print("Fitting CORE baseline (metadata base features, 2025+ full-48h issues)", flush=True)
    baseline = fit_with_features(fit_rows, BASE_FEATURES)
    print("Fitting CORE candidate (base+ICON-raw, identical rows)", flush=True)
    candidate = fit_with_features(fit_rows, CAND_FEATURES)
    assert baseline["od_blend_validation_start"] < start.isoformat(), "blend selection pre-October"

    b_raw, b_blend = blended(baseline, BASE_FEATURES, test_rows)
    c_raw, c_blend = blended(candidate, CAND_FEATURES, test_rows)

    # ---- SELECTOR exploration (separate, experimental): explicit disjoint blocks ----
    # early-base-fit / blend-validation / selector-validation / October test, with
    # purged labels across each boundary. Selector learned on Sep OOF only; Oct
    # untouched for selection. No delay labels; OD Brier only. Not wired into any
    # decision API -- exploratory postprocess rule + retained OOF predictions.
    B1 = pd.Timestamp("2026-08-01", tz="UTC")
    B2 = pd.Timestamp("2026-09-01", tz="UTC")
    early_rows = training.without_stuck_feed(joined.loc[joined.label_available_at < B1].copy())
    blendval_rows = joined.loc[(joined.issue_time >= B1) & (joined.issue_time < B2)
                               & (joined.label_available_at < B2)].dropna(
                                   subset=["y_od", "od_at_issue"]).copy()
    selval_rows = joined.loc[(joined.issue_time >= B2) & (joined.issue_time < start)
                             & (joined.label_available_at < start)].copy()
    assert len(early_rows) > 50000 and len(blendval_rows) > 3000 and len(selval_rows) > 3000, \
        (len(early_rows), len(blendval_rows), len(selval_rows))
    assert early_rows.label_available_at.max() < blendval_rows.issue_time.min(), "purge early/blendval"
    assert blendval_rows.label_available_at.max() < selval_rows.issue_time.min(), "purge blendval/selval"
    assert selval_rows.label_available_at.max() < test_rows.issue_time.min(), "purge selval/October"
    print(f"SELECTOR blocks early {len(early_rows)} blendval {len(blendval_rows)} "
          f"selval {len(selval_rows)} (purged)", flush=True)
    early_models = {}
    for arm, feats in (("baseline", BASE_FEATURES), ("candidate", CAND_FEATURES)):
        clf = fit_classifier(early_rows, feats)
        w = select_blend_weights(blendval_rows, feats, clf)
        early_models[arm] = {"od": clf, "od_model_weight": w}
    sel_common = selval_rows[["y_od", "od_at_issue", "rule_od25"]].notna().all(axis=1)
    selval_scored = selval_rows.loc[sel_common].copy()
    oof_excluded = int((~sel_common).sum())
    assert len(selval_scored) > 2000, len(selval_scored)
    oof = selval_scored[["issue_time", "time", "lead_h", "y_od", "changed_within_lead",
                         "od_at_issue", "rule_od25"]].copy()
    oof["cell"] = blend_keys(selval_scored)
    _, oof["p_baseline"] = blended(early_models["baseline"], BASE_FEATURES, selval_scored)
    _, oof["p_candidate"] = blended(early_models["candidate"], CAND_FEATURES, selval_scored)
    assert np.isfinite(oof[["p_baseline", "p_candidate"]].to_numpy()).all(), "OOF probs finite"
    assert np.isfinite(oof["y_od"].to_numpy(float)).all(), "OOF labels finite"
    oof["model_run_id"] = RUN_ID
    oof.to_parquet(OUT / "oof_selector_validation.parquet", index=False)
    print(f"OOF retained: {len(oof)} valid pre-October out-of-fit rows "
          f"({oof_excluded} excluded on NaN label/prior/rules)", flush=True)
    MIN_CELL_N = 50
    global_brier = {arm: float(np.mean((oof[f"p_{arm}"] - oof.y_od.to_numpy(float)) ** 2))
                    for arm in ("baseline", "candidate")}
    assert all(np.isfinite(v) for v in global_brier.values()), "global OOF Brier finite"
    global_arm = min(global_brier, key=global_brier.get)
    selector_table = {}
    for cell, group in oof.groupby("cell"):
        briers = {arm: float(np.mean((group[f"p_{arm}"] - group.y_od.to_numpy(float)) ** 2))
                  for arm in ("baseline", "candidate")}
        assert all(np.isfinite(v) for v in briers.values()), f"non-finite OOF Brier in {cell}"
        if len(group) >= MIN_CELL_N:
            arm = min(briers, key=briers.get)
            reason = (f"cell {cell} n={len(group)} base_brier={briers['baseline']:.4f} "
                      f"icon_brier={briers['candidate']:.4f} -> {arm}")
            eligible_flag = True
        else:
            arm = global_arm
            reason = (f"cell {cell} n={len(group)} < {MIN_CELL_N}: fallback to global "
                      f"({global_arm} {global_brier[global_arm]:.4f})")
            eligible_flag = False
        selector_table[cell] = {"arm": arm, "n": int(len(group)), "brier_baseline": briers["baseline"],
                                "brier_candidate": briers["candidate"], "eligible": eligible_flag,
                                "reason": reason}
    (OUT / "selector_table.json").write_text(json.dumps(
        {"min_cell_n": MIN_CELL_N, "global_arm": global_arm, "global_brier": global_brier,
         "blocks": {"early_base_fit": f"label_avail < {B1.isoformat()}",
                    "blend_validation": f"{B1.isoformat()} <= issue < {B2.isoformat()}, label_avail < {B2.isoformat()}",
                    "selector_validation": f"{B2.isoformat()} <= issue < {start.isoformat()}, label_avail < {start.isoformat()}",
                    "test": "October issues, label_avail < Nov 1"},
         "cells": selector_table}, indent=2, default=str))
    print(f"SELECTOR cells {len(selector_table)} global={global_arm} "
          f"({global_brier[global_arm]:.4f}); eligible={sum(1 for c in selector_table.values() if c['eligible'])}",
          flush=True)

    # ---- October scoring: fixed arms + equalblend + selector + baselines, same rows ----
    predictions = {"baseline_raw": b_raw, "baseline_blend": b_blend, "icon_raw": c_raw,
                   "icon_blend": c_blend, "equalblend": 0.5 * b_blend + 0.5 * c_blend,
                   "persistence": test_rows.od_at_issue.to_numpy(float),
                   "rules": test_rows.rule_od25.to_numpy(float)}
    test_cells = blend_keys(test_rows)
    arm_of = {cell: spec["arm"] for cell, spec in selector_table.items()}
    test_arm = pd.Series(test_cells).map(arm_of)
    unmapped_cells = sorted(set(test_cells) - set(selector_table))
    if unmapped_cells:
        print(f"SELECTOR cells unseen in Sep OOF (global fallback): {unmapped_cells}", flush=True)
    test_arm = test_arm.fillna(global_arm)
    assert test_arm.isin(("baseline", "candidate")).all()
    # POLICY TRANSFER, labelled: the cell rule was learned on Sep OOF from the
    # early-frozen models, but `selector` applies it to refitted CORE Oct probs.
    # `selector_frozen` instead applies the same rule to early-model Oct probs
    # (fully frozen pipeline, inference only). `global_arm` is the Sep-frozen
    # single arm for every Oct row -- the comparator for cell selection value.
    _, fb_blend = blended(early_models["baseline"], BASE_FEATURES, test_rows)
    _, fc_blend = blended(early_models["candidate"], CAND_FEATURES, test_rows)
    predictions["selector"] = np.where(test_arm.to_numpy() == "candidate", c_blend, b_blend)
    predictions["selector_frozen"] = np.where(test_arm.to_numpy() == "candidate", fc_blend, fb_blend)
    predictions["global_arm"] = fc_blend if global_arm == "candidate" else fb_blend
    for values in predictions.values():
        assert len(values) == len(test_rows) and np.isfinite(values).all()
        assert ((values >= 0) & (values <= 1)).all()
    common = test_rows[["y_od", "rule_od25", "od_at_issue"]].notna().all(axis=1)
    scored = test_rows.loc[common].copy()
    assert (scored[ICON_COLS[:-1]].notna().mean() > 0.99).all(), "scored supplemental non-missing > 99%"
    scored["selector_cell"] = test_cells[common.to_numpy()]
    scored["selector_arm"] = test_arm.to_numpy()[common.to_numpy()]
    scored["selector_eligible"] = scored["selector_cell"].map(
        {cell: spec["eligible"] for cell, spec in selector_table.items()}).fillna(False)
    _reason_of = {cell: spec["reason"] for cell, spec in selector_table.items()}
    scored["selector_reason"] = scored["selector_cell"].map(_reason_of).fillna(
        f"cell unseen in Sep OOF: fallback to global ({global_arm})")
    scored["p_frozen_baseline"] = fb_blend[common.to_numpy()]
    scored["p_frozen_candidate"] = fc_blend[common.to_numpy()]
    scored["model_run_id"] = RUN_ID
    records = []
    for name, values in predictions.items():
        scored[name] = values[common.to_numpy()]
        cand_frame = scored.assign(p_od25=scored[name], p_od25_raw=scored[name])
        slices = {"all_recorded": cand_frame,
                  "suspect_excluded_sensitivity": training.without_stuck_feed(cand_frame),
                  "midnight_issues": cand_frame.loc[cand_frame.issue_time.dt.tz_convert(
                      "Europe/Berlin").dt.hour.eq(0)]}
        for slice_name, subset in slices.items():
            for row in skill(subset, "od"):
                records.append(dict(method=name, slice=slice_name, lead_h=row["lead_h"], n=row["n"],
                                    accuracy=row["model_acc"], brier=row["model_brier"],
                                    changed_n=row["change_n"],
                                    changed_accuracy=row["model_change_acc"]))
    summary = pd.DataFrame(records)
    piv = summary.pivot_table(index=["slice", "lead_h"], columns="method", values="n", observed=True)
    assert (piv.nunique(axis=1) == 1).all(), "arms diverge in row footprint (S5)"
    assert len(summary) == 10 * 3 * 4, len(summary)
    sample = scored.loc[scored.lead_h.eq(6)]
    rep = summary.query("method == 'icon_blend' and slice == 'all_recorded' and lead_h == 6").iloc[0]
    assert np.isclose(rep.accuracy, ((sample.icon_blend >= .5) == sample.y_od).mean())
    assert np.isclose(rep.brier, ((sample.icon_blend - sample.y_od) ** 2).mean())
    summary.to_csv(OUT / "metrics.csv", index=False)
    scored.to_parquet(OUT / "per_row_traces.parquet", index=False)
    joblib.dump({"baseline": baseline, "candidate": candidate,
                 "early_baseline_od": early_models["baseline"], "early_candidate_od": early_models["candidate"],
                 "selector_table": selector_table,
                 "baseline_features": list(BASE_FEATURES), "candidate_features": CAND_FEATURES},
                OUT / "models.joblib", compress=3)
    r18pop = test_rows.dropna(subset=["y_r18", "rule_18_usable", "persistence_18"]).copy()
    assert len(r18pop) > 0, "empty R18 population"
    r18pop["p18_baseline"] = probability(baseline["r18"], r18pop[BASE_FEATURES])
    r18pop["p18_candidate"] = probability(candidate["r18"], r18pop[CAND_FEATURES])
    assert np.isfinite(r18pop[["p18_baseline", "p18_candidate"]].to_numpy()).all()
    r18pop["model_run_id"] = RUN_ID
    r18 = {"baseline_blend": r18_events(r18pop.assign(p_18_usable=r18pop["p18_baseline"])),
           "icon_blend": r18_events(r18pop.assign(p_18_usable=r18pop["p18_candidate"]))}
    (OUT / "r18_events.json").write_text(json.dumps(r18, indent=2, default=str))
    r18pop[["issue_time", "time", "lead_h", "y_r18", "p18_baseline", "p18_candidate",
            "rule_18_usable", "persistence_18", "model_run_id"]].to_parquet(
                OUT / "r18_traces.parquet", index=False)
    print(f"R18 population: {len(r18pop)} rows (separate from OD-scored {len(scored)})", flush=True)
    file_hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                   for folder in (ROOT / "ml", ROOT / "data") for p in folder.rglob("*")
                   if p.is_file() and "__pycache__" not in p.parts}
    file_hashes["icon_supplement.py"] = args.adapter_sha
    file_hashes["resources/ml-support/forecast/normalized/open-meteo-icon-global.csv"] = \
        hashlib.sha256(ICON_CSV.read_bytes()).hexdigest()
    manifest = {"source_commit": args.rev, "source_archive_sha256": args.archive_sha,
      "adapter_sha256": args.adapter_sha, "publication_lag_h": args.lag,
      "offsets_day1_day2_day3": EXPECTED_OFFSETS[args.lag], "model_run_id": RUN_ID,
      "experiment": "CORE: v5 baseline (metadata base feats) vs v5+ICON-raw (+7) on identical 2025+ full-48h issues; Oct exploratory only. SELECTOR: leadxregime best-arm by valid-label Sep-OOF Brier (n>=50 else global), applied to Oct as policy-transfer + frozen-pipeline variants, with a validation-frozen global-arm comparator; experimental postprocess, not a decision API.",
      "baseline_features": list(BASE_FEATURES), "candidate_features": CAND_FEATURES,
      "supplemental_scaling": "raw ICON knots via adapter scale=1.0 default; no fitted bias (S4)",
      "alignment_day1_vs_metar": {"r_shift_minus24h": rm, "r_shift0": r0, "r_shift_plus24h": rp,
                                  "n_pairs": len(grid)},
      "full_build_rows": len(frame), "candidate_issues": len(candidate_issues),
      "complete_issues": len(complete_issues), "eligible_rows": len(eligible),
      "train_rows": len(fit_rows), "test_rows": len(test_rows), "scored_rows": len(scored),
      "selector_blocks": {"early_rows": len(early_rows), "blendval_rows": len(blendval_rows),
                          "selval_rows": len(selval_rows)},
      "selector_global_arm": global_arm, "selector_global_brier": global_brier,
      "oof_valid_rows": len(oof), "oof_excluded_nan": oof_excluded,
      "r18_pop_rows": len(r18pop), "od_scored_rows": len(scored),
      "methods": sorted(summary.method.unique()),
      "selector_transfer": "cell rule learned on Sep OOF from early-frozen models; "
        "'selector' applies it to refitted core Oct probs (POLICY TRANSFER); "
        "'selector_frozen' applies it to early-model Oct probs (frozen pipeline); "
        "'global_arm' is the Sep-frozen single arm for all Oct rows (cell-value comparator)",
      "selector_unmapped_oct_cells": unmapped_cells,
      "selector_exports": ["oof_selector_validation.parquet", "selector_table.json"],
      "train_label_end": fit_rows.label_available_at.max().isoformat(),
      "test_issue_start": test_rows.issue_time.min().isoformat(),
      "test_issue_end": test_rows.issue_time.max().isoformat(), "skipped_issues": skipped,
      "blend_validation_start": baseline["od_blend_validation_start"],
      "python": platform.python_version(), "sklearn": sklearn.__version__,
      "pandas": pd.__version__, "numpy": np.__version__, "elapsed_s": time.time() - started,
      "limitations": [
        "2025+ full-48h issue eligibility drops 2024 training rows for BOTH arms; committed full-history v5 Oct numbers are a separate reference, never a gain claim",
        "October already used in development, not a pristine final lockbox; no selection on Oct (selector from Sep OOF only)",
        "Both lags are 6h/12h day-band proxies; this does not prove historical publication times. Compare arms only within the same lag",
        "suspect_excluded_sensitivity is hindsight-cleaned (whole-run flag); headline all_recorded is primary",
        "Selector is an experimental postprocess rule, separate from any deployed decision API; OD Brier only, no delay labels added to OD",
        "Overlapping forecast rows are correlated; no significance claim",
        "R18 scored on its own valid-label population (r18_traces.parquet), not the OD-scored rows; reported via r18_events only, no closure-skill claim from OD accuracy"],
      "file_sha256": file_hashes}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str))
    print(summary.query("slice == 'all_recorded'").round(5).to_string(index=False))
    print("Primary: Brier 6/24/48 h; guardrail: 1 h non-degradation; slices: headline + hindsight-cleaned + midnight (S6/S8)")
    print("EXPERIMENT_COMPLETE", f"lag={args.lag}", round(time.time() - started, 1), "seconds", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
