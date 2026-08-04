# Industrial Quality Monitor — Copilot Instructions

- Read `AGENTS.md` and the relevant `docs/` files before substantial changes.
- Use `docs/testing.md` for exact commands and report only checks that actually ran.
- Preserve deterministic seeded generation, row identity, label alignment, feature ordering, and split integrity.
- Prevent target leakage, train/test leakage, and fitting preprocessing on held-out data.
- Keep global, grouped, and Isolation Forest behavior explicit; preserve documented small-group fallback rules.
- Do not silently discard invalid rows, failed files, anomalies, or groups.
- Treat anomaly scores as review signals, not root-cause or safety decisions.
- Do not invent datasets, metrics, model performance, APIs, or successful evaluations.
- Add behavior-focused tests for valid, invalid, empty, grouped, deterministic, and artifact cases.
- Keep synthetic results clearly separated from real-factory claims.
- Preserve unrelated work and avoid speculative dashboards or unnecessary dependencies.
- Update schemas, metric definitions, examples, limitations, and project status when behavior changes.
