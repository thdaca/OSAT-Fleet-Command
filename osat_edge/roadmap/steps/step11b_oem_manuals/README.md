# STEP11B_OEM_MANUALS: Local maintenance knowledge


**Primary contributors:** Semiconductor Failure Research + Data Pipeline & Systems Integration.

**Inputs:** approved local maintenance playbooks.

**Outputs:** bounded ManualChunk guidance; no health authority.

## Start here

- [manuals.py](manuals.py)

Read [the behavior tests](../step15_maintenance_ticket/tests/test_steps10_15_maintenance.py), then run from the repository root:

```powershell
.venv\Scripts\python -m unittest osat_edge.roadmap.steps.step15_maintenance_ticket.tests.test_steps10_15_maintenance -v
```

Preserve [evidence and authority boundaries](../../../../docs/EVIDENCE.md).
Use [team guides](../../../../docs/teams/README.md) for a small first contribution.
