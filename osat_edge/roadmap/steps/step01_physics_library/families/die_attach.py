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
    BESI_DIE_BONDER,
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


DIE_ATTACH_FORCE_EXPERIMENT = _experiment(
    "Test closed-loop placement-force consistency with Z position and internal thermal state on the identified die bonder.",
    "Within one verified bond phase, tool and thermal regime, measured force and Z trajectory should be repeatable around the commanded closed-loop profile.",
    ("calibrated bond/placement-force reference", "bond-head Z position", "internal/bond-head temperature", "command and control-mode trace", "phase trigger"),
    ("force command/profile", "Z trajectory", "internal temperature", "tool and material context"),
    "Approved force/Z/temperature sweeps without production damage.",
    ("force-sensor bias", "Z offset", "temperature-sensor bias", "tool change", "control-mode change"),
)


DIE_ATTACH_FORCE_CANDIDATE = ResearchCandidate(
    "die_attach.closed_loop_force_z_temperature_consistency", "die_attach", "bond_head", RelationKind.MACHINE_FITTED, RelationStatus.RESEARCH_ONLY, EvidenceMaturity.LITERATURE_SUPPORTED,
    "Closed-loop bond/placement-force consistency conditioned on Z position, phase, and internal temperature.", "A closed-loop die-bond head controls force along a Z trajectory; thermal and tooling state can shift the repeatable command/feedback relationship.", "Research hypothesis only: force_feedback = f_machine(force_command, Z, phase, internal_temperature, tool_context)",
    ("z_position_error", "stage_temperature", "z_axis_current"), ("actual bond-force feedback", "force command/control mode", "actual Z position and phase", "internal/bond-head temperature semantics", "tool/material context"),
    (EvidenceClaim("modern_bonder_force_z_thermal", "Modern die-bonder documentation specifies bond-force accuracy, bond-head Z control, bond-head thermal control, bond traces, and inline process monitoring.", ("besi_9800_tc_next",), "one modern Besi die-bonder design", "The product page does not establish DA-01 telemetry or an equipment-health relation."),),
    (_measurement("bond_force", "actual closed-loop bond/placement-force feedback", "N", "command versus feedback, sign, control mode, phase, and calibration", missing=True), _measurement("bond_head_z", "actual bond-head Z position", "µm", "absolute/reference frame, sampling, and phase", missing=True), _measurement("internal_temperature", "bond-head or specified internal temperature", "°C", "sensor location, thermal path, and sampling", missing=True), _measurement("bond_phase", "defined placement/bond cycle phase", "state", "cycle trigger and window", missing=True)),
    _uncertainties("force calibration", "Z calibration", "temperature location", "phase alignment"), _discrepancies("controller dynamics", "tool compliance", "material/adhesive behavior", "thermal gradients"),
    (FaultSensitivity("bond-head/tool consistency change", ResidualDirection.MAGNITUDE_ONLY, EvidenceMaturity.HYPOTHESIS, "A physical change may alter a phase-aligned closed-loop force/Z trace, but sensitivity is unverified."),),
    (SensorFailureMode("bond_force", "bias or gain drift", "false force/profile inconsistency", True), SensorFailureMode("bond_head_z", "offset or timing error", "false position-conditioned inconsistency", True)),
    (ResidualFmeaEntry("bond-head/tool consistency change", "force/Z profile changes", "magnitude-only research deviation", ("temperature", "tool", "material", "control mode"), "force/Z/temperature bias", False),),
    "OEM capability supports the measurement concept, but DA-01 lacks verified force, Z, internal-temperature, command, phase, and control-mode semantics.",
    ("force feedback and command", "actual Z and phase", "internal-temperature path", "tool/material context"), DIE_ATTACH_FORCE_EXPERIMENT.rejection_criteria, DIE_ATTACH_FORCE_EXPERIMENT,
    DIE_ATTACH_FORCE_EXPERIMENT.recalibration_triggers, DIE_ATTACH_FORCE_EXPERIMENT.invalidation_triggers,
    "No real DA-01 telemetry contract for the closed-loop quantities.", "Could provide direct bond-head consistency evidence after measurement-system validation.", DIE_ATTACH_FORCE_EXPERIMENT.objective,
    (BESI_DIE_BONDER, JCGM_UNCERTAINTY),
)


DIE_ATTACH_CANDIDATES = (DIE_ATTACH_CANDIDATE, DIE_ATTACH_FORCE_CANDIDATE)
