"""References, experiment records, and evidence audits for Step01."""

from __future__ import annotations

from typing import Mapping, Sequence

import numpy as np

from .schema import (
    EvidenceMaturity,
    ExperimentPlan,
    MeasurementRequirement,
    MeasurementStatus,
    PhysicsReadinessEntry,
    ReferenceType,
    ResearchReference,
    RelationStatus,
    UncertaintyCategory,
    UncertaintySource,
    _MATURITY_ORDER,
)

def _reference(
    key: str,
    citation: str,
    identifier: str,
    reference_type: ReferenceType,
    year: int | None,
    supports: str,
    limits: str,
) -> ResearchReference:
    return ResearchReference(key, citation, identifier, reference_type, year, supports, limits)


ISO_DIAGNOSTICS = _reference(
    "iso_13379_1_2025", "ISO 13379-1:2025, Condition monitoring and diagnostics of machine systems — Data interpretation and diagnostics techniques — Part 1: General guidelines.", "ISO 13379-1:2025", ReferenceType.STANDARD, 2025,
    "Application-specific diagnostic selection and stated operating context.", "A general process standard; it validates no OSAT residual.")
ISO_CONDITION_MONITORING = _reference(
    "iso_17359_2018", "ISO 17359:2018, Condition monitoring and diagnostics of machines — General guidelines, 3rd ed.", "ISO 17359:2018", ReferenceType.STANDARD, 2018,
    "Condition-monitoring programs should define technique, accuracy, operating conditions, acquisition rate, and measurement location.", "General guidance, not equipment-specific thresholds.")
ISO_MEASUREMENT_MANAGEMENT = _reference(
    "iso_10012_2026", "ISO 10012:2026, Quality management — Requirements for measurement management systems, 2nd ed.", "ISO 10012:2026", ReferenceType.STANDARD, 2026,
    "Management of measurement processes and metrological confirmation.", "Conformance is not claimed by this project.")
ISO_VIBRATION_CALIBRATION = _reference(
    "iso_16063_21_2003", "ISO 16063-21:2003, Methods for calibration of vibration and shock transducers — Part 21: Vibration calibration by comparison to a reference transducer.", "ISO 16063-21:2003", ReferenceType.STANDARD, 2003,
    "Comparison calibration of vibration transducers.", "Does not supply machine-health alarm limits.")
ISO_VIBRATION_SCOPE = _reference(
    "iso_20816_3_2022", "ISO 20816-3:2022, Mechanical vibration — Measurement and evaluation of machine vibration — Part 3: Industrial machinery above 15 kW and 120 to 30 000 r/min.", "ISO 20816-3:2022", ReferenceType.STANDARD, 2022,
    "An explicit example of machinery-scope limits for vibration criteria.", "Its >15 kW and <=30 000 r/min scope does not fit the cited 1.8 kW, 60 000 r/min dicing spindle; no limits are imported.")
JCGM_UNCERTAINTY = _reference(
    "jcgm_100_2008", "JCGM 100:2008, Evaluation of measurement data — Guide to the expression of uncertainty in measurement.", "10.59161/JCGM100-2008E", ReferenceType.METROLOGY_GUIDE, 2008,
    "Measurement-model uncertainty budgets and linearized propagation.", "An uncertainty budget needs quantified input distributions/covariances; this code has none for plant sensors.")
JCGM_VIM = _reference(
    "jcgm_200_2012", "JCGM 200:2012, International vocabulary of metrology — Basic and general concepts and associated terms, 3rd ed.", "10.59161/JCGM200-2012", ReferenceType.METROLOGY_GUIDE, 2012,
    "Vocabulary for measurand, calibration, traceability, and uncertainty.", "Terminology does not establish traceability for repository telemetry.")
JCGM_MONTE_CARLO = _reference(
    "jcgm_101_2008", "JCGM 101:2008, Supplement 1 to the GUM — Propagation of distributions using a Monte Carlo method.", "10.59161/JCGM101-2008", ReferenceType.METROLOGY_GUIDE, 2008,
    "Propagation of supplied probability distributions through a measurement model.", "No distributions are available here and no runtime Monte Carlo is implemented.")
NASA_MODEL_STANDARD = _reference(
    "nasa_std_7009b", "NASA-STD-7009B, Standard for Models and Simulations, 2024.", "NASA-STD-7009B", ReferenceType.STANDARD, 2024,
    "Model lifecycle, intended use, acceptance criteria, and credibility-product practices.", "This student project does not claim NASA-standard compliance.")
