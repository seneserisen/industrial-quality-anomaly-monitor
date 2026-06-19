"""Synthetic manufacturing data generation for reproducible demos and tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class GenerationConfig:
    """Configuration for a synthetic production run."""

    rows: int = 3000
    machines: int = 4
    anomaly_rate: float = 0.04
    random_seed: int = 42

    def validate(self) -> None:
        if self.rows < 50:
            raise ValueError("rows must be at least 50")
        if self.machines < 1:
            raise ValueError("machines must be at least 1")
        if not 0 <= self.anomaly_rate < 0.5:
            raise ValueError("anomaly_rate must be in [0, 0.5)")


def generate_production_data(config: GenerationConfig) -> pd.DataFrame:
    """Generate a realistic, labelled manufacturing quality dataset.

    The process combines machine-specific offsets, slow operating drift, measurement noise,
    and four injected failure signatures. The labels are only used for demonstration and
    evaluation; the detection algorithms do not consume them.
    """

    config.validate()
    rng = np.random.default_rng(config.random_seed)
    machine_ids = rng.integers(1, config.machines + 1, size=config.rows)
    time_index = pd.date_range("2026-01-01", periods=config.rows, freq="min")

    machine_offset = (machine_ids - 1) * 0.18
    drift = np.linspace(0.0, 0.7, config.rows)

    temperature = 67.0 + machine_offset + 0.35 * drift + rng.normal(0, 1.15, config.rows)
    vibration = 2.25 + 0.08 * machine_offset + 0.06 * drift + rng.normal(0, 0.18, config.rows)
    pressure = 5.55 - 0.04 * machine_offset + rng.normal(0, 0.14, config.rows)
    cycle_time = 31.5 + 0.30 * machine_offset + 0.20 * drift + rng.normal(0, 0.75, config.rows)
    quality_score = 98.2 - 0.15 * machine_offset - 0.08 * drift + rng.normal(0, 0.35, config.rows)

    anomaly = np.zeros(config.rows, dtype=bool)
    anomaly_type = np.full(config.rows, "normal", dtype=object)
    anomaly_count = int(round(config.rows * config.anomaly_rate))

    if anomaly_count:
        anomaly_indices = rng.choice(config.rows, size=anomaly_count, replace=False)
        signatures = rng.choice(
            ["overheating", "bearing_wear", "pressure_loss", "slow_cycle"],
            size=anomaly_count,
        )
        anomaly[anomaly_indices] = True

        for row_index, signature in zip(anomaly_indices, signatures, strict=True):
            anomaly_type[row_index] = signature
            if signature == "overheating":
                temperature[row_index] += rng.uniform(7.0, 12.0)
                quality_score[row_index] -= rng.uniform(1.0, 2.0)
            elif signature == "bearing_wear":
                vibration[row_index] += rng.uniform(1.0, 2.0)
                temperature[row_index] += rng.uniform(2.0, 4.0)
            elif signature == "pressure_loss":
                pressure[row_index] -= rng.uniform(1.0, 1.8)
                quality_score[row_index] -= rng.uniform(1.2, 2.5)
            else:
                cycle_time[row_index] += rng.uniform(5.0, 9.0)
                quality_score[row_index] -= rng.uniform(0.8, 1.8)

    frame = pd.DataFrame(
        {
            "timestamp": time_index,
            "machine_id": [f"M-{machine_id:02d}" for machine_id in machine_ids],
            "temperature_c": temperature,
            "vibration_mm_s": vibration,
            "pressure_bar": pressure,
            "cycle_time_s": cycle_time,
            "quality_score": np.clip(quality_score, 0, 100),
            "is_injected_anomaly": anomaly,
            "anomaly_type": anomaly_type,
        }
    )
    return frame.round(
        {
            "temperature_c": 3,
            "vibration_mm_s": 3,
            "pressure_bar": 3,
            "cycle_time_s": 3,
            "quality_score": 3,
        }
    )


def save_dataset(frame: pd.DataFrame, output_path: str | Path) -> Path:
    """Persist a generated dataset, creating parent directories when necessary."""

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(destination, index=False)
    return destination
