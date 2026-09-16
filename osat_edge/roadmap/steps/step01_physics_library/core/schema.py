"""Data contracts for auditable Step01 physical-relation research."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Mapping

import numpy as np


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


class ResearchEvidenceTier(str, Enum):
    """Research-source access tier; deliberately separate from ``DataOrigin``.

    These labels describe what evidence exists or may be requested.  They do
    not authorize runtime ingestion, health scoring, or an OSAT provenance
    claim for any bytes.
    """

    PUBLISHED_REAL_OSAT_STUDY = "PUBLISHED_REAL_OSAT_STUDY"
    REQUESTABLE_REAL_OSAT_DATA = "REQUESTABLE_REAL_OSAT_DATA"
    EXECUTED_REAL_OSAT_DATA = "EXECUTED_REAL_OSAT_DATA"


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
    ACADEMIC_THESIS = "ACADEMIC_THESIS"
    DATASET_REPOSITORY = "DATASET_REPOSITORY"
    CORPORATE_REPORT = "CORPORATE_REPORT"


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

    def __post_init__(self) -> None:
        maturity = _MATURITY_ORDER[self.maturity]
        machines = {machine_id.strip() for machine_id in self.machine_ids if machine_id.strip()}
        if maturity >= _MATURITY_ORDER[EvidenceMaturity.SINGLE_MACHINE_VALIDATED] and not machines:
            raise ValueError("SINGLE_MACHINE_VALIDATED evidence requires at least one machine ID")
        if maturity >= _MATURITY_ORDER[EvidenceMaturity.MULTI_MACHINE_VALIDATED] and len(machines) < 2:
            raise ValueError("MULTI_MACHINE_VALIDATED evidence requires at least two distinct machine IDs")
        if maturity >= _MATURITY_ORDER[EvidenceMaturity.BENCH_VALIDATED]:
            if not self.artifact_reference.strip():
                raise ValueError("Physical-validation evidence requires an artifact/reference identifier")
            if not self.independently_verified:
                raise ValueError("Physical-validation evidence requires independent verification")


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
        if _MATURITY_ORDER[self.evidence_maturity] >= _MATURITY_ORDER[EvidenceMaturity.MEASUREMENT_SEMANTICS_VERIFIED]:
            if any(
                requirement.current_schema_status
                is not MeasurementStatus.AVAILABLE_AND_SEMANTICALLY_SUPPORTED
                for requirement in self.measurement_requirements
            ):
                raise ValueError(
                    "MEASUREMENT_SEMANTICS_VERIFIED requires semantically supported required measurements"
                )
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
