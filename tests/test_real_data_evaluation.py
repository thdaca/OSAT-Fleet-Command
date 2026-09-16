from __future__ import annotations

import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from osat_edge.cli import main
from osat_edge.common import DataOrigin
from osat_edge.real_data import (
    DATASET_ORDER,
    DATASETS,
    RealDataEvaluationError,
    _kuka_readers,
    evaluate_all_real_data,
    evaluate_real_dataset,
    write_real_data_report,
)


KUKA_HEADER = ";".join(
    [f"Iststrom_A{axis} (A)" for axis in range(1, 7)] + ["Sample"]
)


def _write_kuka(root: Path, *, bad_unit: bool = False) -> None:
    robot = root / "Robot_R1"
    robot.mkdir(parents=True)
    records = [(100 + index, 1 if index < 6 else 2) for index in range(12)]
    records.extend(((250, 3), (350, 4)))
    header = KUKA_HEADER.replace("Iststrom_A1 (A)", "Iststrom_A1 (mA)") if bad_unit else KUKA_HEADER
    for index, (payload, split) in enumerate(records):
        rows = [header]
        for sample in (0, 12, 24, 36):
            currents = [0.01 * axis + 0.0001 * index + sample * 0.00001 for axis in range(1, 7)]
            rows.append(";".join([*(str(value) for value in currents), str(sample)]))
        (robot / f"collector_{payload}_{split}.csv").write_text(
            "\n".join(rows) + "\n", encoding="utf-8"
        )


