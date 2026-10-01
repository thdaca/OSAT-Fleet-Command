# POST03_EXTERNAL_BENCHMARK: External NASA Milling description


**Primary contributors:** Reliability & Data Research.

**Inputs:** explicit local official NASA Milling artifact.

**Outputs:** descriptive benchmark report, never OSAT health or tickets.

## Start here

- [benchmark.py](benchmark.py)

Read [the behavior tests](tests/test_external_benchmark.py), then run from the repository root:

```powershell
.venv\Scripts\python -m unittest osat_edge.roadmap.post_steps.post03_external_benchmark.tests.test_external_benchmark -v
```

Preserve [evidence and authority boundaries](../../../../docs/EVIDENCE.md).
Use [team guides](../../../../docs/teams/README.md) for a small first contribution.

## Research and reproducibility

- [EXTERNAL BENCHMARK](research/EXTERNAL_BENCHMARK.md)
