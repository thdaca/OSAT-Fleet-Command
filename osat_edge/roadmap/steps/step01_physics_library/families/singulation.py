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
    _discrepancies,
    _experiment,
    _measurement,
    _uncertainties,
)
from ..core.references import (
    DISCO_DAD3660,
    DICING_DYNAMICS,
    ISO_CONDITION_MONITORING,
    ISO_VIBRATION_CALIBRATION,
    ISO_VIBRATION_SCOPE,
)


SINGULATION_EXPERIMENT = _experiment(
    "Calibrate and test a singulation-specific electromechanical spindle-load relation on the actual SG machine.",
    "Within one SG machine, controller, blade/tool, package/material, coolant, and cutting-state regime, controlled load changes may produce a repeatable speed-conditioned current response.",
    ("verified drive semantics", "calibrated speed/current", "feed/depth/phase", "force reference", "high-rate vibration path"),
    ("speed", "feed/depth", "package/material", "blade state"),
    "Controlled approved blade/load states on the actual singulation equipment.",
    ("same current change caused by controller gain", "vibration sensor mounting change", "no-cut run"),
)


SINGULATION_CANDIDATE = ResearchCandidate(
    "singulation.spindle_current_speed_residual", "singulation", "spindle", RelationKind.MACHINE_FITTED, RelationStatus.RESEARCH_ONLY, EvidenceMaturity.LITERATURE_SUPPORTED,
    "SG-specific electromechanical spindle-load consistency relation, calibrated independently for the exact singulation machine.", "A package-singulation spindle may show current/load consistency, but its parameters and envelope must be learned only from the exact SG machine and never copied from WS-01.", "r_I_SG=I_SG-(a_SG_machine n_SG+b_SG_machine) inside an SG-only calibrated envelope",
    ("spindle_current", "spindle_speed", "blade_vibration"), ("verified drive semantics", "feed/cutting state", "blade/tool state", "package/material", "coolant/water drag", "SG-specific load evidence", "vibration bandwidth/axis"),
    (
        EvidenceClaim("disco_package_singulation_monitor", "DISCO documents DAD3660 package-singulation capability and spindle-current condition monitoring.", ("disco_dad3660",), "one commercial dicing/singulation platform", "The product page does not define SG-01 telemetry semantics or validate the proposed relation."),
        EvidenceClaim("no_shared_calibration", "Dicing mechanics and operating context are equipment-specific; the SG candidate therefore requires its own exact-machine calibration.", ("li_2026_dicing_dynamics",), "dicing mechanics", "Literature support does not make WS-01 coefficients transferable."),
    ),
    (_measurement("spindle_speed", "actual singulation spindle speed", "RPM", "actual versus command and controller path"), _measurement("spindle_current", "singulation drive current", "A", "feedback type and aggregation"), _measurement("cut_context", "feed/depth/material/phase", "state", "cycle aligned", missing=True)),
    _uncertainties("speed/current calibration", "alignment", "vibration calibration"), _discrepancies("SG mechanism", "feed/tool/package/coolant context", "controller behavior"),
    (FaultSensitivity("added singulation spindle load", ResidualDirection.POSITIVE, EvidenceMaturity.HYPOTHESIS, "OEM monitoring capability supports study, not a validated sensitivity."),),
    (SensorFailureMode("spindle_current", "positive bias", "false load residual", True),),
    (ResidualFmeaEntry("added cutting load", "current may rise", "positive", ("feed/depth/material",), "current/speed bias", False),),
    "The DAD3660 supports the research mechanism, but no SG-01 measurement semantics or physical validation exists and WS-01 calibration is forbidden.",
    ("SG-specific drive review", "feed/tool/package/coolant context", "reference load", "SG-only calibration", "specified vibration acquisition"), SINGULATION_EXPERIMENT.rejection_criteria, SINGULATION_EXPERIMENT,
    SINGULATION_EXPERIMENT.recalibration_triggers, SINGULATION_EXPERIMENT.invalidation_triggers,
    "SG-01 semantics and validation are absent; fitted parameters and calibration must remain separate and must not transfer from WS-01.", "Could provide SG-specific exact-machine load consistency after independent calibration and validation.", SINGULATION_EXPERIMENT.objective,
    (DISCO_DAD3660, DICING_DYNAMICS, ISO_CONDITION_MONITORING, ISO_VIBRATION_CALIBRATION, ISO_VIBRATION_SCOPE),
)
