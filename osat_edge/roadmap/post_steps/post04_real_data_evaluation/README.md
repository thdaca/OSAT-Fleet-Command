# POST04_REAL_DATA_EVALUATION: Offline dataset evaluation


**Primary contributors:** Reliability & Data Research + Data Pipeline & Systems Integration.

**Inputs:** explicit local datasets with pinned provenance.

**Outputs:** dataset-owned research metrics, coverage, limitations and evidence reproduction.

## Start here

- [evaluation.py](evaluation.py)
- [datasets/](datasets/)
- [core/reporting.py](core/reporting.py)
- [core/evidence_lifecycle.py](core/evidence_lifecycle.py)

Read [the behavior tests](tests/test_real_data_evaluation.py), then run from the repository root:

```powershell
.venv\Scripts\python -m unittest osat_edge.roadmap.post_steps.post04_real_data_evaluation.tests.test_real_data_evaluation -v
```

Preserve [evidence and authority boundaries](../../../../docs/EVIDENCE.md).
Use [team guides](../../../../docs/teams/README.md) for a small first contribution.

## Research and reproducibility

- [REAL DATA CATALOG](research/REAL_DATA_CATALOG.md)
- [REAL OSAT DATA REQUEST](research/REAL_OSAT_DATA_REQUEST.md)

Import reporting and lifecycle functions from `core/`, and dataset helpers from
their `datasets/` module. Shared pure research metrics live in `../metrics.py`.
There is no Step09, Step10 or Step15 dependency in the evaluator.
