# STEP04_FAMILY_DATA: Same-family training data


**Primary contributors:** Data Pipeline & Systems Integration + Machine Learning & Predictive Maintenance.

**Inputs:** real OSAT samples, machine IDs and future observed events.

**Outputs:** validated FamilyDataset and training arrays.

## Start here

- [dataset.py](dataset.py)

Read [the behavior tests](../step07_machine_model/tests/test_steps04_07_models.py), then run from the repository root:

```powershell
.venv\Scripts\python -m unittest osat_edge.roadmap.steps.step07_machine_model.tests.test_steps04_07_models -v
```

Preserve [evidence and authority boundaries](../../../../docs/EVIDENCE.md).
Use [team guides](../../../../docs/teams/README.md) for a small first contribution.
