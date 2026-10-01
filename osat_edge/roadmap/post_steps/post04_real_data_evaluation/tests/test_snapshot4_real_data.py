"""Snapshot 4 provenance, ST-AWFD, and TUHH regression checks."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

import numpy as np

from osat_edge.roadmap.post_steps.post04_real_data_evaluation.core.evidence_lifecycle import (
    CURRENT_EVIDENCE_PATH,
    HISTORICAL_EVIDENCE_SHA256,
    HISTORICAL_EVIDENCE_PATH,
    verify_historical_real_data_artifact,
)
from osat_edge.roadmap.post_steps.post04_real_data_evaluation.core.dataset_context import (
    DEFAULT_EXTERNAL_DATA_ROOT,
    RealDataEvaluationError,
)
from osat_edge.roadmap.post_steps.post04_real_data_evaluation.datasets.tuhh_dad3350 import (
    KEYENCE_PARSER_COMMIT,
    TUHH_FEED_FILES,
    _surface_statistics,
)
from osat_edge.roadmap.post_steps.post04_real_data_evaluation.datasets.st_awfd import (
    ST_AWFD_SPECS,
    ST_THRESHOLD_PROBES,
    _st_feature_sets_for_step,
    _st_identity,
    _validate_st_awfd_matrix,
)
from osat_edge.roadmap.post_steps.post04_real_data_evaluation.evaluation import (
    evaluate_real_dataset,
)
from osat_edge.roadmap.steps.step09_health_risk.health import (
    CRITICAL_ENTRY,
    DEGRADED_ENTRY,
    WATCH_ENTRY,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "resources" / "fixtures"


def _fixture(name: str) -> tuple[tuple[str, ...], np.ndarray]:
    path = FIXTURES / name
    with path.open(encoding="utf-8", newline="") as stream:
        header = tuple(next(csv.reader(stream)))
        matrix = np.loadtxt(stream, delimiter=",", dtype=np.float64, ndmin=2)
    return header, matrix


class Snapshot4RealDataTests(unittest.TestCase):
    def test_schema_fixtures_contain_only_reference_and_anonymous_fields(self) -> None:
        for dataset_id, fixture in (
            ("st-awfd-d1", "st_awfd_d1_schema.csv"),
            ("st-awfd-d2", "st_awfd_d2_schema.csv"),
        ):
            with self.subTest(dataset=dataset_id):
                header, _matrix = _fixture(fixture)
                expected = {
                    "MaterialID", "StepID", "duration_ms", "is_test", "target",
                    *(
                        f"feature_{index}"
                        for index in range(1, ST_AWFD_SPECS[dataset_id]["feature_count"] + 1)
                    ),
                }
                self.assertEqual(expected, set(header))
                self.assertFalse(any("machine" in name.lower() for name in header))

    def test_material_split_and_target_must_be_consistent(self) -> None:
        header, matrix = _fixture("st_awfd_d1_schema.csv")
        columns = {name: index for index, name in enumerate(header)}
        inconsistent_target = matrix.copy()
        inconsistent_target[1, columns["target"]] = 1
        with self.assertRaisesRegex(RealDataEvaluationError, "target changes"):
            _validate_st_awfd_matrix(header, inconsistent_target)
        inconsistent_split = matrix.copy()
        inconsistent_split[1, columns["is_test"]] = 1
        with self.assertRaisesRegex(RealDataEvaluationError, "is_test changes"):
            _validate_st_awfd_matrix(header, inconsistent_split)

    def test_feature_sets_exclude_target_duration_and_optional_steps(self) -> None:
        header, matrix = _fixture("st_awfd_d1_schema.csv")
        material, steps, _duration, features, _targets, metadata = (
            _validate_st_awfd_matrix(header, matrix)
        )
        records = _st_feature_sets_for_step(
            "st-awfd-d1", 2, material, steps, features, metadata
        )
        self.assertEqual(2, len(records))
        names = tuple(feature.name for feature in records[0][3].features)
        self.assertEqual(30, len(names))
        self.assertTrue(all(name.startswith("st-awfd-d1.step_2.feature_") for name in names))
        self.assertTrue(all(name.endswith((".median", ".mad")) for name in names))
        self.assertFalse(any(value in name for name in names for value in ("target", "is_test", "duration", "slope")))
        self.assertEqual([], _st_feature_sets_for_step(
            "st-awfd-d1", -1, material, steps, features, metadata
        ))

    def test_d1_and_d2_benchmark_identities_are_independent(self) -> None:
        d1 = _st_identity("st-awfd-d1", 2)
        d2 = _st_identity("st-awfd-d2", 2)
        self.assertNotEqual(d1.machine_id, d2.machine_id)
        self.assertNotEqual(d1.family, d2.family)
        self.assertNotEqual(d1.station_id, d2.station_id)
        self.assertNotIn(d1.station_id, {"WM-01", "WS-01", "DA-01", "WB-04", "MO-01", "MK-01", "TF-01", "SG-01", "FT-01"})

    def test_threshold_probes_are_frozen_numbers_not_state_machine_calls(self) -> None:
        self.assertEqual(
            {
                "WATCH_ENTRY": WATCH_ENTRY,
                "DEGRADED_ENTRY": DEGRADED_ENTRY,
                "CRITICAL_ENTRY": CRITICAL_ENTRY,
            },
            ST_THRESHOLD_PROBES,
        )

    def test_hash_mismatch_never_receives_verified_real_status(self) -> None:
        fixture = (FIXTURES / "st_awfd_d1_schema.csv").read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "D1.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("D1.csv", fixture)
            report = evaluate_real_dataset("st-awfd-d1", path)
        self.assertEqual("UNVERIFIED_EXTERNAL_INPUT", report["status"])
        self.assertFalse(report["provenance_verified"])
        self.assertIsNone(report["real_data"])

    def test_tuhh_feed_identity_and_surface_parser_bounds(self) -> None:
        self.assertEqual((0.1, 0.2, 0.5, 0.7, 1.0, 5.0), tuple(TUHH_FEED_FILES.values()))
        with self.assertRaisesRegex(RealDataEvaluationError, "dimensions"):
            _surface_statistics(np.zeros((1, 4), dtype=np.float64))
        surface = np.arange(12, dtype=np.float64).reshape(3, 4)
        result = _surface_statistics(surface)
        self.assertEqual([3, 4], result["dimensions"])
        self.assertEqual(1.0, result["valid_pixel_fraction"])

    def test_historical_artifact_is_byte_immutable_and_not_current_reproduction(self) -> None:
        verified = verify_historical_real_data_artifact()
        self.assertEqual("PASS", verified["status"])
        self.assertEqual("0.2.4", verified["release_version"])
        self.assertEqual(HISTORICAL_EVIDENCE_SHA256, verified["artifact_sha256"])
        stored = json.loads(HISTORICAL_EVIDENCE_PATH.read_text(encoding="utf-8"))
        self.assertEqual("0.2.4", stored["release_version"])

    @unittest.skipUnless(
        (DEFAULT_EXTERNAL_DATA_ROOT / "st-awfd-d1" / "D1.zip").is_file(),
        "official ST-AWFD D1 is not locally present",
    )
    def test_official_d1_has_no_leakage_or_state_ticket_claim(self) -> None:
        report = evaluate_real_dataset(
            "st-awfd-d1", DEFAULT_EXTERNAL_DATA_ROOT / "st-awfd-d1"
        )
        self.assertEqual("EXECUTED", report["status"])
        self.assertEqual(1.0, report["pipeline_coverage"])
        self.assertEqual(1.0, report["material_scoring_coverage"])
        self.assertEqual(0.8, report["headline_step_coverage"])
        self.assertEqual(0.0, report["complete_headline_material_coverage"])
        self.assertEqual(
            "legacy evidence-schema alias for material_scoring_coverage",
            report["pipeline_coverage_definition"],
        )
        self.assertEqual(2, report["held_out_label_counts"]["abnormal"])
        self.assertTrue(
            all(item["step_id"] not in {-2, -1, 1} for item in report["step_results"])
        )
        self.assertEqual("NO_SOURCE_ROWS", next(
            item["status"] for item in report["step_results"] if item["step_id"] == 5
        ))
        self.assertEqual([], report["mapped_channels"])
        self.assertFalse(report["canonical_station_mapping"])
        self.assertFalse(report["pipeline"]["step01_physics"])
        self.assertFalse(report["pipeline"]["step05_family_model"])
        self.assertFalse(report["pipeline"]["step09_temporal_state_machine"])
        self.assertFalse(report["pipeline"]["step10_evidence"])
        self.assertFalse(report["pipeline"]["step15_ticket"])
        self.assertEqual(0, report["operational_ticket_count"])
        self.assertIn("not health states", report["threshold_probe_semantics"])
        self.assertEqual(2, report["positive_count"])
        self.assertEqual(1805, report["negative_count"])
        self.assertEqual(2 / 1807, report["positive_prevalence"])
        self.assertEqual(
            report["positive_prevalence"], report["average_precision_baseline"]
        )
        self.assertEqual(
            "LOW_POSITIVE_COUNT_DESCRIPTIVE_ONLY",
            report["positive_count_assessment"],
        )
        self.assertIn("only two abnormal", report["discrimination_evidence_context"])
        self.assertEqual(
            "INDICATIVE_EXTERNAL_DISCRIMINATION_DESCRIPTIVE_ONLY",
            report["discrimination_evidence"],
        )
        self.assertIn("NOT_SUPPORTED", report["threshold_transfer_evidence"])
        self.assertEqual(
            "NONCOMMERCIAL_RESEARCH_BENCHMARK",
            report["data_use_classification"],
        )
        self.assertFalse(
            report["third_party_data_use"]["fleet_command_code_sharealike_claim"]
        )

    @unittest.skipUnless(
        (DEFAULT_EXTERNAL_DATA_ROOT / "st-awfd-d2" / "D2.zip").is_file(),
        "official ST-AWFD D2 is not locally present",
    )
    def test_official_d2_is_independent_and_reports_observed_metrics(self) -> None:
        report = evaluate_real_dataset(
            "st-awfd-d2", DEFAULT_EXTERNAL_DATA_ROOT / "st-awfd-d2"
        )
        self.assertEqual("EXECUTED", report["status"])
        self.assertEqual([1, 2], report["headline_step_ids"])
        self.assertEqual(1.0, report["material_scoring_coverage"])
        self.assertEqual(1.0, report["headline_step_coverage"])
        self.assertEqual(1.0, report["complete_headline_material_coverage"])
        self.assertEqual(367, report["held_out_label_counts"]["abnormal"])
        self.assertEqual(1.0, report["continuous_metrics"]["auroc"])
        self.assertEqual(1.0, report["continuous_metrics"]["average_precision"])

    @unittest.skipUnless(
        (DEFAULT_EXTERNAL_DATA_ROOT / "tuhh-dad3350-surface" / "data_raw.zip").is_file(),
        "official TUHH v1.0 surface dataset is not locally present",
    )
    def test_official_tuhh_is_descriptive_only(self) -> None:
        report = evaluate_real_dataset(
            "tuhh-dad3350-surface",
            DEFAULT_EXTERNAL_DATA_ROOT / "tuhh-dad3350-surface",
        )
        self.assertIn(report["status"], {"EXECUTED_DESCRIPTIVE", "INSPECTED_NOT_EXECUTABLE"})
        self.assertEqual(0, report["operational_ticket_count"])
        if report["status"] == "EXECUTED_DESCRIPTIVE":
            self.assertEqual(KEYENCE_PARSER_COMMIT, report["parser"]["commit"])
            self.assertEqual(6, len(report["surface_maps"]))
            self.assertFalse(report["pipeline"]["step07_machine_model"])
            self.assertFalse(report["pipeline"]["step09_temporal_state_machine"])
            self.assertEqual(
                "DATUM_COMPARABILITY_UNVERIFIED",
                report["median_height_association_status"],
            )
            self.assertEqual(
                [
                    "detrended_height_rms",
                    "detrended_mean_absolute_deviation",
                    "peak_to_valley",
                ],
                report["principal_descriptive_results"],
            )
            self.assertEqual(
                "Public Domain Mark 1.0",
                report["third_party_data_use"]["rights_statement"],
            )
            self.assertIn(
                "not CC0", report["third_party_data_use"]["rights_instrument"]
            )

    def test_current_record_contains_aggregate_results_only(self) -> None:
        if not CURRENT_EVIDENCE_PATH.is_file():
            self.skipTest("current evidence record is generated after evaluator verification")
        stored = json.loads(CURRENT_EVIDENCE_PATH.read_text(encoding="utf-8"))
        self.assertEqual("0.2.5", stored["release_version"])
        self.assertFalse(stored["methodology"]["sample_level_data_committed"])
        serialized = json.dumps(stored)
        self.assertNotIn("MaterialID\":", serialized)
        self.assertNotIn("feature_1\":", serialized)


if __name__ == "__main__":
    unittest.main()
