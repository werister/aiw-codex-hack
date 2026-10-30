"""Train two classifiers and write monthly walk-forward quality artifacts.

Run python -m ml.train. Cached source files must already be present in data/.
"""

import argparse
import hashlib
import json
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance

from ml.features import BERLIN, FEATURES, PUBLICATION_LAG_H, build_features, normalize_obs
from ml.predict import HORIZONS, REGIMES, blend_keys, od_probability, probability, r18_probability
from ml.quality import next_change_timing, od_change_events, period, r18_events, reliability, skill, suspect_od_runs
from ml.rules import RULES, od_state_machine, r18_usable
from ml.significance import compare

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUT = ROOT / "web" / "public" / "data"
MODELS = ROOT / "ml" / "models"
MODEL_VERSION = "walk-forward-v6"


def load_truth():
    truth = pd.read_csv(DATA / "ground_truth" / "dfld_hourly.csv", dtype={"od": str})
    truth["time"] = pd.to_datetime(truth.time, utc=True).astype("datetime64[ns, UTC]")
    truth = truth.sort_values("time")
    truth["available_at"] = truth.time + pd.Timedelta(hours=1)
    return truth


def issue_times(start, end, stride):
    """Issues on the local clock from 00:00, so jury-style midnight issues are trained and tested."""
    days = pd.date_range(start.tz_convert(BERLIN).date(), end.tz_convert(BERLIN).date(), freq="D")
    local = (days.to_numpy()[:, None] + pd.to_timedelta(np.arange(0, 24, stride), unit="h").to_numpy()).ravel()
    times = pd.DatetimeIndex(local).tz_localize(BERLIN, ambiguous="NaT", nonexistent="NaT").dropna().tz_convert("UTC")
    return times[(times >= start) & (times <= end)]


def archived_inputs():
    """Best-match previous runs plus separate models and pressure boxes, all day1/2/3 offsets."""
    nwp = pd.read_parquet(DATA / "openmeteo_previous_runs.parquet")
    for name in ("openmeteo_previous_runs_multimodel.parquet", "openmeteo_previous_runs_pressure.parquet"):
        if (DATA / name).exists():
            nwp = nwp.merge(pd.read_parquet(DATA / name), on="time", how="left", validate="one_to_one")
    nwp["time"] = pd.to_datetime(nwp.time, utc=True)
    return nwp.sort_values("time").reset_index(drop=True)


def dataset(stride=6):
    truth = load_truth()
    obs = normalize_obs(pd.read_parquet(DATA / "eddf_metar.parquet"))
    obs["time"] = obs.time.astype("datetime64[ns, UTC]")
    truth["suspect"] = suspect_od_runs(truth, obs)
    print(f"Flagged {int(truth.suspect.sum())} recorded hours for rule-disagreement sensitivity", flush=True)
    nwp = archived_inputs()
    times = issue_times(max(truth.available_at.min(), nwp.time.min()),
                        min(truth.time.max(), nwp.time.max()) - pd.Timedelta(hours=48), stride)
    target_obs = pd.merge_asof(truth[["time"]], obs[["time", "wind_kt", "wind_dir_deg", "gust_kt"]],
                               on="time", tolerance=pd.Timedelta(hours=1))
    truth["y_r18"] = [r18_usable(s, d, g) for s, d, g in target_obs[["wind_kt", "wind_dir_deg", "gust_kt"]].itertuples(index=False, name=None)]
    truth["y_od"] = truth.od.eq("25").astype(int)
    truth["change_count"] = truth.od.ne(truth.od.shift()).cumsum()
    target = truth.set_index("time")
    frames = []
    skipped = 0
    for number, issue in enumerate(times):
        known = truth.loc[truth.available_at <= issue]
        if known.empty or issue - known.available_at.iloc[-1] > pd.Timedelta(hours=2):
            skipped += 1
            continue
        try:
            obs_start = obs.time.searchsorted(issue - pd.Timedelta(hours=5))
            obs_end = obs.time.searchsorted(issue, side="right")
            nwp_start = nwp.time.searchsorted(issue, side="right")
            nwp_end = nwp.time.searchsorted(issue + pd.Timedelta(hours=48), side="right")
            frame = build_features(issue, obs.iloc[obs_start:obs_end], nwp.iloc[nwp_start:nwp_end], known.od.iloc[-1], known)
        except ValueError:
            skipped += 1
            continue
        labels = target.reindex(frame.time)
        frame["y_od"] = labels.y_od.to_numpy()
        frame["y_r18"] = pd.to_numeric(labels.y_r18).to_numpy()
        frame["label_available_at"] = frame.time + pd.Timedelta(hours=1)
        frame["changed_within_lead"] = labels.change_count.to_numpy() > known.change_count.iloc[-1]
        # Row selection only, never a feature: the flag uses the whole recorded run.
        frame["suspect_target"] = labels.suspect.astype("boolean").fillna(False).to_numpy(bool)
        frame["suspect_input"] = bool(known.suspect.iloc[-1])
        frames.append(frame)
        if number % 500 == 0:
            print(f"Features {number}/{len(times)} issue times", flush=True)
    if not frames:
        raise ValueError("No complete issue trajectories in cached data")
    frame = pd.concat(frames, ignore_index=True)
    print(f"Dataset {len(frame):,} rows, {len(frames):,} issues; {skipped} skipped", flush=True)
    return frame, truth, obs, skipped


