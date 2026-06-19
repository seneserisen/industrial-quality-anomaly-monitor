"""Reporting helpers for monitoring outputs."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import precision_recall_fscore_support


def calculate_metrics(scored_frame: pd.DataFrame) -> dict[str, float | int]:
    """Calculate operational KPIs and optional labelled evaluation metrics."""

    detected = scored_frame["is_detected_anomaly"].astype(bool)
    metrics: dict[str, float | int] = {
        "rows": int(len(scored_frame)),
        "detected_anomalies": int(detected.sum()),
        "detected_anomaly_rate": float(detected.mean()),
        "mean_anomaly_score": float(scored_frame["anomaly_score"].mean()),
        "max_anomaly_score": float(scored_frame["anomaly_score"].max()),
    }

    if "is_injected_anomaly" in scored_frame.columns:
        truth = scored_frame["is_injected_anomaly"].astype(bool)
        precision, recall, f1, _ = precision_recall_fscore_support(
            truth,
            detected,
            average="binary",
            zero_division=0,
        )
        metrics.update(
            {
                "injected_anomalies": int(truth.sum()),
                "precision": float(precision),
                "recall": float(recall),
                "f1_score": float(f1),
            }
        )
    return metrics


def write_metrics(metrics: dict[str, float | int], output_path: str | Path) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


def plot_monitoring_summary(scored_frame: pd.DataFrame, output_path: str | Path) -> Path:
    """Create a compact engineering plot showing sensor behaviour and anomaly scores."""

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    x_axis = pd.to_datetime(scored_frame.get("timestamp"), errors="coerce")
    if x_axis.isna().all():
        x_axis = pd.Series(range(len(scored_frame)))

    fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=True)
    axes[0].plot(x_axis, scored_frame["temperature_c"], linewidth=0.8)
    axes[0].set_ylabel("Temperature [°C]")
    axes[0].set_title("Industrial Quality Monitoring Summary")

    axes[1].plot(x_axis, scored_frame["vibration_mm_s"], linewidth=0.8)
    axes[1].set_ylabel("Vibration [mm/s]")

    axes[2].plot(x_axis, scored_frame["anomaly_score"], linewidth=0.8)
    anomaly_rows = scored_frame["is_detected_anomaly"].astype(bool)
    axes[2].scatter(
        x_axis[anomaly_rows],
        scored_frame.loc[anomaly_rows, "anomaly_score"],
        marker="x",
        label="Detected anomaly",
    )
    axes[2].set_ylabel("Anomaly score")
    axes[2].set_xlabel("Time")
    axes[2].legend(loc="upper right")

    fig.tight_layout()
    fig.savefig(destination, dpi=160)
    plt.close(fig)
    return destination