NASA_MODEL_HANDBOOK = _reference(
    "nasa_hdbk_7009b", "NASA-HDBK-7009B, NASA Handbook for Models and Simulations: An Implementation Guide for NASA-STD-7009B, 2026.", "NASA-HDBK-7009B", ReferenceType.GOVERNMENT_TECHNICAL, 2026,
    "Guidance for communicating model credibility and limitations.", "General model guidance, not evidence for an OSAT relation.")
ASME_UNCERTAINTY = _reference(
    "asme_vvuq_10_2_2021", "ASME VVUQ 10.2-2021, The Role of Uncertainty Quantification in Verification and Validation of Computational Solid Mechanics Models.", "ASME VVUQ 10.2-2021", ReferenceType.STANDARD, 2021,
    "Separation of model-form, numerical, input, experimental, and validation uncertainty.", "Computational-solid-mechanics scope; used only for general V&V/UQ discipline.")
NIST_PHM = _reference(
    "nist_phm4sm", "NIST, Prognostics and Health Management for Reliable Operations in Smart Manufacturing (PHM4SM), project page updated 2025.", "NIST PHM4SM", ReferenceType.GOVERNMENT_TECHNICAL, 2025,
    "PHM verification and validation needs laboratory testbeds, metrics, reference data, and pilot tests.", "NIST work targets manufacturing workcells; it does not validate these OSAT relations.")
NIST_ROADMAP = _reference(
    "nist_ams_100_2", "J. Pellegrino et al., Measurement Science Roadmap for Prognostics and Health Management for Smart Manufacturing Systems, NIST AMS 100-2, 2016.", "10.6028/NIST.AMS.100-2", ReferenceType.GOVERNMENT_TECHNICAL, 2016,
    "Measurement science, PHM performance assessment, V&V, uncertainty, and infrastructure gaps.", "A roadmap, not an equipment validation study.")
KHAN_REVIEW = _reference(
    "khan_2024_physics_learning", "S. Khan, T. Yairi, S. Tsutsumi, and S. Nakasuka, A review of physics-based learning for system health management, Annual Reviews in Control 57 (2024) 100932.", "10.1016/j.arcontrol.2024.100932", ReferenceType.PEER_REVIEWED_REVIEW, 2024,
    "Taxonomy and research state of physics-based learning for health management.", "Broad system-health review; not evidence for a specific OSAT sensor relation.")
DENG_REVIEW = _reference(
    "deng_2023_piml_phm", "W. Deng et al., Physics-informed machine learning in prognostics and health management: State of the art and challenges, Applied Mathematical Modelling 124 (2023) 325–352.", "10.1016/j.apm.2023.07.011", ReferenceType.PEER_REVIEWED_REVIEW, 2023,
    "PIML-PHM taxonomy, opportunities, and limitations.", "Review-level context, not calibration evidence.")
BRAUN_PREPRINT = _reference(
    "braun_2026_piml_phm", "C. Braun, J. Raible, and M. F. Huber, Physics-Informed Machine Learning in Prognostics and Health Management: A Systematic Literature Review, arXiv preprint, submitted 10 August 2026.", "arXiv:2608.10047", ReferenceType.PREPRINT, 2026,
    "Provisional systematic-review context for PIML-PHM evidence gaps.", "Final journal publication was not verified on the review date; preprint only and no relation validation.")
KENNEDY_OHAGAN = _reference(
    "kennedy_ohagan_2001", "M. C. Kennedy and A. O'Hagan, Bayesian calibration of computer models, JRSS B 63(3) (2001) 425–464.", "10.1111/1467-9868.00294", ReferenceType.PEER_REVIEWED_PRIMARY, 2001,
    "Calibration should account for parameter uncertainty and model inadequacy.", "Its Bayesian method is not implemented here; cited for the discrepancy distinction.")
BRYNJARSDOTTIR_OHAGAN = _reference(
    "brynjarsdottir_ohagan_2014", "J. Brynjarsdóttir and A. O'Hagan, Learning about physical parameters: the importance of model discrepancy, Inverse Problems 30 (2014) 114007.", "10.1088/0266-5611/30/11/114007", ReferenceType.PEER_REVIEWED_PRIMARY, 2014,
    "Ignoring model discrepancy can bias and overstate confidence in calibrated parameters.", "Illustrative calibration study; it supplies no discrepancy magnitude for this project.")
RAUE_IDENTIFIABILITY = _reference(
    "raue_2009_identifiability", "A. Raue et al., Structural and practical identifiability analysis of partially observed dynamical models by exploiting the profile likelihood, Bioinformatics 25(15) (2009) 1923–1929.", "10.1093/bioinformatics/btp358", ReferenceType.PEER_REVIEWED_PRIMARY, 2009,
    "Practical identifiability depends on observations and excitation, not only equation form.", "Dynamical biological examples; profile likelihood is not implemented here.")
