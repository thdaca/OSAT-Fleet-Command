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
    _discrepancies,
    _experiment,
    _measurement,
    _uncertainties,
)
from ..core.references import (
    JCGM_UNCERTAINTY,
    KEYENCE_POWER_MONITOR,
    TRUMPF_CONDITION_MONITORING,
)


LASER_EXPERIMENT = _experiment(
    "Test commanded versus measured laser-output stability on the actual marker architecture.",
    "Within one verified control mode, pulse regime, optical plane, and thermal state, measured output should repeat around commanded output.",
    ("commanded laser output", "built-in measured optical output", "calibrated external optical reference", "pulse/duty/controller state", "temperature"),
    ("commanded output", "temperature", "duty/pulse state", "optical-path condition"),
    "Approved output-command sweeps and controlled optical attenuation.",
    ("internal power-sensor gain drift", "attenuation after internal monitor", "controller-mode change", "external-reference drift"),
)


MARKING_CANDIDATE = ResearchCandidate(
    "marking.commanded_measured_laser_output_stability", "marking", "optical", RelationKind.MACHINE_FITTED, RelationStatus.RESEARCH_ONLY, EvidenceMaturity.LITERATURE_SUPPORTED,
    "Commanded laser output versus measured laser output stability.", "Commercial marker architectures can directly monitor optical output; a machine-specific comparison to the command is more defensible than assuming a diode-current/temperature model for an unknown source.", "Delta_P = P_measured - f_machine(P_command, pulse/duty, control_mode, temperature, optical_plane)",
    ("delivered_laser_power", "laser_temperature", "laser_drive_current"), ("commanded laser output", "measured-output sensor definition", "laser architecture", "pulse/duty/Q-switch state", "control mode", "external optical reference"),
    (EvidenceClaim("laser_direct_monitoring", "KEYENCE documents built-in thermopile monitoring that measures laser output during marking for maintenance; commercial systems also use equipment-specific monitoring.", ("keyence_laser_power_monitor", "trumpf_laser_monitoring"), "vendor-specific laser marker systems", "Does not define MK-01 channels, a transferable equation, or a universal limit."),),
    (_measurement("commanded_laser_output", "controller laser-output command", "W", "command basis, pulse/duty/control mode and saturation", missing=True), _measurement("measured_laser_output", "built-in measured optical output at a defined plane", "W", "sensor type, spectral response, sampling plane and aggregation", missing=True), _measurement("external_laser_output", "calibrated reference optical output", "W", "defined plane and traceable calibration", missing=True), _measurement("pulse_state", "pulse/duty/controller state", "state", "cycle aligned", missing=True)),
    _uncertainties("internal power-monitor calibration", "external optical reference", "temperature", "timing"), _discrepancies("architecture/control", "optical-path loss before/after monitor", "pulse dynamics"),
    (FaultSensitivity("source or optical-path degradation", ResidualDirection.NEGATIVE, EvidenceMaturity.HYPOTHESIS, "Delivered power may fall at comparable commanded/thermal state."),),
    (SensorFailureMode("delivered_laser_power", "negative gain drift or contamination", "false degradation", True),),
    (ResidualFmeaEntry("optical/source degradation", "power falls", "negative", ("controller", "temperature", "path contamination"), "power-sensor drift", False),),
    "Actual laser architecture, command and monitor definitions, control state, pulse semantics, and calibrated output plane are unknown; electrical-current relations remain research-only.",
    ("command and measured-output channels", "architecture/OEM review", "calibrated optical reference", "pulse/controller state"), LASER_EXPERIMENT.rejection_criteria, LASER_EXPERIMENT,
    LASER_EXPERIMENT.recalibration_triggers, LASER_EXPERIMENT.invalidation_triggers,
    "No verified command/output measurement pair or architecture-specific semantics.", "Could detect command-to-output consistency loss once direct measurement is metrologically defined.", LASER_EXPERIMENT.objective,
    (KEYENCE_POWER_MONITOR, TRUMPF_CONDITION_MONITORING, JCGM_UNCERTAINTY),
)
