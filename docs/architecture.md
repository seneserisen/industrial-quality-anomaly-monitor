# Architecture

```text
Synthetic generator / CSV input
            |
            v
      Input validation
            |
            v
  Feature matrix preparation
       /            \
Robust Z-score   Isolation Forest
       \            /
        Anomaly score + flag
                |
                v
    CSV + JSON KPIs + PNG report
```

## Design choices

- **Synthetic data first:** the project is runnable without confidential factory data.
- **Robust Z-score baseline:** median and median absolute deviation make the baseline easy to explain to production engineers.
- **Isolation Forest alternative:** captures multivariate combinations and provides a useful comparison with the interpretable baseline.
- **Label separation:** injected labels are used only for evaluation, never as detector inputs.
- **Reproducibility:** every stochastic component accepts a fixed seed, tests run in CI, and dependencies are bounded.

## Extension points

1. Fit baselines per machine or product variant.
2. Stream measurements through MQTT or Kafka.
3. Store KPIs in PostgreSQL or TimescaleDB.
4. Add drift monitoring and model-retraining policies.
5. Expose results with FastAPI and a lightweight dashboard.
