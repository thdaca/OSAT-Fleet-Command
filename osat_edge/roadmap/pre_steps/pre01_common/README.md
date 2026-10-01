# PRE01_COMMON: Shared contracts


**Primary contributors:** Data Pipeline & Systems Integration.

**Inputs:** machine declarations and timestamped measurements.

**Outputs:** immutable identities/windows, explicit origins/modes/states.

## Start here

- [contracts.py](contracts.py)
- [authority.py](authority.py)

Read [the behavior tests](tests/test_security_portability.py), then run from the repository root:

```powershell
.venv\Scripts\python -m unittest osat_edge.roadmap.pre_steps.pre01_common.tests.test_security_portability -v
```

Preserve [evidence and authority boundaries](../../../../docs/EVIDENCE.md).
Use [team guides](../../../../docs/teams/README.md) for a small first contribution.
