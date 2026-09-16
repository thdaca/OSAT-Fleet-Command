"""die attach Step01 research candidate."""

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
    JCGM_UNCERTAINTY,
    LEYBOLD_LEAK,
)


VACUUM_EXPERIMENT = _experiment(
    "Validate isolated-volume pressure-rise inference for the die-attach pickup path.",
    "With pump/valves isolated and volume known, pressure-rise rate increases with a calibrated leak.",
    ("known volume", "valve/pump state", "calibrated pressure gauge", "reference leak", "gas temperature"),
    ("leak rate", "volume", "temperature", "isolation duration"),
    "Introduce approved reference leaks during a controlled non-production isolation sequence.",
    ("outgassing/virtual-leak soak", "gauge offset", "pump still connected"),
)


DIE_ATTACH_CANDIDATE = ResearchCandidate(
    "die_attach.nozzle_vacuum_leak_rate", "die_attach", "vacuum", RelationKind.FIRST_PRINCIPLES, RelationStatus.REJECTED, EvidenceMaturity.LITERATURE_SUPPORTED,
    "Leak-rate inference from a controlled isolated-volume pressure-rise test.", "For known isolated volume and thermal conditions, leak rate relates to pressure rise over time.", "q_L = V Δp/Δt",
    ("nozzle_vacuum",), ("known volume", "valve/pump state", "isolation interval", "time series", "temperature"),
    (EvidenceClaim("pressure_rise", "Pressure-rise leak testing requires a known isolated volume and timed pressure change.", ("leybold_pressure_rise",), "vacuum leak testing", "Running vacuum is not an isolated test."),),
    (_measurement("nozzle_vacuum", "absolute pressure during isolation", "kPa", "absolute/gauge convention, location, bandwidth"), _measurement("isolation_state", "pump/valve isolation state", "state", "verified sealed interval", missing=True), _measurement("isolated_volume", "enclosed pneumatic volume", "m^3", "configuration-specific measured volume", missing=True)),
    _uncertainties("pressure gauge", "volume", "temperature/timing"), _discrepancies("outgassing", "virtual leaks", "seal dynamics"),
    (FaultSensitivity("real leak", ResidualDirection.POSITIVE, EvidenceMaturity.LITERATURE_SUPPORTED, "A larger leak raises pressure faster during valid isolation."),),
    (SensorFailureMode("nozzle_vacuum", "positive drift", "false pressure-rise rate", True),),
    (ResidualFmeaEntry("leak", "faster pressure rise", "positive", ("outgassing", "temperature"), "gauge drift", False),),
    "A single live vacuum value cannot identify leak rate or separate pump, valve, seal, and phase effects.",
    ("controlled isolation state", "known volume", "calibrated time-series gauge", "reference leak"), VACUUM_EXPERIMENT.rejection_criteria, VACUUM_EXPERIMENT,
    VACUUM_EXPERIMENT.recalibration_triggers, VACUUM_EXPERIMENT.invalidation_triggers,
    "Missing the experimental boundary conditions that define the equation.", "A valid offline isolation test could quantify leakage.", VACUUM_EXPERIMENT.objective,
    (LEYBOLD_LEAK, JCGM_UNCERTAINTY),
)
