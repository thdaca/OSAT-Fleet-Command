from __future__ import annotations

from dataclasses import replace
import unittest

import numpy as np

from osat_edge.roadmap.steps.step01_physics_library.step01_physics_library import (
    ALL_MACHINE_FAMILIES,
    INTERCEPT,
    PHYSICS_RELATIONS,
    RESEARCH_CANDIDATES,
    RESEARCH_REFERENCES,
    RESIDUAL_SCALE,
    SLOPE,
    SPEED_HIGH,
    SPEED_LOW,
    SPEED_SPAN,
    EvidenceMaturity,
    MeasurementStatus,
    PhysicsRelation,
    ReferenceType,
    RelationStatus,
    ResearchCandidate,
    UncertaintyCategory,
    ValidationEvidence,
    audit_physics_library,
    calibrate_relation,
    contact_resistance_mohm_for_research,
    physics_readiness_report,
    propagate_linearized_uncertainty,
    relations_for_family,
    research_catalog_for_family,
    residual_diagnostics,
    validate_relation_calibration,
)
from osat_edge.roadmap.steps.step03_physical_residuals.step03_physical_residuals import (
    calculate_physical_residuals,
    fit_relation_parameters,
)
from osat_edge.roadmap.pre_steps.pre01_common.tests.support import window


def relation(relation_id: str = "spindle.current_speed_residual") -> PhysicsRelation:
    return next(item for item in PHYSICS_RELATIONS if item.relation_id == relation_id)


def healthy_signals(count: int = 240) -> dict[str, np.ndarray]:
    speed = np.linspace(18_000.0, 24_000.0, count)
    current = 1.25 + 0.00018 * speed
    return {"spindle_speed": speed, "spindle_current": current}


