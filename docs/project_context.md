# Project Context

## Identity

- Project: Industrial Quality Anomaly Monitor
- Owner: Sadik Enes Erisen
- Maturity: Portfolio MVP
- Stack: Python 3.10–3.12, NumPy, pandas, scikit-learn, Matplotlib, pytest, Ruff, Docker
- Repository visibility: Public
- Licence: MIT

## Purpose

Provide a reproducible manufacturing-data project that generates synthetic multi-machine measurements, detects abnormal process behaviour, exports engineering KPIs and reports, and demonstrates data validation, interpretable statistics, machine learning, testing, and containerised execution.

## Intended users

- manufacturing and quality engineers evaluating software concepts;
- data and automation engineers reviewing reproducible pipelines;
- portfolio reviewers assessing Enes's industrial and Python engineering skills;
- students learning responsible anomaly-monitoring workflows.

## Current validated scope

- deterministic synthetic production data with injected failure labels;
- temperature, vibration, pressure, cycle-time, and quality-score signals;
- robust median/MAD anomaly detection;
- global and machine/group-specific reference baselines;
- documented fallback for groups below the minimum sample size;
- multivariate Isolation Forest detection;
- precision, recall, and F1 evaluation when labels are present;
- CSV, JSON, and PNG artifacts;
- input validation and explicit failure messages;
- unit, integration, and CLI tests;
- Python 3.10–3.12 CI and Docker execution.

## Core invariants

1. Synthetic ground-truth labels remain separate from detector predictions.
2. Seeded generation is reproducible for identical configuration.
3. Row identity, labels, features, and scores remain aligned through the pipeline.
4. Preprocessing and model fitting do not use held-out information improperly.
5. Invalid data is reported rather than silently discarded.
6. Synthetic benchmark results are not presented as real-factory performance.
7. Thresholds and model outputs are review aids, not automated safety or maintenance decisions.

## Current non-goals

- certified process monitoring;
- automatic machine shutdown or maintenance decisions;
- claims of transfer to a real factory without calibration;
- proprietary company data or internal process recipes;
- root-cause diagnosis from anomaly scores alone;
- high-volume streaming or production cloud infrastructure;
- replacing domain-expert review.

## Interfaces requiring compatibility review

- `quality-monitor` CLI arguments and exit behavior;
- input CSV schema and units;
- scored CSV, metrics JSON, and report filenames;
- detector method names and parameters;
- grouped-baseline fallback semantics;
- metric definitions and label conventions;
- Docker entry point and mounted paths.

## Definition of done

- [ ] Acceptance criteria are explicit.
- [ ] Data schema and units are documented.
- [ ] Leakage and split risks are considered.
- [ ] Valid, invalid, empty, grouped, deterministic, and artifact cases are tested where relevant.
- [ ] Metrics are reproduced from a documented dataset and configuration.
- [ ] Public examples are labelled as synthetic.
- [ ] Documentation and project status match behavior.
- [ ] Enes can explain the detector, evaluation design, limitations, and operational boundary.
