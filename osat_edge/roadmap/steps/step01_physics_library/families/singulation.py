"""singulation Step01 research candidate."""

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
    DICING_DYNAMICS,
    ISO_CONDITION_MONITORING,
    ISO_VIBRATION_CALIBRATION,
    ISO_VIBRATION_SCOPE,
    SINGULATION_EXPERIMENT,
    _discrepancies,
    _measurement,
    _uncertainties,
)


SINGULATION_CANDIDATE = ResearchCandidate(
    "singulation.spindle_current_speed_residual", "singulation", "spindle", RelationKind.MACHINE_FITTED, RelationStatus.RESEARCH_ONLY, EvidenceMaturity.HYPOTHESIS,
    "Exact-machine speed-conditioned spindle-current residual for singulation.", "A cutting spindle may show current/load consistency, but wafer-dicing evidence cannot be assumed transferable to a different singulation mechanism.", "r_I=I-(a_machine n+b_machine) inside a separately calibrated envelope",
    ("spindle_current", "spindle_speed", "blade_vibration"), ("verified drive semantics", "feed/depth/phase", "machine-specific force/load evidence", "vibration bandwidth/axis"),
    (EvidenceClaim("no_transfer_by_name", "Dicing mechanisms are coupled and equipment-specific; shared channel names do not establish transferability.", ("li_2026_dicing_dynamics",), "wafer dicing only", "No direct singulation evidence has been verified."),),
    (_measurement("spindle_speed", "actual singulation spindle speed", "RPM", "actual versus command and controller path"), _measurement("spindle_current", "singulation drive current", "A", "feedback type and aggregation"), _measurement("cut_context", "feed/depth/material/phase", "state", "cycle aligned", missing=True)),
    _uncertainties("speed/current calibration", "alignment", "vibration calibration"), _discrepancies("mechanism transfer", "process/context", "controller behavior"),
    (FaultSensitivity("added singulation cutting load", ResidualDirection.POSITIVE, EvidenceMaturity.HYPOTHESIS, "Plausible only; not directly supported for this equipment."),),
    (SensorFailureMode("spindle_current", "positive bias", "false load residual", True),),
    (ResidualFmeaEntry("added cutting load", "current may rise", "positive", ("feed/depth/material",), "current/speed bias", False),),
    "No direct singulation evidence or verified equivalence supports reusing the wafer-saw relation.",
    ("singulation-specific drive review", "context channels", "reference load/force", "specified vibration acquisition"), SINGULATION_EXPERIMENT.rejection_criteria, SINGULATION_EXPERIMENT,
    SINGULATION_EXPERIMENT.recalibration_triggers, SINGULATION_EXPERIMENT.invalidation_triggers,
    "Transferability from wafer dicing has not been demonstrated.", "Could provide exact-machine load consistency if independently validated on singulation equipment.", SINGULATION_EXPERIMENT.objective,
    (DICING_DYNAMICS, ISO_CONDITION_MONITORING, ISO_VIBRATION_CALIBRATION, ISO_VIBRATION_SCOPE),
)

