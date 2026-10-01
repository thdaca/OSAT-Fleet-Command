# STEP03_PHYSICAL_RESIDUALS: Physical residuals


**Primary contributors:** Machine Learning & Predictive Maintenance + Semiconductor Failure Research.

**Inputs:** overlapping windows, approved Step01 relations and fitted parameters.

**Outputs:** physics Feature values or absence when support/domain is insufficient.

## Start here

- [residuals.py](residuals.py)

Read [the behavior tests](tests/test_steps01_03_physics.py), then run from the repository root:

```powershell
.venv\Scripts\python -m unittest osat_edge.roadmap.steps.step03_physical_residuals.tests.test_steps01_03_physics -v
```

Preserve [evidence and authority boundaries](../../../../docs/EVIDENCE.md).
Use [team guides](../../../../docs/teams/README.md) for a small first contribution.
