# Detector Comparison Protocol

## Status

Design specification for the next v0.2 milestone. No comparison metrics in this document are measured results.

## Objective

Compare three anomaly-detection configurations under the same deterministic conditions:

1. Global robust Z-score
2. Machine-aware robust Z-score
3. Isolation Forest

The comparison must be reproducible, fair, and explicit about the limitations of synthetic manufacturing data.

## Research question

How do an interpretable global statistical baseline, a machine-aware statistical baseline, and a multivariate Isolation Forest differ in detection quality, false-alarm behaviour, fault coverage, and execution time on the same labelled synthetic production dataset?

## Frozen dataset configuration

The first published comparison will use exactly one generated CSV with:

| Parameter | Value |
|---|---:|
| Rows | 3,000 |
| Machines | 4 |
| Injected anomaly rate | 0.04 |
| Random seed | 42 |
| Sampling interval | 1 minute |

Generation command:

```bash
quality-monitor generate \
  --rows 3000 \
  --machines 4 \
  --anomaly-rate 0.04 \
  --seed 42 \
  --output examples/detector_comparison/production_data.csv
```

The generated CSV is the single source dataset for all three configurations. A detector must not receive a separately generated dataset.

## Feature set

All configurations use the same five numeric features:

- `temperature_c`
- `vibration_mm_s`
- `pressure_bar`
- `cycle_time_s`
- `quality_score`

The label columns are not detector inputs:

- `is_injected_anomaly`
- `anomaly_type`

They are used only after scoring to calculate evaluation metrics.

## Detector configurations

### A. Global robust Z-score

```text
method: robust-z
threshold: 4.0
group_column: null
min_group_size: 5  # inactive without grouping
```

Purpose:
Provide the simplest interpretable baseline using one median and median absolute deviation per feature across the complete dataset.

### B. Machine-aware robust Z-score

```text
method: robust-z
threshold: 4.0
group_column: machine_id
min_group_size: 20
```

Purpose:
Measure whether separate machine reference distributions reduce false alarms from legitimate machine offsets or reveal local anomalies hidden by the global population.

A minimum group size of 20 is fixed for the published comparison. It is a demonstration choice, not a validated manufacturing requirement.

### C. Isolation Forest

```text
method: isolation-forest
contamination: 0.04
random_seed: 42
```

Purpose:
Provide a multivariate model that can detect unusual combinations of measurements rather than only large deviations in individual features.

## Fairness rules

1. Use the same frozen CSV for all configurations.
2. Use the same feature columns in the same order.
3. Do not tune thresholds or contamination after viewing comparison labels.
4. Do not remove difficult fault types from the evaluation.
5. Do not regenerate the dataset to improve a detector's result.
6. Record every parameter in the published output.
7. Treat runtime measurements as environment-dependent indicators, not universal benchmarks.
8. Keep synthetic performance claims separate from real-factory expectations.

## Required metrics

Each detector result must report:

### Dataset and configuration

- `rows`
- `machines`
- `injected_anomalies`
- `injected_anomaly_rate`
- `method`
- `threshold` or `contamination`
- `group_column`
- `min_group_size`
- `random_seed`

### Detection counts

- `detected_anomalies`
- `true_positives`
- `false_positives`
- `true_negatives`
- `false_negatives`

### Classification metrics

- `precision`
- `recall`
- `f1_score`
- `false_positive_rate`
- `false_negative_rate`

### Operational indicators

- `mean_anomaly_score`
- `max_anomaly_score`
- `runtime_seconds`

### Fault-type coverage

For each injected fault type:

- injected count
- detected count
- recall

Required fault types:

- overheating
- bearing wear
- pressure loss
- slow cycle

## Timing method

Use `time.perf_counter()` immediately before and after detector scoring.

Timing includes:

- detector fitting where applicable
- score calculation
- binary anomaly prediction

Timing excludes:

