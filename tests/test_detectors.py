import numpy as np
import pandas as pd
import pytest

from quality_monitor.detectors import IsolationForestDetector, RobustZScoreDetector


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "temperature_c": [66.9, 67.1, 67.0, 88.0],
            "vibration_mm_s": [2.2, 2.3, 2.2, 5.0],
            "pressure_bar": [5.5, 5.6, 5.5, 3.2],
            "cycle_time_s": [31.0, 31.4, 31.2, 44.0],
            "quality_score": [98.0, 98.1, 98.2, 92.0],
        }
    )


def test_robust_detector_ranks_obvious_outlier_highest() -> None:
    scores, predictions = RobustZScoreDetector(threshold=4.0).predict(_frame())
    assert int(np.argmax(scores)) == 3
    assert bool(predictions[3])


def test_group_baseline_detects_anomaly_hidden_by_machine_offsets() -> None:
    frame = pd.DataFrame(
        {
            "machine_id": ["M-01"] * 5 + ["M-02"] * 5,
            "temperature_c": [0.0, 0.1, -0.1, 0.05, 2.0, 10.0, 10.1, 9.9, 10.05, 9.95],
        }
    )

    _, global_predictions = RobustZScoreDetector(threshold=4.0).predict(
        frame,
        ("temperature_c",),
    )
    grouped_scores, grouped_predictions = RobustZScoreDetector(
        threshold=4.0,
        group_column="machine_id",
    ).predict(frame, ("temperature_c",))

    assert not bool(global_predictions[4])
    assert bool(grouped_predictions[4])
    assert int(np.argmax(grouped_scores)) == 4


def test_small_group_uses_global_fallback() -> None:
    frame = pd.DataFrame(
        {
            "machine_id": ["M-01"] * 5 + ["M-02"],
            "temperature_c": [10.0, 10.1, 9.9, 10.05, 9.95, 12.0],
        }
    )
    scores = RobustZScoreDetector(
        group_column="machine_id",
        min_group_size=5,
    ).score(frame, ("temperature_c",))

    assert np.isfinite(scores).all()
    assert scores.shape == (6,)


def test_missing_grouping_column_is_rejected() -> None:
    with pytest.raises(ValueError, match="missing grouping column"):
        RobustZScoreDetector(group_column="machine_id").predict(_frame())


def test_isolation_forest_output_shapes() -> None:
    frame = pd.concat([_frame()] * 20, ignore_index=True)
    scores, predictions = IsolationForestDetector(contamination=0.1).predict(frame)
    assert scores.shape == (80,)
    assert predictions.shape == (80,)
    assert predictions.dtype == bool


def test_missing_feature_is_rejected() -> None:
    with pytest.raises(ValueError, match="missing required"):
        RobustZScoreDetector().predict(_frame().drop(columns="pressure_bar"))
