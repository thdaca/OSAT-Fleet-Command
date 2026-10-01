# Machine Learning & Predictive Maintenance

**How can a computer-run algorithm use trustworthy measurements to address the
physical problems identified by Semiconductor Failure Research?**

## Entry files

- [Step02 features](../../osat_edge/roadmap/steps/step02_physical_features/features.py):
  Feature/FeatureSet, medians, MAD and robust slope.
- [Step03 residuals](../../osat_edge/roadmap/steps/step03_physical_residuals/residuals.py):
  timestamp alignment and reviewed physics relationships.
- [Step05 family model](../../osat_edge/roadmap/steps/step05_family_model/model.py):
  real-only event risk with machine-isolation checks.
- [Step06 history](../../osat_edge/roadmap/steps/step06_machine_history/history.py):
  windows fully contained in confirmed-healthy intervals.
- [Step07 exact-machine model](../../osat_edge/roadmap/steps/step07_machine_model/model.py):
  context-specific robust references and deviations.
- [Step09 health](../../osat_edge/roadmap/steps/step09_health_risk/health.py):
  subsystem evidence, persistence and hysteresis.
- [Step10 fault evidence](../../osat_edge/roadmap/steps/step10_fault_evidence/evidence.py):
  structured explanations with physical scope and explicit limits.

Start with `robust_slope` and [Steps01–03 tests](../../osat_edge/roadmap/steps/step03_physical_residuals/tests/test_steps01_03_physics.py),
then [model tests](../../osat_edge/roadmap/steps/step07_machine_model/tests/test_steps04_07_models.py)
and [health tests](../../osat_edge/roadmap/steps/step09_health_risk/tests/test_step09_health.py).

## What this team owns

Build the core computational algorithm, including its machine-learning portion.
Translate Failure Research's mechanisms and modeling-feasibility conclusions into
executable strategies: features, physical residuals, statistical or learned
models, health evidence and bounded fault explanations. Choose a method because
it addresses a stated physical question; machine learning is one tool within the
algorithm, not the entire responsibility.

Receive clean measurements, operating context and provenance through Data
Pipeline's interfaces. Run the solution through that same pipeline rather than
building a second independent data path. Work with Failure Research on sensor
meaning, model assumptions and whether the available signals can distinguish the
proposed failure from normal changes or other causes.

## The evaluation handoff

Give Reliability the complete strategy, training sources, split, parameters,
intended output, expected sensitivity and confounders before inspecting held-out
results. Explain which algorithm stages transform a measurement into an output,
which cases should remain unavailable, and what evidence would count against the
method. Return named features, deviations and explicit unavailable reasons to
the pipeline; help UI explain their actual meaning.

A first contribution can document how one feature or residual addresses a
physical hypothesis, including its limitations. A future code version can add a
bounded algorithm change and appropriate tests; the 0.2.6 implementation is frozen.

Keep deterministic core behavior, machine/family isolation, data origin,
unavailable contexts and full-window healthy selection. Family risk stays
advisory. A new method needs an honest validation plan; do not turn risk scores
into probabilities, claim a causal diagnosis from an anomaly, or broaden
health-eligible feature kinds solely to improve favorable results. Optional LLM
wording does not determine health or maintenance authority.
