"""Deterministic qualification and frozen evidence lineage, not scoring."""
import json

from ...pre_steps.pre01_common.contracts import VERSION
from ...pre_steps.pre01_common.authority import AuthorityMode, SHADOW_ALLOWED, SHADOW_FORBIDDEN
from ...steps.step07_machine_model.model_io import canonical_bytes, identity_sha256

from .lineage import frozen_lineage, implementation_identity


def assemble_report(onboarding, operational, enrichment, connectivity):
    outcomes, trace = operational["outcomes"], operational["trace"]
    progression = [t["health"] for t in trace if t["checkpoint"] == "progressive_spindle" and t["transitioned"]]
    recovery = [t["health"] for t in trace if t["checkpoint"] == "recovery" and t["transitioned"]]
    faults = [t for t in trace if t["checkpoint"] == "progressive_spindle" and t["fault_evidence"]]
    ticket_actions = [t["ticket_action"] for t in faults]
    unknown = all(outcomes[key] == "UNKNOWN" for key in (
        "cold_start", "legitimate_context_shift", "missing_required_signal", "stale_telemetry"))
    atomic = outcomes["malformed_atomic_batch"] == {
        "health": "UNKNOWN", "telemetry": "INVALID", "store_unchanged": True, "runtime_alive": True}
    corrupt = outcomes["corrupted_machine_model"] == {"rejected": True, "health": "UNKNOWN"}
    checks = {
        "operational_pipeline": outcomes["healthy_operation"] == "NORMAL" and outcomes["progressive_spindle_anomaly"] == "CRITICAL",
        "onboarding": onboarding["status"] == "PASS" and onboarding["disjoint_validation_windows"],
        "physics": any(t["physics"] and any(d["kind"] == "physics" and d["score"] > 0 for d in t["step07_deviations"]) for t in faults),
        "exact_machine_adaptation": onboarding["save_load_step07_exact"],
        "unknown_safety": unknown and atomic and corrupt,
        "health_progression": progression == ["WATCH", "DEGRADED", "CRITICAL"] and recovery == ["DEGRADED", "WATCH", "NORMAL"],
        "fault_localization": bool(faults) and all(t["fault_evidence"]["suspected_subsystems"] == ("spindle",) for t in faults),
        "ticket_persistence": operational["ticket_count"] == 1 and outcomes["ticket_remains_open_after_recovery"] == "OPEN"
                              and "CREATED" in ticket_actions and "ESCALATED_SAME_TICKET" in ticket_actions,
        "rag_fallback": enrichment["status"] == "PASS",
        "restart_reproducibility": outcomes["process_restart_model_ticket_reload"] == "PASS",
    }
    components = {key: "PASS" if value else "FAIL" for key, value in checks.items()}
    components["connectivity_simulation"] = connectivity["status"]
    lineage = frozen_lineage()
    components["external_evidence_summary"] = lineage["status"]
    report = {
        "schema_version": "OSAT_FULL_POC_V1", "software_version": VERSION, "snapshot": 2,
        "authority": {"mode": AuthorityMode.SHADOW.value, "allowed_subject_to_existing_ticket_policy": sorted(SHADOW_ALLOWED),
                      "forbidden": sorted(SHADOW_FORBIDDEN), "live_equipment_tickets": False},
        "REAL_OSAT_VALIDATED": False, "PROSPECTIVE_PLANT_VALIDATED": False, "PRODUCTION_QUALIFIED": False,
        "qualification": "PASS" if all(v == "PASS" for v in components.values()) else "INCOMPLETE_OR_FAILED",
        "components": components,
        "functional_proof": {
            "scope": "CONTROLLED END-TO-END PROOF OF CONCEPT",
            "onboarding": onboarding, "scenarios": outcomes,
            "health_progression": ["NORMAL", *progression], "recovery_progression": ["CRITICAL", *recovery],
            "decision_trace": trace, "tickets": operational["tickets"], "restart": operational["restart"],
            "enrichment": enrichment, "connectivity": connectivity,
            "ui_validation": "Separate offscreen UI tests; this command produces DecisionTrace without launching the UI.",
        },
        "external_scientific_evidence": lineage,
        "implementation_identity": implementation_identity(),
        "limitations": [
            "Functional system proof using authored synthetic WS-01 telemetry; not independent healthy plant history.",
            "Exact-machine holdout validates this deterministic nominal scenario only, not generalization or failure prediction.",
            "IDLE context has no calibrated model and correctly yields UNKNOWN, not a fault claim.",
            "A digest detects byte corruption, not malicious forgery, authorization or scientific validity.",
            "No family model is required or fitted here; family evidence remains optional/advisory.",
            "No GGUF inference is claimed; authored valid/invalid JSON checks exercise schema/fallback only.",
            "Loopback fixed HSMS simulator is not commercial GEM, OEM or prospective plant interoperability.",
            "MODEL + TICKET RELOAD WITH DETERMINISTIC REPLAY; Step09 live state is not checkpointed.",
            "External scientific evidence is frozen POST04 evidence, never operational WS-01 training or ticket authority.",
            "Tickets remain demo-only and OPEN after health recovery; no equipment control or autonomous closure.",
            "No calibrated failure probabilities, causal diagnosis, REAL_OSAT, prospective or production qualification.",
        ],
    }
    # Normalize dataclass tuples/enums to the JSON contract before returning.
    report = json.loads(canonical_bytes(report))
    report["report_sha256"] = identity_sha256(report)
    return report


def poc_summary(report):
    summary = {key: report[key] for key in (
        "software_version", "snapshot", "authority", "qualification", "report_sha256", "REAL_OSAT_VALIDATED",
        "PROSPECTIVE_PLANT_VALIDATED", "PRODUCTION_QUALIFIED",
    )}
    proof = report["functional_proof"]
    summary["FUNCTIONAL_PROOF"] = {
        "scope": proof["scope"],
        "components": {key: value for key, value in report["components"].items() if key != "external_evidence_summary"},
        **{key: proof[key] for key in ("scenarios", "health_progression", "recovery_progression", "ui_validation")},
    }
    summary["EXTERNAL_SCIENTIFIC_EVIDENCE"] = report["external_scientific_evidence"]
    return summary