FRANK_DING_RESIDUAL = _reference(
    "frank_ding_1997", "P. M. Frank and X. Ding, Survey of robust residual generation and evaluation methods in observer-based fault detection systems, Journal of Process Control 7(6) (1997) 403–424.", "10.1016/S0959-1524(97)00016-4", ReferenceType.PEER_REVIEWED_REVIEW, 1997,
    "Residual evaluation must consider robustness to disturbances and model uncertainty.", "Observer-based dynamic systems differ from this simple static residual.")
DICING_MONITOR_PATENT = _reference(
    "dicing_monitor_patent", "I. Weisshaus and O. Y. Licht, Monitoring system for dicing saws, US patent, 2001.", "US6168500B1", ReferenceType.PATENT, 2001,
    "One dicing-saw implementation used spindle feedback current as a cutting-load signal while holding speed.", "A patent is not validation, does not establish universality, and does not prove fault specificity.")
DICING_DYNAMICS = _reference(
    "li_2026_dicing_dynamics", "J. Li et al., Vibration–force coupled dynamics and fracture evolution in wafer dicing, International Journal of Mechanical Sciences 319 (2026) 111581.", "10.1016/j.ijmecsci.2026.111581", ReferenceType.PEER_REVIEWED_PRIMARY, 2026,
    "Dicing force, vibration, fracture, and clogging dynamics are coupled.", "Published dicing study conditions are not automatically transferable to the demo station.")
DISCO_PRODUCT_LINE = _reference(
    "disco_product_line_2024", "DISCO Corporation, Product Lineup catalog, 2024.", "DISCO product_lineup.pdf", ReferenceType.OEM_TECHNICAL, 2024,
    "Public dicing-saw specifications include spindle examples at 1.8 kW and 60 000 min⁻¹.", "Product examples do not identify the simulated WS-01 hardware or its telemetry semantics.")
MAXON_CONSTANTS = _reference(
    "maxon_motor_constants", "maxon, Motor constants / Motor data and operating ranges, technical guidance.", "maxon motor constants", ReferenceType.OEM_TECHNICAL, 2024,
    "Torque constant relates motor current to produced torque under motor-model assumptions.", "Does not establish the controller's reported-current semantics or spindle losses.")
KEITHLEY_LOW_LEVEL = _reference(
    "keithley_low_level_7", "Keithley Instruments, Low Level Measurements Handbook, 7th ed.", "Keithley Low Level Measurements Handbook, 7th ed.", ReferenceType.MANUFACTURER_APPLICATION_NOTE, 2016,
    "Four-wire sensing, offset compensation, current reversal, settling, and dry-circuit practices for low/contact resistance.", "General metrology guidance; current repository channel names do not prove these practices.")
NI_SOCKET_GUIDANCE = _reference(
    "ni_smu_ic_sockets", "National Instruments, Best Practice for Using NI SMUs to Test IC in Sockets, updated 2025.", "NI SMU IC socket best practice", ReferenceType.MANUFACTURER_APPLICATION_NOTE, 2025,
    "Socket debris, wear, and intermittent connections matter to test connectivity.", "Does not prove this project's voltage channel isolates contact resistance.")
KEYSIGHT_LOW_RESISTANCE = _reference(
    "keysight_low_resistance", "Keysight Technologies, Precise Low Resistance Measurements Using the B2961B and 34420A, application note.", "Keysight 3120-1555", ReferenceType.MANUFACTURER_APPLICATION_NOTE, None,
    "Low-resistance measurement needs suitable current, synchronized voltage, offset control, and appropriate topology.", "Application setup is not evidence that repository telemetry follows it.")
LIU_WAFER_PROBE = _reference(
    "liu_2007_wafer_probe_contact", "D. S. Liu, M. K. Shih, and W. H. Huang, Measurement and analysis of contact resistance in wafer probe testing, Microelectronics Reliability 47(7) (2007) 1086–1094.", "10.1016/j.microrel.2006.07.091", ReferenceType.PEER_REVIEWED_PRIMARY, 2007,
    "Probe contact resistance is affected by contact condition and contamination.", "Wafer-probe contacts are not final-test sockets; no direct transfer claim is made.")
KEYENCE_POWER_MONITOR = _reference(
    "keyence_laser_power_monitor", "KEYENCE America, Laser marking resources: built-in thermopile power monitoring for detecting output-power drops.", "KEYENCE laser marking resource", ReferenceType.OEM_TECHNICAL, 2026,
    "Some commercial laser markers directly monitor optical output power for maintenance.", "Vendor-specific capability; it does not define this repository's channel or a universal degradation model.")
