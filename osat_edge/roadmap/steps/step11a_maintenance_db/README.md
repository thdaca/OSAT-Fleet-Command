# STEP11A_MAINTENANCE_DB: Maintenance persistence


**Primary contributors:** Data Pipeline & Systems Integration.

**Inputs:** deterministic ticket payloads and bounded queries.

**Outputs:** SQLite tickets and same-machine prior context.

## Start here

- [repository.py](repository.py)

Read [the behavior tests](../step15_maintenance_ticket/tests/test_steps10_15_maintenance.py), then run from the repository root:

```powershell
.venv\Scripts\python -m unittest osat_edge.roadmap.steps.step15_maintenance_ticket.tests.test_steps10_15_maintenance -v
```

Preserve [evidence and authority boundaries](../../../../docs/EVIDENCE.md).
Use [team guides](../../../../docs/teams/README.md) for a small first contribution.
