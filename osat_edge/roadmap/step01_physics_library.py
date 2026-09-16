"""Step 01: reviewed engineering claims that may produce runtime evidence.

A relation is executable only after its mechanism, measurement semantics,
operating limits, uncertainty, and falsification path have been made explicit.
Plausible ideas that do not pass that gate remain visible as research records;
they are deliberately unavailable to Step 03.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Mapping

import numpy as np
from sklearn.linear_model import HuberRegressor


AlignedSignals = Mapping[str, np.ndarray]
RelationCompute = Callable[[AlignedSignals, Mapping[str, float]], Mapping[str, float]]
RelationFit = Callable[[AlignedSignals], Mapping[str, float]]


class RelationKind(str, Enum):
    """How much of a relation comes from physics versus machine data."""

    FIRST_PRINCIPLES = "FIRST_PRINCIPLES"
    CONSTITUTIVE = "CONSTITUTIVE"
    SEMI_EMPIRICAL = "SEMI_EMPIRICAL"
    MACHINE_FITTED = "MACHINE_FITTED"
    DIAGNOSTIC_PROXY = "DIAGNOSTIC_PROXY"


class RelationStatus(str, Enum):
    """Whether a reviewed claim may influence the runtime feature path."""

    RUNTIME = "RUNTIME"
    RESEARCH_ONLY = "RESEARCH_ONLY"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class ResearchReference:
    """Short, auditable provenance for one engineering claim."""

    key: str
    citation: str
    identifier: str
    source_type: str
    supports: str


@dataclass(frozen=True)
class PhysicsRelation:
    """An executable claim plus the evidence needed to delimit its use."""

    # These fields are the stable Step-01 interface consumed by Step 03.
    relation_id: str
    machine_families: frozenset[str]
    subsystem: str
    required_channels: tuple[str, ...]
    expected_units: tuple[tuple[str, str], ...]
    compute: RelationCompute
    fit: RelationFit | None
    description: str
    equation: str
    assumptions: tuple[str, ...]

    # Research metadata explains why this claim passed the activation gate.
    kind: RelationKind
    status: RelationStatus
    output_name: str
    output_unit: str
    mechanism: str
    validity_conditions: tuple[str, ...]
    invalidity_conditions: tuple[str, ...]
    confounders: tuple[str, ...]
    calibration_requirements: tuple[str, ...]
    parameter_identifiability_notes: tuple[str, ...]
    uncertainty_sources: tuple[str, ...]
    expected_fault_sensitivity: tuple[str, ...]
    cross_sensitivities: tuple[str, ...]
    falsification_tests: tuple[str, ...]
    instrumentation_gaps: tuple[str, ...]
    references: tuple[ResearchReference, ...]


@dataclass(frozen=True)
class ResearchCandidate:
    """A considered relation that is not executable with current evidence."""

    candidate_id: str
    family: str
    subsystem: str
    kind: RelationKind
    status: RelationStatus
    description: str
    proposed_mechanism: str
    proposed_equation: str
    existing_channels: tuple[str, ...]
    missing_variables: tuple[str, ...]
    decision_reason: str
    additional_instrumentation: tuple[str, ...]
    uncertainty_sources: tuple[str, ...]
    falsification_tests: tuple[str, ...]
    references: tuple[ResearchReference, ...]


# Method sources guide the review process; they do not make this project
# compliant with the standards or validate an equipment-specific relation.
ISO_DIAGNOSTICS = ResearchReference(
    key="iso_13379_1_2025",
    citation=(
        "ISO, Condition monitoring and diagnostics of machine systems — "
        "Data interpretation and diagnostics techniques — Part 1: General "
        "guidelines, 2nd ed., 2025."
    ),
    identifier="ISO 13379-1:2025",
    source_type="international standard",
    supports="Application-specific diagnostic selection and explicit operating context.",
)

JCGM_UNCERTAINTY = ResearchReference(
    key="jcgm_100_2008",
    citation=(
        "JCGM, Evaluation of measurement data — Guide to the expression of "
        "uncertainty in measurement, 2008."
    ),
    identifier="10.59161/JCGM100-2008E",
    source_type="metrology guide",
    supports="Identification and propagation of measurement uncertainty sources.",
)

JCGM_MONTE_CARLO = ResearchReference(
    key="jcgm_101_2008",
    citation=(
        "JCGM, Supplement 1 to the GUM — Propagation of distributions using "
        "a Monte Carlo method, 2008."
    ),
    identifier="10.59161/JCGM101-2008",
    source_type="metrology guide",
    supports="Distribution propagation when justified input distributions exist.",
)

ASME_UNCERTAINTY = ResearchReference(
    key="asme_vvuq_10_2_2021",
    citation=(
        "ASME, The Role of Uncertainty Quantification in Verification and "
        "Validation of Computational Solid Mechanics Models, 2021."
    ),
    identifier="ASME VVUQ 10.2-2021",
    source_type="verification and validation standard",
    supports="Separating model-form, input, numerical, and validation uncertainty.",
)

NASA_MODEL_CREDIBILITY = ResearchReference(
    key="nasa_hdbk_7009b",
    citation=(
        "NASA, NASA Handbook for Models and Simulations: An Implementation "
        "Guide for NASA-STD-7009B, 2026."
    ),
    identifier="NASA-HDBK-7009B",
    source_type="government engineering handbook",
    supports="Stating intended use, assumptions, permissible use, and credibility limits.",
)

DENG_PIML_REVIEW = ResearchReference(
    key="deng_2023_piml_phm",
    citation=(
        "W. Deng, K. T. P. Nguyen, K. Medjaher, C. Gogu, and J. Morio, "
        "Physics-informed machine learning in prognostics and health "
        "management: State of the art and challenges, Applied Mathematical "
        "Modelling 124 (2023) 325–352."
    ),
    identifier="10.1016/j.apm.2023.07.011",
    source_type="peer-reviewed review",
    supports="Taxonomy and limitations of physics-informed knowledge in PHM.",
)

LI_RUL_REVIEW = ResearchReference(
    key="li_2024_physics_rul",
    citation=(
        "H. Li, Z. Zhang, T. Li, and X. Si, A review on physics-informed "
        "data-driven remaining useful life prediction: Challenges and "
        "opportunities, Mechanical Systems and Signal Processing 209 (2024) "
        "111120."
    ),
    identifier="10.1016/j.ymssp.2024.111120",
    source_type="peer-reviewed review",
    supports="Limits, opportunities, and categories of physics-informed RUL methods.",
)

BRAUN_PIML_REVIEW = ResearchReference(
    key="braun_2026_piml_phm",
    citation=(
        "C. Braun, J. Raible, and M. F. Huber, Physics-Informed Machine "
        "Learning in Prognostics and Health Management: A Systematic "
        "Literature Review, 2026."
    ),
    identifier="arXiv:2608.10047",
    source_type="systematic review preprint",
    supports="Evidence gaps, asset concentration, and transferability limits in PIML-PHM.",
)

DICING_MONITOR_PATENT = ResearchReference(
    key="weisshaus_licht_dicing_monitor",
    citation=(
        "I. Weisshaus and O. Y. Licht, Monitoring system for dicing saws, "
        "United States patent, 2001."
    ),
    identifier="US6168500B1",
    source_type="semiconductor-equipment patent",
    supports=(
        "A dicing-saw implementation used spindle feedback current as a load "
        "signal while maintaining blade speed; it does not establish a universal force model."
    ),
)

DICING_DYNAMICS = ResearchReference(
    key="li_2026_dicing_dynamics",
    citation=(
        "J. Li, D. Li, J. Lin, C. Zhang, and J. Cheng, Vibration–force "
        "coupled dynamics and fracture evolution in wafer dicing, "
        "International Journal of Mechanical Sciences 319 (2026) 111581."
    ),
    identifier="10.1016/j.ijmecsci.2026.111581",
    source_type="peer-reviewed primary research",
    supports=(
        "Dicing force is coupled to vibration, fracture, and clogging dynamics; "
        "a current-speed residual omits important process variables."
    ),
)

MOTOR_TORQUE_CONSTANT = ResearchReference(
    key="ti_u_105_motor_constants",
    citation=(
        "Unitrode/Texas Instruments, How to Measure Kt and Kv Without "
        "Measuring Torque or Angular Velocity, Application Note U-105."
    ),
    identifier="TI/Unitrode Application Note U-105",
    source_type="manufacturer application note",
    supports="Motor torque constant relates shaft torque to current under stated motor assumptions.",
)

NI_SOCKET_GUIDANCE = ResearchReference(
    key="ni_smu_ic_sockets",
    citation=(
        "National Instruments, Best Practice for Using NI SMUs to Test IC in "
        "Sockets, updated 2025."
    ),
    identifier="NI supplemental document: SMU IC socket best practice",
    source_type="semiconductor-test application note",
    supports="Spring-pin wear, debris, and intermittent/open socket contacts affect connectivity.",
)

KEYSIGHT_LOW_RESISTANCE = ResearchReference(
    key="keysight_low_resistance",
    citation=(
        "Keysight Technologies, Precise Low Resistance Measurements Using "
        "the B2961B and 34420A, application note."
    ),
    identifier="Keysight 3120-1555",
    source_type="measurement application note",
    supports=(
        "Low-resistance V/I measurement needs adequate current, synchronized "
        "measurement, offset control, and preferably four-wire sensing."
    ),
)

NIST_RESISTANCE = ResearchReference(
    key="nist_circular_470",
    citation=(
        "National Bureau of Standards, Precision Resistors and Their "
        "Measurement, NBS Circular 470, 1958."
    ),
    identifier="NBS Circular 470",
    source_type="government metrology reference",
    supports="Ohm's law and the dependence of precision resistance measurements on conditions.",
)

USACE_HYDRAULICS = ResearchReference(
    key="usace_em_1110_2_1602",
    citation=(
        "U.S. Army Corps of Engineers, Hydraulic Design of Reservoir Outlet "
        "Works, Engineer Manual EM 1110-2-1602, 1980."
    ),
    identifier="EM 1110-2-1602",
    source_type="government engineering manual",
    supports=(
        "Darcy–Weisbach head loss requires a defined pressure/head drop, "
        "geometry, velocity, and a regime-dependent friction factor."
    ),
)

WIRE_BOND_PIEZO = ResearchReference(
    key="or_1998_wire_bond",
    citation=(
        "S. W. Or, H. L. W. Chan, V. C. Lo, and C. W. Yuen, Ultrasonic "
        "wire-bond quality monitoring using piezoelectric sensor, Sensors and "
        "Actuators A 65(1) (1998) 69–75."
    ),
    identifier="10.1016/S0924-4247(97)01638-5",
    source_type="peer-reviewed primary research",
    supports="A dedicated PZT sensor measured vibration amplitude, timing, and harmonics.",
)

WIRE_BOND_ELECTRICAL = ResearchReference(
    key="feng_2011_wire_bond",
    citation=(
        "W. Feng, Q. Meng, Y. Xie, and H. Fan, Wire bonding quality monitoring "
        "via refining process of electrical signal from ultrasonic generator, "
        "Mechanical Systems and Signal Processing 25(3) (2011) 884–900."
    ),
    identifier="10.1016/j.ymssp.2010.09.010",
    source_type="peer-reviewed primary research",
    supports="Electrical monitoring acquired both generator voltage and current and analyzed harmonics/phases.",
)

WIRE_BOND_IMPEDANCE = ResearchReference(
    key="zhang_2004_wire_bond_impedance",
    citation=(
        "D. Zhang, S. Ling, S. Yi, and S. W. Foo, Improved monitoring of "
        "ultrasonic wire bonding via input electrical impedance, 6th "
        "Electronics Packaging Technology Conference, 2004."
    ),
    identifier="10.1109/EPTC.2004.1396634",
    source_type="peer-reviewed conference paper",
    supports="Input-impedance monitoring uses real and imaginary impedance waveforms.",
)

LASER_OUTPUT_MODEL = ResearchReference(
    key="borras_2019_laser_output",
    citation=(
        "R. Borràs, J. del Río Fernández, C. Oriach, and J. Juliachs, Laser "
        "diodes optical output power model, Measurement 133 (2019) 56–67."
    ),
    identifier="10.1016/j.measurement.2018.10.007",
    source_type="peer-reviewed primary research",
    supports="Laser-diode optical output depends on current, threshold, slope efficiency, and temperature.",
)

MOLDING_IN_SITU = ResearchReference(
    key="kahle_2016_transfer_molding",
    citation=(
        "R. Kahle, T. Braun, J. Bauer, K.-F. Becker, M. Schneider-Ramelow, "
        "and K.-D. Lang, In-situ measuring module for transfer molding "
        "process monitoring, IMAPS Proceedings, 2016."
    ),
    identifier="10.4071/isom-2016-THA43",
    source_type="peer-reviewed semiconductor-packaging research",
    supports="Transfer-mold monitoring uses cavity pressure, melt/tool temperature, and cure-related dielectric data.",
)

MOLDING_PROCESS = ResearchReference(
    key="kaya_2019_transfer_molding",
    citation=(
        "B. Kaya, J.-M. Kaiser, K.-F. Becker, T. Braun, and K.-D. Lang, "
        "Process optimization and implementation of online monitoring process "
        "in transfer molding for electronic packaging, Journal of "
        "Microelectronics and Electronic Packaging, 2019."
    ),
    identifier="10.4071/IMAPS.954402",
    source_type="peer-reviewed semiconductor-packaging research",
    supports="Transfer speed, temperature, pressure, preheat, material condition, and cure behavior interact.",
)

LEYBOLD_LEAK_RATE = ResearchReference(
    key="leybold_pressure_rise",
    citation=(
        "Leybold, Fundamentals of Leak Detection: pressure rise and pressure "
        "drop tests, technical reference."
    ),
    identifier="Leybold Fundamentals of Leak Detection",
    source_type="vacuum-equipment technical reference",
    supports="Leak rate from pressure rise requires isolated volume and pressure change over time.",
)


RESEARCH_REFERENCES: tuple[ResearchReference, ...] = (
    ISO_DIAGNOSTICS,
    JCGM_UNCERTAINTY,
    JCGM_MONTE_CARLO,
    ASME_UNCERTAINTY,
    NASA_MODEL_CREDIBILITY,
    DENG_PIML_REVIEW,
    LI_RUL_REVIEW,
    BRAUN_PIML_REVIEW,
    DICING_MONITOR_PATENT,
    DICING_DYNAMICS,
    MOTOR_TORQUE_CONSTANT,
    NI_SOCKET_GUIDANCE,
    KEYSIGHT_LOW_RESISTANCE,
    NIST_RESISTANCE,
    USACE_HYDRAULICS,
    WIRE_BOND_PIEZO,
    WIRE_BOND_ELECTRICAL,
    WIRE_BOND_IMPEDANCE,
    LASER_OUTPUT_MODEL,
    MOLDING_IN_SITU,
    MOLDING_PROCESS,
    LEYBOLD_LEAK_RATE,
)


MINIMUM_SPINDLE_FIT_SAMPLES = 20
MINIMUM_SPINDLE_SPEED_SPAN_RPM = 100.0
MINIMUM_SPINDLE_RELATIVE_SPEED_SPAN = 0.002
MINIMUM_CONTACT_CURRENT_A = 1e-6
CONTACT_CURRENT_SCALE_FRACTION = 1e-3
MINIMUM_RUNTIME_SAMPLES = 3


def _finite_pair(
    signals: AlignedSignals, first: str, second: str
) -> tuple[np.ndarray, np.ndarray]:
    first_values = np.asarray(signals[first], dtype=float).reshape(-1)
    second_values = np.asarray(signals[second], dtype=float).reshape(-1)
    if first_values.shape != second_values.shape:
        return np.array([], dtype=float), np.array([], dtype=float)
    finite = np.isfinite(first_values) & np.isfinite(second_values)
    return first_values[finite], second_values[finite]


def _fit_current_speed(signals: AlignedSignals) -> Mapping[str, float]:
    """Fit an exact-machine healthy current/speed consistency model."""

    speed, current = _finite_pair(signals, "spindle_speed", "spindle_current")
    physical = (speed > 0.0) & (current >= 0.0)
    speed = speed[physical]
    current = current[physical]
    if len(speed) < MINIMUM_SPINDLE_FIT_SAMPLES:
        raise ValueError(
            f"At least {MINIMUM_SPINDLE_FIT_SAMPLES} finite positive-speed "
            "samples are required"
        )

    # A robust 5th-to-95th percentile span prevents one speed outlier from
    # making an otherwise constant-speed calibration appear identifiable.
    speed_span = float(np.percentile(speed, 95.0) - np.percentile(speed, 5.0))
    speed_center = float(np.median(speed))
    required_span = max(
        MINIMUM_SPINDLE_SPEED_SPAN_RPM,
        MINIMUM_SPINDLE_RELATIVE_SPEED_SPAN * abs(speed_center),
    )
    if not np.isfinite(speed_span) or speed_span < required_span:
        raise ValueError(
            "Spindle speed excitation is insufficient: robust span "
            f"{speed_span:.6g} RPM is below {required_span:.6g} RPM"
        )

    # Center and scale for numerical conditioning. Returned slope is converted
    # back to A/RPM so the fitted parameters keep physical units.
    scaled_speed = ((speed - speed_center) / speed_span).reshape(-1, 1)
    try:
        model = HuberRegressor(max_iter=200).fit(scaled_speed, current)
    except (FloatingPointError, ValueError) as exc:
        raise ValueError("Robust spindle calibration failed") from exc
    scaled_slope = float(np.asarray(model.coef_).reshape(-1)[0])
    centered_intercept = float(np.asarray(model.intercept_).reshape(-1)[0])
    slope = scaled_slope / speed_span
    intercept = centered_intercept - slope * speed_center

    with np.errstate(over="ignore", invalid="ignore"):
        residual = current - (intercept + slope * speed)
    finite_residual = residual[np.isfinite(residual)]
    if len(finite_residual) != len(residual):
        raise ValueError("Spindle calibration produced non-finite residuals")
    residual_center = float(np.median(finite_residual))
    residual_mad = float(np.median(np.abs(finite_residual - residual_center)))
    measurement_floor = max(1e-9, 1e-6 * float(np.median(np.abs(current))))
    residual_scale = max(1.4826 * residual_mad, measurement_floor)

    fitted = {
        "slope": slope,
        "intercept": intercept,
        "residual_scale": residual_scale,
        "speed_span_rpm": speed_span,
    }
    if not all(np.isfinite(value) for value in fitted.values()):
        raise ValueError("Spindle calibration produced non-finite parameters")
    return fitted


def _current_speed_residual(
    signals: AlignedSignals, parameters: Mapping[str, float]
) -> Mapping[str, float]:
    if "slope" not in parameters or "intercept" not in parameters:
        return {}
    slope = float(parameters["slope"])
    intercept = float(parameters["intercept"])
    if not np.isfinite(slope) or not np.isfinite(intercept):
        return {}

    speed, current = _finite_pair(signals, "spindle_speed", "spindle_current")
    physical = (speed > 0.0) & (current >= 0.0)
    speed = speed[physical]
    current = current[physical]
    if len(speed) < MINIMUM_RUNTIME_SAMPLES:
        return {}
    with np.errstate(over="ignore", invalid="ignore"):
        residual = current - (intercept + slope * speed)
    residual = residual[np.isfinite(residual)]
    if len(residual) < MINIMUM_RUNTIME_SAMPLES:
        return {}
    return {"spindle.electromechanical_load_residual_a.median": float(np.median(residual))}


def _contact_resistance(
    signals: AlignedSignals, _: Mapping[str, float]
) -> Mapping[str, float]:
    """Return median aligned V/I in mΩ; 1 mV / 1 A equals 1 mΩ."""

    voltage_mv, current_a = _finite_pair(
        signals, "contact_voltage_drop", "site_current"
    )
    if len(current_a) < MINIMUM_RUNTIME_SAMPLES:
        return {}

    current_scale = float(np.percentile(np.abs(current_a), 90.0))
    if not np.isfinite(current_scale):
        return {}
    # This is a numerical/measurement guard, not a production limit. It rejects
    # division where current is absolutely tiny or tiny relative to the window.
    current_floor = max(
        MINIMUM_CONTACT_CURRENT_A,
        CONTACT_CURRENT_SCALE_FRACTION * current_scale,
    )
    usable = np.abs(current_a) > current_floor
    with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
        resistance_mohm = voltage_mv[usable] / current_a[usable]
    # Matching voltage/current polarity gives positive passive resistance.
    resistance_mohm = resistance_mohm[
        np.isfinite(resistance_mohm) & (resistance_mohm >= 0.0)
    ]
    required = max(MINIMUM_RUNTIME_SAMPLES, int(np.ceil(0.5 * len(current_a))))
    if len(resistance_mohm) < required:
        return {}
    return {"contacts.contact_resistance_mohm.median": float(np.median(resistance_mohm))}


PHYSICS_RELATIONS: tuple[PhysicsRelation, ...] = (
    PhysicsRelation(
        relation_id="spindle.current_speed_residual",
        machine_families=frozenset({"wafer_saw", "singulation"}),
        subsystem="spindle",
        required_channels=("spindle_current", "spindle_speed"),
        expected_units=(("spindle_current", "A"), ("spindle_speed", "RPM")),
        compute=_current_speed_residual,
        fit=_fit_current_speed,
        description=(
            "Exact-machine electromechanical spindle-load consistency residual "
            "conditioned on spindle speed."
        ),
        equation="I_res[A] = median(I_measured - (b_machine + m_machine × speed[RPM]))",
        assumptions=(
            "Calibration uses confirmed healthy data from the same installed machine.",
            "Current is a non-negative drive/load-current magnitude and speed is positive.",
            "Calibration and inference represent comparable steady processing regimes.",
            "Unmeasured process variables remain sufficiently stable for the intended comparison.",
        ),
        kind=RelationKind.MACHINE_FITTED,
        status=RelationStatus.RUNTIME,
        output_name="spindle.electromechanical_load_residual_a.median",
        output_unit="A",
        mechanism=(
            "Motor torque is related to current under motor/control assumptions, and a "
            "dicing-saw implementation has used feedback current as a spindle-load signal. "
            "The fitted line is only an exact-machine healthy consistency model; its "
            "residual is not a cutting-force estimate."
        ),
        validity_conditions=(
            "The exact machine has at least 20 healthy aligned samples.",
            "Healthy speed has a robust span of at least 100 RPM and 0.2% of median speed.",
            "Signals describe steady processing rather than startup, braking, or reversal.",
            "The drive/current semantics and controller configuration are unchanged.",
        ),
        invalidity_conditions=(
            "Speed excitation is insufficient to identify the slope.",
            "Motor/drive replacement, control retuning, current-signal scaling, or sensor relocation occurs.",
            "Operating regime, material, blade geometry, or process phase differs materially from calibration.",
            "Inputs are non-finite, negative where magnitude semantics apply, or overflow the model.",
        ),
        confounders=(
            "Feed rate, cut depth, kerf width, blade diameter, blade wear, and workpiece material.",
            "Coolant delivery, acceleration, controller dynamics, bearing friction, and sensor drift.",
            "Model discrepancy when the healthy linear approximation no longer describes the regime.",
        ),
        calibration_requirements=(
            "Fit per exact installed machine using reviewed healthy processing intervals.",
            "Repeat calibration across the allowed speed envelope and preserve drive configuration provenance.",
            "Record a robust residual scale for later validation; Step 01 does not create confidence intervals.",
        ),
        parameter_identifiability_notes=(
            "Slope and intercept are identifiable only with material speed excitation.",
            "A 5th–95th percentile span rejects constant-speed data and isolated speed outliers.",
            "The fitted coefficients are empirical machine parameters, not universal motor constants.",
        ),
        uncertainty_sources=(
            "Current and speed accuracy, quantization, calibration drift, and timestamp alignment.",
            "Finite healthy sample size and robust-regression parameter uncertainty.",
            "Unmeasured process conditions and linear model-form discrepancy.",
        ),
        expected_fault_sensitivity=(
            "A positive residual may accompany added spindle load, friction, clogging, or blade wear.",
            "A negative residual may accompany load loss, disengagement, or changed drive behavior.",
        ),
        cross_sensitivities=(
            "The residual is not fault-specific: feed, material, cut geometry, coolant, and controller changes can move it.",
            "Sensor bias can mimic a mechanical load change.",
        ),
        falsification_tests=(
            "Reject the relation if repeated controlled healthy runs do not show a stable current-speed relationship.",
            "Reject or re-scope it if known load changes do not move the residual consistently at fixed speed.",
            "Invalidate the calibration if drive changes shift the residual without a mechanical change.",
        ),
        instrumentation_gaps=(
            "Feed rate, cut depth, kerf width, blade diameter/wear, material, and controller state are absent.",
            "No calibrated torque or cutting-force reference is available."
        ),
        references=(DICING_MONITOR_PATENT, DICING_DYNAMICS, MOTOR_TORQUE_CONSTANT),
    ),
    PhysicsRelation(
        relation_id="contacts.contact_resistance",
        machine_families=frozenset({"final_test"}),
        subsystem="contacts",
        required_channels=("contact_voltage_drop", "site_current"),
        expected_units=(("contact_voltage_drop", "mV"), ("site_current", "A")),
        compute=_contact_resistance,
        fit=None,
        description="Aligned positive contact-path resistance estimate for repeated final-test contacts.",
        equation="R_contact[mΩ] = median(V_drop[mV] / I_site[A]) over valid aligned samples",
        assumptions=(
            "Voltage drop and current refer to the same contact path and active test interval.",
            "Voltage and current polarity conventions are consistent.",
            "The measured drop is dominated by the intended contact path or its fixed parasitics.",
            "The electrical interval is sufficiently settled for a resistance interpretation.",
        ),
        kind=RelationKind.CONSTITUTIVE,
        status=RelationStatus.RUNTIME,
        output_name="contacts.contact_resistance_mohm.median",
        output_unit="mΩ",
        mechanism=(
            "Ohm's law relates voltage drop and current. Increasing series/contact "
            "resistance can accompany socket contamination, spring-pin wear, or poor "
            "engagement, but this aggregate estimate is not a specific fault diagnosis."
        ),
        validity_conditions=(
            "Aligned samples come from one contact path during an active, settled electrical interval.",
            "At least half the window and at least three samples exceed the numerical current floor.",
            "Voltage/current signs imply non-negative passive resistance.",
            "Connection topology and measurement range remain comparable to the reference condition.",
        ),
        invalidity_conditions=(
            "Current is near zero, source/measurement settling is incomplete, or polarity semantics are inconsistent.",
            "Voltage includes changing lead, relay, device, or fixture drops that cannot be separated.",
            "Self-heating or nonlinear device behavior dominates the measured voltage.",
        ),
        confounders=(
            "Socket and lead temperature, thermal EMF, relay/lead resistance, range changes, and source settling.",
            "Device-under-test behavior, current dependence, contact bounce, contamination, and sensor offsets.",
            "Two-wire topology can combine fixture and contact resistance."
        ),
        calibration_requirements=(
            "Verify channel polarity, topology, timing, and voltage/current synchronization on the installed tester.",
            "Establish repeatability with known-good sockets across intended currents and temperatures.",
            "Use a traceable low-resistance reference or four-wire comparison during validation where practical.",
        ),
        parameter_identifiability_notes=(
            "No fitted coefficient is used, but contact resistance is separable only if other series drops are fixed or measured.",
            "Median of aligned V/I preserves sample-level pairing; ratio of medians could combine different operating instants.",
            "The current floor is a scale-aware numerical guard, not a universal health threshold.",
        ),
        uncertainty_sources=(
            "Voltage/current accuracy, resolution, offsets, synchronization, range switching, and calibration drift.",
            "Thermal EMF, self-heating, contact bounce, and unseparated fixture/lead resistance.",
            "Operating-current and temperature dependence of the contact path."
        ),
        expected_fault_sensitivity=(
            "A sustained positive shift may be sensitive to increasing series resistance or degrading contact repeatability.",
            "Intermittent opens may reduce the count of usable samples rather than yield a stable resistance."
        ),
        cross_sensitivities=(
            "Fixture, relay, DUT, temperature, and measurement-system changes can produce the same shift.",
            "Resistance alone does not identify contamination, wear, misalignment, or another specific cause."
        ),
        falsification_tests=(
            "Reject it as a condition indicator if known-good repeated contacts are not stable under controlled load and temperature.",
            "Reject the path interpretation if a four-wire/reference experiment shows the signal is dominated by leads or DUT voltage.",
            "Invalidate it if controlled resistance changes do not produce the expected V/I change."
        ),
        instrumentation_gaps=(
            "The present channel names do not establish Kelvin sensing, relay/lead subtraction, or source-settling state.",
            "No contact-force, insertion count, or per-pin identity is available."
        ),
        references=(NIST_RESISTANCE, KEYSIGHT_LOW_RESISTANCE, NI_SOCKET_GUIDANCE),
    ),
)


RESEARCH_CANDIDATES: tuple[ResearchCandidate, ...] = (
    ResearchCandidate(
        candidate_id="wafer_mount.roller_current_web_tension",
        family="wafer_mount",
        subsystem="feed",
        kind=RelationKind.MACHINE_FITTED,
        status=RelationStatus.RESEARCH_ONLY,
        description="Roller-drive current as a machine-fitted web-tension consistency model.",
        proposed_mechanism="Motor current can relate to torque, which can map through the roller to web tension.",
        proposed_equation="T_web ≈ f_machine(I_motor, phase, acceleration, radius, transmission, friction)",
        existing_channels=("roller_motor_current", "web_tension", "roller_temperature"),
        missing_variables=("torque constant", "roller radius", "transmission ratio", "motion phase", "acceleration", "friction state"),
        decision_reason=(
            "Both end quantities are measured, but the mechanical mapping and phase semantics are not defined; "
            "a regression would currently be a correlation rather than a controlled torque balance."
        ),
        additional_instrumentation=("encoder-derived acceleration", "drive torque estimate with documented semantics", "roller geometry/configuration record"),
        uncertainty_sources=("current scaling", "tension transducer calibration", "web friction", "roller temperature", "timestamp alignment"),
        falsification_tests=("Apply controlled tension changes by phase and verify a repeatable current response after acceleration/friction compensation.",),
        references=(MOTOR_TORQUE_CONSTANT, ISO_DIAGNOSTICS),
    ),
    ResearchCandidate(
        candidate_id="wafer_saw.coolant_hydraulic_resistance",
        family="wafer_saw",
        subsystem="cooling",
        kind=RelationKind.SEMI_EMPIRICAL,
        status=RelationStatus.RESEARCH_ONLY,
        description="Coolant pressure-drop/flow relation across a defined hydraulic element.",
        proposed_mechanism="Flow through a known branch produces regime- and geometry-dependent head loss.",
        proposed_equation="Δp = f(Re, roughness) × (L/D) × ρv²/2",
        existing_channels=("coolant_pressure", "coolant_flow", "coolant_temperature"),
        missing_variables=("pressure sensor location", "differential pressure", "pipe/nozzle geometry", "fluid properties", "pump/valve state"),
        decision_reason=(
            "The current pressure channel does not say whether it is supply, gauge, or differential pressure. "
            "Therefore pressure/flow has no unique hydraulic-resistance meaning."
        ),
        additional_instrumentation=("differential-pressure taps across a named element", "valve/pump state", "documented fluid and branch geometry"),
        uncertainty_sources=("pressure and flow calibration", "viscosity/temperature", "flow regime", "valve position", "sensor placement"),
        falsification_tests=("Across controlled flow sweeps, verify that measured differential pressure follows the selected hydraulic model and repeats after thermal stabilization.",),
        references=(USACE_HYDRAULICS,),
    ),
    ResearchCandidate(
        candidate_id="die_attach.nozzle_vacuum_leak_rate",
        family="die_attach",
        subsystem="vacuum",
        kind=RelationKind.FIRST_PRINCIPLES,
        status=RelationStatus.REJECTED,
        description="Vacuum pickup leakage inferred from an isolated pressure-rise test.",
        proposed_mechanism="For a known isolated volume, leak rate is proportional to volume times pressure-rise rate.",
        proposed_equation="q_L = V × Δp/Δt",
        existing_channels=("nozzle_vacuum",),
        missing_variables=("isolated volume", "valve state", "pump isolation interval", "pressure time series semantics", "gas temperature", "flow"),
        decision_reason="One running vacuum value cannot distinguish leak, pump behavior, pickup seal, valve state, or commanded operating phase.",
        additional_instrumentation=("valve/pump state", "controlled isolation event", "known pneumatic volume", "calibrated pressure decay/rise sequence", "optional flow sensor"),
        uncertainty_sources=("gauge calibration", "volume", "temperature", "outgassing", "virtual leaks", "timing"),
        falsification_tests=("Introduce calibrated leaks during controlled isolation and verify the inferred rate against a reference leak.",),
        references=(LEYBOLD_LEAK_RATE,),
    ),
    ResearchCandidate(
        candidate_id="wire_bond.ultrasonic_input_impedance",
        family="wire_bond",
        subsystem="ultrasonic",
        kind=RelationKind.DIAGNOSTIC_PROXY,
        status=RelationStatus.REJECTED,
        description="Ultrasonic-generator input impedance/harmonic monitoring during bond formation.",
        proposed_mechanism="The transducer/bond mechanical interaction changes electrical impedance and vibration harmonics.",
        proposed_equation="Z(t, f) = V(t, f) / I(t, f), including real/imaginary or phase information",
        existing_channels=("ultrasonic_current", "ultrasonic_frequency_shift"),
        missing_variables=("ultrasonic voltage waveform", "voltage-current phase", "sampling bandwidth", "bond-phase timing", "transducer amplitude/harmonics"),
        decision_reason=(
            "The literature uses voltage plus current, phase/impedance components, or a dedicated vibration sensor. "
            "Current and low-rate frequency shift alone cannot reconstruct impedance."
        ),
        additional_instrumentation=("synchronized generator voltage/current waveforms", "phase measurement", "bond-cycle trigger", "optional calibrated PZT vibration sensor"),
        uncertainty_sources=("bandwidth", "phase error", "generator topology", "bond phase", "transducer temperature", "sensor loading"),
        falsification_tests=("Compare reconstructed impedance and harmonics with a calibrated analyzer while varying known bond conditions and machine settings.",),
        references=(WIRE_BOND_PIEZO, WIRE_BOND_ELECTRICAL, WIRE_BOND_IMPEDANCE),
    ),
    ResearchCandidate(
        candidate_id="molding.clamp_cavity_force_balance",
        family="molding",
        subsystem="hydraulic",
        kind=RelationKind.SEMI_EMPIRICAL,
        status=RelationStatus.REJECTED,
        description="Force/pressure balance between molding cavity and clamp system.",
        proposed_mechanism="Cavity pressure acting over projected area must be opposed by clamp force during the relevant phase.",
        proposed_equation="F_required(t) = p_cavity(t) × A_projected with dynamic/material corrections",
        existing_channels=("cavity_pressure", "clamp_pressure", "transfer_motor_current", "mold_temperature", "plunger_position_error"),
        missing_variables=("actual clamp force", "projected package/runner area", "transfer/cure phase", "plunger position", "resin rheology", "die layout"),
        decision_reason=(
            "Hydraulic pressure is not clamp force without cylinder geometry and losses, while cavity behavior depends on "
            "phase, material, temperature, speed, and cure. Required geometry may also be protected process information."
        ),
        additional_instrumentation=("actual clamp-force measurement", "phase/position state", "approved projected-area metadata", "cure/dielectric sensing"),
        uncertainty_sources=("sensor location", "hydraulic losses", "material batch and moisture", "temperature", "cavity-to-cavity variation"),
        falsification_tests=("Instrument a controlled mold and compare measured clamp force and cavity pressure through fill, pack, and cure phases across known materials.",),
        references=(MOLDING_IN_SITU, MOLDING_PROCESS),
    ),
    ResearchCandidate(
        candidate_id="marking.laser_output_current_temperature",
        family="marking",
        subsystem="optical",
        kind=RelationKind.MACHINE_FITTED,
        status=RelationStatus.RESEARCH_ONLY,
        description="Delivered optical power versus drive current and temperature for a verified laser architecture.",
        proposed_mechanism="Above threshold, diode output depends on current, threshold current, slope efficiency, and junction temperature.",
        proposed_equation="P_out ≈ η_s(T) × max(I_drive - I_th(T), 0)",
        existing_channels=("delivered_laser_power", "laser_drive_current", "laser_temperature"),
        missing_variables=("laser architecture", "junction temperature", "internal feedback/controller state", "pulse/Q-switch state", "optical-path losses"),
        decision_reason=(
            "The relation is defensible for characterized diode architectures, but the marker may use a fiber laser, "
            "pulsed/Q-switched source, or closed-loop power control. Current telemetry does not resolve that ambiguity."
        ),
        additional_instrumentation=("architecture/OEM confirmation", "controller mode", "pulse energy or duty cycle", "junction-temperature proxy", "calibrated optical reference"),
        uncertainty_sources=("power-sensor calibration", "temperature location", "threshold/slope drift", "feedback control", "optical contamination"),
        falsification_tests=("Perform controlled current-temperature sweeps; reject the simple model if hysteresis, controller saturation, or architecture effects dominate.",),
        references=(LASER_OUTPUT_MODEL,),
    ),
    ResearchCandidate(
        candidate_id="trim_form.motor_current_punch_force",
        family="trim_form",
        subsystem="press",
        kind=RelationKind.MACHINE_FITTED,
        status=RelationStatus.RESEARCH_ONLY,
        description="Press motor current mapped through the mechanism to punch force.",
        proposed_mechanism="Motor current can relate to torque, then gearing/linkage geometry can map torque to punch force by stroke phase.",
        proposed_equation="F_punch(θ) ≈ K_t I × G × mechanical_advantage(θ) / losses",
        existing_channels=("punch_force", "press_motor_current", "die_vibration", "die_temperature"),
        missing_variables=("torque constant", "gear/transmission ratio", "linkage geometry", "stroke phase", "acceleration", "friction/loss model"),
        decision_reason="Measured force permits future calibration, but without phase and transmission semantics a single current-force fit would mix dynamics and tooling state.",
        additional_instrumentation=("stroke angle/phase", "drive torque/current semantics", "mechanism configuration", "synchronized high-rate force/current"),
        uncertainty_sources=("force calibration", "current scaling", "dynamic inertia", "tool temperature", "friction", "sampling alignment"),
        falsification_tests=("Apply controlled forces across stroke phases and verify a repeatable mapping after inertial and friction effects are separated.",),
        references=(MOTOR_TORQUE_CONSTANT,),
    ),
    ResearchCandidate(
        candidate_id="singulation.vibration_load_coupling",
        family="singulation",
        subsystem="spindle",
        kind=RelationKind.DIAGNOSTIC_PROXY,
        status=RelationStatus.RESEARCH_ONLY,
        description="Blade vibration coupled with spindle load for dynamic cutting-state assessment.",
        proposed_mechanism="Blade/tool vibration and cutting force interact through spindle and fracture dynamics.",
        proposed_equation="dynamic state = f(vibration spectrum, load, speed, feed, blade/workpiece state)",
        existing_channels=("blade_vibration", "spindle_current", "spindle_speed"),
        missing_variables=("vibration bandwidth and axis", "feed rate", "cut depth", "blade geometry/wear", "material", "cycle phase"),
        decision_reason="The ordinary low-rate scalar vibration channel cannot support the high-rate dynamic/spectral model described by the literature.",
        additional_instrumentation=("specified high-rate accelerometer path", "tachometer/order reference", "feed/depth/phase context", "blade metadata"),
        uncertainty_sources=("sensor mounting", "bandwidth", "aliasing", "machine resonances", "material and process variation"),
        falsification_tests=("With a dedicated DSP acquisition, verify repeatable vibration/load changes under controlled blade condition and reject features dominated by mounting resonances.",),
        references=(DICING_DYNAMICS,),
    ),
    ResearchCandidate(
        candidate_id="final_test.contact_dissipation_power",
        family="final_test",
        subsystem="contacts",
        kind=RelationKind.DIAGNOSTIC_PROXY,
        status=RelationStatus.RESEARCH_ONLY,
        description="Electrical dissipation in the measured contact path.",
        proposed_mechanism="For aligned voltage drop and current, V × I is path dissipation and equals I²R for an ohmic path.",
        proposed_equation="P_path[mW] = V_drop[mV] × I[A]",
        existing_channels=("contact_voltage_drop", "site_current"),
        missing_variables=("contact-only voltage", "thermal path", "settling state", "per-pin identity", "fixture/relay contribution"),
        decision_reason=(
            "The calculation is dimensionally valid but is strongly current-dependent and less direct for contact degradation "
            "than resistance. It remains available for experimental thermal studies, not runtime health."
        ),
        additional_instrumentation=("contact temperature", "four-wire contact voltage", "known current profile", "per-pin/fixture identity"),
        uncertainty_sources=("voltage/current accuracy", "synchronization", "self-heating", "fixture contributions", "DUT behavior"),
        falsification_tests=("Hold known contact resistance constant while sweeping current and verify that power adds no stable condition information beyond R and temperature.",),
        references=(KEYSIGHT_LOW_RESISTANCE, NIST_RESISTANCE),
    ),
)


ALL_MACHINE_FAMILIES: tuple[str, ...] = (
    "wafer_mount",
    "wafer_saw",
    "die_attach",
    "wire_bond",
    "molding",
    "marking",
    "trim_form",
    "singulation",
    "final_test",
)


def relations_for_family(family: str) -> tuple[PhysicsRelation, ...]:
    """Return only relations approved to execute in Step 03."""

    return tuple(
        relation
        for relation in PHYSICS_RELATIONS
        if relation.status is RelationStatus.RUNTIME
        and family in relation.machine_families
    )


def research_catalog_for_family(
    family: str,
) -> tuple[PhysicsRelation | ResearchCandidate, ...]:
    """Return runtime and non-runtime review records for student inspection."""

    runtime = relations_for_family(family)
    candidates = tuple(
        candidate for candidate in RESEARCH_CANDIDATES if candidate.family == family
    )
    return runtime + candidates


def audit_physics_library() -> tuple[str, ...]:
    """Check internal research-record consistency without becoming a framework."""

    issues: list[str] = []
    relation_ids = [relation.relation_id for relation in PHYSICS_RELATIONS]
    candidate_ids = [candidate.candidate_id for candidate in RESEARCH_CANDIDATES]
    reference_keys = [reference.key for reference in RESEARCH_REFERENCES]
    if len(relation_ids) != len(set(relation_ids)):
        issues.append("Runtime relation IDs must be unique")
    if len(candidate_ids) != len(set(candidate_ids)):
        issues.append("Research candidate IDs must be unique")
    if set(relation_ids) & set(candidate_ids):
        issues.append("Runtime relation and research candidate IDs must not collide")
    if len(reference_keys) != len(set(reference_keys)):
        issues.append("Research reference keys must be unique")

    for relation in PHYSICS_RELATIONS:
        prefix = f"Runtime relation {relation.relation_id!r}"
        if relation.status is not RelationStatus.RUNTIME:
            issues.append(f"{prefix} must have RUNTIME status")
        if not relation.machine_families:
            issues.append(f"{prefix} must name a machine family")
        expected_channels = tuple(channel for channel, _ in relation.expected_units)
        if set(relation.required_channels) != set(expected_channels):
            issues.append(f"{prefix} required channels must match expected-unit keys")
        required_fields = (
            ("description", relation.description),
            ("equation", relation.equation),
            ("assumptions", relation.assumptions),
            ("output name", relation.output_name),
            ("output unit", relation.output_unit),
            ("mechanism", relation.mechanism),
            ("validity conditions", relation.validity_conditions),
            ("invalidity conditions", relation.invalidity_conditions),
            ("confounders", relation.confounders),
            ("calibration requirements", relation.calibration_requirements),
            ("identifiability notes", relation.parameter_identifiability_notes),
            ("uncertainty sources", relation.uncertainty_sources),
            ("fault sensitivity", relation.expected_fault_sensitivity),
            ("cross sensitivities", relation.cross_sensitivities),
            ("falsification tests", relation.falsification_tests),
            ("instrumentation gaps", relation.instrumentation_gaps),
            ("references", relation.references),
        )
        for label, value in required_fields:
            if not value:
                issues.append(f"{prefix} must document {label}")
        if relation.compute is None:
            issues.append(f"{prefix} must provide a compute function")

    for candidate in RESEARCH_CANDIDATES:
        prefix = f"Research candidate {candidate.candidate_id!r}"
        if candidate.status is RelationStatus.RUNTIME:
            issues.append(f"{prefix} must not have RUNTIME status")
        if candidate.family not in ALL_MACHINE_FAMILIES:
            issues.append(f"{prefix} names an unsupported family")
        if not candidate.decision_reason:
            issues.append(f"{prefix} must document its decision reason")
        if not candidate.missing_variables:
            issues.append(f"{prefix} must document missing variables")
        if not candidate.additional_instrumentation:
            issues.append(f"{prefix} must document additional instrumentation")
        if not candidate.uncertainty_sources:
            issues.append(f"{prefix} must document uncertainty sources")
        if not candidate.falsification_tests:
            issues.append(f"{prefix} must document a falsification test")
        if not candidate.references:
            issues.append(f"{prefix} must cite supporting evidence")

    catalog_families = {
        family
        for family in ALL_MACHINE_FAMILIES
        if research_catalog_for_family(family)
    }
    missing_families = set(ALL_MACHINE_FAMILIES) - catalog_families
    if missing_families:
        issues.append(
            "Research catalog is missing machine families: "
            + ", ".join(sorted(missing_families))
        )
    for family in ALL_MACHINE_FAMILIES:
        runtime_ids = {relation.relation_id for relation in relations_for_family(family)}
        expected_ids = {
            relation.relation_id
            for relation in PHYSICS_RELATIONS
            if relation.status is RelationStatus.RUNTIME
            and family in relation.machine_families
        }
        if runtime_ids != expected_ids:
            issues.append(f"relations_for_family({family!r}) leaks or omits relations")
    return tuple(issues)
