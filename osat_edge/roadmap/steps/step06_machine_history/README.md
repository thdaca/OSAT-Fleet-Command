# STEP06_MACHINE_HISTORY: Exact-machine healthy history


**Primary contributors:** Data Pipeline & Systems Integration + Machine Learning & Predictive Maintenance.

**Inputs:** one machine identity, feature windows and confirmed-healthy intervals.

**Outputs:** windows fully contained in healthy intervals.

## Start here

- [history.py](history.py)

Read [the behavior tests](../step07_machine_model/tests/test_steps04_07_models.py), then run from the repository root:

```powershell
.venv\Scripts\python -m unittest osat_edge.roadmap.steps.step07_machine_model.tests.test_steps04_07_models -v
```

Preserve [evidence and authority boundaries](../../../../docs/EVIDENCE.md).
Use [team guides](../../../../docs/teams/README.md) for a small first contribution.
