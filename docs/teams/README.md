# Find your team's entry point

Teams own questions and collaborate across numbered stages. These are routes
into the existing system, not five disconnected pipelines.

- [Machine Learning & Predictive Maintenance](ML_PREDICTIVE_MAINTENANCE.md):
  build the core computational algorithm, including machine learning, to address
  the physical problems identified by Failure Research.
- [Data Pipeline & Systems Integration](DATA_PIPELINE.md): own the full pipeline,
  correct parsing, integration, consistency and whole-system functional validation.
- [UI & Data Visualization](UI_VISUALIZATION.md): make the whole system clear to
  maintenance engineers and factory floor managers, guided by OSAT plant needs.
- [Reliability & Data Research](RELIABILITY_RESEARCH.md): examine full-pipeline
  results for statistical reliability, overfitting and unsupported conclusions.
- [Semiconductor Failure Research](FAILURE_RESEARCH.md): research failure modes
  per machine, their physics and measurements, and whether they could be modeled.

```text
Failure Research → Data Pipeline → ML / Predictive Maintenance
                                      ↓
                 revise hypothesis ← Reliability / Data Research
                                      ↓ supported scoped result
                               UI / Visualization
```

This is the human handoff sequence; software remains PRE-STEPS → STEPS →
POST-STEPS. Data Pipeline continues to integrate and validate the entire flow;
its responsibility does not end when clean data reaches ML. Reliability examines
the outputs of that complete flow, not only an isolated model score. UI shares
plant-user requirements with all teams. Reliability can return SUPPORTED, REVISE,
COLLECT MORE DATA or ABSTAIN and send the work back. These are human research
outcomes, not automatic permission to operate equipment. Read [architecture](../ARCHITECTURE.md),
[evidence](../EVIDENCE.md) and [contributing](../CONTRIBUTING.md) at team boundaries.
