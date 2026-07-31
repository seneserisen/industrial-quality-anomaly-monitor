# Industrial Quality Anomaly Monitor

A reproducible Python project for comparing interpretable statistical monitoring with a multivariate anomaly detector on controlled manufacturing data.

The repository is built around a practical question: when machines have different normal operating ranges, what changes when one global baseline is replaced by machine-aware baselines, and how does either approach compare with Isolation Forest?

## Current status

The executable pipeline currently provides:

- deterministic multi-machine data generation with labelled fault injection;
- global median/MAD robust scoring;
- machine- or group-specific robust baselines with a minimum-sample fallback;
- Isolation Forest scoring;
- precision, recall, F1, confusion counts and per-fault recall;
- a shared-dataset comparison runner for all three detector configurations;
- CSV, JSON and PNG reporting for individual analyses;
- JSON and CSV summaries for detector comparisons;
- command-line, unit, integration and reproducibility tests;
- Docker execution and Python 3.10–3.12 CI.

The data is synthetic. The software and comparison protocol are implemented; real-factory calibration and validation are not.

## Signals and injected conditions

| Signal | Intended interpretation |
| --- | --- |
| `temperature_c` | Thermal condition of a process or machine |
| `vibration_mm_s` | Mechanical condition indicator |
| `pressure_bar` | Pneumatic or hydraulic stability |
| `cycle_time_s` | Throughput and delay indicator |
| `quality_score` | Simplified downstream quality measurement |

The generator can inject overheating, bearing-wear, pressure-loss and slow-cycle patterns. They are deliberately controlled software fixtures, not calibrated physical failure models.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Generate one repeatable dataset:

```bash
quality-monitor generate \
  --rows 3000 \
  --machines 4 \
  --anomaly-rate 0.04 \
  --seed 42 \
  --output data/production_data.csv
```

Run a machine-aware robust analysis:

```bash
quality-monitor analyse \
  --input data/production_data.csv \
  --output-dir artifacts/machine-aware \
  --method robust-z \
  --threshold 4.0 \
  --group-column machine_id \
  --min-group-size 20
```

Run Isolation Forest on the same feature family:

```bash
quality-monitor analyse \
  --input data/production_data.csv \
  --output-dir artifacts/isolation-forest \
  --method isolation-forest \
  --contamination 0.04
```

Each analysis writes scored rows, metrics and a monitoring figure.

## Deterministic detector comparison

```bash
quality-monitor compare \
  --output-dir artifacts/detector_comparison
```

The command generates one in-memory dataset and reuses the same rows and feature order for:

1. global robust Z-score;
2. machine-aware robust Z-score;
3. Isolation Forest.

It records configuration, confusion counts, precision, recall, F1, false-positive and false-negative rates, per-fault recall and median runtime across repeated detector runs. Runtime is descriptive and environment-dependent; deterministic equality checks cover scores and predictions rather than wall-clock duration.

See the [comparison protocol](docs/detector_comparison_protocol.md) and [run guide](docs/running_detector_comparison.md).

## Reproduced baseline

The committed global robust-Z example uses 3,000 rows, four machines, a 4% injected anomaly rate, seed 42 and threshold 4.0.

| Metric | Result |
| --- | ---: |
| Injected anomalies | 120 |
| Detected anomalies | 122 |
| Precision | 0.9836 |
| Recall | 1.0000 |
| F1 | 0.9917 |

The complete output is stored in [`examples/robust_z_metrics.json`](examples/robust_z_metrics.json). These strong values reflect deliberately separable synthetic signatures and should not be interpreted as expected production performance.

## Technology

| Area | Tools |
| --- | --- |
| Data and numerics | Python, NumPy, pandas |
| Detection | Robust median/MAD statistics, scikit-learn Isolation Forest |
| Reporting | Matplotlib, CSV and JSON |
| Interface | Installed command-line application |
| Verification | pytest, pytest-cov, Ruff and GitHub Actions |
| Reproducible execution | Docker and Make |

## Development

```bash
make install
make lint
make test
make demo
```

Or run the checks directly:

```bash
ruff check .
pytest --cov=quality_monitor --cov-report=term-missing
```

## Next work

The next useful milestone is not another headline score. It is a more inspectable comparison:

- preserve aligned row identifiers across detector outputs;
- report pairwise detector agreement and disagreement;
- show which fault types and machines cause disagreements;
- add a comparison figure and written engineering interpretation;
- separate healthy reference data from evaluation data in a later protocol;
- add temporal validation before any claim about deployment behavior.

## Limits and responsible use

- Synthetic faults are intentionally easier to control than real process behavior.
- The current comparison uses the same generated frame to establish baselines and evaluate detections.
- Group size, thresholds and contamination are demonstration parameters, not validated operating limits.
- Runtime depends on hardware, operating system, Python version and background load.
- Real use would require sensor-quality checks, healthy reference data, maintenance labels, temporal validation, expert review and cost-aware threshold selection.
- This is not a certified quality-control or safety system.

The architecture and extension points are described in [`docs/architecture.md`](docs/architecture.md).

## Licence

MIT
