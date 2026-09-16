"""Steps11b–14 demonstration after a deterministic ticket already exists."""
import json

from ....steps.step11b_oem_manuals.step11b_oem_manuals import load_oem_manuals
from ....steps.step12_rag.step12_rag import retrieve_rag_context
from ....steps.step13_local_llm.step13_local_llm import generate_local_llm_json
from ....steps.step14_json_validation.step14_json_validation import validate_llm_json
from .operational import RESOURCES


def run_enrichment(result, repository):
    evidence = result.fault_evidence
    before = repository.active_for_machine(evidence.machine.machine_id)
    passages = retrieve_rag_context(evidence, (), load_oem_manuals(RESOURCES / "poc_maintenance.json"))
    raw = generate_local_llm_json(evidence, passages, model_path=None)
    absent = validate_llm_json(raw, evidence, passages)
    invalid = validate_llm_json('{"health_state":"NORMAL","create_ticket":false}', evidence, passages)
    # Project-authored schema fixture, explicitly NOT a generated GGUF result.
    valid = validate_llm_json(json.dumps({"summary": "Review existing WS-01 spindle evidence.",
        "likely_issue": "Spindle-associated deviations; no causal diagnosis.",
        "recommended_checks": ["Review approved PoC guidance with a qualified reviewer."]}), evidence, passages)
    return {"status": "PASS" if passages and raw is None and absent == invalid
            and valid.backend == "local-llm" and before is not None
            and repository.active_for_machine(evidence.machine.machine_id) == before else "FAIL",
            "ticket_existed_before_retrieval": before is not None,
            "retrieved_source_ids": [p.source_id for p in passages], "llm_required": False,
            "llm_execution": "NOT_CONFIGURED", "authored_schema_fixture_accepted": valid.backend == "local-llm",
            "invalid_authority_fields_rejected": invalid == absent, "fallback_backend": absent.backend,
            "health_authority": False, "ticket_creation_authority": False,
            "ticket_unchanged_by_schema_checks": repository.active_for_machine(evidence.machine.machine_id) == before}
