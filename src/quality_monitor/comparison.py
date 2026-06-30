"""Deterministic comparison runner for the published detector configurations."""

from __future__ import annotations

import csv
import json
import platform
import statistics
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from quality_monitor.data_generation import GenerationConfig, generate_production_data
from quality_monitor.detectors import (
    DEFAULT_FEATURES,
    IsolationForestDetector,
    RobustZScoreDetector,
)
from quality_monitor.evaluation import binary_classification_metrics, fault_type_metrics

FAULT_TYPES = ("overheating", "bearing_wear", "pressure_loss", "slow_cycle")
DetectorFactory = Callable[[], RobustZScoreDetector | IsolationForestDetector]


@dataclass(frozen=True)
class ComparisonConfig:
    """Frozen experiment settings with smaller overrides available for tests."""

    rows: int = 3000
    machines: int = 4
    anomaly_rate: float = 0.04
    dataset_seed: int = 42
    runtime_repetitions: int = 5

    def validate(self) -> None:
        GenerationConfig(
            rows=self.rows,
            machines=self.machines,
            anomaly_rate=self.anomaly_rate,
            random_seed=self.dataset_seed,
        ).validate()
        if self.runtime_repetitions < 1:
            raise ValueError("runtime_repetitions must be at least 1")


def _detector_specifications() -> tuple[
    tuple[str, dict[str, object], DetectorFactory],
    ...,
]:
    return (
        (
            "global_robust_z",
            {
                "method": "robust-z",
                "threshold": 4.0,
                "contamination": None,
                "group_column": None,
                "min_group_size": None,
                "random_seed": None,
            },
            lambda: RobustZScoreDetector(threshold=4.0),
        ),
        (
            "machine_aware_robust_z",
            {
                "method": "robust-z",
                "threshold": 4.0,
                "contamination": None,
                "group_column": "machine_id",
                "min_group_size": 20,
                "random_seed": None,
            },
            lambda: RobustZScoreDetector(
                threshold=4.0,
                group_column="machine_id",
                min_group_size=20,
            ),
        ),
        (
            "isolation_forest",
            {
                "method": "isolation-forest",
                "threshold": None,
                "contamination": 0.04,
                "group_column": None,
                "min_group_size": None,
                "random_seed": 42,
            },
            lambda: IsolationForestDetector(contamination=0.04, random_seed=42),
        ),
    )


def _evaluate_detector(
    frame: pd.DataFrame,
    name: str,
    parameters: dict[str, object],
    factory: DetectorFactory,
    repetitions: int,
) -> dict[str, object]:
    durations: list[float] = []
    reference_scores: np.ndarray | None = None
    reference_predictions: np.ndarray | None = None

    for _ in range(repetitions):
        start = time.perf_counter()
        detector = factory()
        scores, predictions = detector.predict(frame, DEFAULT_FEATURES)
        durations.append(time.perf_counter() - start)

        current_scores = np.asarray(scores, dtype=float)
        current_predictions = np.asarray(predictions, dtype=bool)
        if reference_scores is None:
            reference_scores = current_scores
            reference_predictions = current_predictions
        elif not (
            np.array_equal(reference_predictions, current_predictions)
            and np.allclose(reference_scores, current_scores, rtol=0.0, atol=1e-12)
        ):
            raise RuntimeError(f"detector {name} produced non-deterministic repeated outputs")

    if reference_scores is None or reference_predictions is None:
        raise RuntimeError("detector timing loop produced no results")

    truth = frame["is_injected_anomaly"].to_numpy(dtype=bool)
    metrics = binary_classification_metrics(truth, reference_predictions)
    metrics.update(
        {
            "detected_anomalies": int(np.count_nonzero(reference_predictions)),
            "mean_anomaly_score": float(np.mean(reference_scores)),
            "max_anomaly_score": float(np.max(reference_scores)),
            "runtime_median_seconds": float(statistics.median(durations)),
            "runtime_repetitions": repetitions,
        }
    )

    return {
        "name": name,
        "parameters": parameters,
        "metrics": metrics,
        "fault_type_metrics": fault_type_metrics(
            frame["anomaly_type"].to_numpy(dtype=object),
            reference_predictions,
            fault_types=FAULT_TYPES,
        ),
    }


def _flatten_detector_result(result: dict[str, object]) -> dict[str, object]:
    parameters = result["parameters"]
    metrics = result["metrics"]
    fault_metrics = result["fault_type_metrics"]
    if not isinstance(parameters, dict) or not isinstance(metrics, dict):
        raise TypeError("detector result contains invalid parameter or metric data")
    if not isinstance(fault_metrics, dict):
        raise TypeError("detector result contains invalid fault-type metrics")

    row: dict[str, object] = {"name": result["name"], **parameters, **metrics}
    for fault_type in FAULT_TYPES:
        values = fault_metrics[fault_type]
        if not isinstance(values, dict):
            raise TypeError("fault-type result must be a mapping")
        row[f"{fault_type}_injected_count"] = values["injected_count"]
        row[f"{fault_type}_detected_count"] = values["detected_count"]
        row[f"{fault_type}_recall"] = values["recall"]
    return row


def run_detector_comparison(
    output_dir: str | Path,
    config: ComparisonConfig | None = None,
) -> dict[str, Path]:
    """Run the frozen comparison and export reviewable JSON and CSV summaries."""

    active_config = config or ComparisonConfig()
    active_config.validate()
    frame = generate_production_data(
        GenerationConfig(
            rows=active_config.rows,
            machines=active_config.machines,
            anomaly_rate=active_config.anomaly_rate,
            random_seed=active_config.dataset_seed,
        )
    )

    detector_results = [
        _evaluate_detector(
            frame,
            name,
            parameters,
            factory,
            active_config.runtime_repetitions,
        )
        for name, parameters, factory in _detector_specifications()
    ]

    truth = frame["is_injected_anomaly"].to_numpy(dtype=bool)
    summary = {
        "experiment": {
            "rows": active_config.rows,
            "machines": active_config.machines,
            "anomaly_rate": active_config.anomaly_rate,
            "dataset_seed": active_config.dataset_seed,
            "injected_anomalies": int(np.count_nonzero(truth)),
            "runtime_repetitions": active_config.runtime_repetitions,
            "features": list(DEFAULT_FEATURES),
            "python_version": platform.python_version(),
            "platform": platform.platform(),
        },
        "detectors": detector_results,
    }

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    json_path = destination / "comparison_summary.json"
    csv_path = destination / "comparison_summary.csv"

    json_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    rows = [_flatten_detector_result(result) for result in detector_results]
    fieldnames = list(rows[0])
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return {
        "summary_json": json_path,
        "summary_csv": csv_path,
    }