def cached_dataset(stride):
    """Keep repeat runs cheap without placing development caches in commits."""
    import tempfile

    sources = [DATA / "ground_truth" / "dfld_hourly.csv", DATA / "eddf_metar.parquet",
               DATA / "openmeteo_previous_runs.parquet", DATA / "openmeteo_previous_runs_multimodel.parquet",
               DATA / "openmeteo_previous_runs_pressure.parquet", Path(__file__), ROOT / "ml" / "features.py",
               ROOT / "ml" / "rules.py", ROOT / "ml" / "rules.json", ROOT / "ml" / "quality.py"]
    signature = str(stride) + "".join(f"{p.name}:" + (hashlib.sha256(p.read_bytes()).hexdigest()
                                                    if p.exists() else "absent") for p in sources)
    digest = hashlib.sha256(signature.encode()).hexdigest()[:16]
    cache = Path(tempfile.gettempdir()) / f"eddf-features-{digest}.joblib"
    if cache.exists():
        print("Using cached issue-time features", flush=True)
        return joblib.load(cache)
    result = dataset(stride)
    joblib.dump(result, cache, compress=1)
    return result


def without_stuck_feed(frame):
    """Sensitivity only: unlabel OD rows associated with flagged rule contradictions."""
    frame = frame.copy()
    frame.loc[frame.suspect_target | frame.suspect_input, "y_od"] = np.nan
    return frame


def fit_classifiers(frame):
    models = {}
    for name, label in (("od", "y_od"), ("r18", "y_r18")):
        rows = frame.dropna(subset=[label])
        model = HistGradientBoostingClassifier(max_iter=80, max_leaf_nodes=15, learning_rate=0.08,
            l2_regularization=10, min_samples_leaf=50, early_stopping=False, random_state=42)
        model.fit(rows[FEATURES], rows[label].astype(int))
        models[name] = model
    return models


