"""final test Step01 research candidate."""

from __future__ import annotations

import numpy as np

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
    FINAL_TEST_HANDLER,
    ISO_CONDITION_MONITORING,
    ISO_MEASUREMENT_MANAGEMENT,
    JCGM_VIM,
    KEITHLEY_LOW_LEVEL,
    KEYSIGHT_LOW_RESISTANCE,
    LIU_WAFER_PROBE,
    NI_SOCKET_GUIDANCE,
)


def contact_resistance_mohm_for_research(voltage_drop_mv: float, current_a: float) -> float:
    """Dimension-only V/I helper; it is not an executable health relation."""

    voltage = float(voltage_drop_mv)
    current = float(current_a)
    if not np.isfinite(voltage) or not np.isfinite(current) or abs(current) < 1e-6:
        raise ValueError("Finite voltage and non-negligible current are required")
    result = voltage / current
    if not np.isfinite(result):
        raise ValueError("Resistance result is not finite")
    return result


CONTACT_EXPERIMENT = _experiment(
    "Determine whether repository voltage/current channels isolate final-test contact resistance with adequate metrology.",
    "Four-terminal, contact-local, settled V/I with offset compensation will track controlled contact contamination/wear.",
    ("Kelvin force/sense path", "SMU/nanovoltmeter", "current reversal/offset compensation", "contact force and temperature", "per-pin/fixture identity"),
    ("known resistance", "contact force", "current", "temperature", "contamination/insertion count"),
    "Approved reference resistances and controlled contact contamination/wear specimens.",
    ("lead/relay resistance change", "DUT voltage change", "thermoelectric offset", "current-source settling"),
)


FINAL_TEST_CANDIDATE = ResearchCandidate(
    "final_test.contact_resistance", "final_test", "contacts", RelationKind.CONSTITUTIVE, RelationStatus.RESEARCH_ONLY, EvidenceMaturity.LITERATURE_SUPPORTED,
    "Contact-isolated four-terminal resistance from settled, aligned voltage and current.", "Ohm's law is valid dimensionally, but the measured voltage must isolate the contact path and measurement errors must be controlled.", "R_contact[mΩ]=V_contact[mV]/I_contact[A]",
    ("contact_voltage_drop", "site_current"), ("Kelvin/contact-isolated topology", "force/sense path", "offset compensation", "settling/phase", "fixture and DUT exclusion"),
    (EvidenceClaim("kelvin_requirement", "Low/contact-resistance measurement generally needs four-terminal sensing and offset/thermal control to exclude leads and offsets.", ("keithley_low_level_7",), "precision contact/low resistance", "Repository names and units do not establish the method."), EvidenceClaim("contact_condition", "Contact condition and contamination can affect measured contact resistance.", ("liu_2007_wafer_probe_contact",), "wafer probe testing", "Wafer probes are not final-test sockets.")),
    (_measurement("contact_voltage_drop", "voltage only across the identified contact", "mV", "Kelvin sense, offset compensation, polarity and settling"), _measurement("site_current", "same-path forced/measured current", "A", "source/measure timing and compliance"), _measurement("contact_force", "contact normal force", "N", "per contact or controlled fixture", missing=True)),
    _uncertainties("voltage offset/noise", "current accuracy", "lead/relay contribution", "self-heating"), _discrepancies("DUT/fixture path", "non-ohmic contact", "force/temperature dependence"),
    (FaultSensitivity("contact contamination/wear", ResidualDirection.POSITIVE, EvidenceMaturity.LITERATURE_SUPPORTED, "Can raise contact resistance, but final-test implementation evidence is absent."),),
    (SensorFailureMode("contact_voltage_drop", "positive offset", "false high resistance", True), SensorFailureMode("site_current", "low scale bias", "false high resistance", True)),
    (ResidualFmeaEntry("contact degradation", "contact-local voltage rises at fixed current", "positive resistance", ("force", "temperature", "fixture/DUT"), "voltage/current bias", False),),
    "machines.py supplies only channel names and units; it does not prove Kelvin, contact isolation, settling, or offset compensation.",
    ("four-terminal topology review", "SMU timing/compliance state", "per-contact identity/force", "reference standards"), CONTACT_EXPERIMENT.rejection_criteria, CONTACT_EXPERIMENT,
    CONTACT_EXPERIMENT.recalibration_triggers, CONTACT_EXPERIMENT.invalidation_triggers,
    "The measurand may include leads, relays, fixtures, and DUT voltage rather than the contact alone.", "With verified metrology, direct contact resistance could be a high-value degradation measure.", CONTACT_EXPERIMENT.objective,
    (KEITHLEY_LOW_LEVEL, KEYSIGHT_LOW_RESISTANCE, NI_SOCKET_GUIDANCE, LIU_WAFER_PROBE, JCGM_VIM, ISO_MEASUREMENT_MANAGEMENT),
)


