# PRE-STEPS → STEPS → POST-STEPS

PRE-STEPS own trust contracts. STEPS own analysis and maintenance. POST-STEPS
own demonstrations and isolated research checks. The sibling UI displays results.
Stage numbers identify responsibility; training and monitoring are different paths.
See [data flow](../../docs/ARCHITECTURE.md) and [team routes](../../docs/teams/README.md).

## PRE STEPS

- [pre01_common: Shared contracts](pre_steps/pre01_common/README.md)
- [pre02_machine_registry: Canonical station registry](pre_steps/pre02_machine_registry/README.md)
- [pre03_data_provenance: Source provenance](pre_steps/pre03_data_provenance/README.md)

## STEPS

- [step01_physics_library: Physics and failure research](steps/step01_physics_library/README.md)
- [step02_physical_features: Physical/statistical features](steps/step02_physical_features/README.md)
- [step03_physical_residuals: Physical residuals](steps/step03_physical_residuals/README.md)
- [step04_family_data: Same-family training data](steps/step04_family_data/README.md)
- [step05_family_model: Family risk model](steps/step05_family_model/README.md)
- [step06_machine_history: Exact-machine healthy history](steps/step06_machine_history/README.md)
- [step07_machine_model: Exact-machine baseline](steps/step07_machine_model/README.md)
- [step08_live_telemetry: Telemetry ingestion](steps/step08_live_telemetry/README.md)
- [step09_health_risk: Deterministic health](steps/step09_health_risk/README.md)
- [step10_fault_evidence: Structured fault evidence](steps/step10_fault_evidence/README.md)
- [step11a_maintenance_db: Maintenance persistence](steps/step11a_maintenance_db/README.md)
- [step11b_oem_manuals: Local maintenance knowledge](steps/step11b_oem_manuals/README.md)
- [step12_rag: Local guidance retrieval](steps/step12_rag/README.md)
- [step13_local_llm: Optional local wording](steps/step13_local_llm/README.md)
- [step14_json_validation: Wording validation](steps/step14_json_validation/README.md)
- [step15_maintenance_ticket: Deterministic demo tickets](steps/step15_maintenance_ticket/README.md)

## POST STEPS

- [post01_demo: Synthetic fleet demonstration](post_steps/post01_demo/README.md)
- [post02_reference_replay: Frozen synthetic replay](post_steps/post02_reference_replay/README.md)
- [post03_external_benchmark: External NASA Milling description](post_steps/post03_external_benchmark/README.md)
- [post04_real_data_evaluation: Offline dataset evaluation](post_steps/post04_real_data_evaluation/README.md)
- [post05_full_poc: Full functional proof of concept](post_steps/post05_full_poc/README.md)

Shared [research metrics](post_steps/metrics.py) serve POST03 and POST04 only.
There are no operational decisions in that shared module.

[pipeline.py](../pipeline.py) connects operational stages.
[UI screens](../ui/screens/README.md) own human presentation; they are not numbered stages.