TRUMPF_CONDITION_MONITORING = _reference(
    "trumpf_laser_monitoring", "TRUMPF, Condition Monitoring for lasers and laser systems, service description.", "TRUMPF Condition Monitoring", ReferenceType.OEM_TECHNICAL, 2026,
    "Commercial laser condition monitoring uses equipment-specific service data and algorithms.", "Marketing/service description without an open transferable relation.")
WIRE_BOND_IMPEDANCE = _reference(
    "feng_2011_wire_bond", "W. Feng et al., Wire bonding quality monitoring via refining process of electrical signal from ultrasonic generator, MSSP 25(3) (2011) 884–900.", "10.1016/j.ymssp.2010.09.010", ReferenceType.PEER_REVIEWED_PRIMARY, 2011,
    "Wire-bond electrical monitoring used generator voltage/current and harmonic/phase information.", "Current plus low-rate frequency shift alone is insufficient to reproduce the method.")
WIRE_BOND_PIEZO = _reference(
    "or_1998_wire_bond", "S. W. Or et al., Ultrasonic wire-bond quality monitoring using piezoelectric sensor, Sensors and Actuators A 65(1) (1998) 69–75.", "10.1016/S0924-4247(97)01638-5", ReferenceType.PEER_REVIEWED_PRIMARY, 1998,
    "Dedicated PZT sensing captured dynamic wire-bond vibration behavior.", "Requires a dedicated dynamic sensor path absent from current telemetry.")
MOLDING_MONITOR = _reference(
    "kahle_2016_transfer_molding", "R. Kahle et al., In-situ measuring module for transfer molding process monitoring, IMAPS Proceedings (2016).", "10.4071/isom-2016-THA43", ReferenceType.PEER_REVIEWED_PRIMARY, 2016,
    "Transfer-mold research measures cavity pressure, material/tool temperature, and cure-related information.", "Experimental packaging work does not validate a clamp-pressure residual.")
MOLDING_PROCESS = _reference(
    "kaya_2019_transfer_molding", "B. Kaya et al., Process Optimization and Implementation of Online Monitoring Process in Transfer Molding for Electronic Packaging, JMEP (2019).", "10.4071/IMAPS.954402", ReferenceType.PEER_REVIEWED_PRIMARY, 2019,
    "Transfer molding depends on pressure, temperature, transfer conditions, material state, and cure behavior.", "Does not yield a generic equipment-health ratio from present channels.")
LASER_OUTPUT_MODEL = _reference(
    "borras_2019_laser_output", "R. Borràs et al., Laser diodes optical output power model, Measurement 133 (2019) 56–67.", "10.1016/j.measurement.2018.10.007", ReferenceType.PEER_REVIEWED_PRIMARY, 2019,
    "Compatible laser-diode output depends on drive, threshold/slope efficiency, and temperature.", "Cannot be transferred to an unknown fiber, solid-state, UV, pulsed, or closed-loop marker.")
LEYBOLD_LEAK = _reference(
    "leybold_pressure_rise", "Leybold, Fundamentals of Leak Detection: pressure-rise and pressure-drop tests.", "Leybold Fundamentals of Leak Detection", ReferenceType.OEM_TECHNICAL, None,
    "Pressure-rise leak-rate inference requires a known isolated volume and pressure change over time.", "Vacuum value during operation cannot by itself identify a leak.")
BRANCA_WEB = _reference(
    "branca_2013_web_tension", "C. Branca, P. R. Pagilla, and K. N. Reid, Governing equations for web tension and web velocity in the presence of nonideal rollers, ASME JDSMC 135(1) (2013) 011018.", "10.1115/1.4007974", ReferenceType.PEER_REVIEWED_PRIMARY, 2013,
    "Web tension/velocity dynamics depend on roller mechanics and nonideal effects.", "Not specific to wafer-mount tape handling and requires machine parameters absent here.")


RESEARCH_REFERENCES: tuple[ResearchReference, ...] = (
    ISO_DIAGNOSTICS, ISO_CONDITION_MONITORING, ISO_MEASUREMENT_MANAGEMENT,
    ISO_VIBRATION_CALIBRATION, ISO_VIBRATION_SCOPE, JCGM_UNCERTAINTY,
    JCGM_VIM, JCGM_MONTE_CARLO, NASA_MODEL_STANDARD, NASA_MODEL_HANDBOOK,
    ASME_UNCERTAINTY, NIST_PHM, NIST_ROADMAP, KHAN_REVIEW, DENG_REVIEW,
    BRAUN_PREPRINT,
    KENNEDY_OHAGAN, BRYNJARSDOTTIR_OHAGAN, RAUE_IDENTIFIABILITY,
    FRANK_DING_RESIDUAL, DICING_MONITOR_PATENT, DICING_DYNAMICS,
    DISCO_PRODUCT_LINE, MAXON_CONSTANTS, KEITHLEY_LOW_LEVEL,
    NI_SOCKET_GUIDANCE, KEYSIGHT_LOW_RESISTANCE,
    LIU_WAFER_PROBE, KEYENCE_POWER_MONITOR, TRUMPF_CONDITION_MONITORING,
    WIRE_BOND_IMPEDANCE, WIRE_BOND_PIEZO, MOLDING_MONITOR,
    MOLDING_PROCESS, LASER_OUTPUT_MODEL, LEYBOLD_LEAK, BRANCA_WEB,
)

