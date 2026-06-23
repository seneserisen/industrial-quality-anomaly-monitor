import json

import pandas as pd

from quality_monitor.data_generation import GenerationConfig, generate_production_data, save_dataset
from quality_monitor.pipeline import AnalysisConfig, analyse_frame, run_analysis


def test_analysis_does_not_mutate_input() -> None:
    frame = generate_production_data(GenerationConfig(rows=300, anomaly_rate=0.05))
    original_columns = frame.columns.tolist()
    scored = analyse_frame(frame, AnalysisConfig(method="robust-z", threshold=3.5))

    assert frame.columns.tolist() == original_columns
    assert {"anomaly_score", "is_detected_anomaly"}.issubset(scored.columns)
    assert scored["is_detected_anomaly"].any()


def test_analysis_config_forwards_grouped_baseline_settings() -> None:
    frame = pd.DataFrame(
        {
            "machine_id": ["M-01"] * 5 + ["M-02"] * 5,
            "temperature_c": [0.0, 0.1, -0.1, 0.05, 2.0, 10.0, 10.1, 9.9, 10.05, 9.95],
        }
    )

    global_result = analyse_frame(
        frame,
        AnalysisConfig(
            method="robust-z",
            threshold=4.0,
            features=("temperature_c",),
        ),
    )
    grouped_result = analyse_frame(
        frame,
        AnalysisConfig(
            method="robust-z",
            threshold=4.0,
            features=("temperature_c",),
            group_column="machine_id",
            min_group_size=5,
        ),
    )

    assert not bool(global_result.loc[4, "is_detected_anomaly"])
    assert bool(grouped_result.loc[4, "is_detected_anomaly"])


def test_file_pipeline_generates_expected_artifacts(tmp_path) -> None:
    input_path = save_dataset(
        generate_production_data(GenerationConfig(rows=250, anomaly_rate=0.04)),
        tmp_path / "input.csv",
    )
    outputs = run_analysis(input_path, tmp_path / "artifacts", AnalysisConfig())

    assert all(path.exists() for path in outputs.values())
    metrics = json.loads(outputs["metrics"].read_text(encoding="utf-8"))
    assert metrics["rows"] == 250
    assert "f1_score" in metrics
