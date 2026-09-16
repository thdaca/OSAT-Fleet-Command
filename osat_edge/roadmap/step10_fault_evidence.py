"""Step 10: small structured evidence for degraded-or-worse health."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from ..common import HealthState, MachineIdentity, RuntimeMode
from .step09_health_risk import HealthAssessment


@dataclass(frozen=True)
class FaultEvidence:
    machine: MachineIdentity
    timestamp: dt.datetime
    runtime_mode: RuntimeMode
    health_state: HealthState
    suspected_subsystems: tuple[str, ...]
    evidence_descriptions: tuple[str, ...]
    family_risk_note: str | None = None


def build_fault_evidence(assessment: HealthAssessment) -> FaultEvidence | None:
    if assessment.health_state not in {HealthState.DEGRADED, HealthState.CRITICAL}:
        return None
    descriptions: list[str] = []
    suspected = set(assessment.suspected_subsystems)
    detail = [
        deviation
        for subsystem in assessment.subsystem_health
        if not suspected or subsystem.subsystem in suspected
        for deviation in subsystem.deviations
        if deviation.score > 0
    ]
    kind_priority = {"location": 0, "physics": 1}
    ranked = sorted(
        detail,
        key=lambda item: (kind_priority.get(item.kind, 2), -item.score),
    )
    for deviation in ranked[:6]:
            if deviation.score <= 0:
                continue
            direction = "above" if deviation.z_score >= 0 else "below"
            descriptions.append(
                f"{deviation.feature} in {deviation.subsystem} deviates "
                f"{deviation.z_score:+.2f} robust scales {direction} confirmed healthy behavior"
            )
    family_note = None
    if assessment.family_risk_score is not None and not assessment.suspected_subsystems:
        family_note = (
            "Machine-wide uncalibrated family risk is advisory; no subsystem attribution is supported."
        )
    if not descriptions:
        descriptions.append("Deterministic health evidence is elevated without causal proof.")
    return FaultEvidence(
        machine=assessment.machine,
        timestamp=assessment.timestamp,
        runtime_mode=assessment.runtime_mode,
        health_state=assessment.health_state,
        suspected_subsystems=assessment.suspected_subsystems,
        evidence_descriptions=tuple(descriptions),
        family_risk_note=family_note,
    )
