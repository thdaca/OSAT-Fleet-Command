# STEP05_FAMILY_MODEL: Family risk model


**Primary contributors:** Machine Learning & Predictive Maintenance + Reliability & Data Research.

**Inputs:** validated real same-family event history.

**Outputs:** uncalibrated advisory risk_score; never a health override.

## Start here

- [model.py](model.py)

Read [the behavior tests](../step07_machine_model/tests/test_steps04_07_models.py), then run from the repository root:

```powershell
.venv\Scripts\python -m unittest osat_edge.roadmap.steps.step07_machine_model.tests.test_steps04_07_models -v
```

Preserve [evidence and authority boundaries](../../../../docs/EVIDENCE.md).
Use [team guides](../../../../docs/teams/README.md) for a small first contribution.
