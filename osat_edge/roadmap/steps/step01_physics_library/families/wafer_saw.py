"""Wafer-saw physical relation and research candidate."""

from __future__ import annotations

from typing import Mapping

import numpy as np
from sklearn.linear_model import HuberRegressor

from ..core.schema import (
    AlignedSignals,
    EvidenceClaim,
    EvidenceMaturity,
    ExperimentPlan,
    FaultSensitivity,
    MeasurementRequirement,
    MeasurementStatus,
    ParameterSource,
    ParameterSpec,
    PhysicsRelation,
    RelationKind,
    RelationStatus,
    ResearchCandidate,
    ResidualDirection,
    ResidualFmeaEntry,
    SensorFailureMode,
    UncertaintyCategory,
    UncertaintySource,
)
from ..core.evidence import (
    _discrepancies,
    _experiment,
    _measurement,
    _uncertainties,
)
from ..core.references import (
    ASME_UNCERTAINTY,
    BRAUN_PREPRINT,
    BRYNJARSDOTTIR_OHAGAN,
    DENG_REVIEW,
    DICING_DYNAMICS,
    DICING_MONITOR_PATENT,
    DISCO_DAD3660,
    DISCO_PRODUCT_LINE,
    FRANK_DING_RESIDUAL,
    ISO_CONDITION_MONITORING,
    JCGM_MONTE_CARLO,
    JCGM_UNCERTAINTY,
    JCGM_VIM,
    KENNEDY_OHAGAN,
    KHAN_REVIEW,
    MAXON_CONSTANTS,
    NASA_MODEL_HANDBOOK,
    NASA_MODEL_STANDARD,
    NIST_PHM,
    NIST_ROADMAP,
    RAUE_IDENTIFIABILITY,
    UTAC_WAFER_SAW,
)

MINIMUM_SPINDLE_FIT_SAMPLES = 20
MINIMUM_SPINDLE_SPEED_LEVELS = 6
MINIMUM_SPINDLE_SPEED_SPAN_RPM = 100.0
MINIMUM_SPINDLE_RELATIVE_SPEED_SPAN = 0.002
MINIMUM_RUNTIME_SAMPLES = 3

SLOPE = "current_speed_slope_a_per_rpm"
INTERCEPT = "current_intercept_a"
RESIDUAL_SCALE = "healthy_residual_scale_a"
SPEED_SPAN = "calibrated_speed_span_rpm"
SPEED_LOW = "calibrated_speed_low_rpm"
SPEED_HIGH = "calibrated_speed_high_rpm"


def _finite_pair(signals: AlignedSignals, first: str, second: str) -> tuple[np.ndarray, np.ndarray]:
    first_values = np.asarray(signals[first], dtype=float).reshape(-1)
    second_values = np.asarray(signals[second], dtype=float).reshape(-1)
    if first_values.shape != second_values.shape:
        return np.array([], dtype=float), np.array([], dtype=float)
    finite = np.isfinite(first_values) & np.isfinite(second_values)
    return first_values[finite], second_values[finite]


def _spindle_calibration_arrays(signals: AlignedSignals) -> tuple[np.ndarray, np.ndarray]:
    speed, current = _finite_pair(signals, "spindle_speed", "spindle_current")
    physical = (speed > 0.0) & (current >= 0.0)
    speed, current = speed[physical], current[physical]
    if len(speed) < MINIMUM_SPINDLE_FIT_SAMPLES:
        raise ValueError(f"At least {MINIMUM_SPINDLE_FIT_SAMPLES} finite physical samples are required")
    if len(np.unique(np.round(speed, decimals=6))) < MINIMUM_SPINDLE_SPEED_LEVELS:
        raise ValueError("Spindle speed excitation is insufficient: too few distinct speed levels")
    return speed, current