def _measurement(channel: str, measurand: str, unit: str, semantics: str, *, missing: bool = False) -> MeasurementRequirement:
    return MeasurementRequirement(
        channel, measurand, unit, "equipment channel plus independent reference during experiment", "documented sensor-to-physical path", semantics, "must be documented", "synchronized to machine phase and paired variables", "defined from target dynamics and anti-alias requirements", "calibrate against a suitable reference", "traceability not established", "derive from expected effect and uncertainty budget", MeasurementStatus.MISSING if missing else MeasurementStatus.AVAILABLE_BUT_SEMANTICS_UNVERIFIED,
    )


def _uncertainties(*names: str) -> tuple[UncertaintySource, ...]:
    return tuple(UncertaintySource(name, UncertaintyCategory.MEASUREMENT, "Not quantified for the current repository telemetry.") for name in names)


def _discrepancies(*names: str) -> tuple[UncertaintySource, ...]:
    return tuple(UncertaintySource(name, UncertaintyCategory.MODEL_DISCREPANCY, "Omitted physics or operating context may bias the proposed residual.") for name in names)


def _experiment(
    objective: str,
    hypothesis: str,
    instrumentation: tuple[str, ...],
    factors: tuple[str, ...],
    perturbation: str,
    negative_controls: tuple[str, ...],
) -> ExperimentPlan:
    """Build a complete review record without implying a shared physical model."""

    return ExperimentPlan(
        objective=objective,
        hypothesis=hypothesis,
        equipment_and_specimen=("one identified machine under site/OEM approval", "approved representative or surrogate material"),
        required_instrumentation=instrumentation,
        controlled_factors=factors,
        nuisance_factors=("temperature", "run order", "operator/maintenance state", "material/fixture variation"),
        baseline_condition="Independently reviewed healthy state with metrologically checked instruments.",
        fault_or_perturbation=perturbation,
        negative_controls=negative_controls,
        design_of_experiments="Randomized, replicated, blocked design; include interactions justified by the mechanism and chronological repeats for drift.",
        calibration_data="Predeclared healthy calibration blocks only.",
        validation_data="Separate later blocks and conditions; do not reuse calibration observations.",
        acceptance_criteria=("repeatable directional sensitivity", "stable healthy parameters", "bounded cross-sensitivity", "negative controls do not trigger the same residual"),
        rejection_criteria=("non-repeatable or reversed sensitivity", "large omitted-condition dependence", "sensor artifact mimics target", "held-out performance fails predeclared criteria"),
        recalibration_triggers=("sensor or component replacement", "configuration/firmware change", "approved operating-domain expansion"),
        invalidation_triggers=("measurement semantics cannot be verified", "target effect cannot be separated from confounders", "held-out result fails"),
        safety_and_approval_notes=("research observe-only", "OEM/site approval", "no intentional damage outside an approved test plan", "no autonomous maintenance action"),
        reference_instrument=instrumentation,
        swept_variables=factors,
        sample_repetition_strategy="Replicated conditions in randomized blocks plus chronological repeats; final counts require an approved precision/power plan.",
        sensor_fault_challenge=("bias", "gain", "drift", "dropout", "clipping", "timing offset where relevant"),
        reproducibility_requirement="Repeat across runs/days and later on held-out same-family machines before a transfer claim.",
        data_to_archive=("raw telemetry and reference measurements", "timestamps", "instrument calibration records", "machine/configuration identity", "DOE/run order", "conditions and perturbations"),
        validation_stages=("A measurement-system validation", "B healthy calibration", "C independent healthy validation", "D perturbation challenge", "E confounder challenge", "F sensor-fault challenge", "G run/day repeatability", "H machine reproducibility", "I prospective pilot"),
    )


