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
    _discrepancies,
    _experiment,
    _measurement,
    _uncertainties,
)
from ..core.references import (
    BRANCA_WEB,
    INFINEON_TAPE_TENSION,
    ISO_CONDITION_MONITORING,
    MAXON_CONSTANTS,
)


WEB_EXPERIMENT = _experiment(
    "Test repeatability and drift of dicing-tape tension after mounting, with material and lamination context blocked explicitly.",
    "A direct calibrated tension indicator should remain stable within a fixed tape/roll/lamination regime and change under controlled tension perturbations.",
    ("calibrated direct or optical tension reference", "frame/tape identity", "lamination settings", "optional verified drive torque feedback"),
    ("tape manufacturer/type/material", "roll identity/change", "lamination settings", "frame and temperature"),
    "Safe controlled tension and lamination changes on approved frames.",
    ("roll change at fixed settings", "material change at fixed settings", "sensor offset", "optional current change at fixed tension"),
)


WAFER_MOUNT_CANDIDATE = ResearchCandidate(
    "wafer_mount.dicing_tape_tension_stability", "wafer_mount", "tape_mount", RelationKind.SEMI_EMPIRICAL, RelationStatus.RESEARCH_ONLY, EvidenceMaturity.LITERATURE_SUPPORTED,
    "Direct dicing-tape tension stability and drift within a documented mounting regime.", "Mounted-tape tension depends on tape material, frame deformation/stretch, lamination/roller settings, environment, and time; a direct tension indicator can be trended only within that context.", "Delta_T = T_direct - T_regime_baseline (research only; no universal threshold)",
    ("web_tension", "roller_temperature", "roller_motor_current"), ("direct per-frame tension semantics", "tape maker/type/material", "roll identity", "lamination settings", "frame identity", "time since lamination"),
    (
        EvidenceClaim("mounted_tape_tension", "An Infineon wafer-mounter patent discloses per-tape tension monitoring and identifies tape properties, roll changes, stretching, rollers, lamination, and frame deformation as relevant context.", ("infineon_dicing_tape_tension",), "wafer-mount dicing tape", "Patent disclosure is not independent validation or a health threshold."),
        EvidenceClaim("web_dynamics", "Web tension depends on roller dynamics and nonideal roller behavior.", ("branca_2013_web_tension",), "web handling", "Not wafer-mount validation."),
    ),
    (_measurement("web_tension", "direct dicing-tape tension indicator", "N", "method, axis/location, frame state, calibration, and per-frame timing"), _measurement("roller_motor_current", "optional drive feedback", "A", "actual torque/current semantics and controller scaling; never assumed to equal tension"), _measurement("lamination_context", "tape/roll/frame/settings context", "state", "pseudonymous reviewed categories", missing=True)),
    _uncertainties("tension reference", "frame positioning", "temperature and time"), _discrepancies("anisotropic tape behavior", "lamination mechanics", "material/roll variation"),
    (FaultSensitivity("tension stability or drift", ResidualDirection.MAGNITUDE_ONLY, EvidenceMaturity.LITERATURE_SUPPORTED, "Direct per-frame tension may drift within a fixed, verified regime."),),
    (SensorFailureMode("web_tension", "zero/scale drift", "apparent current-tension inconsistency", True),),
    (ResidualFmeaEntry("tape-tension drift", "direct tension changes within regime", "magnitude drift", ("tape material", "roll change", "lamination settings", "frame", "temperature/time"), "tension-sensor drift", False),),
    "The current repository lacks per-frame measurement semantics and the tape/roll/lamination context required to interpret drift; motor current is not tension without verified drive semantics.",
    ("direct per-frame tension method", "tape/roll/frame context", "lamination settings", "optional verified torque feedback"), WEB_EXPERIMENT.rejection_criteria, WEB_EXPERIMENT,
    WEB_EXPERIMENT.recalibration_triggers, WEB_EXPERIMENT.invalidation_triggers,
    "Missing direct measurement semantics and configuration context; optional motor feedback has unverified torque/current meaning.", "Could provide controlled stability/drift evidence for the actual mounted tape without treating process variation as equipment health.", WEB_EXPERIMENT.objective,
    (INFINEON_TAPE_TENSION, BRANCA_WEB, MAXON_CONSTANTS, ISO_CONDITION_MONITORING),
)