def _fit_current_speed(signals: AlignedSignals) -> Mapping[str, float]:
    """Robust exact-machine calibration with an explicit no-extrapolation range."""

    speed, current = _spindle_calibration_arrays(signals)
    speed_low, speed_high = (float(value) for value in np.percentile(speed, [2.5, 97.5]))
    speed_span = speed_high - speed_low
    speed_center = float(np.median(speed))
    required_span = max(MINIMUM_SPINDLE_SPEED_SPAN_RPM, MINIMUM_SPINDLE_RELATIVE_SPEED_SPAN * abs(speed_center))
    if not np.isfinite(speed_span) or speed_span < required_span:
        raise ValueError(f"Spindle speed excitation is insufficient: robust span {speed_span:.6g} RPM is below {required_span:.6g} RPM")
    scaled_speed = ((speed - speed_center) / speed_span).reshape(-1, 1)
    try:
        model = HuberRegressor(max_iter=300).fit(scaled_speed, current)
    except (FloatingPointError, ValueError) as exc:
        raise ValueError("Robust spindle calibration failed") from exc
    slope = float(np.asarray(model.coef_).reshape(-1)[0]) / speed_span
    intercept = float(model.intercept_) - slope * speed_center
    with np.errstate(over="ignore", invalid="ignore"):
        residual = current - (intercept + slope * speed)
    if not bool(np.all(np.isfinite(residual))):
        raise ValueError("Spindle calibration produced non-finite residuals")
    center = float(np.median(residual))
    mad = float(np.median(np.abs(residual - center)))
    measurement_floor = max(1e-9, 1e-6 * float(np.median(np.abs(current))))
    parameters = {
        SLOPE: slope,
        INTERCEPT: intercept,
        RESIDUAL_SCALE: max(1.4826 * mad, measurement_floor),
        SPEED_SPAN: speed_span,
        SPEED_LOW: speed_low,
        SPEED_HIGH: speed_high,
    }
    if not all(np.isfinite(value) for value in parameters.values()):
        raise ValueError("Spindle calibration produced non-finite parameters")
    return parameters


