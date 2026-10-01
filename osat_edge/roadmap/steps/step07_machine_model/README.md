# STEP07_MACHINE_MODEL: Exact-machine baseline


**Primary contributors:** Machine Learning & Predictive Maintenance + Reliability & Data Research.

**Inputs:** healthy context-specific windows and physics parameters.

**Outputs:** isolated baseline, deviations/unavailable reasons and validated JSON persistence.

## Start here

- [model.py](model.py)
- [model_io.py](model_io.py)

Read [the behavior tests](tests/test_steps04_07_models.py), then run from the repository root:

```powershell
.venv\Scripts\python -m unittest osat_edge.roadmap.steps.step07_machine_model.tests.test_steps04_07_models -v
```

Preserve [evidence and authority boundaries](../../../../docs/EVIDENCE.md).
Use [team guides](../../../../docs/teams/README.md) for a small first contribution.

`evaluate_machine_model` enforces operational origin/mode policy. The numerical
entry point is for isolated research callers and grants no operational authority.
`model_io.py` stores JSON with caller-supplied source/calibration/validation lineage.
