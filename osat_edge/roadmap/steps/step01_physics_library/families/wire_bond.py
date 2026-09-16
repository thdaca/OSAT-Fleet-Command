"""wire bond Step01 research candidate."""

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
    ISO_CONDITION_MONITORING,
    WIRE_BOND_IMPEDANCE,
    WIRE_BOND_PIEZO,
    WIRE_EXPERIMENT,
    _discrepancies,
    _measurement,
    _uncertainties,
)


WIRE_BOND_CANDIDATE = ResearchCandidate(
    "wire_bond.ultrasonic_input_impedance", "wire_bond", "ultrasonic", RelationKind.DIAGNOSTIC_PROXY, RelationStatus.REJECTED, EvidenceMaturity.LITERATURE_SUPPORTED,
    "Phase-resolved ultrasonic-generator impedance/vibration monitoring.", "Bond/contact mechanics affect transducer electrical impedance and vibration during bond phases.", "Z(t,f)=V(t,f)/I(t,f), retaining magnitude and phase",
    ("ultrasonic_current", "ultrasonic_frequency_shift"), ("voltage waveform", "V/I phase", "bandwidth", "bond trigger", "reference bond quality"),
    (EvidenceClaim("wire_impedance", "Published wire-bond monitoring uses generator voltage plus current and phase/harmonic information.", ("feng_2011_wire_bond",), "wire bonding", "Current and low-rate frequency shift do not reconstruct impedance."),),
    (_measurement("ultrasonic_current", "generator current waveform", "A", "waveform bandwidth and point in generator path"), _measurement("ultrasonic_voltage", "generator voltage waveform", "V", "synchronized with current and phase calibrated", missing=True), _measurement("bond_phase", "bond-cycle phase trigger", "state", "phase-aligned events", missing=True)),
    _uncertainties("voltage/current gain", "phase", "trigger timing"), _discrepancies("transducer dynamics", "tool/contact/material", "generator control"),
    (FaultSensitivity("bond interface/tool condition", ResidualDirection.UNKNOWN, EvidenceMaturity.LITERATURE_SUPPORTED, "Published impedance/harmonic signatures can respond to bonding interaction."),),
    (SensorFailureMode("ultrasonic_current", "gain/phase error", "false impedance/harmonic change", True),),
    (ResidualFmeaEntry("bond/tool change", "impedance/harmonics change", "condition dependent", ("temperature", "settings"), "phase/gain error", False),),
    "Required voltage, phase, bandwidth, and bond-cycle semantics are absent.",
    ("synchronized voltage/current", "phase calibration", "bond trigger", "quality reference"), WIRE_EXPERIMENT.rejection_criteria, WIRE_EXPERIMENT,
    WIRE_EXPERIMENT.recalibration_triggers, WIRE_EXPERIMENT.invalidation_triggers,
    "Ordinary low-rate channels cannot reproduce the published measurement.", "Could support bond-interaction research with dedicated acquisition.", WIRE_EXPERIMENT.objective,
    (WIRE_BOND_IMPEDANCE, WIRE_BOND_PIEZO, ISO_CONDITION_MONITORING),
)

