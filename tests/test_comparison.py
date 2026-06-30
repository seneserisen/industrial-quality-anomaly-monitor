import csv
import json

import pytest

from quality_monitor.comparison import FAULT_TYPES, ComparisonConfig, run_detector_comparison


def _stable_summary(summary: dict[str, object]) -> dict[str, object]:
    stable = json.loads(json.dumps(summary))
    experiment = stable["experiment"]
    experiment.pop("python_version")
    experiment.pop("platform")
    for detector in stable["detectors"]:
        detector["metrics"].pop("runtime_median_seconds")
    return stable


def test_comparison_exports_reproducible_json_and_csv(tmp_path) -> None:
    config = ComparisonConfig(
        rows=200,
        machines=4,
        anomaly_rate=0.05,
        dataset_seed=7,
        runtime_repetitions=1,
    )

    first = run_detector_comparison(tmp_path / "first", config)
    second = run_detector_comparison(tmp_path / "second", config)
    first_summary = json.loads(first["summary_json"].read_text(encoding="utf-8"))
    second_summary = json.loads(second["summary_json"].read_text(encoding="utf-8"))

    assert _stable_summary(first_summary) == _stable_summary(second_summary)
    assert [result["name"] for result in first_summary["detectors"]] == [
        "global_robust_z",
        "machine_aware_robust_z",
        "isolation_forest",
    ]
    assert all(
        set(result["fault_type_metrics"]) == set(FAULT_TYPES)
        for result in first_summary["detectors"]
    )

    with first["summary_csv"].open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 3
    assert {"name", "precision", "f1_score", "overheating_recall"} <= set(rows[0])


def test_comparison_rejects_zero_repetitions(tmp_path) -> None:
    with pytest.raises(ValueError, match="runtime_repetitions"):
        run_detector_comparison(
            tmp_path,
            ComparisonConfig(runtime_repetitions=0),
        )
