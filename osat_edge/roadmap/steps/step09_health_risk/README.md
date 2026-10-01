# STEP09_HEALTH_RISK: Deterministic health


**Primary contributors:** Machine Learning & Predictive Maintenance + Reliability & Data Research.

**Inputs:** telemetry status and exact-machine deviations.

**Outputs:** subsystem-first state with persistence/hysteresis or UNKNOWN.

## Start here

- [health.py](health.py)

Read [the behavior tests](tests/test_step09_health.py), then run from the repository root:

```powershell
.venv\Scripts\python -m unittest osat_edge.roadmap.steps.step09_health_risk.tests.test_step09_health -v
```

Preserve [evidence and authority boundaries](../../../../docs/EVIDENCE.md).
Use [team guides](../../../../docs/teams/README.md) for a small first contribution.