WEB_EXPERIMENT = _experiment(
    "Test whether motor current adds interpretable redundancy to direct tape/web tension.",
    "After phase, acceleration, geometry, and friction compensation, drive torque should balance a controlled change in web tension.",
    ("calibrated tension transducer", "drive current/torque feedback", "encoder/acceleration", "roller geometry and temperature"),
    ("tension setpoint", "speed/acceleration", "roller temperature", "web material"),
    "Safe controlled tension changes across motion phases.",
    ("acceleration change at fixed tension", "friction/temperature change", "current-sensor offset"),
)
COOLANT_EXPERIMENT = _experiment(
    "Establish a pressure-drop/flow residual across one named coolant element.",
    "For fixed geometry, fluid, temperature, valve, and pump state, differential pressure follows the selected regime-dependent flow law.",
    ("differential-pressure taps", "calibrated flow and temperature", "valve/pump state", "documented branch geometry"),
    ("flow", "temperature", "valve state", "known restriction"),
    "Insert approved calibrated restrictions without risking cooling loss.",
    ("supply-pressure change with branch resistance fixed", "pressure-sensor bias", "temperature/viscosity change"),
)
VACUUM_EXPERIMENT = _experiment(
    "Validate isolated-volume pressure-rise inference for the die-attach pickup path.",
    "With pump/valves isolated and volume known, pressure-rise rate increases with a calibrated leak.",
    ("known volume", "valve/pump state", "calibrated pressure gauge", "reference leak", "gas temperature"),
    ("leak rate", "volume", "temperature", "isolation duration"),
    "Introduce approved reference leaks during a controlled non-production isolation sequence.",
    ("outgassing/virtual-leak soak", "gauge offset", "pump still connected"),
)
WIRE_EXPERIMENT = _experiment(
    "Determine whether synchronized generator impedance/vibration features respond to controlled bond-quality changes.",
    "Transducer/contact mechanics alter voltage-current phase/impedance and vibration during defined bond phases.",
    ("synchronized high-rate voltage/current", "phase", "bond trigger", "calibrated PZT", "destructive bond-quality reference"),
    ("bond force", "ultrasonic power/time", "wire/pad material", "tool condition"),
    "Approved parameter sweeps and known tool/bond conditions.",
    ("electrical gain/phase injection", "no-contact ultrasonic cycle", "temperature change"),
)
MOLD_EXPERIMENT = _experiment(
    "Test a phase-resolved clamp-force/cavity-pressure balance on an instrumented transfer mold.",
    "Measured clamp force must exceed cavity pressure times approved projected area after characterized dynamic losses.",
    ("actual clamp-force sensor", "cavity-pressure sensors", "position/phase", "tool/material temperature", "approved projected area"),
    ("transfer speed", "temperature", "material state", "clamp force"),
    "Safe pressure/force sweeps on an approved instrumented mold.",
    ("hydraulic sensor offset", "material change", "same pressure with different projected area"),
)
LASER_EXPERIMENT = _experiment(
    "Identify whether delivered optical power is predictable from drive and thermal/controller state for the actual marker architecture.",
    "Within one verified architecture and control mode, delivered power has a repeatable current/temperature relation.",
    ("calibrated optical power reference", "drive current", "temperature", "pulse/duty/controller state"),
    ("power setpoint", "temperature", "duty/pulse state", "optical-path contamination"),
    "Approved power/temperature sweeps and controlled optical attenuation.",
    ("power-sensor gain drift", "attenuation after internal monitor", "controller-mode change"),
)
PRESS_EXPERIMENT = _experiment(
    "Map press drive torque to punch force by stroke phase and separate tool degradation from dynamics.",
    "With known torque constant, transmission, phase, and acceleration, current-derived torque predicts measured punch force.",
    ("calibrated punch force", "drive current/torque", "stroke encoder", "mechanism geometry", "high-rate synchronization"),
    ("stroke phase", "speed/acceleration", "tool condition", "material"),
    "Approved force and tool-condition sweeps across stroke phases.",
    ("acceleration change", "current offset", "friction/temperature change"),
)
SINGULATION_EXPERIMENT = _experiment(
    "Test whether wafer-dicing spindle-load evidence transfers to the specific singulation mechanism.",
    "If the singulation station has equivalent drive/control/cutting mechanics, controlled added load should produce a comparable speed-conditioned current response.",
    ("verified drive semantics", "calibrated speed/current", "feed/depth/phase", "force reference", "high-rate vibration path"),
    ("speed", "feed/depth", "package/material", "blade state"),
    "Controlled approved blade/load states on the actual singulation equipment.",
    ("same current change caused by controller gain", "vibration sensor mounting change", "no-cut run"),
)
CONTACT_EXPERIMENT = _experiment(
    "Determine whether repository voltage/current channels isolate final-test contact resistance with adequate metrology.",
    "Four-terminal, contact-local, settled V/I with offset compensation will track controlled contact contamination/wear.",
    ("Kelvin force/sense path", "SMU/nanovoltmeter", "current reversal/offset compensation", "contact force and temperature", "per-pin/fixture identity"),
    ("known resistance", "contact force", "current", "temperature", "contamination/insertion count"),
    "Approved reference resistances and controlled contact contamination/wear specimens.",
    ("lead/relay resistance change", "DUT voltage change", "thermoelectric offset", "current-source settling"),
)


