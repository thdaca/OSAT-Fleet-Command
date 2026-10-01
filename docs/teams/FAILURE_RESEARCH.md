# Semiconductor Failure Research

**What can fail in each OSAT machine, why would its measurements change, and
could that failure be represented by a computer model?**

## Entry files

- [Evidence catalog](../../osat_edge/roadmap/steps/step01_physics_library/research/EVIDENCE_CATALOG.md)
  and [research roadmap](../../osat_edge/roadmap/steps/step01_physics_library/research/PHYSICS_RESEARCH_ROADMAP_2026.md).
- [Step01 README and family dossiers](../../osat_edge/roadmap/steps/step01_physics_library/README.md).
- [Step01 schema](../../osat_edge/roadmap/steps/step01_physics_library/core/schema.py):
  claims, measurement semantics, uncertainty, maturity and experiments.
- [Wafer-saw family](../../osat_edge/roadmap/steps/step01_physics_library/families/wafer_saw.py):
  example runtime, research-only and rejected relationships.
- [Step01 library](../../osat_edge/roadmap/steps/step01_physics_library/library.py):
  catalog and supported public functions.

Start with a single dossier and its family module, then
[physics credibility tests](../../osat_edge/roadmap/steps/step01_physics_library/tests/test_step01_physics_library.py).
Optional physics-audit dependencies live in Step01 resources and are not core.

## What this team owns

Build a failure-mode inventory for each machine and its relevant submachines or
subsystems. A failure mode is a specific way equipment can stop working correctly;
name the affected part rather than treating every abnormal reading as the same
problem. Investigate the underlying physics, operating conditions, sensors,
measured parameters and model parameters that describe the mechanism.

Research OEM manuals, patents, papers and other credible sources, recording
exactly which claim each supports. Explain the expected measurement change,
required units and timing, applicable operating range, normal lookalikes, sensor
failures and uncertainty. State what observation would contradict the hypothesis
and what experiment could test it.

## The modeling-feasibility handoff

Conclude whether the proposed failure could potentially be represented by a
computer model. Explain what the model would receive and estimate, which physical
or statistical relationship might be usable, which parameters would need fitting,
and whether the available measurements can distinguish the problem from normal
operation or another cause. Name missing sensors, data or assumptions explicitly.

The dossier should say whether modeling appears feasible, needs additional
measurements or evidence, or is not currently feasible, with reasons and a next
experiment. These are written research conclusions, not new software states or
proof that a detector works. A negative feasibility conclusion is useful.

Give Data Pipeline the measurement requirements and meaning; give ML the physical
problem and justified modeling hypothesis. ML builds the executable algorithm.
Reliability's results may require revising the hypothesis or collecting different
measurements. A first contribution can add one failure mode and its feasibility
reasoning to a dossier, without changing approved runtime relations.

Plausible relations stay research-only until semantics, calibration and validation
justify runtime use. Keep rejected claims visible; literature evidence cannot
directly become causal diagnosis or ticket authority. The 0.2.6 application is
frozen; a future algorithm or runtime relationship requires a new code version.
