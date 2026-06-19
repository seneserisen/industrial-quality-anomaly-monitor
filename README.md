# Industrial Quality Anomaly Monitor

A reproducible manufacturing-data project that generates realistic production measurements, detects abnormal process behaviour, and exports engineering KPIs and visual reports.

This portfolio project connects industrial production experience with practical Python, data validation, statistical monitoring, machine learning, testing, Docker, and CI/CD.

## What the project demonstrates

- Synthetic multi-machine production data with controllable failure injection
- Interpretable anomaly detection using robust median/MAD statistics
- Multivariate anomaly detection using Isolation Forest
- Data validation and explicit failure messages
- Precision, recall, and F1 evaluation when labels are available
- CSV, JSON, and PNG reporting artifacts
- Unit and integration tests
- GitHub Actions across Python 3.10–3.12
- Containerised command-line execution

## Monitored process variables

| Signal | Engineering meaning |
|---|---|
| `temperature_c` | Thermal condition of the process or equipment |
| `vibration_mm_s` | Mechanical health and potential bearing wear |
| `pressure_bar` | Pneumatic or hydraulic process stability |
| `cycle_time_s` | Throughput and process-delay indicator |
| `quality_score` | Simplified downstream quality measurement |

Injected failure modes include overheating, bearing wear, pressure loss, and slow-cycle behaviour.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Generate a deterministic dataset:

```bash
quality-monitor generate \
  --rows 3000 \
  --machines 4 \
  --anomaly-rate 0.04 \
  --seed 42 \
  --output data/production_data.csv
```

Run the interpretable baseline:

```bash
quality-monitor analyse \
  --input data/production_data.csv \
  --output-dir artifacts/robust-z \
  --method robust-z \
  --threshold 4.0
```

Run the multivariate model:

```bash
quality-monitor analyse \
  --input data/production_data.csv \
  --output-dir artifacts/isolation-forest \
  --method isolation-forest \
  --contamination 0.04
```

The analysis creates:

```text
artifacts/
├── metrics.json
├── monitoring_summary.png
└── scored_production_data.csv
```

## Example KPI output

```json
{
  "detected_anomalies": 113,
  "detected_anomaly_rate": 0.0377,
  "f1_score": 0.89,
  "precision": 0.92,
  "recall": 0.87,
  "rows": 3000
}
```

Exact values depend on detector settings. The generated dataset is labelled only so detector behaviour can be measured; production datasets normally require expert review or maintenance-event labels.

## Why two detection methods?

### Robust Z-score

The median and median absolute deviation are less sensitive to extreme measurements than the mean and standard deviation. The maximum robust score across features is easy to inspect and explain during an engineering review.

### Isolation Forest

Isolation Forest learns multivariate structure and can identify unusual combinations such as slightly elevated temperature together with vibration and cycle-time drift. It is less directly interpretable, so the robust baseline remains valuable.

## Development

```bash
make install
make lint
make test
make demo
```

Or run the tools directly:

```bash
ruff check .
pytest --cov=quality_monitor --cov-report=term-missing
```

## Docker

```bash
docker build -t industrial-quality-monitor .
docker run --rm -v "$PWD:/workspace" industrial-quality-monitor \
  generate --rows 1000 --output /workspace/data/production_data.csv
```

## Repository structure

```text
.
├── .github/workflows/ci.yml
├── docs/architecture.md
├── src/quality_monitor/
│   ├── cli.py
│   ├── data_generation.py
│   ├── detectors.py
│   ├── pipeline.py
│   └── reporting.py
├── tests/
├── Dockerfile
├── Makefile
└── pyproject.toml
```

See [docs/architecture.md](docs/architecture.md) for the data flow, design decisions, and extension points.

## Responsible use

This repository is a portfolio and learning system, not a certified quality-control product. Thresholds, sensor calibration, maintenance decisions, and safety actions must be validated by domain experts using real process context.

## Author

Sadik Enes Erisen — M.Sc. Autonomy Technologies, FAU Erlangen-Nürnberg; B.Sc. Electrical and Electronics Engineering.

## Licence

MIT
