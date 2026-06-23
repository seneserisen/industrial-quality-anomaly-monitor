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
    """Median/MAD detector with optional group-specific reference baselines.

    A grouped baseline is useful when machines, production lines, or product variants have
    legitimate operating offsets. Groups with too few observations fall back to the global
    reference distribution because their medians and MAD values would otherwise be unstable.
    """

    threshold: float = 4.0
    group_column: str | None = None
    min_group_size: int = 5

    def score(
        self, frame: pd.DataFrame, features: tuple[str, ...] = DEFAULT_FEATURES
    ) -> np.ndarray:
        values = _validated_numeric_matrix(frame, features)
        if self.group_column is None:
            return _robust_scores(values, values)

        if self.group_column not in frame.columns:
            raise ValueError(f"missing grouping column: {self.group_column}")
        if self.min_group_size < 2:
            raise ValueError("min_group_size must be at least 2")

        scores = np.empty(len(frame), dtype=float)
        grouped_positions = frame.groupby(
            self.group_column,
            sort=False,
            dropna=False,
        ).indices

        for positions in grouped_positions.values():
            row_positions = np.asarray(positions, dtype=int)
            reference = values[row_positions]
            if len(row_positions) < self.min_group_size:
                reference = values
            scores[row_positions] = _robust_scores(values[row_positions], reference)

        return scores

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


def build_detector(
    method: str,
    *,
    contamination: float,
    threshold: float,
    group_column: str | None = None,
    min_group_size: int = 5,
) -> object:
    """Construct a detector from pipeline- or CLI-friendly configuration values."""

    if method == "robust-z":
        return RobustZScoreDetector(
            threshold=threshold,
            group_column=group_column,
            min_group_size=min_group_size,
        )
    if method == "isolation-forest":
        return IsolationForestDetector(contamination=contamination)
    raise ValueError(f"unsupported method: {method}")


def _robust_scores(values: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """Score rows against the median and MAD of a reference population."""

    median = np.median(reference, axis=0)
    mad = np.median(np.abs(reference - median), axis=0)
    safe_mad = np.where(mad < 1e-12, 1.0, mad)
    robust_z = 0.6745 * np.abs(values - median) / safe_mad
    return np.max(robust_z, axis=1)


def _validated_numeric_matrix(frame: pd.DataFrame, features: tuple[str, ...]) -> np.ndarray:
    missing = [feature for feature in features if feature not in frame.columns]
    if missing:
        raise ValueError(f"missing required feature columns: {', '.join(missing)}")
    matrix = frame.loc[:, features].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    if not np.isfinite(matrix).all():
        raise ValueError("feature columns contain missing or non-finite values")
    return matrix
