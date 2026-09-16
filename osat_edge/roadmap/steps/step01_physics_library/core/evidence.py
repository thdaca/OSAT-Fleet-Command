"""Generic evidence constructors, readiness reporting, and Step01 audits."""

from __future__ import annotations

from .references import RESEARCH_REFERENCES
from .schema import (
    EvidenceMaturity,
    ExperimentPlan,
    MeasurementRequirement,
    MeasurementStatus,
    PhysicsReadinessEntry,
    RelationStatus,
    UncertaintyCategory,
    UncertaintySource,
    _MATURITY_ORDER,
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
