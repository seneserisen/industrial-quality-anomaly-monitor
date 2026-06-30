"""Command-line interface for data generation and anomaly analysis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from quality_monitor.comparison import run_detector_comparison
from quality_monitor.data_generation import GenerationConfig, generate_production_data, save_dataset
from quality_monitor.pipeline import AnalysisConfig, run_analysis


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="quality-monitor",
        description="Generate and analyse industrial production quality data.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    generate = commands.add_parser("generate", help="Generate a labelled synthetic dataset")
    generate.add_argument("--rows", type=int, default=3000)
    generate.add_argument("--machines", type=int, default=4)
    generate.add_argument("--anomaly-rate", type=float, default=0.04)
    generate.add_argument("--seed", type=int, default=42)
    generate.add_argument("--output", type=Path, default=Path("data/production_data.csv"))

    analyse = commands.add_parser("analyse", aliases=["analyze"], help="Run anomaly detection")
    analyse.add_argument("--input", type=Path, required=True)
    analyse.add_argument("--output-dir", type=Path, default=Path("artifacts"))
    analyse.add_argument(
        "--method",
        choices=["robust-z", "isolation-forest"],
        default="robust-z",
    )
    analyse.add_argument("--contamination", type=float, default=0.04)
    analyse.add_argument("--threshold", type=float, default=4.0)
    analyse.add_argument(
        "--group-column",
        help="Column defining robust-baseline groups, for example machine_id.",
    )
    analyse.add_argument(
        "--min-group-size",
        type=int,
        default=5,
        help="Minimum rows required before a group uses its own robust baseline.",
    )

    compare = commands.add_parser(
        "compare",
        help="Run the frozen three-detector comparison experiment",
    )
    compare.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/detector_comparison"),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "generate":
        config = GenerationConfig(
            rows=args.rows,
            machines=args.machines,
            anomaly_rate=args.anomaly_rate,
            random_seed=args.seed,
        )
        output = save_dataset(generate_production_data(config), args.output)
        print(f"Generated dataset: {output}")
        return 0

    if args.command == "compare":
        outputs = run_detector_comparison(args.output_dir)
        print("Comparison artifacts:")
        for name, path in outputs.items():
            print(f"  {name}: {path}")
        return 0

    if args.min_group_size < 2:
        parser.error("--min-group-size must be at least 2")
    if args.group_column is None and args.min_group_size != 5:
        parser.error("--min-group-size requires --group-column")
    if args.method != "robust-z" and args.group_column is not None:
        parser.error("--group-column is only supported with --method robust-z")

    config = AnalysisConfig(
        method=args.method,
        contamination=args.contamination,
        threshold=args.threshold,
        group_column=args.group_column,
        min_group_size=args.min_group_size,
    )
    outputs = run_analysis(args.input, args.output_dir, config)
    metrics = json.loads(outputs["metrics"].read_text(encoding="utf-8"))
    print(json.dumps(metrics, indent=2, sort_keys=True))
    print("Artifacts:")
    for name, path in outputs.items():
        print(f"  {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
