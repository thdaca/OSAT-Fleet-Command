"""wafer mount Step01 research candidate."""

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
    BRANCA_WEB,
    ISO_CONDITION_MONITORING,
    MAXON_CONSTANTS,
    WEB_EXPERIMENT,
    _discrepancies,
    _measurement,
    _uncertainties,
)


WAFER_MOUNT_CANDIDATE = ResearchCandidate(
    "wafer_mount.roller_current_web_tension", "wafer_mount", "feed", RelationKind.SEMI_EMPIRICAL, RelationStatus.RESEARCH_ONLY, EvidenceMaturity.LITERATURE_SUPPORTED,
    "Motor-current/web-tension consistency relation for the wafer-mount feed.", "Drive torque and roller mechanics contribute to web tension, but acceleration, radius, transmission, friction, and span dynamics matter.", "T_web = f(K_t I, radii, inertia, acceleration, friction, span dynamics)",
    ("roller_motor_current", "web_tension", "roller_temperature"), ("speed/acceleration", "torque/current semantics", "roller geometry", "transmission", "phase"),
    (EvidenceClaim("web_dynamics", "Web tension depends on roller dynamics and nonideal roller behavior.", ("branca_2013_web_tension", "maxon_motor_constants"), "web handling", "Not wafer-mount validation."),),
    (_measurement("roller_motor_current", "drive current/torque feedback", "A", "actual feedback basis and controller scaling"), _measurement("web_tension", "tape/web tension", "N", "sensor location, direction, span, and calibration"), _measurement("roller_speed", "roller speed/acceleration", "rad/s", "actual shaft motion", missing=True)),
    _uncertainties("current scaling", "tension calibration", "alignment"), _discrepancies("friction", "span elasticity", "roller inertia"),
    (FaultSensitivity("roller/feed drag", ResidualDirection.UNKNOWN, EvidenceMaturity.HYPOTHESIS, "Could change current at comparable measured tension."),),
    (SensorFailureMode("web_tension", "zero/scale drift", "apparent current-tension inconsistency", True),),
    (ResidualFmeaEntry("feed drag", "current increases", "condition dependent", ("acceleration", "temperature"), "current/tension bias", False),),
    "Direct tension exists, but mechanical and phase semantics are absent; a generic regression would not be a controlled torque balance.",
    ("encoder/phase", "verified torque feedback", "roller geometry/configuration"), WEB_EXPERIMENT.rejection_criteria, WEB_EXPERIMENT,
    WEB_EXPERIMENT.recalibration_triggers, WEB_EXPERIMENT.invalidation_triggers,
    "Missing motion phase, geometry, and verified current/torque semantics.", "Could provide analytical redundancy for a direct tension sensor.", WEB_EXPERIMENT.objective,
    (BRANCA_WEB, MAXON_CONSTANTS, ISO_CONDITION_MONITORING),
)

