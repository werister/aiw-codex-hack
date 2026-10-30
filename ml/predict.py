"""48-hour probability interface shared with the forecast CLI."""

from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np

from ml.features import FEATURES, build_features

MODEL_PATH = Path(__file__).with_name("models") / "forecast.joblib"


@lru_cache(maxsize=12)
def load_models(path=MODEL_PATH):
    if not path.exists():
        raise FileNotFoundError("Train the models first with python -m ml.train")
    return joblib.load(path)


def models_at_issue(issue):
    """Hindcasts use a saved fit whose target labels precede issue time."""
    import pandas as pd

    candidates = [MODEL_PATH] + sorted(MODEL_PATH.parent.glob("fold-*.joblib"), reverse=True)
    for path in candidates:
        if path.exists():
            models = load_models(path)
            if pd.Timestamp(models["trained_through"]) < issue:
                return models
    raise ValueError("No model trained before this issue time; choose a later hindcast date")


def probability(model, features):
    probabilities = model.predict_proba(features)
    classes = list(model.classes_)
    return probabilities[:, classes.index(1)] if 1 in classes else probabilities[:, 0] * 0


def od_probability(models, frame):
    """Blend with persistence using weights selected before each test fold."""
    p = probability(models["od"], frame[FEATURES])
    weights = models.get("od_model_weight")
    if weights is None:
        return p
    horizon = np.select([frame.lead_h <= 1, frame.lead_h <= 6, frame.lead_h <= 24], [1, 6, 24], default=48)
    alpha = np.array([weights[str(lead)] for lead in horizon])
    return alpha * p + (1 - alpha) * frame.od_at_issue.to_numpy(float)


def predict_48h(issue_time_utc, obs, nwp, od_at_issue):
    """Return 48 rows for leads 1..48 after an explicitly zoned issue time.

    obs: DataFrame with time, wind_dir_deg, wind_kt, gust_kt. IEM aliases
    valid, drct, sknt, gust are accepted. Missing gust uses mean wind.
    Optional obs.attrs['od_history'] with time, od and available_at supplies
    full recorded history for hours since change. Otherwise an od column
    with recorded states supplies hours since change;
    available_at is required for those states, or time + 1h is assumed for
    completed hourly summaries. Observations after issue time are excluded.

    nwp: time plus wind_speed_10m, wind_direction_10m, wind_gusts_10m,
    suffixed _previous_day1, _previous_day2 and _previous_day3 for archived
    offsets, selected at leads 1..18, 19..42 and 43..48 respectively. Never
    use unsuffixed historical day0. Live data accepts wind_kt, wind_dir_deg,
    gust_kt or the unsuffixed source names, with issued_at or retrieved_at
    no later than issue time. Optional pressure_msl, temperature_2m and
    wind_speed_80m follow the same suffix convention.

    od_at_issue: recorded current OD string '25' or '07', known by issue time.
    rule_18_usable and p_18_usable describe INFERRED weather usability.
    """
    import pandas as pd

    history = obs.attrs.get("od_history")
    if history is None and "od" in obs:
        history = obs.rename(columns={"valid": "time"}).copy()
        if "available_at" not in history:
            history["available_at"] = pd.to_datetime(history.time, utc=True) + pd.Timedelta(hours=1)
    frame = build_features(issue_time_utc, obs, nwp, od_at_issue, history)
    models = models_at_issue(pd.Timestamp(issue_time_utc))
    frame["p_od25"] = od_probability(models, frame)
    frame["p_18_usable"] = probability(models["r18"], frame[FEATURES])
    frame["r18_label_type"] = "inferred"
    frame.attrs["model_version"] = models["version"]
    return frame[["time", "lead_h", "wind_dir_deg", "wind_kt", "gust_kt", "tailwind_25_kt",
                  "tailwind_18_kt", "rule_od", "rule_18_usable", "p_od25", "p_18_usable", "r18_label_type"]]
