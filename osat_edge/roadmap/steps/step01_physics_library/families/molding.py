"""molding Step01 research candidate."""

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
    MOLDING_MONITOR,
    MOLDING_PROCESS,
)


MOLD_EXPERIMENT = _experiment(
    "Test a phase-resolved clamp-force/cavity-pressure balance on an instrumented transfer mold.",
    "Measured clamp force must exceed cavity pressure times approved projected area after characterized dynamic losses.",
    ("actual clamp-force sensor", "cavity-pressure sensors", "position/phase", "tool/material temperature", "approved projected area"),
    ("transfer speed", "temperature", "material state", "clamp force"),
    "Safe pressure/force sweeps on an approved instrumented mold.",
    ("hydraulic sensor offset", "material change", "same pressure with different projected area"),
)


MOLDING_CANDIDATE = ResearchCandidate(
    "molding.clamp_cavity_force_balance", "molding", "hydraulic", RelationKind.SEMI_EMPIRICAL, RelationStatus.RESEARCH_ONLY, EvidenceMaturity.LITERATURE_SUPPORTED,
    "Phase-resolved actual clamp-force versus cavity-pressure balance.", "Cavity pressure over projected area contributes force that the clamp system must oppose.", "F_required(t)=p_cavity(t)A_projected plus characterized dynamics/losses",
    ("cavity_pressure", "clamp_pressure", "transfer_motor_current", "mold_temperature", "plunger_position_error"), ("actual clamp force", "projected area", "phase/position", "material/cure state"),
    (EvidenceClaim("mold_instrumentation", "Transfer-mold research uses cavity pressure, temperature, and cure/process context.", ("kahle_2016_transfer_molding",), "electronic packaging transfer molding", "Does not justify treating hydraulic pressure as clamp force."),),
    (_measurement("cavity_pressure", "cavity pressure at named sensor", "MPa", "location, phase, response"), _measurement("clamp_force", "actual clamp force", "N", "direct force measurement", missing=True), _measurement("projected_area", "approved projected cavity/runner area", "m^2", "configuration identity", missing=True)),
    _uncertainties("pressure", "force", "temperature/alignment"), _discrepancies("hydraulic losses", "resin rheology/cure", "cavity distribution"),
    (FaultSensitivity("insufficient clamp force", ResidualDirection.NEGATIVE, EvidenceMaturity.HYPOTHESIS, "Actual clamp force may fall below the phase-specific required force."),),
    (SensorFailureMode("cavity_pressure", "positive bias", "false force deficit", True),),
    (ResidualFmeaEntry("clamp deficit", "lower force relative to cavity pressure", "negative margin", ("area", "material/phase"), "pressure/force bias", False),),
    "Hydraulic pressure is not actual clamp force and the necessary geometry/phase/material context is absent.",
    ("actual force sensor", "approved projected area", "phase/position", "material/cure context"), MOLD_EXPERIMENT.rejection_criteria, MOLD_EXPERIMENT,
    MOLD_EXPERIMENT.recalibration_triggers, MOLD_EXPERIMENT.invalidation_triggers,
    "No actual clamp-force measurand or approved geometry context.", "Could expose force-margin consistency during controlled molding research.", MOLD_EXPERIMENT.objective,
    (MOLDING_MONITOR, MOLDING_PROCESS, ISO_CONDITION_MONITORING),
)