class PhysicsResearchDependencyError(RuntimeError):
    """An optional offline physics-research dependency is unavailable."""


def deterministic_factorial_design(
    factors: Mapping[str, Sequence[float]],
) -> tuple[tuple[str, ...], np.ndarray]:
    """Translate explicit factor levels into a deterministic full-factorial matrix.

    The returned matrix is a research planning aid only.  It does not create
    validation evidence or change any existing :class:`ExperimentPlan` claim.
    """

    try:
        from pydoe import fullfact
    except ImportError as exc:
        raise PhysicsResearchDependencyError(
            "pydoe is required only for offline Step01 experiment planning"
        ) from exc
    names = tuple(factors)
    if not names:
        raise ValueError("At least one explicitly defined factor is required")
    levels = tuple(tuple(float(value) for value in factors[name]) for name in names)
    if any(len(values) < 2 for values in levels):
        raise ValueError("Every factor must define at least two levels")
    if any(not np.all(np.isfinite(values)) for values in levels):
        raise ValueError("Factor levels must be finite")
    indices = np.asarray(fullfact([len(values) for values in levels]), dtype=int)
    matrix = np.empty(indices.shape, dtype=float)
    for column, values in enumerate(levels):
        matrix[:, column] = np.asarray(values, dtype=float)[indices[:, column]]
    return names, matrix


def spindle_residual_symbolic_identity_holds() -> bool:
    """Check the fixed residual algebra offline without evaluating equation text."""

    try:
        from sympy import simplify, symbols
    except ImportError as exc:
        raise PhysicsResearchDependencyError(
            "SymPy is required only for offline Step01 symbolic checks"
        ) from exc
    measured, slope, speed, intercept = symbols("measured slope speed intercept")
    implemented_form = measured - (intercept + slope * speed)
    expanded_form = measured - intercept - slope * speed
    return bool(simplify(implemented_form - expanded_form) == 0)


def physics_readiness_report() -> tuple[PhysicsReadinessEntry, ...]:
    from ..families import ALL_MACHINE_FAMILIES, PHYSICS_RELATIONS, RESEARCH_CANDIDATES

    entries: list[PhysicsReadinessEntry] = []
    for relation in PHYSICS_RELATIONS:
        entries.append(PhysicsReadinessEntry(
            relation.relation_id, ",".join(sorted(relation.machine_families)),
            relation.status, relation.evidence_maturity,
            tuple((item.channel, item.status) for item in relation.measurement_requirements),
            "Exact-machine offline fit available" if relation.fit is not None else "No calibration fit",
            any(
                _MATURITY_ORDER[evidence.maturity] >= _MATURITY_ORDER[EvidenceMaturity.BENCH_VALIDATED]
                and evidence.independently_verified
                and bool(evidence.artifact_reference.strip())
                for evidence in relation.validation_evidence
            ),
            relation.major_blocker, relation.next_experiment,
        ))
    for candidate in RESEARCH_CANDIDATES:
        entries.append(PhysicsReadinessEntry(
            candidate.candidate_id, candidate.family, candidate.status,
            candidate.evidence_maturity,
            tuple((item.channel, item.status) for item in candidate.measurement_requirements),
            "Blocked pending instrumentation and controlled calibration",
            False, candidate.major_blocker, candidate.next_experiment,
        ))
    return tuple(entries)


