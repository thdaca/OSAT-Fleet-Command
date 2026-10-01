"""Snapshot 6 changes interpretation only; Snapshot 5 measurements stay frozen."""

import hashlib
import json
import tempfile
import unittest

from osat_edge.roadmap.post_steps.post04_real_data_evaluation.core.evidence_lifecycle import (
    CURRENT_EVIDENCE_PATH,
)
from osat_edge.roadmap.post_steps.post04_real_data_evaluation.evaluation import (
    evaluate_all_real_data,
)
from osat_edge.roadmap.post_steps.post04_real_data_evaluation.core.reporting import (
    real_data_summary,
)
from osat_edge.roadmap.post_steps.post04_real_data_evaluation.core.reporting import (
    ST_AWFD_DISCRIMINATION_INTERPRETATION,
)
from osat_edge.roadmap.post_steps.post04_real_data_evaluation.datasets.st_awfd import (
    LOW_POSITIVE_COUNT_THRESHOLD,
    _st_discrimination_evidence,
)


STRONG = "SUPPORTED_EXTERNALLY_FOR_STEP07_CONTINUOUS_DISCRIMINATION"
INDICATIVE = "INDICATIVE_EXTERNAL_DISCRIMINATION_DESCRIPTIVE_ONLY"
# Snapshot 5 release evidence, omitting only evaluator/report implementation hashes.
SNAPSHOT5_PAYLOAD_SHA256 = (
    "f3b5220b3f2cf76395537fec0bdba4836f411551d7399493cec1587702ae4254"
)


class Snapshot6InterpretationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.evidence = json.loads(CURRENT_EVIDENCE_PATH.read_text(encoding="utf-8"))
        cls.results = {item["dataset"]: item for item in cls.evidence["results"]}

    def test_d1_cannot_be_strong_below_existing_low_positive_threshold(self) -> None:
        self.assertEqual(10, LOW_POSITIVE_COUNT_THRESHOLD)
        for positive_count in range(LOW_POSITIVE_COUNT_THRESHOLD):
            with self.subTest(positive_count=positive_count):
                self.assertEqual(
                    INDICATIVE, _st_discrimination_evidence("st-awfd-d1", positive_count)
                )
        self.assertEqual(
            STRONG,
            _st_discrimination_evidence("st-awfd-d1", LOW_POSITIVE_COUNT_THRESHOLD),
        )
        self.assertEqual(INDICATIVE, self.results["st-awfd-d1"]["discrimination_evidence"])

    def test_d2_retains_its_classification(self) -> None:
        self.assertEqual(STRONG, _st_discrimination_evidence("st-awfd-d2", 367))
        self.assertEqual(STRONG, self.results["st-awfd-d2"]["discrimination_evidence"])

    def test_d1_metrics_and_low_positive_warning_are_unchanged(self) -> None:
        d1 = self.results["st-awfd-d1"]
        self.assertEqual(2, d1["positive_count"])
        self.assertEqual(1807, d1["held_out_materials"])
        self.assertEqual(0.935180055401662, d1["continuous_metrics"]["auroc"])
        self.assertEqual(0.012303436225975538, d1["continuous_metrics"]["average_precision"])
        self.assertEqual(2 / 1807, d1["positive_prevalence"])
        self.assertEqual(11.1161546301689, d1["average_precision_lift_over_prevalence"])
        self.assertEqual("LOW_POSITIVE_COUNT_DESCRIPTIVE_ONLY", d1["positive_count_assessment"])

    def test_aggregate_interpretation_is_d2_led_and_requires_both_results(self) -> None:
        statement = self.evidence["st_awfd_discrimination_interpretation"]
        self.assertEqual(ST_AWFD_DISCRIMINATION_INTERPRETATION, statement)
        self.assertIn("driven primarily by D2", statement)
        self.assertIn("D1 is statistically fragile corroborative", statement)
        with tempfile.TemporaryDirectory() as directory:
            missing = evaluate_all_real_data(directory)
        self.assertIsNone(missing["st_awfd_discrimination_interpretation"])
        self.assertIsNone(real_data_summary(missing)["st_awfd_discrimination_interpretation"])
        missing["st_awfd_discrimination_interpretation"] = statement
        self.assertEqual(statement, real_data_summary(missing)["st_awfd_discrimination_interpretation"])

    def test_every_snapshot5_scientific_value_remains_exactly_frozen(self) -> None:
        value = json.loads(json.dumps(self.evidence))
        value.pop("evaluator_sha256")
        value.pop("deterministic_comparison_report_sha256")
        value.pop("st_awfd_discrimination_interpretation")
        # Reverse only the explicitly requested D1 interpretation correction.
        for result in value["results"]:
            if result["dataset"] == "st-awfd-d1":
                self.assertEqual(INDICATIVE, result["discrimination_evidence"])
                result["discrimination_evidence"] = STRONG
        payload = (
            json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            + "\n"
        ).encode("utf-8")
        self.assertEqual(SNAPSHOT5_PAYLOAD_SHA256, hashlib.sha256(payload).hexdigest())


if __name__ == "__main__":
    unittest.main()
