# STEP15_MAINTENANCE_TICKET: Deterministic demo tickets


**Primary contributors:** Data Pipeline & Systems Integration + UI & Data Visualization.

**Inputs:** authorized simulation fault evidence and validated/fallback wording.

**Outputs:** persisted demo-only ticket; escalation retains identity, recovery does not close.

## Start here

- [tickets.py](tickets.py)

Read [the behavior tests](tests/test_steps10_15_maintenance.py), then run from the repository root:

```powershell
.venv\Scripts\python -m unittest osat_edge.roadmap.steps.step15_maintenance_ticket.tests.test_steps10_15_maintenance -v
```

Preserve [evidence and authority boundaries](../../../../docs/EVIDENCE.md).
Use [team guides](../../../../docs/teams/README.md) for a small first contribution.
