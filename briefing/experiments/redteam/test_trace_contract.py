"""Red-team scratch tests for the v5 trace / evidence / replay contract.

Scope: trace & evidence contract only. Drives the REAL trained walk-forward-v5
model through ml.predict.predict_48h and ml.forecast.evidence (the paths the
shipped unit tests skip, because those use fallback_predict). No training.

Run:
  .scratch/venv/bin/python -m pytest .scratch/test_trace_contract.py -q
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import ml.predict as predict_mod
from ml.features import FEATURES, MULTIMODELS, nwp_offset_days
from ml.predict import predict_48h, file_sha256, MODEL_PATH

REPO = Path(__file__).resolve().parents[3]

# Issue just after the trained_through cutoff so the final forecast.joblib (the
# newest fit with trained_through < issue) is selected.
ISSUE = pd.Timestamp("2026-10-30T00:00Z")


def build_inputs(issue=ISSUE):
    """A fully-populated archived-offset nwp frame + obs + od history.

    Provides day1/2/3 wind, pressure_msl, temperature_2m, wind_speed/dir_80m,
    pressure boxes n/s/w/e, and the three separate models, all offset-suffixed,
    so the v5 feature vector is genuinely populated rather than mostly NaN.
    """
    targets = pd.date_range(issue + pd.Timedelta(hours=1), periods=48, freq="h")
    nwp = pd.DataFrame({"time": targets})
    for day in (1, 2, 3):
        base = {
            "wind_speed_10m": 8.0 + day,
            "wind_direction_10m": 250.0,
            "wind_gusts_10m": 12.0 + day,
            "pressure_msl": 1013.0,
            "temperature_2m": 10.0,
            "wind_speed_80m": 14.0 + day,
            "wind_direction_80m": 250.0,
            "pressure_n": 1012.0, "pressure_s": 1014.0,
            "pressure_w": 1013.0, "pressure_e": 1013.0,
        }
        for name, value in base.items():
            nwp[f"{name}_previous_day{day}"] = value
        for model in MULTIMODELS:
            nwp[f"{model}__wind_speed_10m_previous_day{day}"] = 8.0 + day
            nwp[f"{model}__wind_direction_10m_previous_day{day}"] = 250.0
    nwp["available_at"] = [t - pd.Timedelta(days=nwp_offset_days(lead)) + pd.Timedelta(hours=6)
                           for lead, t in enumerate(targets, 1)]

    obs = pd.DataFrame({
        "time": pd.date_range(issue - pd.Timedelta(hours=4), issue, freq="30min"),
        "wind_dir_deg": 250.0, "wind_kt": 8.0, "gust_kt": 11.0,
    })
    hist_times = pd.date_range(issue - pd.Timedelta(hours=10), periods=12, freq="h")
    history = pd.DataFrame({"time": hist_times,
                            "available_at": hist_times + pd.Timedelta(hours=1),
                            "od": ["25"] * len(hist_times)})
    obs.attrs["od_history"] = history
    return obs, nwp


def test_model_hash_and_version_binding():
    """attrs record the real selected artifact: v5, correct file, true sha256."""
    obs, nwp = build_inputs()
    frame = predict_48h(ISSUE, obs, nwp, "25")
    a = frame.attrs
    assert a["model_version"] == "walk-forward-v5", a["model_version"]
    selected = MODEL_PATH.parent / a["model_file"]
    # The recorded sha256 is the actual bytes of the selected joblib on disk.
    real = hashlib.sha256(selected.read_bytes()).hexdigest()
    assert a["model_sha256"] == real, (a["model_sha256"], real)
    assert a["model_sha256"] == file_sha256(selected)
    assert pd.Timestamp(a["trained_through"]) < ISSUE


def test_feature_order_matches_trained_metadata():
    """Source-snapshot identity: the model's stored feature list IS FEATURES,
    in the same order predict_48h feeds frame[FEATURES]."""
    meta = json.loads((REPO / "ml/models/metadata.json").read_text())
    assert meta["version"] == "walk-forward-v5"
    assert meta["features"] == FEATURES, "metadata feature order drifted from code FEATURES"
    bundle = predict_mod.load_models(MODEL_PATH)
    assert list(bundle["features"]) == list(FEATURES), "pickled model feature order drifted from code"


def test_feature_order_is_load_bearing_negative_control():
    """NEGATIVE CONTROL: feature order is a silent contract. If predict fed the
    model a permuted column order positionally, probabilities change but NOTHING
    raises. Proves the binding is real and unguarded against positional bugs."""
    from ml.features import build_features

    obs, nwp = build_inputs()
    feat = build_features(ISSUE, obs, nwp, "25", obs.attrs["od_history"])
    bundle = predict_mod.load_models(MODEL_PATH)
    model = bundle["od"]
    idx = list(model.classes_).index(1)
    correct = model.predict_proba(feat[FEATURES])[:, idx]
    shuffled = list(FEATURES)
    rng = np.random.default_rng(0)
    rng.shuffle(shuffled)
    # DataFrame with correct names but shuffled order: sklearn re-checks names
    # AND order, so this RAISES. That is a genuine guard for the common case
    # (a pandas slice in the wrong order is caught, not silently mispredicted).
    with pytest.raises(ValueError, match="same order"):
        model.predict_proba(feat[shuffled])
    # Positional (numpy) permutation strips names: sklearn cannot catch it, so
    # output is silently corrupted. This is the residual risk if any caller ever
    # feeds a bare array. predict_48h currently always passes frame[FEATURES]
    # (a named, correctly-ordered DataFrame), so it is safe today.
    permuted_np = model.predict_proba(feat[shuffled].to_numpy())[:, idx]
    max_abs_np = float(np.max(np.abs(correct - permuted_np)))
    print(f"\n[feature-order] numpy-permuted max|delta|={max_abs_np:.6f} (silent); "
          f"df-permuted -> ValueError (guarded)")
    assert max_abs_np > 1e-6, "feature order had no positional effect (unexpected)"


def test_run_id_is_deterministic_and_input_sensitive():
    """Replay contract: identical inputs -> identical run_id; a changed issue
    input -> different run_id. Rebuilds run_id via the documented payload."""
    from ml import forecast as fc

    obs, nwp = build_inputs()
    frame = predict_48h(ISSUE, obs, nwp, "25")

    def run_id_for(issue, sha, issue_inputs, per_hour):
        payload = json.dumps([fc.utc_text(issue), sha, issue_inputs, per_hour],
                             sort_keys=True, default=str)
        return hashlib.sha256(payload.encode()).hexdigest()[:12]

    sha = frame.attrs["model_sha256"]
    issue_inputs = {"metar_time": "2026-10-30T00:00Z", "od_at_issue": "25"}
    per_hour = [{"blend_key": "1:active"}]
    a = run_id_for(ISSUE, sha, issue_inputs, per_hour)
    b = run_id_for(ISSUE, sha, issue_inputs, per_hour)
    assert a == b, "run_id not deterministic for identical inputs"
    c = run_id_for(ISSUE, sha, {**issue_inputs, "od_at_issue": "07"}, per_hour)
    assert a != c, "run_id did NOT change when an issue input changed"
    # And a different model sha must change the run_id (artifact binding).
    d = run_id_for(ISSUE, "0" * 64, issue_inputs, per_hour)
    assert a != d, "run_id did NOT change when model hash changed"


def test_missing_required_wind_is_caught_negative_control():
    """NEGATIVE CONTROL: drop day2 wind coverage -> predict must refuse, not
    silently fill. Proves missing inputs are caught."""
    obs, nwp = build_inputs()
    broken = nwp.drop(columns=[c for c in nwp.columns if c.endswith("_previous_day2")
                               and c.startswith(("wind_speed_10m", "wind_direction_10m", "wind_gusts_10m"))])
    with pytest.raises(ValueError, match="coverage"):
        predict_48h(ISSUE, broken, obs=obs, nwp=None) if False else predict_48h(ISSUE, obs, broken, "25")


def test_future_observation_excluded_negative_control():
    """NEGATIVE CONTROL: observations after issue must not change the vector."""
    obs, nwp = build_inputs()
    base = predict_48h(ISSUE, obs, nwp, "25")
    tainted = obs.copy()
    tainted.attrs["od_history"] = obs.attrs["od_history"]
    # append a post-issue METAR with absurd wind
    future = pd.DataFrame({"time": [ISSUE + pd.Timedelta(hours=1)],
                           "wind_dir_deg": [90.0], "wind_kt": [99.0], "gust_kt": [120.0]})
    tainted = pd.concat([tainted, future], ignore_index=True)
    tainted.attrs["od_history"] = obs.attrs["od_history"]
    after = predict_48h(ISSUE, tainted, nwp, "25")
    pd.testing.assert_series_equal(base.p_od25, after.p_od25, check_names=False)


def test_cli_evidence_run_id_real_pipeline_parity():
    """CLI/predict parity: ml.forecast.evidence() over REAL predict_48h output
    yields a stable run_id across two independent runs, and the per-hour
    `inputs` block round-trips every EVIDENCE column named in metadata/predict."""
    from ml import forecast as fc

    obs, nwp = build_inputs()

    def full_run():
        frame = predict_48h(ISSUE, obs.copy(), nwp.copy(), "25")
        frame.attrs.update(predict_48h(ISSUE, obs.copy(), nwp.copy(), "25").attrs)
        hours = fc.format_hours(frame, ISSUE)
        known = obs.attrs["od_history"].loc[
            obs.attrs["od_history"].available_at <= ISSUE, ["time", "od", "available_at"]]
        ev = fc.evidence(frame, hours, ISSUE, fc.live.normalize_metar(obs), known, nwp, "25",
                         "test-provenance")
        return ev, hours

    ev1, hours1 = full_run()
    ev2, _ = full_run()
    assert ev1["run_id"] == ev2["run_id"], "run_id not reproducible across identical real runs"
    assert ev1["model_artifact"]["version"] == "walk-forward-v5"
    assert ev1["model_artifact"]["sha256"] == file_sha256(MODEL_PATH.parent / ev1["model_artifact"]["file"])
    # Every per-hour inputs block carries the evidence fields (feature->trace binding).
    required_keys = {"nwp_offset_days", "wind_kt_metar_scaled", "blend_key", "blend_weight", "p_od25_raw"}
    for hour in hours1:
        assert required_keys.issubset(hour["inputs"].keys()), hour["inputs"].keys()
    # Changing od_at_issue must change the run_id (issue-input sensitivity, end to end).
    frame07 = predict_48h(ISSUE, obs.copy(), nwp.copy(), "07")
    hours07 = fc.format_hours(frame07, ISSUE)
    known = obs.attrs["od_history"].loc[
        obs.attrs["od_history"].available_at <= ISSUE, ["time", "od", "available_at"]]
    ev07 = fc.evidence(frame07, hours07, ISSUE, fc.live.normalize_metar(obs), known, nwp, "07", "test")
    assert ev07["run_id"] != ev1["run_id"], "run_id insensitive to od_at_issue change"
