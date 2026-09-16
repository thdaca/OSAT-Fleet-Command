"""Snapshot 5 reporting semantics, rights, organization, and anti-drift checks."""

from __future__ import annotations

import hashlib
import json
from contextlib import ExitStack
from pathlib import Path
import unittest
from unittest.mock import patch

from osat_edge.roadmap.post_steps.post04_real_data_evaluation.post04_real_data_evaluation import (
    CURRENT_EVIDENCE_PATH,
    DEFAULT_EXTERNAL_DATA_ROOT,
    SNAPSHOT4_EVIDENCE_ARTIFACT_SHA256,
    SNAPSHOT4_SCIENTIFIC_PAYLOAD_SHA256,
    THIRD_PARTY_DATA_USE_PATH,
    current_real_data_evidence_record,
    evaluate_all_real_data,
    snapshot4_result_sha256,
    snapshot4_scientific_payload_sha256,
)


SNAPSHOT4_RESULT_SHA256 = {
    "st-awfd-d1": "90e8bf2e7741a1d99df7f435b120efc6587ed33164113145f2839aabf0d3425e",
    "st-awfd-d2": "ea6e650af8a966ac1e31297579c9fc25245bd62623e1823d2df2d3113aad2fd5",
    "tuhh-dad3350-surface": "7ee362761285e8384e90d7315f3c6233b0c21f40e14b6e11e2d7cfae63f319ce",
    "kuka-kr3": "6d20a8b5861f1025e6bae0dd862df51efc4139338197e9da687a8807752b735f",
    "nasa-milling": "41464f3b711ed5d18f93cecb59eae10727cec6b93c9ad25c7165374e445e2bbd",
    "r2r-web-tension": "8b736751f905f3210979b70b05841c6742dc3dd37ece28877f2b51c0363edbe6",
    "uci-secom": "cd87eddde68861797e444cdcc596674df484c3fd18a24af0afb903eaa068c462",
}


