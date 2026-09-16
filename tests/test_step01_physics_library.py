from __future__ import annotations

import unittest

import numpy as np

from osat_edge.roadmap.step01_physics_library import (
    ALL_MACHINE_FAMILIES,
    PHYSICS_RELATIONS,
    RESEARCH_CANDIDATES,
    RESEARCH_REFERENCES,
    PhysicsRelation,
    RelationStatus,
    ResearchCandidate,
    audit_physics_library,
    relations_for_family,
    research_catalog_for_family,
)
from osat_edge.roadmap.step03_physical_residuals import (
    calculate_physical_residuals,
    fit_relation_parameters,
)
from support import window


def relation(relation_id: str) -> PhysicsRelation:
    return next(item for item in PHYSICS_RELATIONS if item.relation_id == relation_id)


class LibraryInvariantTests(unittest.TestCase):
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

    def test_runtime_relations_have_complete_research_records(self) -> None:
        for item in PHYSICS_RELATIONS:
            with self.subTest(relation=item.relation_id):
                self.assertIs(RelationStatus.RUNTIME, item.status)
                self.assertTrue(item.references)
                self.assertTrue(item.assumptions)
                self.assertTrue(item.validity_conditions)
                self.assertTrue(item.invalidity_conditions)
                self.assertTrue(item.confounders)
                self.assertTrue(item.uncertainty_sources)
                self.assertTrue(item.expected_fault_sensitivity)
                self.assertTrue(item.cross_sensitivities)
                self.assertTrue(item.falsification_tests)
                self.assertTrue(item.instrumentation_gaps)
                self.assertTrue(item.output_name)
                self.assertTrue(item.output_unit)

    def test_every_machine_family_has_a_research_catalog(self) -> None:
        self.assertEqual(9, len(ALL_MACHINE_FAMILIES))
        for family in ALL_MACHINE_FAMILIES:
            with self.subTest(family=family):
                self.assertTrue(research_catalog_for_family(family))

    def test_runtime_api_excludes_non_runtime_candidates(self) -> None:
        non_runtime_ids = {item.candidate_id for item in RESEARCH_CANDIDATES}
        for family in ALL_MACHINE_FAMILIES:
            runtime_ids = {item.relation_id for item in relations_for_family(family)}
            self.assertTrue(runtime_ids.isdisjoint(non_runtime_ids))
            self.assertTrue(
                all(item.status is RelationStatus.RUNTIME for item in relations_for_family(family))
            )

    def test_rejected_candidates_explain_decision_and_instrumentation_gap(self) -> None:
        rejected = [
            item for item in RESEARCH_CANDIDATES
            if item.status is RelationStatus.REJECTED
        ]
        self.assertTrue(rejected)
        for item in rejected:
            with self.subTest(candidate=item.candidate_id):
                self.assertTrue(item.decision_reason)
                self.assertTrue(item.missing_variables)
                self.assertTrue(item.additional_instrumentation)
                self.assertTrue(item.references)

    def test_coolant_ratio_is_research_only_and_not_executable(self) -> None:
        catalog = research_catalog_for_family("wafer_saw")
        coolant = next(
            item for item in catalog
            if isinstance(item, ResearchCandidate)
            and item.candidate_id == "wafer_saw.coolant_hydraulic_resistance"
        )
        self.assertIs(RelationStatus.RESEARCH_ONLY, coolant.status)
        self.assertNotIn(
            "cooling.pressure_flow",
            {item.relation_id for item in relations_for_family("wafer_saw")},
        )


class SpindleRelationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.item = relation("spindle.current_speed_residual")
        self.assertIsNotNone(self.item.fit)

    def test_known_healthy_linear_relation_is_recovered(self) -> None:
        speed = np.linspace(20_000.0, 22_000.0, 100)
        current = 1.25 + 0.00018 * speed
        parameters = self.item.fit(  # type: ignore[misc]
            {"spindle_speed": speed, "spindle_current": current}
        )
        self.assertAlmostEqual(0.00018, parameters["slope"], places=7)
        self.assertAlmostEqual(1.25, parameters["intercept"], places=3)
        self.assertGreater(parameters["residual_scale"], 0.0)
        self.assertGreaterEqual(parameters["speed_span_rpm"], 100.0)

    def test_robust_fit_resists_moderate_current_outliers(self) -> None:
        speed = np.linspace(20_000.0, 22_000.0, 120)
        current = 1.5 + 0.0002 * speed
        current[::17] += 12.0
        parameters = self.item.fit(  # type: ignore[misc]
            {"spindle_speed": speed, "spindle_current": current}
        )
        self.assertAlmostEqual(0.0002, parameters["slope"], places=6)
        self.assertAlmostEqual(1.5, parameters["intercept"], places=2)

    def test_insufficient_speed_span_is_rejected(self) -> None:
        speed = np.linspace(20_000.0, 20_050.0, 60)
        current = 1.0 + 0.0002 * speed
        with self.assertRaisesRegex(ValueError, "excitation is insufficient"):
            self.item.fit(  # type: ignore[misc]
                {"spindle_speed": speed, "spindle_current": current}
            )

    def test_constant_speed_is_rejected_instead_of_creating_fake_slope(self) -> None:
        speed = np.full(60, 25_000.0)
        current = np.linspace(4.0, 5.0, 60)
        with self.assertRaisesRegex(ValueError, "excitation is insufficient"):
            self.item.fit(  # type: ignore[misc]
                {"spindle_speed": speed, "spindle_current": current}
            )

    def test_one_speed_outlier_does_not_fake_excitation(self) -> None:
        speed = np.full(60, 25_000.0)
        speed[-1] = 40_000.0
        current = np.full(60, 5.0)
        with self.assertRaisesRegex(ValueError, "excitation is insufficient"):
            self.item.fit(  # type: ignore[misc]
                {"spindle_speed": speed, "spindle_current": current}
            )

    def test_added_current_at_fixed_speed_gives_positive_residual(self) -> None:
        speed = np.linspace(20_000.0, 22_000.0, 100)
        healthy = 1.5 + 0.0002 * speed
        parameters = self.item.fit(  # type: ignore[misc]
            {"spindle_speed": speed, "spindle_current": healthy}
        )
        output = self.item.compute(
            {"spindle_speed": speed, "spindle_current": healthy + 0.4},
            parameters,
        )
        self.assertAlmostEqual(0.4, output[self.item.output_name], places=3)

    def test_nonfinite_and_extreme_inference_never_emits_fake_number(self) -> None:
        output = self.item.compute(
            {
                "spindle_speed": np.array([20_000.0, 20_100.0, np.nan, np.inf]),
                "spindle_current": np.array([5.0, 5.1, 5.2, 1e308]),
            },
            {"slope": 0.0001, "intercept": 3.0},
        )
        self.assertEqual({}, output)
        self.assertEqual(
            {},
            self.item.compute(
                {
                    "spindle_speed": np.full(8, 1e308),
                    "spindle_current": np.full(8, 1e308),
                },
                {"slope": 1e308, "intercept": 1e308},
            ),
        )

    def test_step03_rejects_wrong_spindle_units(self) -> None:
        speed = np.linspace(20_000.0, 22_000.0, 60)
        windows = {
            "spindle_speed": window("spindle_speed", "rad/s", speed),
            "spindle_current": window("spindle_current", "A", 1.0 + speed * 0.0002),
        }
        with self.assertRaisesRegex(ValueError, "timestamp-overlapping"):
            fit_relation_parameters("wafer_saw", self.item.relation_id, windows)


class ContactResistanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.item = relation("contacts.contact_resistance")

    def test_known_resistance_and_milliohm_units_are_recovered(self) -> None:
        current = np.linspace(0.5, 2.0, 20)
        voltage_mv = 12.5 * current
        output = self.item.compute(
            {"contact_voltage_drop": voltage_mv, "site_current": current}, {}
        )
        self.assertEqual("mΩ", self.item.output_unit)
        self.assertAlmostEqual(12.5, output[self.item.output_name], places=10)

    def test_aligned_sample_ratios_are_used(self) -> None:
        current = np.array([1.0, 2.0, 4.0, 8.0, 16.0, 32.0])
        resistance = np.array([10.0, 10.0, 10.0, 30.0, 30.0, 30.0])
        output = self.item.compute(
            {
                "contact_voltage_drop": resistance * current,
                "site_current": current,
            },
            {},
        )
        self.assertAlmostEqual(20.0, output[self.item.output_name])

    def test_near_zero_current_is_suppressed(self) -> None:
        output = self.item.compute(
            {
                "contact_voltage_drop": np.full(10, 1.0),
                "site_current": np.full(10, 1e-12),
            },
            {},
        )
        self.assertEqual({}, output)

    def test_consistent_reversed_polarity_is_valid(self) -> None:
        current = -np.linspace(0.5, 2.0, 10)
        output = self.item.compute(
            {"contact_voltage_drop": 8.0 * current, "site_current": current}, {}
        )
        self.assertAlmostEqual(8.0, output[self.item.output_name])

    def test_mismatched_polarity_is_suppressed(self) -> None:
        current = np.linspace(0.5, 2.0, 10)
        output = self.item.compute(
            {"contact_voltage_drop": -8.0 * current, "site_current": current}, {}
        )
        self.assertEqual({}, output)

    def test_noisy_repeated_contacts_use_robust_median(self) -> None:
        rng = np.random.default_rng(7)
        current = rng.uniform(0.8, 1.2, 101)
        resistance = 15.0 + rng.normal(0.0, 0.4, 101)
        resistance[0] = 500.0
        output = self.item.compute(
            {
                "contact_voltage_drop": resistance * current,
                "site_current": current,
            },
            {},
        )
        self.assertAlmostEqual(15.0, output[self.item.output_name], delta=0.15)

    def test_nonfinite_samples_are_ignored_without_singularity(self) -> None:
        current = np.array([1.0, 1.0, 1.0, 1.0, np.nan, np.inf])
        voltage = np.array([10.0, 10.0, 10.0, 10.0, 10.0, 10.0])
        output = self.item.compute(
            {"contact_voltage_drop": voltage, "site_current": current}, {}
        )
        self.assertTrue(np.isfinite(output[self.item.output_name]))

    def test_step03_compatibility_produces_contact_feature(self) -> None:
        current = np.linspace(0.5, 2.0, 20)
        windows = {
            "contact_voltage_drop": window(
                "contact_voltage_drop", "mV", 9.0 * current
            ),
            "site_current": window("site_current", "A", current),
        }
        features = calculate_physical_residuals("final_test", windows)
        self.assertEqual(1, len(features))
        self.assertEqual(self.item.output_name, features[0].name)
        self.assertAlmostEqual(9.0, features[0].value)


if __name__ == "__main__":
    unittest.main()