class RealDataEvaluationTests(unittest.TestCase):
    def test_registry_order_and_provenance_are_explicit(self) -> None:
        self.assertEqual(tuple(DATASETS), DATASET_ORDER)
        self.assertEqual(10, len(DATASET_ORDER))
        self.assertEqual("A", DATASETS["wafer-dicing-chang-2024"]["evidence_class"])
        self.assertEqual("B", DATASETS["phm-2018-ion-mill"]["evidence_class"])
        self.assertEqual("D", DATASETS["kuka-kr3"]["evidence_class"])

    def test_compatible_kuka_fixture_is_not_declared_real_without_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_kuka(root)
            report = evaluate_real_dataset("kuka-kr3", root)
        self.assertEqual("UNVERIFIED_EXTERNAL_INPUT", report["status"])
        self.assertEqual(DataOrigin.EXTERNAL_BENCHMARK.value, report["origin"])
        self.assertIsNone(report["source"])
        self.assertIsNone(report["real_data"])
        self.assertIsNone(report["synthetic_data"])
        self.assertFalse(report["provenance_verified"])
        self.assertEqual(14, report["runs"])
        self.assertEqual(1, report["machines"])

    def test_authenticated_kuka_fixture_uses_only_run_level_step02_step07(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_kuka(root)
            _source, content_hash, _md5, _files = _kuka_readers(root)
            with patch(
                "osat_edge.real_data.KUKA_OFFICIAL_CSV_SET_SHA256", content_hash
            ):
                report = evaluate_real_dataset("kuka-kr3", root)
        self.assertEqual("EXECUTED", report["status"])
        self.assertTrue(report["provenance_verified"])
        self.assertEqual(6, report["channel_coverage"]["mapped"])
        self.assertEqual(6, report["channel_coverage"]["total"])
        self.assertEqual(7, report["source_field_coverage"]["total_fields_including_timestamp"])
        self.assertFalse(report["full_station_representation"])
        self.assertTrue(report["pipeline"]["bounded_store"])
        self.assertTrue(report["pipeline"]["step02_run_statistics"])
        self.assertFalse(report["pipeline"]["step02_timing_features"])
        self.assertTrue(report["pipeline"]["step07_numerical_deviation"])
        self.assertFalse(report["pipeline"]["step09_health"])
        self.assertFalse(report["pipeline"]["step10_evidence"])
        self.assertFalse(report["pipeline"]["step15_ticket"])
        self.assertEqual(0, report["operational_ticket_count"])
        self.assertIsNone(report["classification_metrics"])
        self.assertEqual(1.0, report["pipeline_coverage"])
        self.assertEqual(["location", "spread"], report["feature_kinds_used"])
        self.assertEqual(
            "D1-D3 nominal calibration / D4 evaluation",
            report["machine_results"][0]["split"],
        )
        self.assertNotIn("state_distribution", report)
        self.assertNotIn("fault_evidence_records", report)

    def test_kuka_mapping_fails_closed_on_wrong_unit_header(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_kuka(root, bad_unit=True)
            with self.assertRaisesRegex(RealDataEvaluationError, "ampere units"):
                evaluate_real_dataset("kuka-kr3", root)

    def test_all_reports_present_invalid_data_as_rejected_not_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_kuka(root / "kuka-kr3", bad_unit=True)
            report = evaluate_all_real_data(root)
        kuka = next(item for item in report["datasets"] if item["dataset"] == "kuka-kr3")
        self.assertEqual("REJECTED_INVALID", kuka["status"])
        self.assertEqual(1, report["summary"]["rejected_invalid"])
        self.assertEqual(9, report["summary"]["unavailable"])

    def test_secom_labels_are_not_recast_as_equipment_health(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "secom.data").write_text(
                "1 NaN 3\n2 4 6\n7 8 9\n", encoding="utf-8"
            )
            (root / "secom_labels.data").write_text(
                '-1 "01/01/2008 00:00:00"\n1 "01/01/2008 00:01:00"\n-1 "01/01/2008 00:02:00"\n',
                encoding="utf-8",
            )
            report = evaluate_real_dataset("uci-secom", root)
        self.assertEqual("UNVERIFIED_EXTERNAL_INPUT", report["status"])
        self.assertEqual(
            {"pass": 2, "fail": 1}, report["observed_label_counts"]
        )
        self.assertIsNone(report["real_data"])
        self.assertEqual(0, report["operational_ticket_count"])

    def test_all_is_offline_and_missing_data_are_reported_honestly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = evaluate_all_real_data(root)
            self.assertFalse((root / ".artifacts").exists())
        self.assertEqual(10, report["summary"]["attempted"])
        self.assertEqual(10, report["summary"]["unavailable"])
        self.assertEqual(0, report["summary"]["operational_tickets"])

    def test_report_is_written_only_when_explicitly_called(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = evaluate_all_real_data(root / "missing")
            output = root / "reports"
            self.assertFalse(output.exists())
            path = write_real_data_report(report, output)
            stored = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual("comparison.json", path.name)
        self.assertEqual(DATASET_ORDER, tuple(stored["dataset_order"]))

    def test_report_excludes_runtime_and_is_byte_deterministic(self) -> None:
        first = {"dataset": "example", "runtime": {"elapsed_seconds": 1.0}, "value": 7}
        second = {"dataset": "example", "runtime": {"elapsed_seconds": 9.0}, "value": 7}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first_path = write_real_data_report(first, root / "first")
            second_path = write_real_data_report(second, root / "second")
            first_bytes = first_path.read_bytes()
            second_bytes = second_path.read_bytes()
        self.assertEqual(first_bytes, second_bytes)
        self.assertNotIn(b"runtime", first_bytes)

    def test_extracted_directory_resource_limits_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_kuka(root)
            with patch("osat_edge.real_data.MAXIMUM_KUKA_MEMBERS", 1):
                with self.assertRaisesRegex(RealDataEvaluationError, "too many files"):
                    evaluate_real_dataset("kuka-kr3", root)

    def test_cli_requires_a_path_for_one_dataset(self) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = main(["evaluate-real", "--dataset", "kuka-kr3"])
        self.assertEqual(2, result)
        self.assertIn("requires --path", stderr.getvalue())

    def test_committed_release_result_is_small_deterministic_and_code_pinned(self) -> None:
        root = Path(__file__).resolve().parents[1]
        result_path = root / "benchmarks" / "results" / "0.2.4-real-data.json"
        result = json.loads(result_path.read_text(encoding="utf-8"))
        evaluator = (root / "osat_edge" / "real_data.py").read_bytes()
        self.assertLess(result_path.stat().st_size, 20_000)
        self.assertEqual("0.2.4", result["release_version"])
        self.assertEqual(hashlib.sha256(evaluator).hexdigest(), result["evaluator_sha256"])
        serialized = json.dumps(result)
        self.assertNotIn('"runtime"', serialized)
        kuka = next(item for item in result["results"] if item["dataset"] == "kuka-kr3")
        self.assertFalse(kuka["step09_health_used"])
        self.assertFalse(kuka["step10_evidence_used"])

    def test_external_evaluator_has_no_step15_dependency(self) -> None:
        source = (
            Path(__file__).resolve().parents[1] / "osat_edge" / "real_data.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("step15_maintenance_ticket", source)
        self.assertNotIn("create_or_update_ticket", source)
        self.assertNotIn("from .roadmap.step09_health_risk", source)
        self.assertNotIn("from .roadmap.step10_fault_evidence", source)
        self.assertNotIn("from .roadmap.step06_machine_history", source)


if __name__ == "__main__":
    unittest.main()
