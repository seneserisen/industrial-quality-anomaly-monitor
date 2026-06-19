"""Anomaly detection algorithms used by the monitoring pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler

DEFAULT_FEATURES = (
    "temperature_c",
    "vibration_mm_s",
    "pressure_bar",
    "cycle_time_s",
    "quality_score",
)


class Detector(Protocol):
    """Common interface for detector implementations."""

    def score(self, frame: pd.DataFrame, features: tuple[str, ...]) -> np.ndarray:
        """Return a non-negative anomaly score for each row."""


@dataclass(frozen=True)
class RobustZScoreDetector:
    """Median/MAD-based detector that is interpretable and resistant to outliers."""

    threshold: float = 4.0

    def score(
        self, frame: pd.DataFrame, features: tuple[str, ...] = DEFAULT_FEATURES
    ) -> np.ndarray:
        values = _validated_numeric_matrix(frame, features)
        median = np.median(values, axis=0)
        mad = np.median(np.abs(values - median), axis=0)
        safe_mad = np.where(mad < 1e-12, 1.0, mad)
        robust_z = 0.6745 * np.abs(values - median) / safe_mad
        return np.max(robust_z, axis=1)

    def predict(
        self, frame: pd.DataFrame, features: tuple[str, ...] = DEFAULT_FEATURES
    ) -> tuple[np.ndarray, np.ndarray]:
        scores = self.score(frame, features)
        return scores, scores >= self.threshold


@dataclass(frozen=True)
class IsolationForestDetector:
    """Multivariate detector for interactions that univariate thresholds may miss."""

    contamination: float = 0.04
    random_seed: int = 42

    def predict(
        self, frame: pd.DataFrame, features: tuple[str, ...] = DEFAULT_FEATURES
    ) -> tuple[np.ndarray, np.ndarray]:
        if not 0 < self.contamination < 0.5:
            raise ValueError("contamination must be in (0, 0.5)")
        values = _validated_numeric_matrix(frame, features)
        scaled = RobustScaler().fit_transform(values)
        model = IsolationForest(
            contamination=self.contamination,
            n_estimators=250,
            random_state=self.random_seed,
            n_jobs=-1,
        )
        raw_scores = -model.fit(scaled).score_samples(scaled)
        predictions = model.predict(scaled) == -1
        return raw_scores, predictions


def build_detector(method: str, *, contamination: float, threshold: float) -> object:
    """Construct a detector from a CLI-friendly method name."""

    if method == "robust-z":
        return RobustZScoreDetector(threshold=threshold)
    if method == "isolation-forest":
        return IsolationForestDetector(contamination=contamination)
    raise ValueError(f"unsupported method: {method}")


def _validated_numeric_matrix(frame: pd.DataFrame, features: tuple[str, ...]) -> np.ndarray:
    missing = [feature for feature in features if feature not in frame.columns]
    if missing:
        raise ValueError(f"missing required feature columns: {', '.join(missing)}")
    matrix = frame.loc[:, features].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    if not np.isfinite(matrix).all():
        raise ValueError("feature columns contain missing or non-finite values")
    return matrix
