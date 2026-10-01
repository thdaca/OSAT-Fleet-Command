# POST02_REFERENCE_REPLAY: Frozen synthetic replay


**Primary contributors:** Reliability & Data Research + Data Pipeline & Systems Integration.

**Inputs:** bundled checksummed fixture or a supplied reference directory.

**Outputs:** strictly validated replay, observed checkpoints and demo tickets.

## Start here

- [artifact.py](artifact.py)
- [replay.py](replay.py)

Read [the behavior tests](tests/test_reference_replay.py), then run from the repository root:

```powershell
.venv\Scripts\python -m unittest osat_edge.roadmap.post_steps.post02_reference_replay.tests.test_reference_replay -v
```

Preserve [evidence and authority boundaries](../../../../docs/EVIDENCE.md).
Use [team guides](../../../../docs/teams/README.md) for a small first contribution.

## Research and reproducibility

- [REFERENCE REPLAY](research/REFERENCE_REPLAY.md)
