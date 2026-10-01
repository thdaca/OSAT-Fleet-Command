# Reliability & Data Research

**Are the full pipeline's algorithm outputs statistically credible and reliable,
and what weaknesses or unsupported conclusions remain?**

## Entry files

- [POST02 artifact](../../osat_edge/roadmap/post_steps/post02_reference_replay/artifact.py)
  and [replay](../../osat_edge/roadmap/post_steps/post02_reference_replay/replay.py):
  repeatable synthetic operational checks, not plant-performance evidence.
- [POST03 benchmark](../../osat_edge/roadmap/post_steps/post03_external_benchmark/benchmark.py):
  external NASA Milling description, isolated from operational models.
- [POST04 evaluation](../../osat_edge/roadmap/post_steps/post04_real_data_evaluation/evaluation.py)
  and [dataset catalog](../../osat_edge/roadmap/post_steps/post04_real_data_evaluation/research/REAL_DATA_CATALOG.md):
  dataset owners, provenance, mappings, coverage, splits and limitations.
- [Shared metrics](../../osat_edge/roadmap/post_steps/metrics.py): deterministic
  research correlation, distributions and binary discrimination.
- [POST05 PoC](../../osat_edge/roadmap/post_steps/post05_full_poc/README.md):
  functional checks, restart, decision traces and lineage.

Start with one POST04 dataset and [its tests](../../osat_edge/roadmap/post_steps/post04_real_data_evaluation/tests/test_real_data_evaluation.py).
The snapshot4/5/6 tests there protect historical evidence and interpretation.

## What this team owns

Investigate results from the complete pipeline, including how parsing, data
selection, feature construction, fitting, scoring, health rules and reporting
shape the final output. An isolated model score cannot establish the reliability
of the whole algorithm. Receive the strategy and declared scope from ML, and the
input lineage and integration behavior from Data Pipeline.

Ask whether the statistical argument makes sense. Check normal variability,
false alarms, missed detections, confounders, coverage and stability across
conditions. Look for overfitting, leakage between training and evaluation,
repeated tuning on test results, selection bias and misleading comparisons.
Decide what counts as an independent example: many overlapping windows from one
machine or event do not automatically provide many independent pieces of evidence.

## Honest evaluation and handoff

Use suitable held-out machines, time periods, materials or events for the claim
being tested. Keep fitting and threshold selection separate from final evaluation.
Report sample limitations, unavailable metrics, uncertainty and unsupported
claims explicitly. Check that full-pipeline output and its displayed interpretation
do not make a stronger claim than the experiment supports.

Return SUPPORTED, REVISE, COLLECT MORE DATA or ABSTAIN with source identity,
split, scope, uncertainty and a next experiment. These are human research
conclusions, not runtime gates or permission to operate equipment. Negative
results are useful. Data Pipeline checks functional correctness of the whole
system; this team checks the statistical credibility of its results. Passing one
does not establish the other.

A first contribution can explain one result's unit of analysis, possible
confounder or generalization limit without rewriting its historical evidence.
Do not hide coverage gaps or treat discrimination as threshold calibration.
External results never create operational health or tickets. Loop back to Failure
Research, Data Pipeline and ML when evidence fails. Preserve frozen 0.2.6 code
and all historical reports; new evaluations must be identified separately.
