# PRE03_DATA_PROVENANCE: Source provenance


**Primary contributors:** Data Pipeline & Systems Integration + Reliability & Data Research.

**Inputs:** local source bytes, label semantics and explicit mappings.

**Outputs:** verified or rejected REAL_OSAT source declarations.

## Start here

- [provenance.py](provenance.py)

Read [the behavior tests](tests/test_pre03_data_provenance.py), then run from the repository root:

```powershell
.venv\Scripts\python -m unittest osat_edge.roadmap.pre_steps.pre03_data_provenance.tests.test_pre03_data_provenance -v
```

Preserve [evidence and authority boundaries](../../../../docs/EVIDENCE.md).
Use [team guides](../../../../docs/teams/README.md) for a small first contribution.
