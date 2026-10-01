# PRE02_MACHINE_REGISTRY: Canonical station registry


**Primary contributors:** Data Pipeline & Systems Integration + Semiconductor Failure Research.

**Inputs:** reviewed equipment/channel requirements.

**Outputs:** nine station profiles and approved canonical channel specifications.

## Start here

- [registry.py](registry.py)

Read [the behavior tests](../pre01_common/tests/test_security_portability.py), then run from the repository root:

```powershell
.venv\Scripts\python -m unittest osat_edge.roadmap.pre_steps.pre01_common.tests.test_security_portability -v
```

Preserve [evidence and authority boundaries](../../../../docs/EVIDENCE.md).
Use [team guides](../../../../docs/teams/README.md) for a small first contribution.