def audit_physics_library() -> tuple[str, ...]:
    """Strong internal audit.  It checks records, never physical validity."""

    from ..families import ALL_MACHINE_FAMILIES, PHYSICS_RELATIONS, RESEARCH_CANDIDATES
    from ..families.wafer_saw import INTERCEPT, RESIDUAL_SCALE, SLOPE, SPEED_HIGH, SPEED_LOW, SPEED_SPAN

    issues: list[str] = []
    relation_ids = [item.relation_id for item in PHYSICS_RELATIONS]
    candidate_ids = [item.candidate_id for item in RESEARCH_CANDIDATES]
    reference_keys = [item.key for item in RESEARCH_REFERENCES]
    if len(relation_ids) != len(set(relation_ids)):
        issues.append("Runtime relation IDs must be unique")
    if len(candidate_ids) != len(set(candidate_ids)):
        issues.append("Candidate IDs must be unique")
    if set(relation_ids) & set(candidate_ids):
        issues.append("Runtime and candidate IDs must not collide")
    if len(reference_keys) != len(set(reference_keys)):
        issues.append("Reference keys must be unique")
    known_references = set(reference_keys)
    if set(candidate.family for candidate in RESEARCH_CANDIDATES) | {family for relation in PHYSICS_RELATIONS for family in relation.machine_families} != set(ALL_MACHINE_FAMILIES):
        issues.append("Every machine family must have a research record")

    for relation in PHYSICS_RELATIONS:
        prefix = f"Runtime relation {relation.relation_id!r}"
        if relation.status is not RelationStatus.RUNTIME_RESEARCH:
            issues.append(f"{prefix} is not runtime research")
        if _MATURITY_ORDER[relation.evidence_maturity] >= _MATURITY_ORDER[EvidenceMaturity.BENCH_VALIDATED]:
            issues.append(f"{prefix} exceeds the evidence allowed for the current repository")
        if set(relation.required_channels) != {name for name, _ in relation.expected_units}:
            issues.append(f"{prefix} channels and units differ")
        if not relation.machine_families or not relation.machine_families.issubset(ALL_MACHINE_FAMILIES):
            issues.append(f"{prefix} names an invalid family")
        if not relation.output_name or not relation.output_unit:
            issues.append(f"{prefix} must define output name and unit")
        if not relation.validity_conditions or not relation.invalidity_conditions or not relation.confounders:
            issues.append(f"{prefix} must define validity, invalidity, and confounders")
        if relation.fit is not None and {item.name for item in relation.parameter_specs} != {SLOPE, INTERCEPT, RESIDUAL_SCALE, SPEED_SPAN, SPEED_LOW, SPEED_HIGH}:
            issues.append(f"{prefix} fitted parameters lack exact ParameterSpec records")
        required_values = (relation.evidence_claims, relation.measurement_requirements, relation.measurement_uncertainty_sources, relation.model_discrepancy_sources, relation.target_fault_sensitivities, relation.sensor_failure_modes, relation.residual_fmea, relation.falsification_tests, relation.recalibration_triggers, relation.invalidation_triggers, relation.references)
        if any(not value for value in required_values):
            issues.append(f"{prefix} has an incomplete credibility record")
        plan = relation.experiment_plan
        if not (plan.reference_instrument and plan.swept_variables and plan.negative_controls
                and plan.sensor_fault_challenge and plan.validation_stages
                and plan.reproducibility_requirement and plan.data_to_archive):
            issues.append(f"{prefix} has an incomplete validation/falsification plan")
        for claim in relation.evidence_claims:
            if not set(claim.reference_keys).issubset(known_references):
                issues.append(f"{prefix} cites an unknown reference key")
        if any(source.category is not UncertaintyCategory.MODEL_DISCREPANCY for source in relation.model_discrepancy_sources):
            issues.append(f"{prefix} mixes model discrepancy with measurement uncertainty")

    for candidate in RESEARCH_CANDIDATES:
        prefix = f"Candidate {candidate.candidate_id!r}"
        if candidate.status is RelationStatus.RUNTIME_RESEARCH:
            issues.append(f"{prefix} leaks into runtime status")
        if candidate.family not in ALL_MACHINE_FAMILIES:
            issues.append(f"{prefix} names an invalid family")
        if _MATURITY_ORDER[candidate.evidence_maturity] >= _MATURITY_ORDER[EvidenceMaturity.BENCH_VALIDATED]:
            issues.append(f"{prefix} claims unsupported physical maturity")
        required_values = (candidate.evidence_claims, candidate.measurement_requirements, candidate.uncertainty_sources, candidate.model_discrepancy_sources, candidate.target_fault_sensitivities, candidate.sensor_failure_modes, candidate.residual_fmea, candidate.decision_reason, candidate.additional_instrumentation, candidate.falsification_tests, candidate.recalibration_triggers, candidate.invalidation_triggers, candidate.major_blocker, candidate.potential_value, candidate.references)
        if any(not value for value in required_values):
            issues.append(f"{prefix} has an incomplete research record")
        if not all(requirement.measurement_method and requirement.calibration_requirement for requirement in candidate.measurement_requirements):
            issues.append(f"{prefix} has an incomplete instrumentation requirement")
        for claim in candidate.evidence_claims:
            if claim.reference_keys and not set(claim.reference_keys).issubset(known_references):
                issues.append(f"{prefix} cites an unknown reference key")
    if any("20816" in relation.equation for relation in PHYSICS_RELATIONS):
        issues.append("ISO 20816 limits must not be imported into runtime equations")
    return tuple(issues)

