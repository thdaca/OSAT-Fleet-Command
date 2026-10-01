# STEP13_LOCAL_LLM: Optional local wording


**Primary contributors:** Machine Learning & Predictive Maintenance + UI & Data Visualization.

**Inputs:** existing deterministic evidence and retrieved passages.

**Outputs:** optional raw JSON; absence/failure leaves fallback available.

## Start here

- [llm.py](llm.py)

Read [the behavior tests](../step15_maintenance_ticket/tests/test_steps10_15_maintenance.py), then run from the repository root:

```powershell
.venv\Scripts\python -m unittest osat_edge.roadmap.steps.step15_maintenance_ticket.tests.test_steps10_15_maintenance -v
```

Preserve [evidence and authority boundaries](../../../../docs/EVIDENCE.md).
Use [team guides](../../../../docs/teams/README.md) for a small first contribution.
