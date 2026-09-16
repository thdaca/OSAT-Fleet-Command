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