def fit(frame):
    # Choose persistence weights on an earlier, chronological validation block.
    # The external walk-forward test month never selects these weights.
    validation_start = frame.issue_time.max() - pd.Timedelta(days=60)
    earlier = frame.loc[frame.label_available_at < validation_start]
    validation_all = frame.loc[frame.issue_time >= validation_start]
    validation = validation_all.dropna(subset=["y_od"])
    candidates = fit_classifiers(earlier)
    raw = probability(candidates["od"], validation[FEATURES])
    y = validation.y_od.to_numpy(float)
    prior = validation.od_at_issue.to_numpy(float)
    keys = blend_keys(validation)

    def best_alpha(selected):
        if not selected.any():
            return 1.0
        losses = [(float(np.mean((alpha * raw[selected] + (1 - alpha) * prior[selected] - y[selected]) ** 2)), alpha)
                  for alpha in np.round(np.linspace(0, 1, 11), 1)]
        return float(min(losses)[1])

    weights = {}
    for horizon in HORIZONS:
        fallback = best_alpha(np.char.startswith(keys, horizon + ":"))
        for regime in REGIMES:
            # Night and calm hours may lean on persistence; sparse regimes use the lead weight.
            selected = keys == f"{horizon}:{regime}"
            weights[f"{horizon}:{regime}"] = best_alpha(selected) if selected.sum() >= 50 else fallback
    models = fit_classifiers(frame)
    models["od_model_weight"] = weights
    models["od_blend_validation_period"] = period(validation.issue_time)
    r18_validation = validation_all.dropna(subset=["y_r18", "persistence_18"])
    r18_raw = (probability(candidates["r18"], r18_validation[FEATURES])
               if len(r18_validation) else np.array([], dtype=float))
    r18_prior = r18_validation.persistence_18.to_numpy(float)
    r18_y = r18_validation.y_r18.to_numpy(float)
    r18_horizon = np.select([r18_validation.lead_h <= 1, r18_validation.lead_h <= 6,
                            r18_validation.lead_h <= 24], HORIZONS[:3], default=HORIZONS[3])
    r18_weights, support = {}, {}
    for horizon in HORIZONS:
        selected = r18_horizon == horizon
        support[horizon] = {"n": int(selected.sum()), "closed_rows": int((r18_y[selected] == 0).sum())}
        # A closure-free validation set cannot justify a pure-open persistence forecast.
        if selected.sum() < 50 or not (r18_y[selected] == 0).any():
            r18_weights[horizon] = 1.0
            continue
        losses = [(float(np.mean((alpha * r18_raw[selected] + (1 - alpha) * r18_prior[selected]
                                  - r18_y[selected]) ** 2)), alpha)
                  for alpha in np.round(np.linspace(0, 1, 11), 1)]
        r18_weights[horizon] = float(min(losses)[1])
    models["r18_model_weight"] = r18_weights
    models["r18_blend_validation_period"] = period(r18_validation.issue_time) if len(r18_validation) else None
    models["r18_blend_validation_support"] = support
    return models


def predict(models, frame):
    frame = frame.copy()
    frame["p_od25_raw"] = probability(models["od"], frame[FEATURES])
    frame["p_od25"] = od_probability(models, frame)
    frame["p_18_usable_raw"] = probability(models["r18"], frame[FEATURES])
    frame["p_18_usable"] = r18_probability(models, frame)
    return frame


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def ensemble_skill(frame):
    compared = frame.assign(rule_od25=frame.rule_od25_ens, rule_18_usable=frame.rule_18_ens)
    return {name: skill(compared, name) for name in ("od", "r18")}


