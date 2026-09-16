"""marking Step01 research candidate."""

from __future__ import annotations

from ..core.schema import (
    EvidenceClaim,
    EvidenceMaturity,
    FaultSensitivity,
    RelationKind,
    RelationStatus,
    ResearchCandidate,
    ResidualDirection,
    ResidualFmeaEntry,
    SensorFailureMode,
)
from ..core.evidence import (
    JCGM_UNCERTAINTY,
    KEYENCE_POWER_MONITOR,
    LASER_EXPERIMENT,
    LASER_OUTPUT_MODEL,
    TRUMPF_CONDITION_MONITORING,
    _discrepancies,
    _measurement,
    _uncertainties,
)


MARKING_CANDIDATE = ResearchCandidate(
    "marking.laser_output_drive_temperature", "marking", "optical", RelationKind.MACHINE_FITTED, RelationStatus.RESEARCH_ONLY, EvidenceMaturity.LITERATURE_SUPPORTED,
    "Delivered optical power consistency with drive, temperature, pulse, and controller state.", "Laser output can depend on drive and temperature, but the form is architecture/control-specific.", "P_delivered=f_machine(I_drive,T,pulse/duty,controller,optical path)",
    ("delivered_laser_power", "laser_drive_current", "laser_temperature"), ("laser architecture", "junction-temperature proxy", "pulse/duty/Q-switch state", "feedback state", "reference power"),
    (EvidenceClaim("laser_direct_monitoring", "Commercial marker/laser systems use direct power and equipment-specific monitoring for maintenance.", ("keyence_laser_power_monitor", "trumpf_laser_monitoring"), "vendor-specific laser systems", "Does not define a transferable equation or this channel's semantics."),),
    (_measurement("delivered_laser_power", "delivered optical power at defined plane", "W", "sensor type, spectral response, sampling point"), _measurement("laser_drive_current", "architecture-specific drive current", "A", "current path and control mode"), _measurement("pulse_state", "pulse energy/duty/controller state", "state", "cycle aligned", missing=True)),
    _uncertainties("power calibration", "current", "temperature"), _discrepancies("architecture/control", "optical-path loss", "pulse dynamics"),
    (FaultSensitivity("source or optical-path degradation", ResidualDirection.NEGATIVE, EvidenceMaturity.HYPOTHESIS, "Delivered power may fall at comparable commanded/thermal state."),),
    (SensorFailureMode("delivered_laser_power", "negative gain drift or contamination", "false degradation", True),),
    (ResidualFmeaEntry("optical/source degradation", "power falls", "negative", ("controller", "temperature", "path contamination"), "power-sensor drift", False),),
    "Actual laser architecture, control state, pulse semantics, and calibrated output plane are unknown.",
    ("architecture/OEM review", "calibrated optical reference", "pulse/controller state"), LASER_EXPERIMENT.rejection_criteria, LASER_EXPERIMENT,
    LASER_EXPERIMENT.recalibration_triggers, LASER_EXPERIMENT.invalidation_triggers,
    "No verified architecture-specific measurement model.", "Could detect output consistency loss once direct measurement is metrologically defined.", LASER_EXPERIMENT.objective,
    (KEYENCE_POWER_MONITOR, TRUMPF_CONDITION_MONITORING, LASER_OUTPUT_MODEL, JCGM_UNCERTAINTY),
)

