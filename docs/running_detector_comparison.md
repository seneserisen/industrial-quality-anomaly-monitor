# Running the Detector Comparison

The comparison command implements the frozen experiment defined in
[`detector_comparison_protocol.md`](detector_comparison_protocol.md).

## Command

```bash
quality-monitor compare \
  --output-dir artifacts/detector_comparison
```

The runner regenerates one deterministic labelled dataset and reuses the same in-memory frame for:

1. Global robust Z-score
2. Machine-aware robust Z-score
3. Isolation Forest

The published configuration is fixed to:

- 3,000 rows
- 4 machines
- 4% injected anomaly rate
- Dataset seed 42
- Robust Z-score threshold 4.0
- Machine-aware minimum group size 20
- Isolation Forest contamination 0.04 and random seed 42
- Five complete detector runs for median runtime reporting

## Outputs

```text
artifacts/detector_comparison/
├── comparison_summary.json
└── comparison_summary.csv
```

The JSON report contains experiment metadata, detector parameters, confusion counts, precision,
recall, F1, false-positive and false-negative rates, score summaries, median runtime, and recall by
injected fault type. The CSV report contains the same detector-level information in a flat format.

Runtime measurements include detector construction, fitting where applicable, scoring, and binary
prediction. They exclude dataset generation and file writing. Runtime values are environment-dependent
indicators, not universal performance claims.

## Reproducibility boundary

The detector outputs are checked across repeated runs. The command raises an error if repeated runs
produce different scores or predictions under the frozen random seeds. Runtime is expected to vary,
so it is not part of deterministic equality checks in the test suite.

## Limitations

The dataset contains deliberately separable synthetic faults. The same frame is used to establish
reference distributions and evaluate detection. These results are not evidence of production readiness.
Real deployments require healthy reference data, temporal validation, sensor-quality checks,
maintenance labels, and cost-based threshold calibration.
