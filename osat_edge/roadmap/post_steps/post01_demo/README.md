# POST01_DEMO: Synthetic fleet demonstration


**Primary contributors:** Data Pipeline & Systems Integration + UI & Data Visualization.

**Inputs:** authored deterministic signals for nine registered stations.

**Outputs:** same operational pipeline with demo-only injection and tickets.

## Start here

- [demo.py](demo.py)

Read [the behavior tests](tests/test_pipeline_demo.py), then run from the repository root:

```powershell
.venv\Scripts\python -m unittest osat_edge.roadmap.post_steps.post01_demo.tests.test_pipeline_demo -v
```

Preserve [evidence and authority boundaries](../../../../docs/EVIDENCE.md).
Use [team guides](../../../../docs/teams/README.md) for a small first contribution.
