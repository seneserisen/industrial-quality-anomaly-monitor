"""End-to-end monitoring pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from quality_monitor.detectors import DEFAULT_FEATURES, build_detector
from quality_monitor.reporting import calculate_metrics, plot_monitoring_summary, write_metrics


@dataclass(frozen=True)
class AnalysisConfig:
    """Runtime parameters for a monitoring analysis."""

    method: str = "robust-z"
    contamination: float = 0.04
    threshold: float = 4.0
    features: tuple[str, ...] = DEFAULT_FEATURES


def load_dataset(input_path: str | Path) -> pd.DataFrame:
    source = Path(input_path)
    if not source.exists():
        raise FileNotFoundError(f"input dataset does not exist: {source}")
    frame = pd.read_csv(source)
    if frame.empty:
        raise ValueError("input dataset is empty")
    return frame


def analyse_frame(frame: pd.DataFrame, config: AnalysisConfig) -> pd.DataFrame:
    """Score a frame and append detector outputs without mutating the input."""

    detector = build_detector(
        config.method,
        contamination=config.contamination,
        threshold=config.threshold,
    )
    scores, predictions = detector.predict(frame, config.features)
    result = frame.copy()
    result["anomaly_score"] = scores
    result["is_detected_anomaly"] = predictions
    return result


def run_analysis(
    input_path: str | Path,
    output_dir: str | Path,
    config: AnalysisConfig,
) -> dict[str, Path]:
    """Run the full file-based pipeline and return generated artifact paths."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    scored = analyse_frame(load_dataset(input_path), config)

    scored_path = output / "scored_production_data.csv"
    metrics_path = output / "metrics.json"
    plot_path = output / "monitoring_summary.png"

    scored.to_csv(scored_path, index=False)
    write_metrics(calculate_metrics(scored), metrics_path)
    plot_monitoring_summary(scored, plot_path)

    return {
        "scored_data": scored_path,
        "metrics": metrics_path,
        "plot": plot_path,
    }
