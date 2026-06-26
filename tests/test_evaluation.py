import numpy as np
import pandas as pd
import pytest

from quality_monitor.evaluation import (
    binary_classification_metrics,
    confusion_counts,
    fault_type_metrics,
)
from quality_monitor.reporting import calculate_metrics


def test_confusion_counts_match_known_predictions() -> None:
    counts = confusion_counts(
        truth=[1, 1, 0, 0, 1, 0],
        detected=[1, 0, 1, 0, 1, 0],
    )

    assert counts == {
        "true_positives": 2,
        "false_positives": 1,
        "true_negatives": 2,
        "false_negatives": 1,
    }


def test_binary_classification_metrics_include_zero_safe_rates() -> None:
    metrics = binary_classification_metrics(
        truth=[True, True, False, False, True, False],
        detected=[True, False, True, False, True, False],
    )

    assert metrics["precision"] == pytest.approx(2 / 3)
    assert metrics["recall"] == pytest.approx(2 / 3)
    assert metrics["f1_score"] == pytest.approx(2 / 3)
    assert metrics["false_positive_rate"] == pytest.approx(1 / 3)
    assert metrics["false_negative_rate"] == pytest.approx(1 / 3)


def test_binary_classification_metrics_return_zero_for_undefined_rates() -> None:
    metrics = binary_classification_metrics(
        truth=[False, False, False],
        detected=[False, False, False],
    )

    assert metrics["true_negatives"] == 3
    assert metrics["precision"] == 0.0
    assert metrics["recall"] == 0.0
    assert metrics["f1_score"] == 0.0
    assert metrics["false_positive_rate"] == 0.0
    assert metrics["false_negative_rate"] == 0.0


def test_fault_type_metrics_exclude_normal_rows_and_calculate_recall() -> None:
    metrics = fault_type_metrics(
        anomaly_types=[
            "normal",
            "overheating",
            "bearing_wear",
            "overheating",
            "slow_cycle",
        ],
        detected=[True, True, False, False, True],
    )

    assert metrics == {
        "bearing_wear": {
            "injected_count": 1,
            "detected_count": 0,
            "recall": 0.0,
        },
        "overheating": {
            "injected_count": 2,
            "detected_count": 1,
            "recall": 0.5,
        },
        "slow_cycle": {
            "injected_count": 1,
            "detected_count": 1,
            "recall": 1.0,
        },
    }


def test_fault_type_metrics_include_required_fault_with_no_examples() -> None:
    metrics = fault_type_metrics(
        anomaly_types=["normal", "overheating"],
        detected=[False, True],
        fault_types=["overheating", "pressure_loss"],
    )

    assert list(metrics) == ["overheating", "pressure_loss"]
    assert metrics["pressure_loss"] == {
        "injected_count": 0,
        "detected_count": 0,
        "recall": 0.0,
    }


def test_reporting_uses_reusable_binary_metrics() -> None:
    frame = pd.DataFrame(
        {
            "is_detected_anomaly": [True, False, True, False],
            "is_injected_anomaly": [True, True, False, False],
            "anomaly_score": [7.0, 1.0, 5.0, 0.5],
        }
    )

    metrics = calculate_metrics(frame)

    assert metrics["true_positives"] == 1
    assert metrics["false_positives"] == 1
    assert metrics["true_negatives"] == 1
    assert metrics["false_negatives"] == 1
    assert metrics["false_positive_rate"] == pytest.approx(0.5)
    assert metrics["false_negative_rate"] == pytest.approx(0.5)


@pytest.mark.parametrize(
    ("truth", "detected", "message"),
    [
        ([True], [True, False], "equal lengths"),
        ([[True]], [True], "one-dimensional"),
        ([True, None], [True, False], "missing values"),
        ([True, 2], [True, False], "boolean or binary"),
    ],
)
def test_binary_evaluation_rejects_invalid_inputs(
    truth: list[object],
    detected: list[object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        confusion_counts(truth, detected)


def test_fault_type_metrics_reject_invalid_labels() -> None:
    with pytest.raises(ValueError, match="missing values"):
        fault_type_metrics(["normal", np.nan], [False, True])

    with pytest.raises(ValueError, match="duplicates"):
        fault_type_metrics(
            ["normal", "overheating"],
            [False, True],
            fault_types=["overheating", "overheating"],
        )
