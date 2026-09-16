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
    BESI_FICO_MOLDING,
    ISO_CONDITION_MONITORING,
    MOLDING_MONITOR,
    MOLDING_PROCESS,
)


MOLD_EXPERIMENT = _experiment(
    "Test phase-resolved clamp-force, transfer-pressure, and mold-temperature consistency on an instrumented semiconductor transfer mold.",
    "Within a fixed tool/material/phase regime, actual clamp-force and transfer-pressure profiles should be repeatable conditional on mold-zone temperatures.",
    ("actual clamp-force feedback/reference", "transfer and cavity pressure", "multi-zone mold temperature", "position/phase", "cavity vacuum"),
    ("clamp-force profile", "transfer-pressure profile", "mold-zone temperature", "vacuum", "tool/material state"),
    "Safe force/pressure/temperature sweeps on an approved instrumented mold.",
    ("force/pressure sensor offset", "material change", "temperature-zone bias", "vacuum change", "tool change"),
)


MOLDING_CANDIDATE = ResearchCandidate(
    "molding.clamp_transfer_temperature_consistency", "molding", "mold_press", RelationKind.SEMI_EMPIRICAL, RelationStatus.RESEARCH_ONLY, EvidenceMaturity.LITERATURE_SUPPORTED,
    "Phase-resolved clamp-force / transfer-pressure / mold-temperature consistency.", "Modern transfer molding controls clamp force, transfer pressure, temperature zones, and cavity vacuum; their measured profiles may provide equipment-consistency evidence only within a fixed process context.", "Research hypothesis only: [F_clamp(t), p_transfer(t)] = f_machine(T_zones(t), phase, vacuum, tool, material)",
    ("cavity_pressure", "clamp_pressure", "mold_temperature", "plunger_position_error", "transfer_motor_current"), ("actual clamp force", "transfer-pressure semantics", "multi-zone temperatures", "cavity vacuum", "phase/position", "tool/material/cure context"),
    (
        EvidenceClaim("fico_controls", "Besi/Fico documents dynamic and active clamp-force control, dynamic transfer-pressure control, accurate multi-zone temperature control, and cavity vacuum on semiconductor molding equipment.", ("besi_fico_molding_line",), "one Fico molding line", "Product capability does not define MO-01 telemetry or validate a health residual."),
        EvidenceClaim("mold_instrumentation", "Transfer-mold research uses cavity pressure, temperature, and cure/process context.", ("kahle_2016_transfer_molding",), "electronic packaging transfer molding", "Does not justify treating hydraulic pressure as clamp force."),
    ),
    (_measurement("clamp_force", "actual clamp-force feedback", "N", "force definition, control mode, phase and calibration", missing=True), _measurement("transfer_pressure", "actual transfer-pressure feedback", "MPa", "sensor location, gauge/reference, control phase and bandwidth", missing=True), _measurement("mold_temperature_zones", "multi-zone mold temperatures", "°C", "zone identity, calibration and phase alignment", missing=True), _measurement("cavity_vacuum", "cavity vacuum pressure", "kPa", "absolute/gauge basis, location and phase", missing=True), _measurement("mold_phase", "press/transfer cycle phase", "state", "position/time trigger and window", missing=True)),
    _uncertainties("force calibration", "pressure calibration", "temperature-zone calibration", "phase alignment"), _discrepancies("hydraulic/servo dynamics", "resin rheology/cure", "cavity/tool distribution", "vacuum/material state"),
    (FaultSensitivity("insufficient clamp force", ResidualDirection.NEGATIVE, EvidenceMaturity.HYPOTHESIS, "Actual clamp force may fall below the phase-specific required force."),),
    (SensorFailureMode("cavity_pressure", "positive bias", "false force deficit", True),),
    (ResidualFmeaEntry("clamp deficit", "lower force relative to cavity pressure", "negative margin", ("area", "material/phase"), "pressure/force bias", False),),
    "The OEM source supports the controlled quantities, but MO-01 channel names do not establish actual clamp force, transfer pressure, temperature zones, vacuum, phase, or process context.",
    ("actual clamp-force feedback", "transfer-pressure feedback", "temperature-zone identity", "cavity vacuum", "phase/position", "tool/material context"), MOLD_EXPERIMENT.rejection_criteria, MOLD_EXPERIMENT,
    MOLD_EXPERIMENT.recalibration_triggers, MOLD_EXPERIMENT.invalidation_triggers,
    "No verified MO-01 measurement semantics or fixed process-context boundary.", "Could expose coordinated press/transfer/thermal consistency during controlled molding research.", MOLD_EXPERIMENT.objective,
    (BESI_FICO_MOLDING, MOLDING_MONITOR, MOLDING_PROCESS, ISO_CONDITION_MONITORING),
)
