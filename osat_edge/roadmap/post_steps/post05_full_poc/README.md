# POST05_FULL_POC: Full functional proof of concept


**Primary contributors:** Reliability & Data Research + Data Pipeline & Systems Integration.

**Inputs:** fresh synthetic onboarding/scenarios and optional loopback simulator.

**Outputs:** decision traces, restart checks and separately verified evidence lineage.

## Start here

- [poc.py](poc.py)
- [scenarios/](scenarios/)
- [trace.py](trace.py)
- [reporting.py](reporting.py)
- [lineage.py](lineage.py)

Read [the behavior tests](tests/test_full_poc.py), then run from the repository root:

```powershell
.venv\Scripts\python -m unittest osat_edge.roadmap.post_steps.post05_full_poc.tests.test_full_poc -v
```

Preserve [evidence and authority boundaries](../../../../docs/EVIDENCE.md).
Use [team guides](../../../../docs/teams/README.md) for a small first contribution.

## Research and reproducibility

- [FULL POC](research/FULL_POC.md)

`scenarios/` owns onboarding, operational, enrichment and loopback checks.
`trace.py` observes decisions. `lineage.py` verifies historical source bytes
in a read-only ZIP separately from current source and frozen evidence.
Read [release guidance](../../../../docs/RELEASES.md) before changing release pins.
