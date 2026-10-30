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

from ml.features import FEATURES, build_features, normalize_obs
from ml.predict import probability
from ml.quality import next_change_timing, period, reliability, skill
from ml.rules import RULES, od_state_machine, r18_usable

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUT = ROOT / "web" / "public" / "data"
MODELS = ROOT / "ml" / "models"


def load_truth():
    truth = pd.read_csv(DATA / "ground_truth" / "dfld_hourly.csv", dtype={"od": str})
    truth["time"] = pd.to_datetime(truth.time, utc=True)
    truth = truth.sort_values("time")
    truth["available_at"] = truth.time + pd.Timedelta(hours=1)
    return truth


def dataset(stride=6):
    truth = load_truth()
    obs = normalize_obs(pd.read_parquet(DATA / "eddf_metar.parquet"))
    nwp = pd.read_parquet(DATA / "openmeteo_previous_runs.parquet")
    nwp["time"] = pd.to_datetime(nwp.time, utc=True)
    nwp = nwp.sort_values("time")
    times = pd.date_range(max(truth.available_at.min(), nwp.time.min()),
                          min(truth.time.max(), nwp.time.max()) - pd.Timedelta(hours=48), freq=f"{stride}h")
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
               DATA / "openmeteo_previous_runs.parquet", Path(__file__), ROOT / "ml" / "features.py"]
    signature = str(stride) + "".join(f"{p}:{p.stat().st_size}:{p.stat().st_mtime_ns}" for p in sources)
    digest = hashlib.sha256(signature.encode()).hexdigest()[:16]
    cache = Path(tempfile.gettempdir()) / f"eddf-features-{digest}.joblib"
    if cache.exists():
        print("Using cached issue-time features", flush=True)
        return joblib.load(cache)
    result = dataset(stride)
    joblib.dump(result, cache, compress=1)
    return result


def fit(frame):
    models = {}
    for name, label in (("od", "y_od"), ("r18", "y_r18")):
        rows = frame.dropna(subset=[label])
        model = HistGradientBoostingClassifier(max_iter=80, max_leaf_nodes=15, learning_rate=0.08,
            l2_regularization=10, min_samples_leaf=50, early_stopping=False, random_state=42)
        model.fit(rows[FEATURES], rows[label].astype(int))
        models[name] = model
    return models


