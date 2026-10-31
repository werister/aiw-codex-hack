import numpy as np
import pandas as pd

from ml.features import FEATURES
from ml.predict import r18_probability


class FixedProbability:
    classes_ = np.array([0, 1])

    def __init__(self, positive_probability):
        self.positive_probability = np.asarray(positive_probability, dtype=float)

    def predict_proba(self, features):
        assert len(features) == len(self.positive_probability)
        return np.column_stack((1 - self.positive_probability, self.positive_probability))


def prediction_frame(leads, prior):
    frame = pd.DataFrame({name: np.zeros(len(leads), dtype=float) for name in FEATURES})
    frame["time"] = pd.date_range("2026-10-30T00:00:00Z", periods=len(leads), freq="h")
    frame["lead_h"] = leads
    frame["persistence_18"] = prior
    return frame


def test_r18_uses_horizon_weights_at_bucket_boundaries():
    leads = [1, 2, 6, 7, 24, 25, 48]
    raw = np.full(len(leads), 0.8)
    prior = np.full(len(leads), 0.2)
    weights = {"1": 0.1, "6": 0.2, "24": 0.3, "48": 0.4}

    actual = r18_probability(
        {"r18": FixedProbability(raw), "r18_model_weight": weights},
        prediction_frame(leads, prior),
    )

    alphas = np.array([0.1, 0.2, 0.2, 0.3, 0.3, 0.4, 0.4])
    np.testing.assert_allclose(actual, alphas * raw + (1 - alphas) * prior)


def test_r18_missing_persistence_uses_raw_probability():
    raw = np.array([0.8, 0.6, 0.3])
    frame = prediction_frame([1, 6, 48], [0.2, np.nan, np.nan])

    actual = r18_probability(
        {"r18": FixedProbability(raw), "r18_model_weight": {"1": 0.0, "6": 0.0, "48": 0.0}},
        frame,
    )

    np.testing.assert_allclose(actual, [0.2, 0.6, 0.3])


def test_r18_old_artifact_without_weights_returns_raw_probability():
    raw = np.array([0.1, 0.5, 0.9])
    frame = prediction_frame([1, 24, 48], [0.95, 0.05, 0.7])

    actual = r18_probability({"r18": FixedProbability(raw)}, frame)

    np.testing.assert_allclose(actual, raw)
