from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from osat_edge.cli import main
from osat_edge.common import DataOrigin
from osat_edge.real_data import (
    DATASET_ORDER,
    DATASETS,
    RealDataEvaluationError,
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

    def test_tiny_kuka_fixture_uses_external_pipeline_without_tickets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_kuka(root)
            report = evaluate_real_dataset("kuka-kr3", root)
        self.assertEqual("EXECUTED", report["status"])
        self.assertEqual(DataOrigin.EXTERNAL_BENCHMARK.value, report["origin"])
        self.assertEqual(14, report["runs"])
        self.assertEqual(1, report["machines"])
        self.assertEqual(6, report["channel_coverage"]["mapped"])
        self.assertEqual(6, report["channel_coverage"]["total"])
        self.assertEqual(7, report["source_field_coverage"]["total_fields_including_timestamp"])
        self.assertFalse(report["full_station_representation"])
        self.assertTrue(report["pipeline"]["bounded_store"])
        self.assertTrue(report["pipeline"]["step02_features"])
        self.assertTrue(report["pipeline"]["step07_exact_machine_score"])
        self.assertTrue(report["pipeline"]["step09_health"])
        self.assertTrue(report["pipeline"]["step10_evidence"])
        self.assertFalse(report["pipeline"]["step15_ticket"])
        self.assertEqual(0, report["operational_ticket_count"])
        self.assertIsNone(report["classification_metrics"])
        self.assertEqual(1.0, report["pipeline_coverage"])

    def test_kuka_mapping_fails_closed_on_wrong_unit_header(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_kuka(root, bad_unit=True)
            with self.assertRaisesRegex(RealDataEvaluationError, "ampere units"):
                evaluate_real_dataset("kuka-kr3", root)

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
        self.assertEqual("INSPECTED_NOT_EXECUTABLE", report["status"])
        self.assertEqual({"pass": 2, "fail": 1}, report["label_counts"])
        self.assertEqual(0, report["channel_coverage"]["mapped"])
        self.assertIsNone(report["classification_metrics"])
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

    def test_cli_requires_a_path_for_one_dataset(self) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = main(["evaluate-real", "--dataset", "kuka-kr3"])
        self.assertEqual(2, result)
        self.assertIn("requires --path", stderr.getvalue())

    def test_external_evaluator_has_no_step15_dependency(self) -> None:
        source = (
            Path(__file__).resolve().parents[1] / "osat_edge" / "real_data.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("step15_maintenance_ticket", source)
        self.assertNotIn("create_or_update_ticket", source)


if __name__ == "__main__":
    unittest.main()
