"""Step 01: auditable engineering claims for physical residual research.

This module deliberately distinguishes a correct software implementation from a
validated physical model.  A relation reaches the Step 03 runtime path only when
its present evidence and telemetry semantics justify research use.  Passing unit
tests never advances physical-evidence maturity.
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
    """Origin of the mathematical form; not a credibility rating."""

    FIRST_PRINCIPLES = "FIRST_PRINCIPLES"
    CONSTITUTIVE = "CONSTITUTIVE"
    SEMI_EMPIRICAL = "SEMI_EMPIRICAL"
    MACHINE_FITTED = "MACHINE_FITTED"
    DIAGNOSTIC_PROXY = "DIAGNOSTIC_PROXY"


class RelationStatus(str, Enum):
    """Lifecycle state.  Only RUNTIME_RESEARCH is returned to Step 03."""

    CANDIDATE = "CANDIDATE"
    RESEARCH_ONLY = "RESEARCH_ONLY"
    RUNTIME_RESEARCH = "RUNTIME_RESEARCH"
    INVALIDATED = "INVALIDATED"
    REJECTED = "REJECTED"


class EvidenceMaturity(str, Enum):
    """Evidence ladder; software tests do not move a claim up this ladder."""

    HYPOTHESIS = "HYPOTHESIS"
    LITERATURE_SUPPORTED = "LITERATURE_SUPPORTED"
    MEASUREMENT_SEMANTICS_VERIFIED = "MEASUREMENT_SEMANTICS_VERIFIED"
    BENCH_VALIDATED = "BENCH_VALIDATED"
    SINGLE_MACHINE_VALIDATED = "SINGLE_MACHINE_VALIDATED"
    MULTI_MACHINE_VALIDATED = "MULTI_MACHINE_VALIDATED"
    PROSPECTIVE_PILOT_VALIDATED = "PROSPECTIVE_PILOT_VALIDATED"


class ReferenceType(str, Enum):
    STANDARD = "STANDARD"
    METROLOGY_GUIDE = "METROLOGY_GUIDE"
    PEER_REVIEWED_PRIMARY = "PEER_REVIEWED_PRIMARY"
    PEER_REVIEWED_REVIEW = "PEER_REVIEWED_REVIEW"
    OEM_TECHNICAL = "OEM_TECHNICAL"
    PATENT = "PATENT"
    TEXTBOOK = "TEXTBOOK"
    MANUFACTURER_APPLICATION_NOTE = "MANUFACTURER_APPLICATION_NOTE"
    GOVERNMENT_TECHNICAL = "GOVERNMENT_TECHNICAL"
    PREPRINT = "PREPRINT"


class MeasurementStatus(str, Enum):
    AVAILABLE_BUT_SEMANTICS_UNVERIFIED = "AVAILABLE_BUT_SEMANTICS_UNVERIFIED"
    AVAILABLE_AND_SEMANTICALLY_SUPPORTED = "AVAILABLE_AND_SEMANTICALLY_SUPPORTED"
    MISSING = "MISSING"


class ParameterSource(str, Enum):
    KNOWN_CONSTANT = "KNOWN_CONSTANT"
    MACHINE_FITTED = "MACHINE_FITTED"
    NUISANCE_PARAMETER = "NUISANCE_PARAMETER"
    DIRECT_MEASUREMENT = "DIRECT_MEASUREMENT"
    OEM_DOCUMENTATION = "OEM_DOCUMENTATION"
    LITERATURE = "LITERATURE"


class UncertaintyCategory(str, Enum):
    MEASUREMENT = "MEASUREMENT"
    PARAMETER = "PARAMETER"
    TEMPORAL_ALIGNMENT = "TEMPORAL_ALIGNMENT"
    OPERATING_CONDITION = "OPERATING_CONDITION"
    MODEL_FORM = "MODEL_FORM"

    # Clear vocabulary aliases retained for callers that describe the concept,
    # while serialized values follow the research-review terminology.
    ALIGNMENT = "TEMPORAL_ALIGNMENT"
    MODEL_DISCREPANCY = "MODEL_FORM"


class ResidualDirection(str, Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    MAGNITUDE_ONLY = "MAGNITUDE_ONLY"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ResearchReference:
    key: str
    citation: str
    identifier: str
    reference_type: ReferenceType
    publication_year: int | None
    supports: str
    scope_limitations: str


@dataclass(frozen=True)
class EvidenceClaim:
    claim_id: str
    statement: str
    reference_keys: tuple[str, ...]
    evidence_scope: str
    limitations: str

    @property
    def scope_limitations(self) -> str:
        return self.limitations


@dataclass(frozen=True)
class MeasurementRequirement:
    channel: str
    measurand: str
    required_unit: str
    measurement_method: str
    measurement_location_or_path: str
    semantics_required: str
    sign_convention: str
    timing_requirement: str
    bandwidth_requirement: str
    calibration_requirement: str
    traceability_requirement: str
    minimum_resolution_if_known: str
    current_schema_status: MeasurementStatus
    calibration_state: str = "UNKNOWN"
    uncertainty_state: str = "NOT_QUANTIFIED"
    traceability_state: str = "NOT_ESTABLISHED"
    possible_sensor_drift: str = "UNKNOWN"
    possible_quantization: str = "UNKNOWN"
    possible_conversion_scaling_uncertainty: str = "UNKNOWN"
    notes: str = ""

    @property
    def status(self) -> MeasurementStatus:
        return self.current_schema_status


@dataclass(frozen=True)
class ParameterSpec:
    name: str
    physical_interpretation: str
    unit: str
    source: ParameterSource
    allowed_domain: str
    required_excitation: str
    identifiability_notes: str
    recalibration_triggers: tuple[str, ...]


@dataclass(frozen=True)
class UncertaintySource:
    name: str
    category: UncertaintyCategory
    description: str
    quantified: bool = False


@dataclass(frozen=True)
class FaultSensitivity:
    mechanism_or_fault: str
    expected_direction: ResidualDirection
    evidence_maturity: EvidenceMaturity
    rationale: str


@dataclass(frozen=True)
class SensorFailureMode:
    channel: str
    failure_mode: str
    effect_on_output: str
    can_mimic_degradation: bool


@dataclass(frozen=True)
class ResidualFmeaEntry:
    physical_fault_or_degradation: str
    expected_measurement_effect: str
    expected_residual_effect: str
    likely_confounders: tuple[str, ...]
    mimicking_sensor_fault: str
    can_localize_cause: bool


@dataclass(frozen=True)
class ExperimentPlan:
    objective: str
    hypothesis: str
    equipment_and_specimen: tuple[str, ...]
    required_instrumentation: tuple[str, ...]
    controlled_factors: tuple[str, ...]
    nuisance_factors: tuple[str, ...]
    baseline_condition: str
    fault_or_perturbation: str
    negative_controls: tuple[str, ...]
    design_of_experiments: str
    calibration_data: str
    validation_data: str
    acceptance_criteria: tuple[str, ...]
    rejection_criteria: tuple[str, ...]
    recalibration_triggers: tuple[str, ...]
    invalidation_triggers: tuple[str, ...]
    safety_and_approval_notes: tuple[str, ...]
    reference_instrument: tuple[str, ...] = ()
    swept_variables: tuple[str, ...] = ()
    sample_repetition_strategy: str = ""
    sensor_fault_challenge: tuple[str, ...] = ()
    reproducibility_requirement: str = ""
    data_to_archive: tuple[str, ...] = ()
    validation_stages: tuple[str, ...] = ()


@dataclass(frozen=True)
class ValidationEvidence:
    evidence_id: str
    maturity: EvidenceMaturity
    machine_ids: tuple[str, ...]
    artifact_reference: str
    independently_verified: bool
    description: str


@dataclass(frozen=True)
class ApplicabilityEnvelope:
    calibrated_ranges: tuple[tuple[str, float, float, str], ...]
    categorical_conditions: tuple[str, ...]
    notes: tuple[str, ...]


@dataclass(frozen=True)
class ResidualDiagnostics:
    sample_count: int
    finite_output_fraction: float
    median: float
    mad: float
    chronological_drift: float
    conditioning_slope: float | None
    lag1_autocorrelation: float | None
    maximum_autocorrelation: float | None
    fraction_outside_envelope: float


@dataclass(frozen=True)
class ParameterStabilityDiagnostics:
    assessable: bool
    block_count: int
    parameter_relative_ranges: tuple[tuple[str, float], ...]
    notes: tuple[str, ...]


@dataclass(frozen=True)
class CalibrationReport:
    relation_id: str
    parameters: tuple[tuple[str, float], ...]
    sample_count: int
    excitation_summary: tuple[tuple[str, float], ...]
    applicability_envelope: ApplicabilityEnvelope
    calibration_diagnostics: ResidualDiagnostics
    parameter_stability: ParameterStabilityDiagnostics
    blockers: tuple[str, ...]
    valid: bool


@dataclass(frozen=True)
class ValidationDiagnostics:
    relation_id: str
    calibration_report: CalibrationReport
    validation_diagnostics: ResidualDiagnostics
    independent_data: bool
    shared_data_note: str
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class PhysicsReadinessEntry:
    item_id: str
    family: str
    status: RelationStatus
    evidence_maturity: EvidenceMaturity
    measurement_statuses: tuple[tuple[str, MeasurementStatus], ...]
    calibration_capability: str
    validation_evidence_available: bool
    major_blocker: str
    next_experiment: str


_MATURITY_ORDER = {value: index for index, value in enumerate(EvidenceMaturity)}


@dataclass(frozen=True)
class PhysicsRelation:
    """Executable relation.  The first ten fields are the Step 03 contract."""

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
    kind: RelationKind
    status: RelationStatus
    evidence_maturity: EvidenceMaturity
    output_name: str
    output_unit: str
    mechanism: str
    validity_conditions: tuple[str, ...]
    invalidity_conditions: tuple[str, ...]
    confounders: tuple[str, ...]
    calibration_requirements: tuple[str, ...]
    parameter_specs: tuple[ParameterSpec, ...]
    evidence_claims: tuple[EvidenceClaim, ...]
    measurement_requirements: tuple[MeasurementRequirement, ...]
    measurement_uncertainty_sources: tuple[UncertaintySource, ...]
    model_discrepancy_sources: tuple[UncertaintySource, ...]
    target_fault_sensitivities: tuple[FaultSensitivity, ...]
    cross_sensitivities: tuple[str, ...]
    sensor_failure_modes: tuple[SensorFailureMode, ...]
    residual_fmea: tuple[ResidualFmeaEntry, ...]
    falsification_tests: tuple[str, ...]
    experiment_plan: ExperimentPlan
    recalibration_triggers: tuple[str, ...]
    invalidation_triggers: tuple[str, ...]
    instrumentation_gaps: tuple[str, ...]
    references: tuple[ResearchReference, ...]
    validation_evidence: tuple[ValidationEvidence, ...]
    major_blocker: str
    next_experiment: str

    @property
    def target_sensitivities(self) -> tuple[FaultSensitivity, ...]:
        return self.target_fault_sensitivities

    def __post_init__(self) -> None:
        if self.status is not RelationStatus.RUNTIME_RESEARCH:
            raise ValueError("PhysicsRelation must have RUNTIME_RESEARCH status")
        if _MATURITY_ORDER[self.evidence_maturity] >= _MATURITY_ORDER[EvidenceMaturity.BENCH_VALIDATED]:
            matching = [
                evidence for evidence in self.validation_evidence
                if _MATURITY_ORDER[evidence.maturity] >= _MATURITY_ORDER[self.evidence_maturity]
                and evidence.independently_verified
                and evidence.artifact_reference.strip()
            ]
            if not matching:
                raise ValueError("BENCH_VALIDATED or higher requires independent validation evidence")
            machine_ids = {machine_id for evidence in matching for machine_id in evidence.machine_ids}
            if self.evidence_maturity is EvidenceMaturity.SINGLE_MACHINE_VALIDATED and not machine_ids:
                raise ValueError("SINGLE_MACHINE_VALIDATED requires a named machine")
            if _MATURITY_ORDER[self.evidence_maturity] >= _MATURITY_ORDER[EvidenceMaturity.MULTI_MACHINE_VALIDATED] and len(machine_ids) < 2:
                raise ValueError("MULTI_MACHINE_VALIDATED requires at least two machines")


@dataclass(frozen=True)
class ResearchCandidate:
    candidate_id: str
    family: str
    subsystem: str
    kind: RelationKind
    status: RelationStatus
    evidence_maturity: EvidenceMaturity
    description: str
    proposed_mechanism: str
    proposed_equation: str
    existing_channels: tuple[str, ...]
    missing_variables: tuple[str, ...]
    evidence_claims: tuple[EvidenceClaim, ...]
    measurement_requirements: tuple[MeasurementRequirement, ...]
    uncertainty_sources: tuple[UncertaintySource, ...]
    model_discrepancy_sources: tuple[UncertaintySource, ...]
    target_fault_sensitivities: tuple[FaultSensitivity, ...]
    sensor_failure_modes: tuple[SensorFailureMode, ...]
    residual_fmea: tuple[ResidualFmeaEntry, ...]
    decision_reason: str
    additional_instrumentation: tuple[str, ...]
    falsification_tests: tuple[str, ...]
    experiment_plan: ExperimentPlan
    recalibration_triggers: tuple[str, ...]
    invalidation_triggers: tuple[str, ...]
    major_blocker: str
    potential_value: str
    next_experiment: str
    references: tuple[ResearchReference, ...]

    @property
    def target_sensitivities(self) -> tuple[FaultSensitivity, ...]:
        return self.target_fault_sensitivities


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
    return residual[finite], speed[inside][finite], ~inside


def _current_speed_residual(signals: AlignedSignals, parameters: Mapping[str, float]) -> Mapping[str, float]:
    residual, _, _ = _raw_spindle_residuals(signals, parameters)
    if len(residual) < MINIMUM_RUNTIME_SAMPLES:
        return {}
    return {"spindle.electromechanical_load_residual_a.median": float(np.median(residual))}


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
    description="Exact-machine robust residual of reported spindle current conditioned on actual spindle speed.",
    equation="r_I = I_reported - (a_machine n_actual + b_machine), evaluated only inside the calibrated speed envelope",
    assumptions=("same exact machine and controller configuration", "healthy calibration data", "reported current meaning is stable", "operating conditions are represented by calibration", "no extrapolation"),
    kind=RelationKind.MACHINE_FITTED,
    status=RelationStatus.RUNTIME_RESEARCH,
    evidence_maturity=EvidenceMaturity.LITERATURE_SUPPORTED,
    output_name="spindle.electromechanical_load_residual_a.median",
    output_unit="A",
    mechanism="Under bounded drive/control conditions, extra spindle/cutting load may require extra motor current; the fitted relation removes first-order speed dependence.",
    validity_conditions=("wafer-saw family only", "exact machine used for calibration", "speed inside robust calibration limits", "same drive semantics/configuration", "sufficient aligned finite samples"),
    invalidity_conditions=("another family or machine", "outside calibrated speed", "controller/sensor change", "unknown commanded-versus-actual semantics", "unrepresented feed/depth/material regime"),
    confounders=("feed and cut depth", "blade/material state", "coolant", "drive efficiency/control", "temperature", "acceleration/transients"),
    calibration_requirements=("at least 20 healthy samples", "at least six speed levels", "robust speed span", "chronological block stability review", "separate held-out validation"),
    parameter_specs=SPINDLE_PARAMETERS,
    evidence_claims=(
        EvidenceClaim("spindle_current_as_load_proxy", "Spindle feedback current has been used as a cutting-load signal in a dicing-saw design.", ("dicing_monitor_patent",), "dicing-saw implementation", "Patent evidence is not validation or fault specificity."),
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
        UncertaintySource("omitted cutting state", UncertaintyCategory.MODEL_DISCREPANCY, "Feed, depth, material, blade, coolant, acceleration, and control behavior are omitted."),
        UncertaintySource("linear form", UncertaintyCategory.MODEL_DISCREPANCY, "Healthy current-speed behavior may be nonlinear or regime-dependent."),
    ),
    target_fault_sensitivities=(
        FaultSensitivity("added mechanical/cutting load", ResidualDirection.POSITIVE, EvidenceMaturity.LITERATURE_SUPPORTED, "Expected to require more reported motor current under stable speed-control semantics."),
        FaultSensitivity("blade wear or clogging", ResidualDirection.POSITIVE, EvidenceMaturity.HYPOTHESIS, "Could increase load, but direct repeatable station evidence is absent."),
    ),
    cross_sensitivities=("increased feed/depth", "material change", "coolant change", "acceleration", "drive/controller thermal state"),
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
        ResidualFmeaEntry("increased mechanical/cutting load", "current rises for comparable speed/context", "positive", ("feed/depth/material", "coolant", "acceleration"), "current positive bias or speed negative bias", False),
        ResidualFmeaEntry("drive efficiency/control change", "current-speed mapping shifts", "either direction", ("temperature", "firmware/gain"), "current scale drift", False),
    ),
    falsification_tests=("held-out residual still depends on speed/feed/depth", "controlled load does not produce repeatable expected direction", "sensor offset is indistinguishable from target degradation", "block parameters are unstable"),
    experiment_plan=SPINDLE_EXPERIMENT,
    recalibration_triggers=SPINDLE_EXPERIMENT.recalibration_triggers,
    invalidation_triggers=SPINDLE_EXPERIMENT.invalidation_triggers,
    instrumentation_gaps=("verified current semantics", "traceable speed/current calibration", "feed/depth/phase context", "reference load/force for validation"),
    references=(DICING_MONITOR_PATENT, DICING_DYNAMICS, DISCO_PRODUCT_LINE, MAXON_CONSTANTS, ISO_CONDITION_MONITORING, JCGM_UNCERTAINTY, JCGM_MONTE_CARLO, NASA_MODEL_STANDARD, NASA_MODEL_HANDBOOK, ASME_UNCERTAINTY, RAUE_IDENTIFIABILITY, BRYNJARSDOTTIR_OHAGAN, FRANK_DING_RESIDUAL),
    validation_evidence=(),
    major_blocker="No bench or machine study has established telemetry semantics, confounder robustness, target sensitivity, or sensor-fault discrimination.",
    next_experiment=SPINDLE_EXPERIMENT.objective,
)


PHYSICS_RELATIONS: tuple[PhysicsRelation, ...] = (SPINDLE_RELATION,)


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


RESEARCH_CANDIDATES: tuple[ResearchCandidate, ...] = (
    ResearchCandidate(
        "wafer_mount.roller_current_web_tension", "wafer_mount", "feed", RelationKind.SEMI_EMPIRICAL, RelationStatus.RESEARCH_ONLY, EvidenceMaturity.LITERATURE_SUPPORTED,
        "Motor-current/web-tension consistency relation for the wafer-mount feed.", "Drive torque and roller mechanics contribute to web tension, but acceleration, radius, transmission, friction, and span dynamics matter.", "T_web = f(K_t I, radii, inertia, acceleration, friction, span dynamics)",
        ("roller_motor_current", "web_tension", "roller_temperature"), ("speed/acceleration", "torque/current semantics", "roller geometry", "transmission", "phase"),
        (EvidenceClaim("web_dynamics", "Web tension depends on roller dynamics and nonideal roller behavior.", ("branca_2013_web_tension", "maxon_motor_constants"), "web handling", "Not wafer-mount validation."),),
        (_measurement("roller_motor_current", "drive current/torque feedback", "A", "actual feedback basis and controller scaling"), _measurement("web_tension", "tape/web tension", "N", "sensor location, direction, span, and calibration"), _measurement("roller_speed", "roller speed/acceleration", "rad/s", "actual shaft motion", missing=True)),
        _uncertainties("current scaling", "tension calibration", "alignment"), _discrepancies("friction", "span elasticity", "roller inertia"),
        (FaultSensitivity("roller/feed drag", ResidualDirection.UNKNOWN, EvidenceMaturity.HYPOTHESIS, "Could change current at comparable measured tension."),),
        (SensorFailureMode("web_tension", "zero/scale drift", "apparent current-tension inconsistency", True),),
        (ResidualFmeaEntry("feed drag", "current increases", "condition dependent", ("acceleration", "temperature"), "current/tension bias", False),),
        "Direct tension exists, but mechanical and phase semantics are absent; a generic regression would not be a controlled torque balance.",
        ("encoder/phase", "verified torque feedback", "roller geometry/configuration"), WEB_EXPERIMENT.rejection_criteria, WEB_EXPERIMENT,
        WEB_EXPERIMENT.recalibration_triggers, WEB_EXPERIMENT.invalidation_triggers,
        "Missing motion phase, geometry, and verified current/torque semantics.", "Could provide analytical redundancy for a direct tension sensor.", WEB_EXPERIMENT.objective,
        (BRANCA_WEB, MAXON_CONSTANTS, ISO_CONDITION_MONITORING),
    ),
    ResearchCandidate(
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
    ),
    ResearchCandidate(
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
    ),
    ResearchCandidate(
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
    ),
    ResearchCandidate(
        "molding.clamp_cavity_force_balance", "molding", "hydraulic", RelationKind.SEMI_EMPIRICAL, RelationStatus.RESEARCH_ONLY, EvidenceMaturity.LITERATURE_SUPPORTED,
        "Phase-resolved actual clamp-force versus cavity-pressure balance.", "Cavity pressure over projected area contributes force that the clamp system must oppose.", "F_required(t)=p_cavity(t)A_projected plus characterized dynamics/losses",
        ("cavity_pressure", "clamp_pressure", "transfer_motor_current", "mold_temperature", "plunger_position_error"), ("actual clamp force", "projected area", "phase/position", "material/cure state"),
        (EvidenceClaim("mold_instrumentation", "Transfer-mold research uses cavity pressure, temperature, and cure/process context.", ("kahle_2016_transfer_molding",), "electronic packaging transfer molding", "Does not justify treating hydraulic pressure as clamp force."),),
        (_measurement("cavity_pressure", "cavity pressure at named sensor", "MPa", "location, phase, response"), _measurement("clamp_force", "actual clamp force", "N", "direct force measurement", missing=True), _measurement("projected_area", "approved projected cavity/runner area", "m^2", "configuration identity", missing=True)),
        _uncertainties("pressure", "force", "temperature/alignment"), _discrepancies("hydraulic losses", "resin rheology/cure", "cavity distribution"),
        (FaultSensitivity("insufficient clamp force", ResidualDirection.NEGATIVE, EvidenceMaturity.HYPOTHESIS, "Actual clamp force may fall below the phase-specific required force."),),
        (SensorFailureMode("cavity_pressure", "positive bias", "false force deficit", True),),
        (ResidualFmeaEntry("clamp deficit", "lower force relative to cavity pressure", "negative margin", ("area", "material/phase"), "pressure/force bias", False),),
        "Hydraulic pressure is not actual clamp force and the necessary geometry/phase/material context is absent.",
        ("actual force sensor", "approved projected area", "phase/position", "material/cure context"), MOLD_EXPERIMENT.rejection_criteria, MOLD_EXPERIMENT,
        MOLD_EXPERIMENT.recalibration_triggers, MOLD_EXPERIMENT.invalidation_triggers,
        "No actual clamp-force measurand or approved geometry context.", "Could expose force-margin consistency during controlled molding research.", MOLD_EXPERIMENT.objective,
        (MOLDING_MONITOR, MOLDING_PROCESS, ISO_CONDITION_MONITORING),
    ),
    ResearchCandidate(
        "marking.laser_output_drive_temperature", "marking", "optical", RelationKind.MACHINE_FITTED, RelationStatus.RESEARCH_ONLY, EvidenceMaturity.LITERATURE_SUPPORTED,
        "Delivered optical power consistency with drive, temperature, pulse, and controller state.", "Laser output can depend on drive and temperature, but the form is architecture/control-specific.", "P_delivered=f_machine(I_drive,T,pulse/duty,controller,optical path)",
        ("delivered_laser_power", "laser_drive_current", "laser_temperature"), ("laser architecture", "junction-temperature proxy", "pulse/duty/Q-switch state", "feedback state", "reference power"),
        (EvidenceClaim("laser_direct_monitoring", "Commercial marker/laser systems use direct power and equipment-specific monitoring for maintenance.", ("keyence_laser_power_monitor", "trumpf_laser_monitoring"), "vendor-specific laser systems", "Does not define a transferable equation or this channel's semantics."),),
        (_measurement("delivered_laser_power", "delivered optical power at defined plane", "W", "sensor type, spectral response, sampling point"), _measurement("laser_drive_current", "architecture-specific drive current", "A", "current path and control mode"), _measurement("pulse_state", "pulse energy/duty/controller state", "state", "cycle aligned", missing=True)),
        _uncertainties("power calibration", "current", "temperature"), _discrepancies("architecture/control", "optical-path loss", "pulse dynamics"),
        (FaultSensitivity("source or optical-path degradation", ResidualDirection.NEGATIVE, EvidenceMaturity.HYPOTHESIS, "Delivered power may fall at comparable commanded/thermal state."),),
        (SensorFailureMode("delivered_laser_power", "negative gain drift or contamination", "false degradation", True),),
        (ResidualFmeaEntry("optical/source degradation", "power falls", "negative", ("controller", "temperature", "path contamination"), "power-sensor drift", False),),
        "Actual laser architecture, control state, pulse semantics, and calibrated output plane are unknown.",
        ("architecture/OEM review", "calibrated optical reference", "pulse/controller state"), LASER_EXPERIMENT.rejection_criteria, LASER_EXPERIMENT,
        LASER_EXPERIMENT.recalibration_triggers, LASER_EXPERIMENT.invalidation_triggers,
        "No verified architecture-specific measurement model.", "Could detect output consistency loss once direct measurement is metrologically defined.", LASER_EXPERIMENT.objective,
        (KEYENCE_POWER_MONITOR, TRUMPF_CONDITION_MONITORING, LASER_OUTPUT_MODEL, JCGM_UNCERTAINTY),
    ),
    ResearchCandidate(
        "trim_form.motor_current_punch_force", "trim_form", "press", RelationKind.SEMI_EMPIRICAL, RelationStatus.RESEARCH_ONLY, EvidenceMaturity.LITERATURE_SUPPORTED,
        "Stroke-resolved drive-torque to punch-force consistency.", "Motor current can map to torque, then linkage/transmission and phase map torque to force after dynamics/losses.", "F(θ)=K_t I G mechanical_advantage(θ)-inertia/friction",
        ("punch_force", "press_motor_current", "die_vibration", "die_temperature"), ("torque constant", "transmission/linkage", "stroke phase", "acceleration", "loss model"),
        (EvidenceClaim("motor_to_force", "Motor current can map to torque but force requires the intervening mechanism and state.", ("maxon_motor_constants",), "motor mechanics", "No press-specific parameters are available."),),
        (_measurement("punch_force", "actual punch force", "kN", "load-cell location and dynamic calibration"), _measurement("press_motor_current", "actual drive current/torque feedback", "A", "feedback definition and phase"), _measurement("stroke_phase", "press angle/position/acceleration", "rad", "encoder-derived actual state", missing=True)),
        _uncertainties("force", "current", "phase/alignment"), _discrepancies("linkage/inertia", "friction", "tool/material effects"),
        (FaultSensitivity("tool wear/damage", ResidualDirection.UNKNOWN, EvidenceMaturity.HYPOTHESIS, "May change phase-specific force/current relationship."),),
        (SensorFailureMode("punch_force", "gain drift", "false consistency change", True),),
        (ResidualFmeaEntry("tool condition change", "force/current waveform changes", "condition dependent", ("material", "phase", "friction"), "force/current gain drift", False),),
        "Current and force cannot be related without stroke phase, mechanism, and dynamic terms.",
        ("stroke encoder", "verified torque feedback", "mechanism configuration", "high-rate alignment"), PRESS_EXPERIMENT.rejection_criteria, PRESS_EXPERIMENT,
        PRESS_EXPERIMENT.recalibration_triggers, PRESS_EXPERIMENT.invalidation_triggers,
        "Missing phase-resolved mechanism and drive semantics.", "Could provide redundant tooling/load evidence after a controlled mechanics study.", PRESS_EXPERIMENT.objective,
        (MAXON_CONSTANTS, ISO_CONDITION_MONITORING),
    ),
    ResearchCandidate(
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
    ),
    ResearchCandidate(
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
    ),
)


ALL_MACHINE_FAMILIES: tuple[str, ...] = (
    "wafer_mount", "wafer_saw", "die_attach", "wire_bond", "molding",
    "marking", "trim_form", "singulation", "final_test",
)


def relations_for_family(family: str) -> tuple[PhysicsRelation, ...]:
    """Return runtime research relations only; Step 03 depends on this gate."""

    return tuple(relation for relation in PHYSICS_RELATIONS if relation.status is RelationStatus.RUNTIME_RESEARCH and family in relation.machine_families)


def research_catalog_for_family(family: str) -> tuple[PhysicsRelation | ResearchCandidate, ...]:
    runtime = relations_for_family(family)
    candidates = tuple(candidate for candidate in RESEARCH_CANDIDATES if candidate.family == family)
    return runtime + candidates


def _autocorrelation(values: np.ndarray, lag: int) -> float | None:
    if len(values) <= lag or float(np.std(values[:-lag])) == 0.0 or float(np.std(values[lag:])) == 0.0:
        return None
    result = float(np.corrcoef(values[:-lag], values[lag:])[0, 1])
    return result if np.isfinite(result) else None


def residual_diagnostics(
    residuals: np.ndarray,
    conditioning: np.ndarray | None = None,
    outside_envelope: np.ndarray | None = None,
) -> ResidualDiagnostics:
    """Deterministic residual structure checks; these are not release scores."""

    raw = np.asarray(residuals, dtype=float).reshape(-1)
    finite_mask = np.isfinite(raw)
    values = raw[finite_mask]
    finite_fraction = float(np.mean(finite_mask)) if len(raw) else 0.0
    outside_fraction = float(np.mean(np.asarray(outside_envelope, dtype=bool))) if outside_envelope is not None and len(outside_envelope) else 0.0
    if not len(values):
        nan = float("nan")
        return ResidualDiagnostics(0, finite_fraction, nan, nan, nan, None, None, None, outside_fraction)
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    split = len(values) // 2
    drift = float(np.median(values[split:]) - np.median(values[:split])) if split else 0.0
    slope: float | None = None
    if conditioning is not None:
        condition = np.asarray(conditioning, dtype=float).reshape(-1)
        if len(condition) == len(raw):
            x = condition[finite_mask]
            valid = np.isfinite(x)
            x, y = x[valid], values[valid]
            if len(x) >= 3 and float(np.ptp(x)) > 0.0:
                slope_value = float(np.polyfit(x, y, 1)[0])
                slope = slope_value if np.isfinite(slope_value) else None
    correlations = [value for lag in range(1, min(10, len(values) // 4) + 1) if (value := _autocorrelation(values, lag)) is not None]
    lag1 = _autocorrelation(values, 1)
    maximum = max((abs(value) for value in correlations), default=None)
    return ResidualDiagnostics(len(values), finite_fraction, median, mad, drift, slope, lag1, maximum, outside_fraction)


def _block_parameter_stability(signals: AlignedSignals, blocks: int = 3) -> ParameterStabilityDiagnostics:
    speed, current = _finite_pair(signals, "spindle_speed", "spindle_current")
    if blocks < 2 or len(speed) < blocks * MINIMUM_SPINDLE_FIT_SAMPLES:
        return ParameterStabilityDiagnostics(False, blocks, (), ("Insufficient samples for chronological block fits.",))
    fitted: list[Mapping[str, float]] = []
    for indices in np.array_split(np.arange(len(speed)), blocks):
        try:
            fitted.append(_fit_current_speed({"spindle_speed": speed[indices], "spindle_current": current[indices]}))
        except ValueError as exc:
            return ParameterStabilityDiagnostics(False, blocks, (), (f"Block calibration failed: {exc}",))
    relative_ranges: list[tuple[str, float]] = []
    for name in (SLOPE, INTERCEPT, RESIDUAL_SCALE):
        values = np.asarray([item[name] for item in fitted])
        denominator = max(abs(float(np.median(values))), 1e-12)
        relative_ranges.append((name, float(np.ptp(values)) / denominator))
    return ParameterStabilityDiagnostics(True, blocks, tuple(relative_ranges), ("Chronological deterministic blocks; no bootstrap inference.",))


def calibrate_relation(relation_id: str, signals: AlignedSignals, *, blocks: int = 3) -> CalibrationReport:
    relation = next((item for item in PHYSICS_RELATIONS if item.relation_id == relation_id), None)
    if relation is None or relation.fit is None:
        raise ValueError(f"No fitted runtime relation {relation_id!r}")
    parameters = dict(relation.fit(signals))
    residual, speed, outside = _raw_spindle_residuals(signals, parameters)
    diagnostics = residual_diagnostics(residual, speed, outside)
    stability = _block_parameter_stability(signals, blocks)
    blockers: list[str] = []
    if not stability.assessable:
        blockers.append("Parameter stability is not assessable across chronological blocks.")
    envelope = ApplicabilityEnvelope(
        (("spindle_speed", parameters[SPEED_LOW], parameters[SPEED_HIGH], "RPM"),),
        ("exact machine used for calibration", "unchanged controller/current semantics", "represented healthy cutting regimes"),
        ("Evaluation outside the speed range is refused, not extrapolated.", "Other operating variables remain unbounded until measured."),
    )
    return CalibrationReport(
        relation_id=relation_id,
        parameters=tuple(parameters.items()),
        sample_count=diagnostics.sample_count,
        excitation_summary=(("speed_low_rpm", parameters[SPEED_LOW]), ("speed_high_rpm", parameters[SPEED_HIGH]), ("speed_span_rpm", parameters[SPEED_SPAN])),
        applicability_envelope=envelope,
        calibration_diagnostics=diagnostics,
        parameter_stability=stability,
        blockers=tuple(blockers),
        valid=diagnostics.sample_count >= MINIMUM_RUNTIME_SAMPLES and stability.assessable,
    )


def validate_relation_calibration(
    relation_id: str,
    calibration_signals: AlignedSignals,
    validation_signals: AlignedSignals,
) -> ValidationDiagnostics:
    """Fit calibration data and report diagnostics on separately supplied data."""

    report = calibrate_relation(relation_id, calibration_signals)
    parameters = dict(report.parameters)
    relation = next(item for item in PHYSICS_RELATIONS if item.relation_id == relation_id)
    shared = calibration_signals is validation_signals
    for channel in relation.required_channels:
        if channel in calibration_signals and channel in validation_signals:
            shared = shared or bool(np.shares_memory(np.asarray(calibration_signals[channel]), np.asarray(validation_signals[channel])))
    residual, speed, outside = _raw_spindle_residuals(validation_signals, parameters)
    diagnostics = residual_diagnostics(residual, speed, outside)
    blockers = list(report.blockers)
    if shared:
        blockers.append("Validation data share identity or memory with calibration data.")
    if diagnostics.sample_count < MINIMUM_RUNTIME_SAMPLES:
        blockers.append("Too few held-out observations fall inside the applicability envelope.")
    return ValidationDiagnostics(
        relation_id, report, diagnostics, not shared,
        "Separate objects with non-shared array memory were supplied." if not shared else "Shared or non-independent data were detected; this is not independent validation.",
        tuple(blockers),
    )


def propagate_linearized_uncertainty(jacobian: np.ndarray, covariance: np.ndarray) -> float:
    """Return sqrt(J Σ Jᵀ) for one scalar output; no distributions are invented."""

    j = np.asarray(jacobian, dtype=float).reshape(1, -1)
    sigma = np.asarray(covariance, dtype=float)
    if sigma.shape != (j.shape[1], j.shape[1]):
        raise ValueError("Covariance dimensions must match the Jacobian")
    if not bool(np.all(np.isfinite(j))) or not bool(np.all(np.isfinite(sigma))):
        raise ValueError("Jacobian and covariance must be finite")
    if not bool(np.allclose(sigma, sigma.T, rtol=1e-10, atol=1e-12)):
        raise ValueError("Covariance must be symmetric")
    eigenvalues = np.linalg.eigvalsh(sigma)
    if float(np.min(eigenvalues)) < -1e-12:
        raise ValueError("Covariance must be positive semidefinite")
    variance = float((j @ sigma @ j.T).item())
    if variance < -1e-12:
        raise ValueError("Propagated variance cannot be negative")
    return float(np.sqrt(max(variance, 0.0)))


def physics_readiness_report() -> tuple[PhysicsReadinessEntry, ...]:
    entries: list[PhysicsReadinessEntry] = []
    for relation in PHYSICS_RELATIONS:
        entries.append(PhysicsReadinessEntry(
            relation.relation_id, ",".join(sorted(relation.machine_families)),
            relation.status, relation.evidence_maturity,
            tuple((item.channel, item.status) for item in relation.measurement_requirements),
            "Exact-machine offline fit available" if relation.fit is not None else "No calibration fit",
            bool(relation.validation_evidence), relation.major_blocker, relation.next_experiment,
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
