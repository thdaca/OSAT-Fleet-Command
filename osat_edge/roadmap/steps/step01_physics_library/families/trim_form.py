"""trim form Step01 research candidate."""

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
    ISO_CONDITION_MONITORING,
    MAXON_CONSTANTS,
)


PRESS_EXPERIMENT = _experiment(
    "Map press drive torque to punch force by stroke phase and separate tool degradation from dynamics.",
    "With known torque constant, transmission, phase, and acceleration, current-derived torque predicts measured punch force.",
    ("calibrated punch force", "drive current/torque", "stroke encoder", "mechanism geometry", "high-rate synchronization"),
    ("stroke phase", "speed/acceleration", "tool condition", "material"),
    "Approved force and tool-condition sweeps across stroke phases.",
    ("acceleration change", "current offset", "friction/temperature change"),
)


TRIM_FORM_CANDIDATE = ResearchCandidate(
    "trim_form.motor_current_punch_force", "trim_form", "press", RelationKind.SEMI_EMPIRICAL, RelationStatus.RESEARCH_ONLY, EvidenceMaturity.LITERATURE_SUPPORTED,
    "Stroke-resolved drive-torque to punch-force consistency.", "Motor current can map to torque, then linkage/transmission and phase map torque to force after dynamics/losses.", "F(θ)=K_t I G mechanical_advantage(θ)-inertia/friction",
    ("punch_force", "press_motor_current", "die_vibration", "die_temperature"), ("torque constant", "transmission/linkage", "stroke phase", "acceleration", "loss model"),
    (EvidenceClaim("motor_to_force", "Motor current can map to torque but force requires the intervening mechanism and state.", ("maxon_motor_constants",), "motor mechanics", "No press-specific parameters are available."),),
    (_measurement("punch_force", "actual punch force", "kN", "load-cell location and dynamic calibration"), _measurement("press_motor_current", "actual drive current/torque feedback", "A", "feedback definition and phase"), _measurement("stroke_phase", "press angle/position/acceleration", "rad", "encoder-derived actual state", missing=True)),
    _uncertainties("force", "current", "phase/alignment"), _discrepancies("linkage/inertia", "friction", "tool/material effects"),
    (FaultSensitivity("tool wear/damage", ResidualDirection.UNKNOWN, EvidenceMaturity.HYPOTHESIS, "May change phase-specific force/current relationship."),),
    (SensorFailureMode("punch_force", "gain drift", "false consistency change", True),),
    (ResidualFmeaEntry("tool condition change", "force/current waveform changes", "condition dependent", ("material", "phase", "friction"), "force/current gain drift", False),),
    "Current and force cannot be related without stroke phase, mechanism, and dynamic terms.",
    ("stroke encoder", "verified torque feedback", "mechanism configuration", "high-rate alignment"), PRESS_EXPERIMENT.rejection_criteria, PRESS_EXPERIMENT,
    PRESS_EXPERIMENT.recalibration_triggers, PRESS_EXPERIMENT.invalidation_triggers,
    "Missing phase-resolved mechanism and drive semantics.", "Could provide redundant tooling/load evidence after a controlled mechanics study.", PRESS_EXPERIMENT.objective,
    (MAXON_CONSTANTS, ISO_CONDITION_MONITORING),
)
