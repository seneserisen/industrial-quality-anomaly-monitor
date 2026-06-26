"""Reusable evaluation helpers for labelled anomaly-detection results."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

BinaryValues = Sequence[bool | int] | np.ndarray
LabelValues = Sequence[str] | np.ndarray


def _as_binary_array(values: BinaryValues, name: str) -> np.ndarray:
    array = np.asarray(values, dtype=object)
    if array.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional")
    if bool(pd.isna(array).any()):
        raise ValueError(f"{name} must not contain missing values")
    if not bool(np.isin(array, [False, True, 0, 1]).all()):
        raise ValueError(f"{name} must contain only boolean or binary values")
    return array.astype(bool, copy=False)


def _safe_ratio(numerator: int, denominator: int) -> float:
    return float(numerator / denominator) if denominator else 0.0


def confusion_counts(
    truth: BinaryValues,
    detected: BinaryValues,
) -> dict[str, int]:
    """Return binary confusion counts for anomaly labels and predictions."""

    truth_array = _as_binary_array(truth, "truth")
    detected_array = _as_binary_array(detected, "detected")
    if truth_array.shape != detected_array.shape:
        raise ValueError("truth and detected must have equal lengths")

    true_positives = int(np.count_nonzero(truth_array & detected_array))
    false_positives = int(np.count_nonzero(~truth_array & detected_array))
    true_negatives = int(np.count_nonzero(~truth_array & ~detected_array))
    false_negatives = int(np.count_nonzero(truth_array & ~detected_array))

    return {
        "true_positives": true_positives,
        "false_positives": false_positives,
        "true_negatives": true_negatives,
        "false_negatives": false_negatives,
    }


def binary_classification_metrics(
    truth: BinaryValues,
    detected: BinaryValues,
) -> dict[str, float | int]:
    """Calculate confusion counts and zero-safe binary classification rates."""

    counts = confusion_counts(truth, detected)
    true_positives = counts["true_positives"]
    false_positives = counts["false_positives"]
    true_negatives = counts["true_negatives"]
    false_negatives = counts["false_negatives"]

    precision = _safe_ratio(true_positives, true_positives + false_positives)
    recall = _safe_ratio(true_positives, true_positives + false_negatives)
    f1_score = _safe_ratio(
        2 * true_positives,
        2 * true_positives + false_positives + false_negatives,
    )
    false_positive_rate = _safe_ratio(
        false_positives,
        false_positives + true_negatives,
    )
    false_negative_rate = _safe_ratio(
        false_negatives,
        false_negatives + true_positives,
    )

    return {
        **counts,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "false_positive_rate": false_positive_rate,
        "false_negative_rate": false_negative_rate,
    }


def fault_type_metrics(
    anomaly_types: LabelValues,
    detected: BinaryValues,
    *,
    fault_types: Sequence[str] | None = None,
    normal_label: str = "normal",
) -> dict[str, dict[str, float | int]]:
    """Calculate injected counts, detected counts, and recall by fault type."""

    type_array = np.asarray(anomaly_types, dtype=object)
    if type_array.ndim != 1:
        raise ValueError("anomaly_types must be one-dimensional")
    if bool(pd.isna(type_array).any()):
        raise ValueError("anomaly_types must not contain missing values")
    if not all(isinstance(value, str) for value in type_array.tolist()):
        raise ValueError("anomaly_types must contain only strings")

    detected_array = _as_binary_array(detected, "detected")
    if type_array.shape != detected_array.shape:
        raise ValueError("anomaly_types and detected must have equal lengths")

    if fault_types is None:
        selected_types = sorted(set(type_array.tolist()) - {normal_label})
    else:
        selected_types = list(fault_types)
        if not all(isinstance(fault_type, str) for fault_type in selected_types):
            raise ValueError("fault_types must contain only strings")
        if len(selected_types) != len(set(selected_types)):
            raise ValueError("fault_types must not contain duplicates")
        if any(
            not fault_type or fault_type == normal_label
            for fault_type in selected_types
        ):
            raise ValueError("fault_types must contain non-empty non-normal labels")

    metrics: dict[str, dict[str, float | int]] = {}
    for fault_type in selected_types:
        fault_rows = type_array == fault_type
        injected_count = int(np.count_nonzero(fault_rows))
        detected_count = int(np.count_nonzero(detected_array[fault_rows]))
        metrics[fault_type] = {
            "injected_count": injected_count,
            "detected_count": detected_count,
            "recall": _safe_ratio(detected_count, injected_count),
        }
    return metrics
