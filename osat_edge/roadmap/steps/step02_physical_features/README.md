# STEP02_PHYSICAL_FEATURES: Physical/statistical features


**Primary contributors:** Machine Learning & Predictive Maintenance.

**Inputs:** usable per-channel windows and equipment-state context.

**Outputs:** FeatureSet with robust median, MAD and slope features.

## Start here

- [features.py](features.py)

Read [the behavior tests](../step03_physical_residuals/tests/test_steps01_03_physics.py), then run from the repository root:

```powershell
.venv\Scripts\python -m unittest osat_edge.roadmap.steps.step03_physical_residuals.tests.test_steps01_03_physics -v
```

Preserve [evidence and authority boundaries](../../../../docs/EVIDENCE.md).
Use [team guides](../../../../docs/teams/README.md) for a small first contribution.
