# Testing and Verification

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## Fast checks

```bash
ruff check .
pytest --cov=quality_monitor --cov-report=term-missing
```

Equivalent Make targets:

```bash
make lint
make test
```

## Demonstration workflow

```bash
make demo
```

Or run explicitly:

```bash
quality-monitor generate \
  --rows 3000 \
  --machines 4 \
  --anomaly-rate 0.04 \
  --seed 42 \
  --output data/production_data.csv

quality-monitor analyse \
  --input data/production_data.csv \
  --output-dir artifacts/robust-z \
  --method robust-z \
  --threshold 4.0
```

## Grouped baseline check

```bash
quality-monitor analyse \
  --input data/production_data.csv \
  --output-dir artifacts/machine-aware \
  --method robust-z \
  --threshold 4.0 \
  --group-column machine_id \
  --min-group-size 20
```

Verify that groups below the sample gate use the documented global fallback and that the output identifies grouping behavior clearly.

## Isolation Forest check

```bash
quality-monitor analyse \
  --input data/production_data.csv \
  --output-dir artifacts/isolation-forest \
  --method isolation-forest \
  --contamination 0.04
```

## Docker check

```bash
docker build -t industrial-quality-monitor .
docker run --rm -v "$PWD:/workspace" industrial-quality-monitor \
  generate --rows 1000 --output /workspace/data/production_data.csv
```

Do not mark Docker behavior verified when only local Python execution ran.

## Required data-integrity checks

For affected changes, verify relevant:

- required columns, types, units, nulls, infinities, duplicates, and invalid ranges;
- deterministic output for identical seed and configuration;
- row identity and label alignment after transformations;
- train, validation, test, or reference-population separation;
- preprocessing fitted only on allowed data;
- grouped baseline behavior and small-group fallback;
- stable feature ordering between fit and score;
- explicit errors for empty or invalid inputs;
- output CSV, JSON, and PNG existence and readability.

## Required evaluation checks

- report dataset size and class counts;
- define positive-label semantics;
- verify confusion-matrix counts independently;
- report precision, recall, and F1 only when labels are available;
- separate threshold selection from final held-out evaluation;
- avoid claiming real-factory generalisation from synthetic data;
- record seed, anomaly rate, detector, threshold or contamination, and group settings.

## CI boundary

The current workflow installs the package and runs Ruff and pytest with coverage on Python 3.10–3.12. It does not establish real-factory accuracy, streaming scalability, operational safety, or production deployment readiness.

## Baseline failures

Record pre-existing failures in `docs/project_status.md` before attributing them to new work.
