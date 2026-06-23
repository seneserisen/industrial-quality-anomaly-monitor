import json

import pytest

from quality_monitor.cli import build_parser, main


def test_analyse_parser_accepts_grouped_baseline_options() -> None:
    args = build_parser().parse_args(
        [
            "analyse",
            "--input",
            "production.csv",
            "--method",
            "robust-z",
            "--group-column",
            "machine_id",
            "--min-group-size",
            "12",
        ]
    )

    assert args.group_column == "machine_id"
    assert args.min_group_size == 12


def test_grouped_analysis_runs_end_to_end_from_cli(tmp_path, capsys) -> None:
    dataset = tmp_path / "production.csv"
    output_dir = tmp_path / "artifacts"

    generate_exit = main(
        [
            "generate",
            "--rows",
            "100",
            "--machines",
            "2",
            "--anomaly-rate",
            "0.05",
            "--seed",
            "7",
            "--output",
            str(dataset),
        ]
    )
    analyse_exit = main(
        [
            "analyse",
            "--input",
            str(dataset),
            "--output-dir",
            str(output_dir),
            "--method",
            "robust-z",
            "--group-column",
            "machine_id",
            "--min-group-size",
            "10",
        ]
    )

    assert generate_exit == 0
    assert analyse_exit == 0
    assert dataset.exists()
    assert (output_dir / "scored_production_data.csv").exists()
    assert (output_dir / "monitoring_summary.png").exists()

    metrics = json.loads((output_dir / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["rows"] == 100
    assert "detected_anomalies" in metrics

    output = capsys.readouterr().out
    assert "Generated dataset:" in output
    assert "Artifacts:" in output


def test_grouped_options_are_rejected_for_isolation_forest(capsys) -> None:
    with pytest.raises(SystemExit):
        main(
            [
                "analyse",
                "--input",
                "production.csv",
                "--method",
                "isolation-forest",
                "--group-column",
                "machine_id",
            ]
        )

    assert "only supported with --method robust-z" in capsys.readouterr().err