class Snapshot5ReportingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.evidence = json.loads(CURRENT_EVIDENCE_PATH.read_text(encoding="utf-8"))
        cls.results = {
            item["dataset"]: item for item in cls.evidence["results"]
        }

    def test_entire_snapshot4_scientific_payload_is_frozen(self) -> None:
        self.assertEqual(
            SNAPSHOT4_EVIDENCE_ARTIFACT_SHA256,
            self.evidence["snapshot4_evidence_artifact_sha256"],
        )
        self.assertEqual(
            SNAPSHOT4_SCIENTIFIC_PAYLOAD_SHA256,
            self.evidence["snapshot4_scientific_payload_sha256"],
        )
        self.assertEqual(
            SNAPSHOT4_SCIENTIFIC_PAYLOAD_SHA256,
            snapshot4_scientific_payload_sha256(self.evidence),
        )

    def test_existing_dataset_scientific_results_are_identical(self) -> None:
        for dataset_id, expected in SNAPSHOT4_RESULT_SHA256.items():
            with self.subTest(dataset=dataset_id):
                self.assertEqual(
                    expected,
                    snapshot4_result_sha256(self.results[dataset_id]),
                )

    @unittest.skipUnless(
        (DEFAULT_EXTERNAL_DATA_ROOT / "st-awfd-d1" / "D1.zip").is_file(),
        "official external datasets are not locally present",
    )
    def test_live_external_reproduction_never_fits_family_or_runs_health(self) -> None:
        forbidden_calls = (
            "osat_edge.roadmap.steps.step05_family_model.step05_family_model.fit_family_model",
            "osat_edge.roadmap.steps.step05_family_model.step05_family_model.FamilyModel.__post_init__",
            "osat_edge.roadmap.steps.step09_health_risk.step09_health_risk.HealthEngine.assess",
            "osat_edge.roadmap.steps.step09_health_risk.step09_health_risk.StateTracker.update",
        )
        with ExitStack() as stack:
            for target in forbidden_calls:
                stack.enter_context(patch(target, side_effect=AssertionError(target)))
            report = evaluate_all_real_data(DEFAULT_EXTERNAL_DATA_ROOT)
        self.assertEqual(0, report["summary"]["operational_tickets"])
        for result in report["datasets"]:
            self.assertEqual(0, result.get("operational_ticket_count", 0))
        # Partial local datasets can still exercise the isolation guards. Only
        # assert the complete frozen record when the full pinned set is present.
        if report["summary"] == self.evidence["summary"]:
            reproduced = current_real_data_evidence_record(report)
            self.assertEqual(self.evidence, reproduced)

    def test_st_coverage_and_imbalance_are_explicit(self) -> None:
        d1 = self.results["st-awfd-d1"]
        self.assertEqual(1.0, d1["material_scoring_coverage"])
        self.assertEqual(0.8, d1["headline_step_coverage"])
        self.assertEqual(0.0, d1["complete_headline_material_coverage"])
        self.assertEqual(2, d1["positive_count"])
        self.assertEqual(1805, d1["negative_count"])
        self.assertEqual(2 / 1807, d1["positive_prevalence"])
        self.assertEqual(
            d1["continuous_metrics"]["average_precision"] / d1["positive_prevalence"],
            d1["average_precision_lift_over_prevalence"],
        )
        self.assertEqual(
            "average_precision / positive_prevalence",
            d1["average_precision_lift_definition"],
        )
        self.assertEqual(
            "LOW_POSITIVE_COUNT_DESCRIPTIVE_ONLY",
            d1["positive_count_assessment"],
        )
        self.assertNotIn(1, [
            item["step_id"] for item in d1["step_results"]
        ])

    def test_discrimination_is_separate_from_threshold_transfer(self) -> None:
        for dataset_id in ("st-awfd-d1", "st-awfd-d2"):
            result = self.results[dataset_id]
            expected = (
                "INDICATIVE_EXTERNAL_DISCRIMINATION_DESCRIPTIVE_ONLY"
                if dataset_id == "st-awfd-d1"
                else "SUPPORTED_EXTERNALLY_FOR_STEP07_CONTINUOUS_DISCRIMINATION"
            )
            self.assertEqual(expected, result["discrimination_evidence"])
            self.assertIn("NOT_SUPPORTED", result["threshold_transfer_evidence"])
            self.assertFalse(result["pipeline"]["step05_family_model"])
            self.assertFalse(result["pipeline"]["step09_temporal_state_machine"])
            self.assertFalse(result["pipeline"]["step10_evidence"])
            self.assertFalse(result["pipeline"]["step15_ticket"])
        self.assertEqual(0, self.evidence["summary"]["operational_tickets"])

    def test_third_party_data_use_inventory_is_pinned_and_precise(self) -> None:
        expected_hash = hashlib.sha256(THIRD_PARTY_DATA_USE_PATH.read_bytes()).hexdigest()
        self.assertEqual(
            expected_hash,
            self.evidence["third_party_data_use_inventory"]["sha256"],
        )
        inventory = json.loads(THIRD_PARTY_DATA_USE_PATH.read_text(encoding="utf-8"))
        by_id = {item["identifier"]: item for item in inventory["entries"]}
        st = by_id["st-awfd-d1-and-d2"]
        self.assertEqual("NONCOMMERCIAL_RESEARCH_BENCHMARK", st["purpose"])
        self.assertFalse(st["raw_data_in_repository_or_release"])
        self.assertFalse(st["fleet_command_code_sharealike_claim"])
        tuhh = by_id["tuhh-dad3350-surface"]
        self.assertEqual("Public Domain Mark 1.0", tuhh["rights_statement"])
        self.assertIn("not CC0", tuhh["rights_instrument"])
        parser = by_id["convert-keyence-files"]
        self.assertEqual("Unlicense", parser["license"])
        self.assertTrue(parser["independent_validation_required"])

    def test_tuhh_principal_metrics_do_not_use_absolute_median_height(self) -> None:
        tuhh = self.results["tuhh-dad3350-surface"]
        self.assertEqual(
            "DATUM_COMPARABILITY_UNVERIFIED",
            tuhh["median_height_association_status"],
        )
        self.assertNotIn("median_height", tuhh["principal_descriptive_results"])
        self.assertEqual(
            [
                "detrended_height_rms",
                "detrended_mean_absolute_deviation",
                "peak_to_valley",
            ],
            tuhh["principal_descriptive_results"],
        )

    def test_post04_public_module_is_thin_and_dataset_owned(self) -> None:
        root = Path(__file__).resolve().parents[1]
        public = root / "post04_real_data_evaluation.py"
        self.assertLess(len(public.read_text(encoding="utf-8").splitlines()), 200)
        for relative in (
            "core/metrics.py",
            "core/evidence_lifecycle.py",
            "core/reporting.py",
            "datasets/st_awfd.py",
            "datasets/tuhh_dad3350.py",
            "datasets/kuka.py",
            "datasets/nasa_milling.py",
            "datasets/r2r.py",
            "datasets/secom.py",
            "datasets/forinfpro_himd.py",
        ):
            self.assertTrue((root / relative).is_file(), relative)


if __name__ == "__main__":
    unittest.main()