def predict(models, frame):
    frame = frame.copy()
    frame["p_od25"] = probability(models["od"], frame[FEATURES])
    frame["p_18_usable"] = probability(models["r18"], frame[FEATURES])
    return frame


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def evaluate(frame, truth, obs, months, stride, skipped):
    last_month = frame.issue_time.max().tz_localize(None).to_period("M")
    folds, oos, ins = [], [], []
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
        models["trained_through"] = train.label_available_at.max().isoformat()
        models["version"] = "walk-forward-v1"
        MODELS.mkdir(parents=True, exist_ok=True)
        joblib.dump(models, MODELS / f"fold-{month}.joblib", compress=3)
        train_predictions = predict(models, train)
        test_predictions = predict(models, test)
        # All train rows are scored; aggregate reports repeated expanding-window
        # fits explicitly, rather than presenting a single independent sample.
        ins.append(train_predictions)
        oos.append(test_predictions)
        folds.append({"month": str(month), "train_period": period(train.issue_time),
            "train_target_end": train.label_available_at.max().isoformat(), "test_period": period(test.issue_time),
            "train_n": len(train), "test_n": len(test),
            "in_sample": {name: skill(train_predictions, name) for name in ("od", "r18")},
            "out_of_sample": {name: skill(test_predictions, name) for name in ("od", "r18")}})
        print(f"Walk-forward {month}: train {len(train):,}, test {len(test):,}", flush=True)
        print(pd.DataFrame(skill(test_predictions, "od"))[["lead_h", "n", "model_acc", "rule_acc", "persistence_acc", "model_brier"]].to_string(index=False), flush=True)
        final_fold_models = models
    out = pd.concat(oos, ignore_index=True)
    inside = pd.concat(ins, ignore_index=True)
    # Permutations use only the final held-out month and its preceding fit.
    labelled = oos[-1].dropna(subset=["y_od"])
    heldout = labelled.sample(n=min(5000, len(labelled)), random_state=42)
    permutation = permutation_importance(final_fold_models["od"], heldout[FEATURES], heldout.y_od.astype(int),
        scoring="neg_brier_score", n_repeats=3, random_state=42, n_jobs=1)
    drivers = sorted([{"feature": feature, "importance": float(value)}
                      for feature, value in zip(FEATURES, permutation.importances_mean)],
                     key=lambda row: row["importance"], reverse=True)[:10]
    observed_od = od_state_machine(obs[["time", "wind_dir_deg", "wind_kt", "gust_kt"]].itertuples(index=False, name=None))
    observed = obs[["time"]].assign(rule_od=observed_od)
    comparison = pd.merge_asof(truth, observed, on="time", tolerance=pd.Timedelta(hours=2)).dropna(subset=["rule_od"])
    elapsed_years = (truth.time.max() - truth.time.min()).total_seconds() / (365.25 * 86400)
    changes = int(truth.od.ne(truth.od.shift()).sum() - 1)
    base_rates = {"od25_share": float(truth.y_od.mean()), "changes_per_year": changes / elapsed_years,
                  "r18_closed_share": float(1 - pd.to_numeric(truth.y_r18).mean())}
    backtest = {"train_period": folds[-1]["train_period"], "test_period": period(out.issue_time),
        "labels": "OD: recorded DFLD stable-hour proxy. Runway 18: inferred from METAR and official wind limits.",
        "rules_version": RULES["version"], "base_rates": base_rates,
        "od": skill(out, "od"), "r18": skill(out, "r18"), "drivers": drivers,
        "r18_label_type": "inferred"}
    half_hour = pd.read_csv(DATA / "ground_truth" / "dfld_half_hourly.csv.gz", dtype={"od": str})
    local = (pd.to_datetime(half_hour.date_local) + pd.to_timedelta(half_hour.hour_local, unit="h")
             + pd.to_timedelta(half_hour.minute_local, unit="m"))
    half_hour["time"] = local.dt.tz_localize("Europe/Berlin", ambiguous="NaT", nonexistent="NaT").dt.tz_convert("UTC")
    half_hour = half_hour.dropna(subset=["time"])
    quality = {"schema_version": 1, "evaluation": "expanding monthly walk-forward",
        "r18_label_type": "inferred", "issue_stride_h": stride, "folds": folds,
        "in_sample": {name: skill(inside, name) for name in ("od", "r18")},
        "out_of_sample": {name: skill(out, name) for name in ("od", "r18")},
        "reliability": {name: reliability(out, name) for name in ("od", "r18")},
        "confidence_reliability": {name: reliability(out, name, confidence=True) for name in ("od", "r18", "combined")},
        "certainty_reliability": reliability(out, "certainty"),
        "next_change": next_change_timing(out, half_hour), "drivers": drivers,
        "rule_label_comparison": {"n": len(comparison), "agreement": float(comparison.od.eq(comparison.rule_od).mean())},
        "data_sources": [
            {"name": "DFLD recorded operating directions", "url": "https://www.dfld.de/Mess/StatWetter.php?R=1&D=01.10.2026", "file": "data/ground_truth/dfld_hourly.csv"},
            {"name": "IEM EDDF METAR", "url": "https://mesonet.agron.iastate.edu/request/download.phtml", "file": "data/eddf_metar.parquet"},
            {"name": "Open-Meteo previous runs", "url": "https://open-meteo.com/en/docs/previous-runs-api", "file": "data/openmeteo_previous_runs.parquet"}],
        "coverage": {"feature_rows": len(frame), "skipped_issue_times": skipped, "observed_base_rates": base_rates},
        "limitations": [
            "Previous-day offsets proxy availability. No original publication timestamps are present; strict publication-before-T cannot be verified, especially at leads 24 and 48 where the proxy equals T.",
            "DFLD hourly OD is used only after hour end. Upstream publication delays and summer clock offset remain unverified. Recorded OD is a public operational proxy, not a certified movement log.",
            "Stable-hour OD accuracy excludes DFLD transition hours. Next-change scoring instead uses the half-hour source and excludes incomplete windows.",
            "Runway 18 targets are inferred weather usability; missing or variable METAR directions are unlabelled, not assumed open.",
            "In-sample aggregates repeat rows across expanding folds. OOS monthly folds do not overlap; overlapping 48-hour forecast windows are correlated.",
            "Timing metrics use 6-hourly issue windows by default, not independent events. No probability recalibration was fitted to held-out data."]}
    dump(OUTPUT / "backtest.json", backtest)
    dump(OUTPUT / "quality.json", quality)
    return backtest, quality


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--issue-stride", type=int, default=6)
    parser.add_argument("--months", type=int, default=6)
    args = parser.parse_args()
    if args.issue_stride < 1 or args.months < 6:
        parser.error("issue-stride must be positive and months must be at least six")
    warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*generic.*")
    frame, truth, obs, skipped = cached_dataset(args.issue_stride)
    backtest, quality = evaluate(frame, truth, obs, args.months, args.issue_stride, skipped)
    models = fit(frame)
    models["features"] = FEATURES
    models["trained_through"] = frame.label_available_at.max().isoformat()
    models["version"] = "walk-forward-v1"
    MODELS.mkdir(parents=True, exist_ok=True)
    joblib.dump(models, MODELS / "forecast.joblib", compress=3)
    dump(MODELS / "metadata.json", {"version": models["version"], "features": FEATURES,
        "trained_through": models["trained_through"], "n": len(frame), "r18_label_type": "inferred"})
    print("Outputs written to web/public/data/; final models saved to ml/models/", flush=True)
    print("Observed base rates, runway 18 inferred:", json.dumps(backtest["base_rates"]), flush=True)
    print(pd.DataFrame(backtest["od"]).to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
