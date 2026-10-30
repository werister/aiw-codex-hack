from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ml.challengers import _horizon_alpha, opposite_to_p25, physical_blend, safe_output, split_fold


def test_outer_split_purges_training_labels_and_marks_month_overhang():
    frame = pd.DataFrame({
        "issue_time": pd.to_datetime(["2026-06-29T23:00Z", "2026-06-30T23:00Z",
                                      "2026-07-31T23:00Z"], utc=True),
        "label_available_at": pd.to_datetime(["2026-06-30T00:00Z", "2026-07-01T00:00Z",
                                                "2026-08-01T00:00Z"], utc=True),
    })

    _, start, _, train, test = split_fold(frame, "2026-07")

    assert train.label_available_at.max() < start
    assert len(train) == 1
    assert test.point_in_outer_fold.tolist() == [False]


def test_opposite_probability_maps_to_od25_for_both_issue_directions():
    result = opposite_to_p25([0.2, 0.2], [1, 0])

    np.testing.assert_allclose(result, [0.8, 0.2])


def test_physical_blend_uses_v6_if_rule_is_missing():
    result = physical_blend([0.7, 0.2], [0.3, np.nan], [0.8, 0.4])

    np.testing.assert_allclose(result, [0.62, 0.2])


def test_physical_weights_extract_one_lambda_for_each_lead_bucket():
    rows = pd.DataFrame({"lead_h": [1, 2, 7, 25]})
    weights = {str(lead): {"lambda_baseline": value} for lead, value in
               ((1, 0.9), (6, 1.0), (24, 0.9), (48, 0.8))}

    np.testing.assert_allclose(_horizon_alpha(rows, weights), [0.9, 1.0, 0.9, 0.8])


def test_output_path_cannot_target_production_artifacts(tmp_path: Path):
    root = tmp_path / "repo"
    (root / "ml/models").mkdir(parents=True)
    (root / "web/public").mkdir(parents=True)

    research = tmp_path / "research/challengers"
    assert safe_output(research, root) == research
    with pytest.raises(ValueError, match="outside ml/models and web/public"):
        safe_output(root / "ml/models/forecast.joblib", root)
    with pytest.raises(ValueError, match="outside ml/models and web/public"):
        safe_output(root / "web/public/forecasts", root)
    with pytest.raises(ValueError, match="limited to a new subfolder"):
        safe_output(root / "ml/tests/output", root)

    in_repo_research = root / "verification/challengers"
    assert safe_output(in_repo_research, root) == in_repo_research
    in_repo_research.mkdir(parents=True)
    sentinel = in_repo_research / "report.json"
    sentinel.write_text("keep this report")
    with pytest.raises(ValueError, match="already exists; use --rescore"):
        safe_output(in_repo_research, root)
    assert sentinel.read_text() == "keep this report"
    assert safe_output(in_repo_research, root, allow_existing=True) == in_repo_research
    assert sentinel.read_text() == "keep this report"

    link = tmp_path / "repo-link"
    try:
        link.symlink_to(root / "verification", target_is_directory=True)
    except OSError:
        link = None  # Windows without the symlink privilege (WinError 1314)
    if link is not None:
        with pytest.raises(ValueError, match="through a symlink"):
            safe_output(link / "challengers", root)
    with pytest.raises(ValueError, match="repository root"):
        safe_output(root, root)
