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


def test_isolation_forest_output_shapes() -> None:
    frame = pd.concat([_frame()] * 20, ignore_index=True)
    scores, predictions = IsolationForestDetector(contamination=0.1).predict(frame)
    assert scores.shape == (80,)
    assert predictions.shape == (80,)
    assert predictions.dtype == bool


def test_missing_feature_is_rejected() -> None:
    with pytest.raises(ValueError, match="missing required"):
        RobustZScoreDetector().predict(_frame().drop(columns="pressure_bar"))
