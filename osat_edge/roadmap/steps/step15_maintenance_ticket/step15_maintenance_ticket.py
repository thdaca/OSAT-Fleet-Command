"""Step 15: final deterministic ticket with optional validated prose."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any, Mapping

from ...pre_steps.pre01_common.pre01_common import HealthState, RuntimeMode, health_rank
from ..step10_fault_evidence.step10_fault_evidence import FaultEvidence
from ..step11a_maintenance_db.step11a_maintenance_db import MaintenanceRepository
from ..step14_json_validation.step14_json_validation import TicketEnrichment


@dataclass(frozen=True)
class MaintenanceTicket:
    ticket_id: str
    created_utc: str
    updated_utc: str
    machine_id: str
    station_id: str
    family: str
    status: str
    priority: str
    health_state: str
    suspected_subsystems: tuple[str, ...]
    summary: str
    likely_issue: str
    recommended_checks: tuple[str, ...]
    evidence_descriptions: tuple[str, ...]
    explanation_backend: str
    demo_only: bool

    def to_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        for name in (
            "suspected_subsystems",
            "recommended_checks",
            "evidence_descriptions",
        ):
            payload[name] = list(payload[name])
        return payload

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "MaintenanceTicket":
        value = dict(payload)
        for name in (
            "suspected_subsystems",
            "recommended_checks",
            "evidence_descriptions",
        ):
            value[name] = tuple(value[name])
        return cls(**value)


def _priority(health_state: HealthState) -> str:
    return {
        HealthState.DEGRADED: "HIGH",
        HealthState.CRITICAL: "URGENT",
    }[health_state]


def create_or_update_ticket(
    repository: MaintenanceRepository,
    evidence: FaultEvidence,
    enrichment: TicketEnrichment,
) -> MaintenanceTicket | None:
    """Simulation may persist demo tickets; replay/live remain observe-only."""

    if evidence.runtime_mode is not RuntimeMode.SIMULATION:
        return None
    existing_payload = repository.active_for_machine(evidence.machine.machine_id)
    timestamp = evidence.timestamp.isoformat()
    if existing_payload is not None:
        existing = MaintenanceTicket.from_payload(existing_payload)
        existing_state = HealthState(existing.health_state)
        if health_rank(evidence.health_state) < health_rank(existing_state):
            return existing
        ticket = replace(
            existing,
            updated_utc=timestamp,
            priority=_priority(evidence.health_state),
            health_state=evidence.health_state.value,
            suspected_subsystems=evidence.suspected_subsystems,
            summary=enrichment.summary,
            likely_issue=enrichment.likely_issue,
            recommended_checks=enrichment.recommended_checks,
            evidence_descriptions=evidence.evidence_descriptions,
            explanation_backend=enrichment.backend,
        )
        repository.update(ticket.to_payload())
        return ticket
    ticket = MaintenanceTicket(
        ticket_id=(
            f"{evidence.machine.station_id}-"
            f"{evidence.timestamp.strftime('%Y%m%dT%H%M%S%f')}"
        ),
        created_utc=timestamp,
        updated_utc=timestamp,
        machine_id=evidence.machine.machine_id,
        station_id=evidence.machine.station_id,
        family=evidence.machine.family,
        status="OPEN",
        priority=_priority(evidence.health_state),
        health_state=evidence.health_state.value,
        suspected_subsystems=evidence.suspected_subsystems,
        summary=enrichment.summary,
        likely_issue=enrichment.likely_issue,
        recommended_checks=enrichment.recommended_checks,
        evidence_descriptions=evidence.evidence_descriptions,
        explanation_backend=enrichment.backend,
        demo_only=True,
    )
    repository.save(ticket.to_payload())
    return ticket


def list_tickets(
    repository: MaintenanceRepository, *, limit: int = 200
) -> list[MaintenanceTicket]:
    return [
        MaintenanceTicket.from_payload(payload)
        for payload in repository.list_tickets(limit=limit)
    ]
