# Snapshot 1 → snapshot 2 module names

Numbered directories stay in place. Update imports to the owning module; no
old-path compatibility layer is added. CLI commands are unchanged.

- `pre01_common/pre01_common.py` → `pre01_common/contracts.py`
- `pre02_machine_registry/pre02_machine_registry.py` → `pre02_machine_registry/registry.py`
- `pre03_data_provenance/pre03_data_provenance.py` → `pre03_data_provenance/provenance.py`
- `step01_physics_library/step01_physics_library.py` → `step01_physics_library/library.py`
- `step02_physical_features/step02_physical_features.py` → `step02_physical_features/features.py`
- `step03_physical_residuals/step03_physical_residuals.py` → `step03_physical_residuals/residuals.py`
- `step04_family_data/step04_family_data.py` → `step04_family_data/dataset.py`
- `step05_family_model/step05_family_model.py` → `step05_family_model/model.py`
- `step06_machine_history/step06_machine_history.py` → `step06_machine_history/history.py`
- `step07_machine_model/step07_machine_model.py` → `step07_machine_model/model.py`
- `step08_live_telemetry/step08_live_telemetry.py` → `step08_live_telemetry/sources.py`, `store.py`, `secs_gem.py`
- `step09_health_risk/step09_health_risk.py` → `step09_health_risk/health.py`
- `step10_fault_evidence/step10_fault_evidence.py` → `step10_fault_evidence/evidence.py`
- `step11a_maintenance_db/step11a_maintenance_db.py` → `step11a_maintenance_db/repository.py`
- `step11b_oem_manuals/step11b_oem_manuals.py` → `step11b_oem_manuals/manuals.py`
- `step12_rag/step12_rag.py` → `step12_rag/retrieval.py`
- `step13_local_llm/step13_local_llm.py` → `step13_local_llm/llm.py`
- `step14_json_validation/step14_json_validation.py` → `step14_json_validation/validation.py`
- `step15_maintenance_ticket/step15_maintenance_ticket.py` → `step15_maintenance_ticket/tickets.py`
- `post01_demo/post01_demo.py` → `post01_demo/demo.py`
- `post02_reference_replay/post02_reference_replay.py` → `post02_reference_replay/replay.py`
- `post03_external_benchmark/post03_external_benchmark.py` → `post03_external_benchmark/benchmark.py`
- `post04_real_data_evaluation/post04_real_data_evaluation.py` → `post04_real_data_evaluation/evaluation.py`
- `post05_full_poc/post05_full_poc.py` → `post05_full_poc/poc.py`

PRE01 `core/authority.py` and Step07 `core/model_io.py` move directly into their
stage. POST02 uses `artifact.py` for validation and `replay.py` for execution.
POST05 uses `lineage.py`, `trace.py` and `reporting.py` directly. POST04 imports
reporting/lifecycle/dataset helpers from their owners; shared metrics move to
`post_steps/metrics.py`. UI fields are owned by each `window.<name>_screen`.