- synthetic dataset generation
- CSV loading
- plot rendering
- writing output files

The report must state the Python version and platform when measured.

## Required artifacts

The implementation milestone should produce:

```text
examples/detector_comparison/
├── production_data.csv
├── comparison_summary.json
├── comparison_summary.csv
├── detector_comparison.png
├── global_robust_metrics.json
├── machine_aware_robust_metrics.json
└── isolation_forest_metrics.json
```

The scored row-level CSV files should be generated locally but do not need to be committed if their size makes the repository noisy. The summary artifacts must remain small and reviewable.

## Proposed JSON schema

The structure below defines fields, not measured values:

```json
{
  "experiment": {
    "rows": 3000,
    "machines": 4,
    "anomaly_rate": 0.04,
    "dataset_seed": 42,
    "features": [
      "temperature_c",
      "vibration_mm_s",
      "pressure_bar",
      "cycle_time_s",
      "quality_score"
    ],
    "python_version": "<measured>",
    "platform": "<measured>"
  },
  "detectors": [
    {
      "name": "global_robust_z",
      "parameters": {
        "threshold": 4.0,
        "group_column": null,
        "min_group_size": null
      },
      "metrics": {
        "detected_anomalies": null,
        "true_positives": null,
        "false_positives": null,
        "true_negatives": null,
        "false_negatives": null,
        "precision": null,
        "recall": null,
        "f1_score": null,
        "false_positive_rate": null,
        "false_negative_rate": null,
        "mean_anomaly_score": null,
        "max_anomaly_score": null,
        "runtime_seconds": null
      },
      "fault_type_recall": {
        "overheating": null,
        "bearing_wear": null,
        "pressure_loss": null,
        "slow_cycle": null
      }
    }
  ]
}
```

## Comparison plot specification

The first comparison figure should contain three clearly labelled views:

1. Precision, recall, and F1 by detector
2. False positives and false negatives by detector
3. Recall by injected fault type

Do not place raw anomaly scores from different detector families on one shared numeric axis without normalisation. Robust Z-scores and Isolation Forest scores do not have directly comparable scales.

## Interpretation questions

The final report must answer:

1. Did machine-aware baselines reduce false positives compared with the global baseline?
2. Did they improve recall for any local machine anomaly pattern?
3. Which injected fault type was hardest for each detector?
4. Did Isolation Forest improve multivariate detection at the cost of interpretability?
5. Were runtime differences meaningful at 3,000 rows?
6. Which detector would be preferred for an engineer-facing alert system, and why?
7. Which findings are specific to the synthetic generator?

## Required caveats

The published report must state that:

- Synthetic faults are deliberately separable.
- The same dataset is currently used to establish baselines and evaluate detections.
- The comparison is not evidence of production readiness.
- Real deployment requires healthy reference data, temporal validation, sensor-quality checks, maintenance labels, and cost-based threshold calibration.
- Runtime values depend on hardware, operating system, Python version, and background load.

## Implementation plan

The protocol should be implemented in later sessions as separate, reviewable increments:

### Session 1 — protocol design

- Add this document
- Review fields, fairness rules, and artifact names
- Do not publish metrics

### Session 2 — reusable evaluation functions

- Add confusion-count and fault-type metrics
- Add unit tests
- Do not add plotting yet

### Session 3 — comparison runner

- Run all three configurations on one frozen dataset
- Export JSON and CSV summaries
- Add reproducibility tests

### Session 4 — visualisation and interpretation

- Add the comparison plot
- Publish measured artifacts
- Add engineering interpretation to the README

## Acceptance criteria

The milestone is complete when a reviewer can:

1. Generate or use the frozen dataset.
2. Run one documented comparison command.
3. Reproduce all three detector summaries.
4. Inspect confusion counts and fault-type recall.
5. View one comparison figure.
6. Understand the parameter choices and limitations.
7. Confirm that all published numbers came from committed reproducible code.
