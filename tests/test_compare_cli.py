from pathlib import Path

from quality_monitor.cli import build_parser, main


def test_compare_parser_uses_default_output_directory() -> None:
    args = build_parser().parse_args(["compare"])
    assert args.output_dir == Path("artifacts/detector_comparison")


def test_compare_cli_reports_artifacts(tmp_path, monkeypatch, capsys) -> None:
    summary_json = tmp_path / "comparison_summary.json"
    summary_csv = tmp_path / "comparison_summary.csv"

    def fake_comparison(output_dir):
        assert output_dir == tmp_path
        return {"summary_json": summary_json, "summary_csv": summary_csv}

    monkeypatch.setattr("quality_monitor.cli.run_detector_comparison", fake_comparison)

    assert main(["compare", "--output-dir", str(tmp_path)]) == 0
    output = capsys.readouterr().out
    assert "Comparison artifacts:" in output
    assert str(summary_json) in output
    assert str(summary_csv) in output
