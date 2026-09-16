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
    GALLANT_TRIM_FORM,
    ISO_CONDITION_MONITORING,
    MAXON_CONSTANTS,
    TAIJIN_TRIM_FORM,
)


PRESS_EXPERIMENT = _experiment(
    "Test stroke-aligned servo load/torque/force profile consistency and separate tooling change from motion dynamics.",
    "Within fixed package geometry, tooling, drive mode, and stroke conditions, measured servo-load and reference-force profiles should be repeatable by stroke position.",
    ("servo load/torque feedback", "calibrated punch force", "stroke encoder", "drive/control semantics", "tool and package geometry identity", "high-rate synchronization"),
    ("stroke phase", "speed/acceleration", "tool condition", "package geometry/material"),
    "Approved load, package-geometry, and tool-condition sweeps across stroke phases.",
    ("acceleration change", "current offset", "friction/temperature change"),
)


TRIM_FORM_CANDIDATE = ResearchCandidate(
    "trim_form.stroke_aligned_servo_load_profile_consistency", "trim_form", "press", RelationKind.SEMI_EMPIRICAL, RelationStatus.RESEARCH_ONLY, EvidenceMaturity.LITERATURE_SUPPORTED,
    "Stroke-aligned servo load/torque/force profile consistency.", "Semiconductor trim/form machines use electric/servo cam presses; a phase-aligned servo-load profile may carry tooling information only when drive semantics, mechanism, package geometry, and reference force are known.", "Research hypothesis only: L_servo(theta) and F_reference(theta) are compared within one machine/tool/package regime",
    ("punch_force", "press_motor_current", "die_vibration", "die_temperature"), ("servo load/torque semantics", "stroke position/velocity/acceleration", "transmission/linkage", "package geometry", "tooling identity/condition", "reference force"),
    (
        EvidenceClaim("semiconductor_servo_cam", "Semiconductor trim/form OEM information describes electric cam servo equipment and 3-5 ton-class servo punch capability.", ("gallant_trim_form", "taijin_trim_form"), "semiconductor trim/form equipment capability", "Product specifications do not define TF-01 feedback channels or health sensitivity."),
        EvidenceClaim("motor_to_force", "Motor current can map to torque only under documented motor/drive assumptions; punch force also requires the intervening mechanism and state.", ("maxon_motor_constants",), "motor mechanics", "No press-specific parameters are available."),
    ),
    (_measurement("servo_load_or_torque", "actual servo load or torque feedback", "N*m", "feedback definition, scaling, control mode, limits and filtering", missing=True), _measurement("punch_force", "reference punch force", "kN", "load-cell location, bandwidth and dynamic calibration"), _measurement("stroke_position", "actual stroke angle/position", "rad", "encoder reference, direction, velocity/acceleration and trigger", missing=True), _measurement("tool_package_context", "tooling and package-geometry context", "state", "stable pseudonymous identifiers and change record", missing=True)),
    _uncertainties("servo load/torque scaling", "force reference", "stroke position/alignment"), _discrepancies("linkage/inertia", "friction", "tool/package/material effects"),
    (FaultSensitivity("tool wear/damage", ResidualDirection.UNKNOWN, EvidenceMaturity.HYPOTHESIS, "May change phase-specific force/current relationship."),),
    (SensorFailureMode("punch_force", "gain drift", "false consistency change", True),),
    (ResidualFmeaEntry("tool condition change", "force/current waveform changes", "condition dependent", ("material", "phase", "friction"), "force/current gain drift", False),),
    "Motor current is not punch force without drive semantics; the comparison also requires stroke phase, mechanism, package geometry, tooling condition, and dynamic terms.",
    ("stroke encoder", "verified servo load/torque feedback", "reference force", "mechanism configuration", "tool/package context", "high-rate alignment"), PRESS_EXPERIMENT.rejection_criteria, PRESS_EXPERIMENT,
    PRESS_EXPERIMENT.recalibration_triggers, PRESS_EXPERIMENT.invalidation_triggers,
    "Missing phase-resolved mechanism, tool/package context, reference force, and drive semantics.", "Could provide redundant tooling/load evidence after a controlled mechanics study.", PRESS_EXPERIMENT.objective,
    (GALLANT_TRIM_FORM, TAIJIN_TRIM_FORM, MAXON_CONSTANTS, ISO_CONDITION_MONITORING),
)
