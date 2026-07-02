# Project Status

- Last updated: 2 July 2026
- Maturity: Portfolio MVP
- Current package version: `0.1.0`
- Default branch: `main`

## Implemented and documented

- deterministic synthetic multi-machine data generation;
- overheating, bearing-wear, pressure-loss, and slow-cycle failure injection;
- input validation and explicit failure reporting;
- global robust median/MAD detector;
- machine/group-aware robust detector with minimum-group fallback;
- Isolation Forest multivariate detector;
- precision, recall, and F1 evaluation when labels are available;
- scored CSV, metrics JSON, and PNG reporting;
- CLI, Make targets, Docker execution, tests, and Python 3.10–3.12 CI.

## Current limitations

- public KPI examples use deliberately separable synthetic failure signatures;
- real manufacturing data, sensor calibration, maintenance labels, and expert validation are not included;
- anomaly detection does not establish root cause;
- no streaming ingestion or online model lifecycle is implemented;
- no production authentication, monitoring, retention, or incident process exists;
- thresholds are demonstration settings, not universal operational limits.

## Verification status

| Check | Status | Evidence or boundary |
|---|---|---|
| Package installation | Automated | Python 3.10–3.12 CI |
| Ruff lint | Automated | `.github/workflows/ci.yml` |
| pytest and coverage | Automated | CLI, unit, and integration behavior |
| Deterministic synthetic generation | Implemented and tested | Fixed seed and configuration |
| Artifact generation | Implemented and tested | CSV, JSON, PNG |
| Docker build/run | Documented | Must be run separately when Docker behavior changes |
| Real-factory validation | Not performed | Requires authorised real data and domain review |
| Data leakage audit | Partially implicit | Must be explicit for future training/split features |

## Highest-value next improvements

1. Add a deterministic three-detector comparison runner covering global robust Z-score, machine-aware robust Z-score, and Isolation Forest.
2. Produce one comparison report with aligned rows, thresholds, metrics, and disagreement cases.
3. Add explicit split and leakage controls before introducing learned preprocessing or tuning.
4. Add drift or time-window evaluation using synthetic temporal scenarios.
5. Document calibration and deployment requirements for a hypothetical real-factory pilot without claiming implementation.

## Main risks and technical debt

- excellent synthetic scores can mislead reviewers if the data-generation assumptions are not visible;
- grouped and global baselines can be compared incorrectly if row identity or reference populations drift;
- contamination and threshold tuning can leak test information;
- future time-series work may violate independence assumptions used by random splits;
- dependencies use ranges rather than a lockfile;
- generated examples can become stale after model changes.

## Active governance work

The `chore/ai-project-governance` branch adds project-specific AI-assisted engineering instructions and review controls without changing detector behavior, tests, or current CI.