HANDLER_EXPERIMENT = _experiment(
    "Establish the measurement semantics needed to study test-handler motor signatures against independently adjudicated equipment events.",
    "Phase-aligned motor current/position/velocity signatures may change with handler mechanical condition when motor, drive, control mode, motion command, contact cycle, and DUT test context are known.",
    ("motor/drive channel dictionary", "actual position and velocity", "motion-cycle trigger", "control mode and motor identity", "maintenance/fault adjudication", "downstream DUT electrical-test context"),
    ("motion phase", "position/velocity/acceleration", "motor/control mode", "handler tooling/contact state", "DUT context pseudonym"),
    "Approved healthy repeats and independently adjudicated maintenance/fault intervals; no intentional production damage.",
    ("current-sensor bias", "motion-profile change", "motor/controller change", "DUT electrical change without handler fault", "window shift"),
)


FINAL_TEST_HANDLER_CANDIDATE = ResearchCandidate(
    "final_test.handler_motor_signature_consistency", "final_test", "handler_motion", RelationKind.DIAGNOSTIC_PROXY, RelationStatus.RESEARCH_ONLY, EvidenceMaturity.LITERATURE_SUPPORTED,
    "Test-handler motor-signature consistency with downstream DUT electrical-test context.", "Real semiconductor final-test research demonstrates that upstream handler motor signatures and downstream DUT electrical-test readouts can jointly support equipment fault detection; a physical relation still requires identified motion and drive semantics.", "DEFERRED: no physical equation until current, position, velocity, motor, drive, control-mode, and motion-phase semantics are known.",
    ("handler_motor_current", "handler_vibration", "contact_voltage_drop", "site_current"), ("actual position", "actual velocity/acceleration", "motor/drive identity", "control mode", "motion command and phase", "handler tooling", "adjudicated equipment-fault intervals"),
    (EvidenceClaim("real_semiconductor_final_test", "A 2026 semiconductor final-test study combines upstream test-handler motor signatures with downstream DUT electrical-test results for equipment fault detection/prognostics.", ("roy_2026_final_test_handler",), "real semiconductor final-test production", "Strong domain evidence is not raw data, measurement semantics, a transferable equation, or FT-01 validation."),),
    (_measurement("handler_motor_current", "identified handler-motor drive current", "A", "motor, drive, current basis, control mode, filtering and motion phase"), _measurement("handler_position", "actual mechanism or motor position", "mm", "coordinate, encoder path, command versus actual and phase", missing=True), _measurement("handler_velocity", "actual mechanism or motor velocity", "mm/s", "derivation/filtering, direction and alignment", missing=True), _measurement("handler_phase", "defined handler motion/contact phase", "state", "cycle trigger and window", missing=True), _measurement("dut_test_context", "pseudonymous downstream DUT electrical-result context", "state", "test-result meaning without customer/product identity", missing=True)),
    _uncertainties("motor-current scaling", "position/velocity calibration", "phase alignment", "maintenance/fault boundaries"), _discrepancies("motion/controller behavior", "handler tooling/friction", "DUT/contact/test coupling", "operating context"),
    (FaultSensitivity("handler mechanical/equipment fault", ResidualDirection.MAGNITUDE_ONLY, EvidenceMaturity.HYPOTHESIS, "Published domain evidence motivates study but does not establish direction for FT-01."),),
    (SensorFailureMode("handler_motor_current", "bias, gain drift, or clipping", "false motor-signature change", True), SensorFailureMode("handler_phase", "timing/window error", "different motion segments compared", True)),
    (ResidualFmeaEntry("handler equipment condition change", "motor signature changes within motion phase", "undefined until study", ("motion profile", "motor/control mode", "tooling", "DUT/contact context"), "current/position/window error", False),),
    "The publication establishes a credible real-semiconductor use case, but no FT-01 raw data or current/position/velocity/motor/control semantics exist.",
    ("motor/drive dictionary", "position/velocity", "phase trigger", "control mode", "pseudonymous DUT context", "adjudicated events"), HANDLER_EXPERIMENT.rejection_criteria, HANDLER_EXPERIMENT,
    HANDLER_EXPERIMENT.recalibration_triggers, HANDLER_EXPERIMENT.invalidation_triggers,
    "No FT-01 motion semantics, raw study data, or adjudicated equipment-fault intervals.", "Could support a physically scoped handler-motion consistency study once measurement semantics are verified.", HANDLER_EXPERIMENT.objective,
    (FINAL_TEST_HANDLER, ISO_CONDITION_MONITORING),
)


FINAL_TEST_CANDIDATES = (FINAL_TEST_CANDIDATE, FINAL_TEST_HANDLER_CANDIDATE)
