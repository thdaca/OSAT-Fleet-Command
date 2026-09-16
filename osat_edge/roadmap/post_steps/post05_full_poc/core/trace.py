"""Read pipeline outputs after decisions; this module never scores telemetry."""
from dataclasses import asdict

from ....pre_steps.pre01_common.core.authority import AuthorityMode
from ....steps.step07_machine_model.core.model_io import identity_sha256
from ..scenarios.onboarding import NOMINAL_DESIGNATION


def decision_trace(checkpoint, pipeline, result, previous_state, artifact_sha, prior_ticket):
    assessment = result.assessment
    ticket = pipeline.repository.active_for_machine(pipeline.identity.machine_id)
    action = "NONE"
    if ticket is not None:
        if prior_ticket is None:
            action = "CREATED"
        elif prior_ticket["priority"] != ticket["priority"]:
            action = "ESCALATED_SAME_TICKET"
        elif prior_ticket != ticket:
            action = "UPDATED_SAME_TICKET"
        else:
            action = "RETAINED_OPEN"
    fault = None
    if result.fault_evidence is not None:
        fault = asdict(result.fault_evidence)
        fault["timestamp"] = result.fault_evidence.timestamp.isoformat()
    return {
        "checkpoint": checkpoint, "machine": asdict(assessment.machine),
        "timestamp": assessment.timestamp.isoformat(), "context": assessment.equipment_state.value,
        "authority": AuthorityMode.SHADOW.value, "runtime_mode": assessment.runtime_mode.value,
        "DataOrigin": pipeline.source.origin.value, "nominal_designation": NOMINAL_DESIGNATION,
        "telemetry": {"state": "VALID" if result.telemetry_status.valid else "INVALID",
                      "observable": result.telemetry_status.observable,
                      "issues": list(result.telemetry_status.issues)},
        "physics": [asdict(f) for f in result.feature_set.features if f.kind == "physics"]
                   if result.feature_set else [],
        "exact_machine_model_artifact_sha256": artifact_sha,
        "step07_deviations": [asdict(d) for s in assessment.subsystem_health for d in s.deviations],
        "advisory_family_risk": assessment.family_risk_score,
        "previous_health": previous_state, "health": assessment.health_state.value,
        "transitioned": assessment.transitioned, "transition_reason": assessment.reason,
        "subsystem_evidence": [{"subsystem": s.subsystem, "health": s.state.value,
                                "score": s.score, "reason": s.reason} for s in assessment.subsystem_health],
        "fault_evidence": fault, "ticket_action": action,
        "ticket": {key: ticket[key] for key in ("ticket_id", "machine_id", "station_id",
                   "priority", "status", "demo_only", "suspected_subsystems")} if ticket else None,
    }


def store_identity(pipeline):
    """Digest public store reads, including complete bounded streams and context."""
    from datetime import timedelta
    from ...post01_demo.post01_demo import DEMO_START
    store = pipeline.store
    windows = store.windows([s.name for s in pipeline.station.channels],
                            end=DEMO_START + timedelta(days=1), duration=timedelta(days=2))
    context = store.latest_context()
    return identity_sha256({
        "streams": {name: {"timestamps": w.timestamps.tolist(), "values": w.values.tolist(),
                           "unit": w.unit} for name, w in windows.items()},
        "context": {**asdict(context), "timestamp": context.timestamp.isoformat()} if context else None,
    })
