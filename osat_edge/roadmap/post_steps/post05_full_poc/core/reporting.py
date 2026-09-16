"""Deterministic qualification and frozen evidence lineage, not scoring."""
import hashlib
import json
from pathlib import Path

from ....pre_steps.pre01_common.pre01_common import VERSION
from ....pre_steps.pre01_common.core.authority import AuthorityMode, SHADOW_ALLOWED, SHADOW_FORBIDDEN
from ....pre_steps.pre03_data_provenance.pre03_data_provenance import canonical_file_set_sha256_v2
from ....steps.step07_machine_model.core.model_io import canonical_bytes, identity_sha256

POST05_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = POST05_ROOT.parents[3]
COMMITTED_POC_PATH = POST05_ROOT / "resources" / "0.2.6-poc.json"


def frozen_lineage():
    manifest = json.loads((POST05_ROOT / "resources" / "frozen_025_science.json").read_text(encoding="utf-8"))
    changed = [name for name, expected in manifest["files"].items()
               if not (PROJECT_ROOT / name).is_file()
               or hashlib.sha256((PROJECT_ROOT / name).read_bytes()).hexdigest() != expected]
    if changed:
        raise ValueError("Frozen scientific/source bytes changed: " + ", ".join(changed))
    evidence_path = POST05_ROOT.parent / "post04_real_data_evaluation/resources/0.2.5-real-data.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    return {
        "status": "PASS", "baseline": manifest["baseline"], "baseline_zip_sha256": manifest["archive_sha256"],
        "frozen_file_count": len(manifest["files"]), "frozen_manifest_sha256": identity_sha256(manifest),
        "external_evidence_artifact_sha256": hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
        "external_evidence_release": evidence["release_version"],
        "external_evidence_summary": evidence["summary"],
        "st_awfd_interpretation": evidence["st_awfd_discrimination_interpretation"],
        "external_results": [{key: item[key] for key in (
            "dataset", "status", "source_sha256", "continuous_metrics", "discrimination_evidence",
            "threshold_transfer_evidence", "principal_descriptive_results", "operational_ticket_count",
        ) if key in item} for item in evidence["results"]],
        "external_data_used_for_operational_model": False,
        "verification_scope": "frozen bytes and reported evidence; re-execution is a separate POST04 command",
    }


def implementation_identity():
    paths = [PROJECT_ROOT / "osat_edge/pipeline.py"]
    for directory in (PROJECT_ROOT / "osat_edge/roadmap/pre_steps", PROJECT_ROOT / "osat_edge/roadmap/steps", POST05_ROOT):
        paths.extend(p for p in directory.rglob("*.py") if not any(part in {"tests", "resources"} for part in p.parts))
    paths.append(POST05_ROOT / "resources/poc_maintenance.json")
    items = [(p.relative_to(PROJECT_ROOT).as_posix(), p.read_bytes()) for p in sorted(set(paths))]
    return {"method": "CANONICAL_FILE_SET_SHA256_V2", "file_count": len(items),
            "sha256": canonical_file_set_sha256_v2(items),
            "meaning": "implementation identity, not REAL_OSAT provenance"}


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
        "schema_version": "OSAT_FULL_POC_V1", "software_version": VERSION, "snapshot": 1,
        "authority": {"mode": AuthorityMode.SHADOW.value, "allowed_subject_to_existing_ticket_policy": sorted(SHADOW_ALLOWED),
                      "forbidden": sorted(SHADOW_FORBIDDEN), "live_equipment_tickets": False},
        "REAL_OSAT_VALIDATED": False, "PROSPECTIVE_PLANT_VALIDATED": False, "PRODUCTION_QUALIFIED": False,
        "qualification": "PASS" if all(v == "PASS" for v in components.values()) else "INCOMPLETE_OR_FAILED",
        "components": components, "onboarding": onboarding, "scenarios": outcomes,
        "health_progression": ["NORMAL", *progression], "recovery_progression": ["CRITICAL", *recovery],
        "decision_trace": trace, "tickets": operational["tickets"], "restart": operational["restart"],
        "enrichment": enrichment, "connectivity": connectivity, "evidence_lineage": lineage,
        "implementation_identity": implementation_identity(),
        "limitations": [
            "Functional system proof using authored synthetic WS-01 telemetry; not independent healthy plant history.",
            "Exact-machine holdout validates this deterministic nominal scenario only, not generalization or failure prediction.",
            "IDLE context has no calibrated model and correctly yields UNKNOWN, not a fault claim.",
            "A digest detects byte corruption, not malicious forgery, authorization or scientific validity.",
            "No family model is required or fitted here; family evidence remains optional/advisory.",
            "No GGUF inference is claimed; authored valid/invalid JSON checks exercise schema/fallback only.",
            "Loopback fixed HSMS simulator is not commercial GEM, OEM or prospective plant interoperability.",
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
    return {key: report[key] for key in (
        "software_version", "snapshot", "authority", "qualification", "components", "scenarios",
        "health_progression", "recovery_progression", "report_sha256", "REAL_OSAT_VALIDATED",
        "PROSPECTIVE_PLANT_VALIDATED", "PRODUCTION_QUALIFIED",
    )}