class LibraryCredibilityTests(unittest.TestCase):
    def test_internal_audit_passes(self) -> None:
        self.assertEqual((), audit_physics_library())

    def test_ids_and_reference_keys_are_unique(self) -> None:
        relation_ids = [item.relation_id for item in PHYSICS_RELATIONS]
        candidate_ids = [item.candidate_id for item in RESEARCH_CANDIDATES]
        reference_keys = [item.key for item in RESEARCH_REFERENCES]
        self.assertEqual(len(relation_ids), len(set(relation_ids)))
        self.assertEqual(len(candidate_ids), len(set(candidate_ids)))
        self.assertEqual(len(reference_keys), len(set(reference_keys)))
        self.assertTrue(set(relation_ids).isdisjoint(candidate_ids))

    def test_only_wafer_saw_spindle_is_runtime_active(self) -> None:
        self.assertEqual(1, len(PHYSICS_RELATIONS))
        self.assertEqual((relation(),), relations_for_family("wafer_saw"))
        for family in set(ALL_MACHINE_FAMILIES) - {"wafer_saw"}:
            self.assertEqual((), relations_for_family(family))

    def test_runtime_record_is_research_and_not_physically_validated(self) -> None:
        item = relation()
        self.assertIs(RelationStatus.RUNTIME_RESEARCH, item.status)
        self.assertIs(EvidenceMaturity.LITERATURE_SUPPORTED, item.evidence_maturity)
        self.assertEqual((), item.validation_evidence)

    def test_impossible_maturity_advancement_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "semantically supported"):
            replace(relation(), evidence_maturity=EvidenceMaturity.BENCH_VALIDATED)

    def test_multi_machine_maturity_requires_more_than_one_machine(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least two distinct machine IDs"):
            ValidationEvidence(
                "one-machine", EvidenceMaturity.MULTI_MACHINE_VALIDATED,
                ("WS-REAL-01",), "controlled-study-artifact", True,
                "Synthetic metadata used only to exercise consistency checks.",
            )

    def test_physical_validation_evidence_requires_artifact_and_independence(self) -> None:
        with self.assertRaisesRegex(ValueError, "artifact"):
            ValidationEvidence(
                "bench", EvidenceMaturity.BENCH_VALIDATED, (), "", True, "test"
            )
        with self.assertRaisesRegex(ValueError, "independent"):
            ValidationEvidence(
                "bench", EvidenceMaturity.BENCH_VALIDATED, (), "artifact", False, "test"
            )

    def test_single_machine_maturity_requires_named_machine(self) -> None:
        with self.assertRaisesRegex(ValueError, "machine ID"):
            ValidationEvidence(
                "single", EvidenceMaturity.SINGLE_MACHINE_VALIDATED,
                (), "artifact", True, "test",
            )

    def test_every_family_has_a_research_catalog(self) -> None:
        self.assertEqual(9, len(ALL_MACHINE_FAMILIES))
        for family in ALL_MACHINE_FAMILIES:
            with self.subTest(family=family):
                self.assertTrue(research_catalog_for_family(family))

    def test_runtime_relation_has_full_credibility_record(self) -> None:
        item = relation()
        for value in (
            item.evidence_claims,
            item.measurement_requirements,
            item.parameter_specs,
            item.measurement_uncertainty_sources,
            item.model_discrepancy_sources,
            item.target_fault_sensitivities,
            item.sensor_failure_modes,
            item.residual_fmea,
            item.falsification_tests,
            item.recalibration_triggers,
            item.invalidation_triggers,
            item.references,
        ):
            self.assertTrue(value)

    def test_every_fitted_parameter_has_exact_parameter_spec(self) -> None:
        self.assertEqual(
            {SLOPE, INTERCEPT, RESIDUAL_SCALE, SPEED_SPAN, SPEED_LOW, SPEED_HIGH},
            {item.name for item in relation().parameter_specs},
        )

    def test_measurement_uncertainty_and_model_discrepancy_are_separate(self) -> None:
        item = relation()
        self.assertTrue(all(source.category is not UncertaintyCategory.MODEL_DISCREPANCY for source in item.measurement_uncertainty_sources))
        self.assertTrue(all(source.category is UncertaintyCategory.MODEL_DISCREPANCY for source in item.model_discrepancy_sources))

    def test_references_are_typed_and_scope_limited(self) -> None:
        for item in RESEARCH_REFERENCES:
            with self.subTest(reference=item.key):
                self.assertIsInstance(item.reference_type, ReferenceType)
                self.assertTrue(item.identifier)
                self.assertTrue(item.supports)
                self.assertTrue(item.scope_limitations)

    def test_readiness_report_has_one_entry_per_record(self) -> None:
        report = physics_readiness_report()
        self.assertEqual(len(PHYSICS_RELATIONS) + len(RESEARCH_CANDIDATES), len(report))
        self.assertTrue(all(item.major_blocker and item.next_experiment for item in report))
        spindle = next(item for item in report if item.item_id == relation().relation_id)
        self.assertFalse(spindle.validation_evidence_available)

    def test_candidates_have_detailed_experiment_and_failure_records(self) -> None:
        for item in RESEARCH_CANDIDATES:
            with self.subTest(candidate=item.candidate_id):
                self.assertTrue(item.experiment_plan.negative_controls)
                self.assertTrue(item.experiment_plan.design_of_experiments)
                self.assertTrue(item.experiment_plan.calibration_data)
                self.assertTrue(item.experiment_plan.validation_data)
                self.assertTrue(item.experiment_plan.acceptance_criteria)
                self.assertTrue(item.experiment_plan.rejection_criteria)
                self.assertTrue(item.experiment_plan.reference_instrument)
                self.assertTrue(item.experiment_plan.swept_variables)
                self.assertTrue(item.experiment_plan.sample_repetition_strategy)
                self.assertTrue(item.experiment_plan.sensor_fault_challenge)
                self.assertEqual(9, len(item.experiment_plan.validation_stages))
                self.assertTrue(item.experiment_plan.data_to_archive)
                self.assertTrue(item.sensor_failure_modes)
                self.assertTrue(item.residual_fmea)
                self.assertTrue(item.potential_value)

    def test_candidate_records_never_leak_into_runtime(self) -> None:
        runtime_ids = {item.relation_id for family in ALL_MACHINE_FAMILIES for item in relations_for_family(family)}
        self.assertTrue(runtime_ids.isdisjoint(item.candidate_id for item in RESEARCH_CANDIDATES))
        self.assertTrue(all(item.status is not RelationStatus.RUNTIME_RESEARCH for item in RESEARCH_CANDIDATES))

    def test_contact_resistance_is_demoted_for_unverified_semantics(self) -> None:
        item = next(candidate for candidate in RESEARCH_CANDIDATES if candidate.candidate_id == "final_test.contact_resistance")
        self.assertIs(RelationStatus.RESEARCH_ONLY, item.status)
        self.assertIn("Kelvin", item.decision_reason)
        self.assertTrue(all(requirement.status is not MeasurementStatus.AVAILABLE_AND_SEMANTICALLY_SUPPORTED for requirement in item.measurement_requirements))
        self.assertEqual((), relations_for_family("final_test"))

    def test_singulation_spindle_is_not_transferred_from_wafer_saw(self) -> None:
        item = next(candidate for candidate in RESEARCH_CANDIDATES if candidate.candidate_id.startswith("singulation.spindle"))
        self.assertIs(RelationStatus.RESEARCH_ONLY, item.status)
        self.assertIn("transfer", item.major_blocker.lower())
        self.assertEqual((), relations_for_family("singulation"))

    def test_wire_vacuum_and_molding_shortcuts_are_not_runtime(self) -> None:
        for family, prefix in (
            ("wire_bond", "wire_bond.ultrasonic"),
            ("die_attach", "die_attach.nozzle"),
            ("molding", "molding.clamp"),
        ):
            with self.subTest(family=family):
                self.assertEqual((), relations_for_family(family))
                self.assertTrue(any(candidate.candidate_id.startswith(prefix) for candidate in RESEARCH_CANDIDATES))

    def test_iso_20816_is_scope_evidence_not_a_runtime_alarm(self) -> None:
        scope = next(reference for reference in RESEARCH_REFERENCES if reference.key == "iso_20816_3_2022")
        self.assertIn("15 kW", scope.scope_limitations)
        self.assertIn("60 000", scope.scope_limitations)
        self.assertNotIn("20816", relation().equation)

    def test_software_outputs_are_residuals_not_probabilities(self) -> None:
        self.assertIn("residual", relation().output_name)
        self.assertNotIn("probability", relation().output_name)

    def test_active_measurements_explicitly_leave_metrology_unknown(self) -> None:
        for requirement in relation().measurement_requirements:
            self.assertEqual("UNKNOWN", requirement.calibration_state)
            self.assertEqual("NOT_QUANTIFIED", requirement.uncertainty_state)
            self.assertEqual("NOT_ESTABLISHED", requirement.traceability_state)
            self.assertIs(MeasurementStatus.AVAILABLE_BUT_SEMANTICS_UNVERIFIED, requirement.current_schema_status)


class SpindleCalibrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.item = relation()
        self.assertIsNotNone(self.item.fit)

    def test_known_healthy_relation_is_recovered(self) -> None:
        parameters = self.item.fit(healthy_signals())  # type: ignore[misc]
        self.assertAlmostEqual(0.00018, parameters[SLOPE], places=7)
        self.assertAlmostEqual(1.25, parameters[INTERCEPT], places=3)
        self.assertGreater(parameters[RESIDUAL_SCALE], 0.0)

    def test_robust_fit_resists_current_outliers(self) -> None:
        signals = healthy_signals()
        signals["spindle_current"][::19] += 12.0
        parameters = self.item.fit(signals)  # type: ignore[misc]
        self.assertAlmostEqual(0.00018, parameters[SLOPE], places=6)
        self.assertAlmostEqual(1.25, parameters[INTERCEPT], places=2)

    def test_fit_is_order_invariant(self) -> None:
        signals = healthy_signals()
        permutation = np.random.default_rng(5).permutation(len(signals["spindle_speed"]))
        first = self.item.fit(signals)  # type: ignore[misc]
        second = self.item.fit({key: value[permutation] for key, value in signals.items()})  # type: ignore[misc]
        for name in (SLOPE, INTERCEPT, RESIDUAL_SCALE, SPEED_LOW, SPEED_HIGH):
            self.assertAlmostEqual(first[name], second[name], places=8)

    def test_too_few_samples_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "At least 20"):
            self.item.fit(healthy_signals(19))  # type: ignore[misc]

    def test_too_few_distinct_speed_levels_are_rejected(self) -> None:
        speed = np.repeat(np.arange(5, dtype=float) + 20_000.0, 10)
        with self.assertRaisesRegex(ValueError, "distinct speed"):
            self.item.fit({"spindle_speed": speed, "spindle_current": 2.0 + speed * 0.0002})  # type: ignore[misc]

    def test_insufficient_speed_span_is_rejected(self) -> None:
        speed = np.linspace(20_000.0, 20_050.0, 60)
        with self.assertRaisesRegex(ValueError, "span"):
            self.item.fit({"spindle_speed": speed, "spindle_current": 1.0 + speed * 0.0002})  # type: ignore[misc]

    def test_fit_records_robust_applicability_envelope(self) -> None:
        signals = healthy_signals()
        parameters = self.item.fit(signals)  # type: ignore[misc]
        self.assertAlmostEqual(np.percentile(signals["spindle_speed"], 2.5), parameters[SPEED_LOW])
        self.assertAlmostEqual(np.percentile(signals["spindle_speed"], 97.5), parameters[SPEED_HIGH])
        self.assertAlmostEqual(parameters[SPEED_HIGH] - parameters[SPEED_LOW], parameters[SPEED_SPAN])

    def test_in_domain_added_current_has_positive_direction(self) -> None:
        signals = healthy_signals()
        parameters = self.item.fit(signals)  # type: ignore[misc]
        output = self.item.compute({"spindle_speed": signals["spindle_speed"], "spindle_current": signals["spindle_current"] + 0.4}, parameters)
        self.assertAlmostEqual(0.4, output[self.item.output_name], places=3)

    def test_outside_envelope_is_refused_without_extrapolation(self) -> None:
        parameters = self.item.fit(healthy_signals())  # type: ignore[misc]
        speed = np.linspace(50_000.0, 60_000.0, 30)
        output = self.item.compute({"spindle_speed": speed, "spindle_current": 1.25 + 0.00018 * speed}, parameters)
        self.assertEqual({}, output)

    def test_exact_20k_to_40k_calibration_refuses_60k(self) -> None:
        speed = np.linspace(20_000.0, 40_000.0, 200)
        parameters = self.item.fit({"spindle_speed": speed, "spindle_current": 2.0 + speed * 0.0001})  # type: ignore[misc]
        test_speed = np.full(8, 60_000.0)
        self.assertEqual({}, self.item.compute({"spindle_speed": test_speed, "spindle_current": 2.0 + test_speed * 0.0001}, parameters))

    def test_mixed_domain_evaluation_uses_only_in_domain_samples(self) -> None:
        signals = healthy_signals()
        parameters = self.item.fit(signals)  # type: ignore[misc]
        speed = np.array([19_000.0, 20_000.0, 21_000.0, 22_000.0, 60_000.0])
        current = 1.25 + 0.00018 * speed + np.array([0.2, 0.2, 0.2, 0.2, 100.0])
        output = self.item.compute({"spindle_speed": speed, "spindle_current": current}, parameters)
        self.assertAlmostEqual(0.2, output[self.item.output_name], places=3)

    def test_missing_or_invalid_envelope_parameters_refuse_output(self) -> None:
        signals = healthy_signals(30)
        self.assertEqual({}, self.item.compute(signals, {SLOPE: 0.1, INTERCEPT: 1.0}))
        invalid = {SLOPE: 0.1, INTERCEPT: 1.0, SPEED_LOW: 10.0, SPEED_HIGH: 5.0}
        self.assertEqual({}, self.item.compute(signals, invalid))

    def test_nonfinite_extreme_data_never_emit_a_fake_number(self) -> None:
        parameters = self.item.fit(healthy_signals())  # type: ignore[misc]
        output = self.item.compute({"spindle_speed": np.array([np.nan, np.inf, 1e308]), "spindle_current": np.array([1.0, 1e308, 1e308])}, parameters)
        self.assertEqual({}, output)

    def test_extreme_finite_current_is_rejected_as_numerically_implausible(self) -> None:
        parameters = self.item.fit(healthy_signals())  # type: ignore[misc]
        speed = np.full(8, 21_000.0)
        self.assertEqual({}, self.item.compute({"spindle_speed": speed, "spindle_current": np.full(8, 1e200)}, parameters))

    def test_negative_current_sign_error_is_rejected(self) -> None:
        parameters = self.item.fit(healthy_signals())  # type: ignore[misc]
        self.assertEqual({}, self.item.compute({"spindle_speed": np.full(8, 21_000.0), "spindle_current": np.full(8, -1.0)}, parameters))

    def test_fit_does_not_impose_unsupported_positive_slope(self) -> None:
        speed = np.linspace(18_000.0, 24_000.0, 100)
        current = 10.0 - 0.0002 * speed
        parameters = self.item.fit({"spindle_speed": speed, "spindle_current": current})  # type: ignore[misc]
        self.assertLess(parameters[SLOPE], 0.0)

    def test_calibration_report_includes_envelope_diagnostics_and_stability(self) -> None:
        report = calibrate_relation(self.item.relation_id, healthy_signals(), blocks=3)
        self.assertEqual(self.item.relation_id, report.relation_id)
        self.assertEqual("spindle_speed", report.applicability_envelope.calibrated_ranges[0][0])
        self.assertGreater(report.calibration_diagnostics.sample_count, 0)
        self.assertTrue(report.parameter_stability.assessable)

    def test_block_stability_reports_when_data_are_insufficient(self) -> None:
        report = calibrate_relation(self.item.relation_id, healthy_signals(40), blocks=3)
        self.assertFalse(report.parameter_stability.assessable)
        self.assertTrue(report.blockers)

    def test_copied_validation_arrays_are_not_independent(self) -> None:
        calibration = healthy_signals()
        validation = {key: value.copy() for key, value in healthy_signals().items()}
        report = validate_relation_calibration(self.item.relation_id, calibration, validation)
        self.assertFalse(report.independent_data)
        self.assertTrue(any("copy" in blocker.lower() for blocker in report.blockers))
        self.assertGreater(report.validation_diagnostics.sample_count, 0)

    def test_different_arrays_without_run_provenance_are_not_independent(self) -> None:
        calibration = healthy_signals()
        validation = healthy_signals()
        validation["spindle_current"] = validation["spindle_current"] + 0.01
        report = validate_relation_calibration(self.item.relation_id, calibration, validation)
        self.assertFalse(report.independent_data)
        self.assertTrue(any("provenance" in blocker.lower() for blocker in report.blockers))

    def test_disjoint_declared_runs_with_distinct_observations_are_independent(self) -> None:
        calibration = healthy_signals()
        validation = healthy_signals()
        validation["spindle_current"] = validation["spindle_current"] + 0.01
        report = validate_relation_calibration(
            self.item.relation_id,
            calibration,
            validation,
            calibration_run_ids=("calibration-run-1",),
            validation_run_ids=("validation-run-1",),
        )
        self.assertTrue(report.independent_data)

    def test_overlapping_declared_runs_are_not_independent(self) -> None:
        calibration = healthy_signals()
        validation = healthy_signals()
        validation["spindle_current"] = validation["spindle_current"] + 0.01
        report = validate_relation_calibration(
            self.item.relation_id,
            calibration,
            validation,
            calibration_run_ids=("run-1",),
            validation_run_ids=("run-1",),
        )
        self.assertFalse(report.independent_data)
        self.assertTrue(any("disjoint" in blocker.lower() for blocker in report.blockers))

    def test_rejected_candidate_output_reduces_finite_fraction(self) -> None:
        calibration = healthy_signals()
        validation = healthy_signals()
        validation["spindle_current"] = validation["spindle_current"].copy()
        validation["spindle_current"][len(validation["spindle_current"]) // 2] = 1e200
        report = validate_relation_calibration(
            self.item.relation_id,
            calibration,
            validation,
            calibration_run_ids=("calibration-run",),
            validation_run_ids=("validation-run",),
        )
        self.assertLess(report.validation_diagnostics.finite_output_fraction, 1.0)
        self.assertGreater(report.validation_diagnostics.sample_count, 0)

    def test_shared_calibration_validation_data_are_flagged(self) -> None:
        signals = healthy_signals()
        report = validate_relation_calibration(self.item.relation_id, signals, signals)
        self.assertFalse(report.independent_data)
        self.assertTrue(any("share" in blocker.lower() for blocker in report.blockers))

    def test_step03_fit_and_compute_contract_remains_compatible(self) -> None:
        signals = healthy_signals(80)
        windows = {
            "spindle_speed": window("spindle_speed", "RPM", signals["spindle_speed"]),
            "spindle_current": window("spindle_current", "A", signals["spindle_current"]),
        }
        parameters = fit_relation_parameters("wafer_saw", self.item.relation_id, windows)
        features = calculate_physical_residuals("wafer_saw", windows, fitted_parameters={self.item.relation_id: parameters})
        self.assertEqual(1, len(features))
        self.assertAlmostEqual(0.0, features[0].value, places=4)

    def test_wrong_units_suppress_runtime_physics(self) -> None:
        signals = healthy_signals(80)
        windows = {
            "spindle_speed": window("spindle_speed", "rad/s", signals["spindle_speed"]),
            "spindle_current": window("spindle_current", "A", signals["spindle_current"]),
        }
        self.assertEqual((), calculate_physical_residuals("wafer_saw", windows, fitted_parameters={self.item.relation_id: {}}))

    def test_timestamp_offset_suppresses_step03_physics(self) -> None:
        signals = healthy_signals(80)
        parameters = self.item.fit(signals)  # type: ignore[misc]
        windows = {
            "spindle_speed": window("spindle_speed", "RPM", signals["spindle_speed"], start=0),
            "spindle_current": window("spindle_current", "A", signals["spindle_current"], start=200),
        }
        self.assertEqual((), calculate_physical_residuals("wafer_saw", windows, fitted_parameters={self.item.relation_id: parameters}))

    def test_sensor_fault_injections_are_bounded_and_documented(self) -> None:
        signals = healthy_signals(100)
        parameters = self.item.fit(signals)  # type: ignore[misc]
        bias = self.item.compute({"spindle_speed": signals["spindle_speed"], "spindle_current": signals["spindle_current"] + 0.3}, parameters)
        gain = self.item.compute({"spindle_speed": signals["spindle_speed"], "spindle_current": signals["spindle_current"] * 1.05}, parameters)
        dropout = self.item.compute({"spindle_speed": signals["spindle_speed"], "spindle_current": np.full(100, np.nan)}, parameters)
        clipped = self.item.compute({"spindle_speed": signals["spindle_speed"], "spindle_current": np.minimum(signals["spindle_current"] + 0.3, 5.0)}, parameters)
        self.assertGreater(bias[self.item.output_name], 0.0)
        self.assertGreater(gain[self.item.output_name], 0.0)
        self.assertEqual({}, dropout)
        self.assertTrue(not clipped or np.isfinite(clipped[self.item.output_name]))
        documented = " ".join(mode.failure_mode for mode in self.item.sensor_failure_modes).lower()
        for fault in ("offset", "gain", "drift", "dropout", "clipping", "noise", "misalignment", "stale"):
            self.assertIn(fault, documented)


class DiagnosticsAndMetrologyTests(unittest.TestCase):
    def test_residual_diagnostics_report_robust_location_scale_and_drift(self) -> None:
        values = np.concatenate((np.zeros(50), np.ones(50)))
        result = residual_diagnostics(values)
        self.assertEqual(100, result.sample_count)
        self.assertAlmostEqual(0.5, result.median)
        self.assertAlmostEqual(1.0, result.chronological_drift)

    def test_conditioning_dependence_is_reported(self) -> None:
        conditioning = np.linspace(0.0, 10.0, 100)
        result = residual_diagnostics(3.0 * conditioning + 1.0, conditioning)
        self.assertIsNotNone(result.conditioning_slope)
        self.assertAlmostEqual(3.0, result.conditioning_slope or 0.0, places=8)

    def test_omitted_feed_variable_is_exposed_by_diagnostics(self) -> None:
        speed = np.linspace(20_000.0, 30_000.0, 160)
        calibration = {"spindle_speed": speed, "spindle_current": 1.0 + 0.0002 * speed}
        parameters = relation().fit(calibration)  # type: ignore[misc]
        feed = np.linspace(0.0, 10.0, len(speed))
        current = 1.0 + 0.0002 * speed + 0.05 * feed
        residual = current - (parameters[INTERCEPT] + parameters[SLOPE] * speed)
        result = residual_diagnostics(residual, feed)
        self.assertAlmostEqual(0.05, result.conditioning_slope or 0.0, places=6)

    def test_serial_structure_and_nonfinite_fraction_are_reported(self) -> None:
        values = np.concatenate((np.linspace(0.0, 1.0, 100), [np.nan]))
        result = residual_diagnostics(values)
        self.assertGreater(result.lag1_autocorrelation or 0.0, 0.9)
        self.assertLess(result.finite_output_fraction, 1.0)

    def test_fraction_outside_envelope_is_reported(self) -> None:
        result = residual_diagnostics(np.arange(4.0), outside_envelope=np.array([False, True, False, True]))
        self.assertEqual(0.5, result.fraction_outside_envelope)

    def test_linear_uncertainty_propagation_matches_j_sigma_j_transpose(self) -> None:
        result = propagate_linearized_uncertainty(np.array([2.0, -1.0]), np.diag([0.25, 4.0]))
        self.assertAlmostEqual(np.sqrt(5.0), result)

    def test_uncertainty_propagation_rejects_bad_covariance(self) -> None:
        with self.assertRaisesRegex(ValueError, "symmetric"):
            propagate_linearized_uncertainty(np.array([1.0, 1.0]), np.array([[1.0, 2.0], [0.0, 1.0]]))
        with self.assertRaisesRegex(ValueError, "positive semidefinite"):
            propagate_linearized_uncertainty(np.array([1.0]), np.array([[-1.0]]))

    def test_contact_research_helper_has_correct_milliohm_dimensions(self) -> None:
        self.assertAlmostEqual(12.5, contact_resistance_mohm_for_research(25.0, 2.0))
        with self.assertRaises(ValueError):
            contact_resistance_mohm_for_research(1.0, 0.0)

    def test_contact_dimension_properties_hold_where_valid(self) -> None:
        base = contact_resistance_mohm_for_research(20.0, 2.0)
        self.assertAlmostEqual(2.0 * base, contact_resistance_mohm_for_research(40.0, 2.0))
        self.assertAlmostEqual(0.5 * base, contact_resistance_mohm_for_research(20.0, 4.0))


if __name__ == "__main__":
    unittest.main()