def evaluate(frame, truth, obs, months, stride, skipped, compare_label_policy=False):
    last_month = frame.issue_time.max().tz_localize(None).to_period("M")
    folds, oos, ins, excluded_fit_oos = [], [], [], []
    sensitivity_folds = []
    final_fold_models = None
    for month in pd.period_range(last_month - months + 1, last_month, freq="M"):
        start = month.start_time.tz_localize("UTC")
        end = (month + 1).start_time.tz_localize("UTC")
        # Purge outcomes crossing the boundary, including the label's full hour.
        train = frame.loc[frame.label_available_at < start]
        test = frame.loc[(frame.issue_time >= start) & (frame.issue_time < end) & (frame.label_available_at < end)]
        if train.empty or test.empty:
            raise ValueError(f"Insufficient data for monthly fold {month}")
        assert train.label_available_at.max() < test.issue_time.min()
        models = fit(train)
        models["od_training_label_policy"] = "all-recorded"
        models["trained_through"] = train.label_available_at.max().isoformat()
        models["version"] = MODEL_VERSION
        models["publication_lag_h"] = PUBLICATION_LAG_H
        MODELS.mkdir(parents=True, exist_ok=True)
        joblib.dump(models, MODELS / f"fold-{month}.joblib", compress=3)
        train_predictions = predict(models, train)
        test_predictions = predict(models, test)
        if compare_label_policy:
            filtered = without_stuck_feed(train)
            if train.y_od.equals(filtered.y_od):
                excluded_fit_oos.append(test_predictions.copy())
                sensitivity_folds.append({"month": str(month), "status": "identical_training_labels"})
            else:
                inner_start = filtered.issue_time.max() - pd.Timedelta(days=60)
                earlier = filtered.loc[filtered.label_available_at < inner_start]
                validation = filtered.loc[filtered.issue_time >= inner_start]
                if earlier.y_od.dropna().empty or validation.y_od.dropna().empty:
                    sensitivity_folds.append({"month": str(month), "status": "skipped_no_od_labels"})
                else:
                    alternative = fit(filtered)
                    excluded_fit_oos.append(predict(alternative, test))
                    sensitivity_folds.append({"month": str(month), "status": "refitted"})
        # All train rows are scored; aggregate reports repeated expanding-window
        # fits explicitly, rather than presenting a single independent sample.
        ins.append(train_predictions)
        oos.append(test_predictions)
        folds.append({"month": str(month), "train_period": period(train.issue_time),
            "train_target_end": train.label_available_at.max().isoformat(), "test_period": period(test.issue_time),
            "train_n": len(train), "test_n": len(test),
            "od_model_weight": models["od_model_weight"],
            "od_blend_validation_period": models["od_blend_validation_period"],
            "r18_model_weight": models["r18_model_weight"],
            "r18_blend_validation_support": models["r18_blend_validation_support"],
            "in_sample": {name: skill(train_predictions, name) for name in ("od", "r18")},
            "out_of_sample": {name: skill(test_predictions, name) for name in ("od", "r18")},
            "out_of_sample_stuck_feed_excluded": {"od": skill(without_stuck_feed(test_predictions), "od")}})
        print(f"Walk-forward {month}: train {len(train):,}, test {len(test):,}", flush=True)
        print(pd.DataFrame(skill(test_predictions, "od"))[["lead_h", "n", "raw_model_acc", "blend_acc", "rule_acc", "persistence_acc", "blend_brier"]].to_string(index=False), flush=True)
        final_fold_models = models
    out = pd.concat(oos, ignore_index=True)
    inside = pd.concat(ins, ignore_index=True)
    # Permutations use only the final held-out month and its preceding fit.
    labelled = oos[-1].dropna(subset=["y_od"])
    heldout = labelled.sample(n=min(5000, len(labelled)), random_state=42)
    def blended_score(estimator, features, labels):
        # Blend regimes need the target time, which is not a model feature.
        features = features.assign(time=heldout.time.loc[features.index])
        p = od_probability({"od": estimator, "od_model_weight": final_fold_models["od_model_weight"]}, features)
        return -float(np.mean((p - labels.to_numpy(float)) ** 2))

    permutation = permutation_importance(final_fold_models["od"], heldout[FEATURES], heldout.y_od.astype(int),
        scoring=blended_score, n_repeats=3, random_state=42, n_jobs=1)
    drivers = sorted([{"feature": feature, "importance": float(value)}
                      for feature, value in zip(FEATURES, permutation.importances_mean)],
                     key=lambda row: row["importance"], reverse=True)[:10]
    # Day-clustered bootstrap CIs, McNemar and Diebold-Mariano against both baselines.
    significance = {"od": compare(out, "od"), "od_stuck_feed_excluded": compare(without_stuck_feed(out), "od"),
                    "r18": compare(out, "r18")}
    sensitivity = {"primary_training_policy": "all-recorded", "test_policy": "all-recorded",
                   "rule_disagreement_filter_is_verified_feed_failure": False,
                   "same_test_rows": len(excluded_fit_oos) == len(oos),
                   "comparison_run": compare_label_policy,
                   "complete_comparison": len(excluded_fit_oos) == len(oos), "folds": sensitivity_folds}
    if len(excluded_fit_oos) == len(oos):
        alternative_out = pd.concat(excluded_fit_oos, ignore_index=True)
        sensitivity["exclude_flagged_training_od"] = {name: skill(alternative_out, name) for name in ("od", "r18")}
    observed_od = od_state_machine(obs[["time", "wind_dir_deg", "wind_kt", "gust_kt"]].itertuples(index=False, name=None))
    observed = obs[["time"]].assign(rule_od=observed_od)
    comparison = pd.merge_asof(truth, observed, on="time", tolerance=pd.Timedelta(hours=2)).dropna(subset=["rule_od"])
    elapsed_years = (truth.time.max() - truth.time.min()).total_seconds() / (365.25 * 86400)
    changes = int(truth.od.ne(truth.od.shift()).sum() - 1)
    base_rates = {"od25_share": float(truth.y_od.mean()), "changes_per_year": changes / elapsed_years,
                  "r18_closed_share": float(1 - pd.to_numeric(truth.y_r18).mean())}
    backtest = {"train_period": folds[-1]["train_period"], "test_period": period(out.issue_time),
        "model_version": MODEL_VERSION, "training_label_policy": "all-recorded",
        "labels": "OD: recorded DFLD stable-hour proxy. Runway 18: inferred from METAR and official wind limits.",
        "rules_version": RULES["version"], "base_rates": base_rates,
        "od": skill(out, "od"), "r18": skill(out, "r18"), "drivers": drivers,
        "od_stuck_feed_excluded": skill(without_stuck_feed(out), "od"),
        "significance": significance,
        "ensemble_rule_comparison": ensemble_skill(out), "label_policy_sensitivity": sensitivity,
        "r18_events": r18_events(out),
        "r18_label_type": "inferred", "publication_lag_h": PUBLICATION_LAG_H,
        "served_prediction": "blend", "model_fields": "model_* aliases blend_*; raw_model_* scores the unblended classifier"}
    half_hour = pd.read_csv(DATA / "ground_truth" / "dfld_half_hourly.csv.gz", dtype={"od": str})
    local = (pd.to_datetime(half_hour.date_local) + pd.to_timedelta(half_hour.hour_local, unit="h")
             + pd.to_timedelta(half_hour.minute_local, unit="m"))
    half_hour["time"] = local.dt.tz_localize("Europe/Berlin", ambiguous="NaT", nonexistent="NaT").dt.tz_convert("UTC")
    half_hour = half_hour.dropna(subset=["time"])
    quality = {"schema_version": 1, "evaluation": "expanding monthly walk-forward",
        "model_version": MODEL_VERSION, "training_label_policy": "all-recorded",
        "r18_label_type": "inferred", "issue_stride_h": stride, "folds": folds,
        "publication_lag_h": PUBLICATION_LAG_H,
        "forecast_offsets": [{"lead_start": 1, "lead_end": 18, "previous_day": 1},
                             {"lead_start": 19, "lead_end": 42, "previous_day": 2},
                             {"lead_start": 43, "lead_end": 48, "previous_day": 3}],
        "in_sample": {name: skill(inside, name) for name in ("od", "r18")},
        "out_of_sample": {name: skill(out, name) for name in ("od", "r18")},
        "out_of_sample_stuck_feed_excluded": {"od": skill(without_stuck_feed(out), "od")},
        "significance": significance,
        "ensemble_rule_comparison": ensemble_skill(out), "label_policy_sensitivity": sensitivity,
        "r18_events": r18_events(out),
        "reliability": {name: reliability(out, name) for name in ("od", "r18")},
        "confidence_reliability": {name: reliability(out, name, confidence=True) for name in ("od", "r18", "combined")},
        "certainty_reliability": reliability(out, "certainty"),
        "next_change": next_change_timing(out, half_hour), "od_change_events": od_change_events(out, half_hour),
        "drivers": drivers,
        "rule_label_comparison": {"n": len(comparison), "agreement": float(comparison.od.eq(comparison.rule_od).mean())},
        "data_sources": [
            {"name": "DFLD recorded operating directions", "url": "https://www.dfld.de/Mess/StatWetter.php?R=1&D=01.10.2026", "file": "data/ground_truth/dfld_hourly.csv"},
            {"name": "IEM EDDF METAR", "url": "https://mesonet.agron.iastate.edu/request/download.phtml", "file": "data/eddf_metar.parquet"},
            {"name": "Open-Meteo previous runs", "url": "https://open-meteo.com/en/docs/previous-runs-api", "file": "data/openmeteo_previous_runs.parquet"}],
        "coverage": {"feature_rows": len(frame), "skipped_issue_times": skipped, "observed_base_rates": base_rates,
                     "stuck_feed_hours": int(truth.suspect.sum()),
                     "stuck_feed_period": period(truth.time[truth.suspect]) if truth.suspect.any() else None},
        "limitations": [
            "A six-hour publication lag is applied: previous_day1 for leads 1-18, day2 for 19-42, day3 for 43-48. Each target time minus its offset plus six hours must be no later than issue time. Exact publication timestamps remain unavailable; the six-hour lag is a conservative availability assumption.",
            "DFLD hourly OD is used only after hour end. Upstream publication delays and summer clock offset remain unverified. Recorded OD is a public operational proxy, not a certified movement log.",
            "Stable-hour OD accuracy excludes DFLD transition hours. Next-change scoring instead uses the half-hour source and excludes incomplete windows.",
            "Runway 18 targets are inferred weather usability; missing or variable METAR directions are unlabelled, not assumed open.",
            "In-sample aggregates repeat rows across expanding folds. OOS monthly folds do not overlap; overlapping 48-hour forecast windows are correlated.",
            "Timing metrics use 6-hourly issue windows; od_change_events separately deduplicates events and matches warnings. OD and R18 persistence weights minimize Brier score on a preceding 60-day validation block; held-out data never selects weights. Sparse or closure-free R18 validation retains the raw model.",
            "Issues run every six hours on the Europe/Berlin clock from 00:00, matching jury-day issues. Blend weights are chosen per lead bucket (1, 2-6, 7-24, 25-48 h) and target regime: night (23:00-05:00 local), calm (forecast 10 m wind below 2.5 kt) or active.",
            "Inputs add ECMWF IFS, GFS and ICON previous runs and forecast pressure about 200 km N/S/W/E of FRA, under the same day1/day2/day3 offsets and six-hour lag. Wind speeds are scaled to METAR level with ratios fitted on 2024 only, before every test month. ICON-D2 ensemble spread has no archive before 29 Jul 2026 and is not used.",
            "Runway 18 events require complete labelled issue windows and comparable available predictions. Counts describe overlapping positive issue windows, not unique closure episodes; unknown or missing windows are excluded explicitly.",
            "OD runs with repeated 10 kt landing-tailwind contradictions are flagged for sensitivity, not proven feed failure. Primary training and scoring retain all recorded labels. Additional exclusion scores and optional excluded-label refits are explicitly separate and do not choose the primary model."]}
    dump(OUTPUT / "backtest.json", backtest)
    dump(OUTPUT / "quality.json", quality)
    return backtest, quality


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--issue-stride", type=int, default=6)
    parser.add_argument("--months", type=int, default=12)
    parser.add_argument("--compare-label-policy", action="store_true",
                        help="Also refit each fold excluding rule-disagreement OD labels; score identical test rows")
    args = parser.parse_args()
    if args.issue_stride < 1 or 24 % args.issue_stride or args.months < 6:
        parser.error("issue-stride must divide 24 hours and months must be at least six")
    warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*generic.*")
    frame, truth, obs, skipped = cached_dataset(args.issue_stride)
    backtest, quality = evaluate(frame, truth, obs, args.months, args.issue_stride, skipped, args.compare_label_policy)
    models = fit(frame)
    models["od_training_label_policy"] = "all-recorded"
    models["features"] = FEATURES
    models["trained_through"] = frame.label_available_at.max().isoformat()
    models["version"] = MODEL_VERSION
    models["publication_lag_h"] = PUBLICATION_LAG_H
    MODELS.mkdir(parents=True, exist_ok=True)
    joblib.dump(models, MODELS / "forecast.joblib", compress=3)
    dump(MODELS / "metadata.json", {"version": models["version"], "features": FEATURES,
        "trained_through": models["trained_through"], "n": len(frame), "r18_label_type": "inferred",
        "od_model_weight": models["od_model_weight"], "od_blend_validation_period": models["od_blend_validation_period"],
        "od_training_label_policy": models["od_training_label_policy"],
        "r18_model_weight": models["r18_model_weight"],
        "r18_blend_validation_period": models["r18_blend_validation_period"],
        "r18_blend_validation_support": models["r18_blend_validation_support"],
        "publication_lag_h": PUBLICATION_LAG_H})
    print("Outputs written to web/public/data/; final models saved to ml/models/", flush=True)
    print("Observed base rates, runway 18 inferred:", json.dumps(backtest["base_rates"]), flush=True)
    columns = ["lead_h", "n", "blend_acc", "rule_acc", "persistence_acc", "blend_brier", "persistence_brier"]
    print("All recorded hours:", pd.DataFrame(backtest["od"])[columns].to_string(index=False), sep="\n", flush=True)
    print("Rule-disagreement sensitivity (flagged hours excluded):", pd.DataFrame(backtest["od_stuck_feed_excluded"])[columns].to_string(index=False),
          sep="\n", flush=True)


if __name__ == "__main__":
    main()
