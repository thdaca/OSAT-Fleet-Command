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
    _discrepancies,
    _experiment,
    _measurement,
    _uncertainties,
)
from ..core.references import (
    ISO_CONDITION_MONITORING,
    PTI_WIRE_BOND,
    WIRE_BOND_IMPEDANCE,
    WIRE_BOND_PIEZO,
)


WIRE_EXPERIMENT = _experiment(
    "Determine whether synchronized generator impedance/vibration features respond to controlled bond-quality changes.",
    "Transducer/contact mechanics alter voltage-current phase/impedance and vibration during defined bond phases.",
    ("synchronized high-rate voltage/current", "phase", "bond trigger", "calibrated PZT", "destructive bond-quality reference"),
    ("bond force", "ultrasonic power/time", "wire/pad material", "tool condition"),
    "Approved parameter sweeps and known tool/bond conditions.",
    ("electrical gain/phase injection", "no-contact ultrasonic cycle", "temperature change"),
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


WIRE_ELECTRICAL_EXPERIMENT = _experiment(
    "Test ultrasonic-generator electrical-load consistency during one explicitly defined bond phase.",
    "Within a fixed generator control mode, bond phase/window, drive frequency, tool identity, and machine context, generator electrical-load measurements may be repeatable and respond to controlled tool/contact changes.",
    ("machine-reported USG current", "voltage where available", "documented impedance definition", "phase/frequency", "bond trigger/window", "tool/capillary identity"),
    ("bond phase/window", "control mode", "drive frequency", "tool/capillary", "bond force and material context"),
    "Approved tool/contact/parameter conditions with independent inspection outcomes.",
    ("current/impedance sensor bias", "control-mode change", "no-contact cycle", "tool identity change", "window shift"),
)


WIRE_BOND_ELECTRICAL_CANDIDATE = ResearchCandidate(
    "wire_bond.ultrasonic_generator_electrical_load_consistency", "wire_bond", "ultrasonic", RelationKind.DIAGNOSTIC_PROXY, RelationStatus.RESEARCH_ONLY, EvidenceMaturity.LITERATURE_SUPPORTED,
    "Ultrasonic-generator electrical-load consistency during a defined bond phase.", "Machine-reported generator current and impedance may describe a repeatable electrical-load state only when the controller, frequency, phase/window, impedance definition, tool, and machine context are fixed and documented.", "No derived-impedance equation: compare explicitly defined machine-reported electrical-load measurements within a frozen bond-phase context.",
    ("ultrasonic_current", "ultrasonic_frequency_shift", "bond_force"), ("control mode", "voltage where available", "phase", "drive frequency", "machine impedance definition", "bond phase/window", "tool/capillary identity", "machine context"),
    (
        EvidenceClaim("pti_osat_wire_bond_fields", "A Powertech OSAT production study reports Capillary Count, Bond Height Delta, Deformation, Die Height, Die Tilt, Bond Force, USG Impedance, USG Current, Z at Contact, and Z at End of Bonding.", ("pti_wire_bond_2026",), "real OSAT production wire bonding", "The paper supplies field names but no engineering units or public raw records; inspection anomalies are not machine-fault labels."),
        EvidenceClaim("pti_data_requestable", "The publisher states that company-confidential data are available from the corresponding author on reasonable request.", ("pti_wire_bond_2026",), "data-access statement", "Requestable does not mean obtained, executable, or approved for ingestion."),
    ),
    (_measurement("usg_current", "machine-reported ultrasonic-generator current in the defined phase/window", "mA", "control mode, current basis, bandwidth, aggregation, and path"), _measurement("usg_impedance", "machine-computed ultrasonic-generator impedance", "ohm", "OEM definition; never reconstructed or assumed from the field name", missing=True), _measurement("usg_voltage", "generator voltage where available", "V", "path, bandwidth, phase calibration, and synchronization", missing=True), _measurement("drive_frequency", "actual ultrasonic drive frequency", "Hz", "command versus actual and phase-window aggregation", missing=True), _measurement("bond_phase", "defined bond phase/window", "state", "cycle trigger, start/end, and aggregation", missing=True), _measurement("tool_identity", "pseudonymous tool/capillary and machine context", "state", "stable pseudonyms and change history", missing=True)),
    _uncertainties("current/voltage scaling", "machine-impedance definition", "phase/window alignment", "frequency aggregation"), _discrepancies("generator control behavior", "transducer/tool/contact dynamics", "bond material and recipe context"),
    (FaultSensitivity("ultrasonic generator/tool/load consistency change", ResidualDirection.MAGNITUDE_ONLY, EvidenceMaturity.HYPOTHESIS, "The OSAT fields justify a targeted study, not a diagnostic direction or threshold."),),
    (SensorFailureMode("usg_current", "bias or gain drift", "false electrical-load change", True), SensorFailureMode("bond_phase", "window shift", "different phase compared as if equivalent", True)),
    (ResidualFmeaEntry("generator/tool/load consistency change", "phase-window electrical fields change", "magnitude-only research deviation", ("control mode", "frequency", "tool/capillary", "bond phase", "machine/recipe context"), "current/impedance/window error", False),),
    "Real OSAT fields support the research question, but their measurement semantics, engineering units, machine context, and physical fault labels are unavailable.",
    ("field dictionary and units", "control mode and drive frequency", "phase/window trigger", "tool/capillary identity", "voltage where available", "inspection/maintenance context"), WIRE_ELECTRICAL_EXPERIMENT.rejection_criteria, WIRE_ELECTRICAL_EXPERIMENT,
    WIRE_ELECTRICAL_EXPERIMENT.recalibration_triggers, WIRE_ELECTRICAL_EXPERIMENT.invalidation_triggers,
    "No approved WB-04 raw data or complete generator measurement semantics.", "Could test a narrow, phase-specific electrical-load consistency hypothesis without treating machine-computed impedance as derived impedance.", WIRE_ELECTRICAL_EXPERIMENT.objective,
    (PTI_WIRE_BOND, WIRE_BOND_IMPEDANCE, ISO_CONDITION_MONITORING),
)


WIRE_BOND_CANDIDATES = (WIRE_BOND_CANDIDATE, WIRE_BOND_ELECTRICAL_CANDIDATE)
