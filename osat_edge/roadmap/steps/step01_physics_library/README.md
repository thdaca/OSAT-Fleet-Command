# STEP01_PHYSICS_LIBRARY: Physics and failure research


**Primary contributors:** Semiconductor Failure Research + Reliability & Data Research.

**Inputs:** reviewed references, measurands and healthy calibration evidence.

**Outputs:** runtime relations, research/rejected catalog, uncertainty and calibration diagnostics.

## Start here

- [library.py](library.py)
- [families/](families/)
- [core/schema.py](core/schema.py)
- [core/calibration.py](core/calibration.py)

Read [the behavior tests](tests/test_step01_physics_library.py), then run from the repository root:

```powershell
.venv\Scripts\python -m unittest osat_edge.roadmap.steps.step01_physics_library.tests.test_step01_physics_library -v
```

Preserve [evidence and authority boundaries](../../../../docs/EVIDENCE.md).
Use [team guides](../../../../docs/teams/README.md) for a small first contribution.

## Research and reproducibility

- [EVIDENCE CATALOG](research/EVIDENCE_CATALOG.md)
- [PHYSICS RESEARCH ROADMAP 2026](research/PHYSICS_RESEARCH_ROADMAP_2026.md)
- [STEP01 PHYSICS LIBRARY RESEARCH](research/STEP01_PHYSICS_LIBRARY_RESEARCH.md)

## Choose one equipment family

- [die attach dossier](research/die_attach/DOSSIER.md)
- [final test dossier](research/final_test/DOSSIER.md)
- [marking dossier](research/marking/DOSSIER.md)
- [molding dossier](research/molding/DOSSIER.md)
- [singulation dossier](research/singulation/DOSSIER.md)
- [trim form dossier](research/trim_form/DOSSIER.md)
- [wafer mount dossier](research/wafer_mount/DOSSIER.md)
- [wafer saw dossier](research/wafer_saw/DOSSIER.md)
- [wire bond dossier](research/wire_bond/DOSSIER.md)

`core/` owns explicit schema, references, calibration, diagnostics, units and
uncertainty functions. `families/` owns physical relationships by equipment type.
The optional audit command is `python resources/run_physics_research_audit.py`
when run inside this stage, with its optional requirements installed.
