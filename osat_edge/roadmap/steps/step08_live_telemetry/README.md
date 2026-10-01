# STEP08_LIVE_TELEMETRY: Telemetry ingestion


**Primary contributors:** Data Pipeline & Systems Integration.

**Inputs:** approved timestamped samples, context, live queue or replay.

**Outputs:** atomic bounded streams, usable windows and explicit quality/observability.

## Start here

- [sources.py](sources.py)
- [store.py](store.py)
- [secs_gem.py](secs_gem.py)

Read [the behavior tests](tests/test_step08_telemetry.py), then run from the repository root:

```powershell
.venv\Scripts\python -m unittest osat_edge.roadmap.steps.step08_live_telemetry.tests.test_step08_telemetry -v
```

Preserve [evidence and authority boundaries](../../../../docs/EVIDENCE.md).
Use [team guides](../../../../docs/teams/README.md) for a small first contribution.

`sources.py` owns poll/batch behavior. `store.py` owns atomic acceptance and quality.
`secs_gem.py` owns fail-closed source mapping. Sensors remain independently timed.