def _raw_spindle_residuals(
    signals: AlignedSignals, parameters: Mapping[str, float]
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    required = (SLOPE, INTERCEPT, RESIDUAL_SCALE, SPEED_LOW, SPEED_HIGH)
    if any(name not in parameters for name in required):
        return np.array([]), np.array([]), np.array([], dtype=bool)
    values = np.asarray([parameters[name] for name in required], dtype=float)
    if (not bool(np.all(np.isfinite(values))) or parameters[SPEED_LOW] >= parameters[SPEED_HIGH]
            or parameters[RESIDUAL_SCALE] <= 0.0):
        return np.array([]), np.array([]), np.array([], dtype=bool)
    speed, current = _finite_pair(signals, "spindle_speed", "spindle_current")
    physical = (speed > 0.0) & (current >= 0.0)
    speed, current = speed[physical], current[physical]
    inside = (speed >= parameters[SPEED_LOW]) & (speed <= parameters[SPEED_HIGH])
    with np.errstate(over="ignore", invalid="ignore"):
        expected = parameters[INTERCEPT] + parameters[SLOPE] * speed[inside]
        residual = current[inside] - expected
        # This very broad relative bound is only an overflow/adversarial-data
        # safeguard.  It is not an equipment limit or health threshold.
        numerical_limit = 1e6 * np.maximum.reduce(
            (np.ones_like(expected), np.abs(expected), np.full_like(expected, parameters[RESIDUAL_SCALE]))
        )
    finite = np.isfinite(residual) & (np.abs(residual) <= numerical_limit)
    # Retain one diagnostic slot for every in-domain candidate. Runtime callers
    # filter these sentinels, while offline diagnostics can report rejection.
    diagnostic_residual = np.where(finite, residual, np.nan)
    return diagnostic_residual, speed[inside], ~inside


def _current_speed_residual(signals: AlignedSignals, parameters: Mapping[str, float]) -> Mapping[str, float]:
    residual, _, _ = _raw_spindle_residuals(signals, parameters)
    finite = residual[np.isfinite(residual)]
    if len(finite) < MINIMUM_RUNTIME_SAMPLES:
        return {}
    return {"spindle.electromechanical_load_residual_a.median": float(np.median(finite))}

SPINDLE_MEASUREMENTS = (
    MeasurementRequirement(
        "spindle_speed", "actual spindle rotational speed", "RPM", "controller or independently verified tachometer speed", "wafer-saw spindle shaft/controller feedback path", "actual speed, not command; averaging and sign documented", "positive for normal cutting rotation", "timestamp aligned to current within characterized lag", "sufficient for speed changes in the low-rate residual", "compare against a traceable tachometer over the calibration range", "traceability chain not yet established", "resolve <=10 RPM or justify another value", MeasurementStatus.AVAILABLE_BUT_SEMANTICS_UNVERIFIED,
        notes="machines.py supplies only a name and unit."),
    MeasurementRequirement(
        "spindle_current", "spindle drive current used by the electromechanical controller", "A", "controller feedback with documented phase/RMS/DC-bus semantics", "wafer-saw spindle drive feedback path", "actual feedback and aggregation basis, not current limit or command", "positive magnitude for motoring load", "timestamp aligned to actual speed; controller filtering delay characterized", "preserve load variations relevant to the chosen window", "compare with calibrated current measurement at controlled operating points", "traceability chain not yet established", "resolve <=0.01 A or justify another value", MeasurementStatus.AVAILABLE_BUT_SEMANTICS_UNVERIFIED,
        notes="Current is a proxy for load only under bounded drive/control assumptions."),
)

SPINDLE_PARAMETERS = (
    ParameterSpec(SLOPE, "healthy exact-machine change in reported current per RPM", "A/RPM", ParameterSource.MACHINE_FITTED, "only within calibrated speed and unchanged controller/configuration", ">=20 healthy samples, >=6 speed levels, and robust speed span", "slope and intercept can confound loss, control, thermal, and unrecorded process load", ("spindle/drive replacement", "controller firmware or gain change", "material/blade/process regime change")),
    ParameterSpec(INTERCEPT, "fitted healthy current at zero-speed extrapolation; numerical intercept, not physical idle current", "A", ParameterSource.MACHINE_FITTED, "used only with the calibrated speed range", "same excitation as slope", "correlated with slope and physically uninterpretable at zero speed", ("same triggers as slope",)),
    ParameterSpec(RESIDUAL_SCALE, "robust spread of healthy calibration residuals", "A", ParameterSource.MACHINE_FITTED, "calibration population and operating regime", "healthy repeats spanning nuisance conditions", "mixes measurement noise, process variability, and model discrepancy; not a calibrated probability scale", ("sensor recalibration", "sustained healthy-distribution change")),
    ParameterSpec(SPEED_SPAN, "robust 2.5th-to-97.5th percentile speed span", "RPM", ParameterSource.MACHINE_FITTED, "calibration dataset", "intentional multi-level speed excitation", "documents coverage rather than a physical coefficient", ("new calibration dataset",)),
    ParameterSpec(SPEED_LOW, "lower no-extrapolation boundary", "RPM", ParameterSource.MACHINE_FITTED, "inclusive lower boundary", "healthy data at the low operating range", "quantile boundary excludes sparse extremes", ("approved operating range expansion",)),
    ParameterSpec(SPEED_HIGH, "upper no-extrapolation boundary", "RPM", ParameterSource.MACHINE_FITTED, "inclusive upper boundary", "healthy data at the high operating range", "quantile boundary excludes sparse extremes", ("approved operating range expansion",)),
)

SPINDLE_EXPERIMENT = ExperimentPlan(
    objective="Determine whether a speed-conditioned spindle-current residual is repeatable and sensitive to controlled wafer-saw spindle/cutting degradation.",
    hypothesis="Within a fixed machine, controller, blade, material, and recipe regime, added mechanical cutting/load demand increases reported current relative to the healthy speed-conditioned baseline.",
    equipment_and_specimen=("one instrumented wafer dicing saw", "approved surrogate wafers/coupons", "documented blade lots and condition states"),
    required_instrumentation=("independent tachometer", "calibrated current reference", "feed/depth/phase state", "optional force and high-rate vibration references"),
    controlled_factors=("spindle speed", "feed rate", "cut depth", "blade type/condition", "coolant state", "material"),
    nuisance_factors=("temperature", "controller filtering", "run order", "blade dressing", "fixture and wafer variation"),
    baseline_condition="OEM-acceptable machine and blade verified by maintenance/metrology review.",
    fault_or_perturbation="Safe staged load changes and approved seeded blade wear/imbalance conditions; no uncontrolled equipment damage.",
    negative_controls=("speed change with load held constant", "current-sensor offset injection", "no-cut spindle run", "repeat after thermal equilibration"),
    design_of_experiments="Randomized blocked factorial across speed, feed, depth, material, and condition with chronological repeats reserved for drift assessment.",
    calibration_data="Early healthy blocks only; fit exact-machine coefficients and freeze the envelope.",
    validation_data="Later non-overlapping healthy and seeded-condition blocks, with machine/time split recorded.",
    acceptance_criteria=("stable coefficients across healthy chronological blocks", "low residual dependence on speed/feed/depth within scope", "predeclared directional response under target perturbation", "sensor-offset negative control is distinguishable"),
    rejection_criteria=("response reverses or disappears on held-out blocks", "conditioning dependence remains material", "sensor faults mimic degradation without detection", "false response to negative controls"),
    recalibration_triggers=("drive/spindle replacement", "controller or sensor change", "approved regime expansion"),
    invalidation_triggers=("current semantics differ from documented basis", "required context cannot be observed", "held-out response is not repeatable"),
    safety_and_approval_notes=("OEM/site approval required", "observe-only research output", "use approved specimens and perturbations", "no autonomous machine action"),
    reference_instrument=("independent traceable tachometer", "calibrated current reference", "external force/torque or validated controller-load reference if feasible"),
    swept_variables=("spindle speed", "feed rate", "cut depth", "known blade/load state"),
    sample_repetition_strategy="Multiple cuts per condition, chronological repeats on multiple days, and later reproduction on another same-family machine; final counts set by an approved power/precision study.",
    sensor_fault_challenge=("offline current bias/gain/drift/dropout/clipping", "speed bias/gain/dropout", "controlled timestamp offset"),
    reproducibility_requirement="Repeat across runs/days, then on held-out same-family machines before any multi-machine claim.",
    data_to_archive=("raw reference and equipment telemetry", "timestamps and alignment record", "machine/configuration identity", "calibration certificates", "DOE/run order", "frozen parameters/envelope", "maintenance and perturbation records"),
    validation_stages=("A measurement-system validation", "B healthy calibration", "C independent healthy validation", "D controlled perturbation challenge", "E confounder challenge", "F sensor-fault challenge", "G repeatability across runs/days", "H reproducibility across machines", "I prospective plant validation"),
)


SPINDLE_RELATION = PhysicsRelation(
    relation_id="spindle.current_speed_residual",
    machine_families=frozenset({"wafer_saw"}),
    subsystem="spindle",
    required_channels=("spindle_speed", "spindle_current"),
    expected_units=(("spindle_speed", "RPM"), ("spindle_current", "A")),
    compute=_current_speed_residual,
    fit=_fit_current_speed,
    description="Exact-machine robust electromechanical spindle-load consistency residual of reported current conditioned on actual speed.",
    equation="r_I = I_reported - (a_machine n_actual + b_machine), evaluated only inside the calibrated speed envelope",
    assumptions=("same exact machine and controller configuration", "healthy calibration data", "reported current meaning is stable", "operating conditions are represented by calibration", "no extrapolation"),
    kind=RelationKind.MACHINE_FITTED,
    status=RelationStatus.RUNTIME_RESEARCH,
    evidence_maturity=EvidenceMaturity.LITERATURE_SUPPORTED,
    output_name="spindle.electromechanical_load_residual_a.median",
    output_unit="A",
    mechanism="Under bounded drive/control conditions, a change in spindle electromechanical load may change reported motor current; the fitted relation removes first-order speed dependence.",
    validity_conditions=("wafer-saw family only", "exact machine used for calibration", "speed inside robust calibration limits", "same drive semantics/configuration", "sufficient aligned finite samples"),
    invalidity_conditions=("another family or machine", "outside calibrated speed", "controller/sensor change", "unknown commanded-versus-actual semantics", "unrepresented feed/cutting/material regime"),
    confounders=("feed/cutting state", "blade/tool state", "material", "coolant/water drag", "drive efficiency/control", "temperature", "acceleration/transients"),
    calibration_requirements=("at least 20 healthy samples", "at least six speed levels", "robust speed span", "chronological block stability review", "separate held-out validation"),
    parameter_specs=SPINDLE_PARAMETERS,
    evidence_claims=(
        EvidenceClaim("spindle_current_condition_monitor", "DISCO explicitly lists spindle-current monitoring as a DAD3660 condition-monitor function.", ("disco_dad3660",), "DISCO dicing/singulation equipment capability", "The OEM page does not define current semantics or validate this equation."),
        EvidenceClaim("spindle_current_as_load_proxy", "A dicing-saw patent uses spindle feedback current as an implementation-specific load signal while speed is controlled.", ("dicing_monitor_patent",), "dicing-saw implementation", "Patent evidence is not validation or fault specificity."),
        EvidenceClaim("motor_current_torque", "Motor torque can be proportional to current under documented motor/controller assumptions.", ("maxon_motor_constants",), "motor engineering", "Unknown controller current semantics, losses, and control loops limit transfer."),
        EvidenceClaim("dicing_multiphysics", "Wafer-dicing force and vibration depend on coupled fracture/process dynamics.", ("li_2026_dicing_dynamics",), "wafer dicing research", "Motivates confounder control; does not validate this linear relation."),
    ),
    measurement_requirements=SPINDLE_MEASUREMENTS,
    measurement_uncertainty_sources=(
        UncertaintySource("speed calibration and quantization", UncertaintyCategory.MEASUREMENT, "Unknown speed accuracy/resolution and aggregation."),
        UncertaintySource("current calibration and filtering", UncertaintyCategory.MEASUREMENT, "Unknown scaling, RMS/phase meaning, bandwidth, and offsets."),
        UncertaintySource("timestamp/drive lag", UncertaintyCategory.ALIGNMENT, "Speed and current may represent different filtered time intervals."),
    ),
    model_discrepancy_sources=(
        UncertaintySource("omitted cutting state", UncertaintyCategory.MODEL_DISCREPANCY, "Feed/cutting state, blade/tool state, material, coolant/water drag, acceleration, and control behavior are omitted."),
        UncertaintySource("linear form", UncertaintyCategory.MODEL_DISCREPANCY, "Healthy current-speed behavior may be nonlinear or regime-dependent."),
    ),
    target_fault_sensitivities=(
        FaultSensitivity("added mechanical/cutting load", ResidualDirection.POSITIVE, EvidenceMaturity.LITERATURE_SUPPORTED, "Expected to require more reported motor current under stable speed-control semantics."),
        FaultSensitivity("blade wear or clogging", ResidualDirection.POSITIVE, EvidenceMaturity.HYPOTHESIS, "Could increase load, but direct repeatable station evidence is absent."),
    ),
    cross_sensitivities=("feed/cutting-state change", "blade/tool-state change", "material change", "coolant/water-drag change", "acceleration", "drive/controller thermal state"),
    sensor_failure_modes=(
        SensorFailureMode("spindle_current", "positive offset or scale drift", "positive residual", True),
        SensorFailureMode("spindle_current", "gain error", "speed-dependent residual bias", True),
        SensorFailureMode("spindle_current", "clipping", "suppressed or distorted residual", True),
        SensorFailureMode("spindle_current", "dropout or non-finite value", "sample excluded; no output if insufficient data", False),
        SensorFailureMode("spindle_current", "noise increase", "larger residual spread and unstable median in short windows", True),
        SensorFailureMode("spindle_speed", "negative bias or lag", "apparent positive residual depending on slope", True),
        SensorFailureMode("spindle_speed", "gain error or quantization", "speed-dependent residual structure", True),
        SensorFailureMode("spindle_speed", "timestamp misalignment", "transient residual correlated with acceleration", True),
        SensorFailureMode("either", "stuck/stale value", "suppressed or spurious residual", True),
    ),
    residual_fmea=(
        ResidualFmeaEntry("increased electromechanical spindle load", "current rises for comparable speed/context", "positive", ("feed/cutting state", "blade/tool state", "material", "coolant/water drag", "acceleration"), "current positive bias or speed negative bias", False),
        ResidualFmeaEntry("drive efficiency/control change", "current-speed mapping shifts", "either direction", ("temperature", "firmware/gain"), "current scale drift", False),
    ),
    falsification_tests=("held-out residual still depends on speed/feed/depth", "controlled load does not produce repeatable expected direction", "sensor offset is indistinguishable from target degradation", "block parameters are unstable"),
    experiment_plan=SPINDLE_EXPERIMENT,
    recalibration_triggers=SPINDLE_EXPERIMENT.recalibration_triggers,
    invalidation_triggers=SPINDLE_EXPERIMENT.invalidation_triggers,
    instrumentation_gaps=("verified current semantics", "traceable speed/current calibration", "feed/depth/phase context", "reference load/force for validation"),
    references=(DISCO_DAD3660, DICING_MONITOR_PATENT, DICING_DYNAMICS, DISCO_PRODUCT_LINE, UTAC_WAFER_SAW, MAXON_CONSTANTS, ISO_CONDITION_MONITORING, JCGM_UNCERTAINTY, JCGM_MONTE_CARLO, NASA_MODEL_STANDARD, NASA_MODEL_HANDBOOK, ASME_UNCERTAINTY, RAUE_IDENTIFIABILITY, BRYNJARSDOTTIR_OHAGAN, FRANK_DING_RESIDUAL),
    validation_evidence=(),
    major_blocker="No bench or machine study has established telemetry semantics, confounder robustness, target sensitivity, or sensor-fault discrimination.",
    next_experiment=SPINDLE_EXPERIMENT.objective,
)


COOLANT_EXPERIMENT = _experiment(
    "Establish a pressure-drop/flow residual across one named coolant element.",
    "For fixed geometry, fluid, temperature, valve, and pump state, differential pressure follows the selected regime-dependent flow law.",
    ("differential-pressure taps", "calibrated flow and temperature", "valve/pump state", "documented branch geometry"),
    ("flow", "temperature", "valve state", "known restriction"),
    "Insert approved calibrated restrictions without risking cooling loss.",
    ("supply-pressure change with branch resistance fixed", "pressure-sensor bias", "temperature/viscosity change"),
)


WAFER_SAW_CANDIDATE = ResearchCandidate(
    "wafer_saw.coolant_hydraulic_resistance", "wafer_saw", "cooling", RelationKind.SEMI_EMPIRICAL, RelationStatus.RESEARCH_ONLY, EvidenceMaturity.HYPOTHESIS,
    "Pressure-drop/flow residual across one defined coolant element.", "Flow through known geometry creates regime- and property-dependent head loss.", "Δp = f(Re, roughness)(L/D)ρv²/2",
    ("coolant_pressure", "coolant_flow", "coolant_temperature"), ("differential pressure", "sensor locations", "geometry", "fluid properties", "pump/valve state"),
    (EvidenceClaim("hydraulic_balance", "A physically meaningful restriction relation needs differential pressure, geometry, flow regime, and fluid properties.", (), "fluid mechanics", "No equipment-specific source currently supports the channel semantics."),),
    (_measurement("coolant_pressure", "differential pressure across named element", "kPa", "upstream/downstream location and gauge/reference"), _measurement("coolant_flow", "branch volumetric flow", "L/min", "named branch and direction"), _measurement("valve_state", "valve/pump operating state", "state", "synchronized categorical state", missing=True)),
    _uncertainties("pressure calibration", "flow calibration", "temperature"), _discrepancies("unknown geometry", "viscosity/regime", "pump/valve dynamics"),
    (FaultSensitivity("restriction/clogging", ResidualDirection.POSITIVE, EvidenceMaturity.HYPOTHESIS, "Restriction may increase pressure drop at a fixed flow."),),
    (SensorFailureMode("coolant_pressure", "offset", "shifted residual", True), SensorFailureMode("coolant_flow", "scale drift", "condition-dependent residual", True)),
    (ResidualFmeaEntry("restriction", "higher Δp for flow", "positive", ("viscosity", "valve state"), "pressure/flow bias", False),),
    "The single pressure name does not establish supply, gauge, or differential pressure.",
    ("differential-pressure taps", "branch geometry", "valve/pump state"), COOLANT_EXPERIMENT.rejection_criteria, COOLANT_EXPERIMENT,
    COOLANT_EXPERIMENT.recalibration_triggers, COOLANT_EXPERIMENT.invalidation_triggers,
    "No defined pressure drop across a named element.", "Could detect coolant restriction after measurement semantics are established.", COOLANT_EXPERIMENT.objective,
    (ISO_CONDITION_MONITORING, JCGM_VIM),
)
