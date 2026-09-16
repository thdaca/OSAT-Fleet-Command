from __future__ import annotations

import contextlib
import datetime as dt
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from osat_edge.ui.cli import main
from osat_edge.roadmap.pre_steps.pre01_common.pre01_common import DataOrigin, EquipmentState, VERSION
from osat_edge.roadmap.post_steps.post04_real_data_evaluation.post04_real_data_evaluation import (
    HISTORICAL_EVIDENCE_PATH,
    DATASET_ORDER,
    DATASETS,
    RealDataEvaluationError,
    _fit_nominal_benchmark_model,
    _r2r_source_field_coverage,
    current_real_data_evidence_record,
    evaluate_all_real_data,
    evaluate_real_dataset,
    verify_committed_real_data_evidence,
    write_real_data_report,
)
from osat_edge.roadmap.steps.step02_physical_features.step02_physical_features import Feature, FeatureSet
from osat_edge.roadmap.steps.step06_machine_history.step06_machine_history import HealthyInterval, MachineHistory
from osat_edge.roadmap.steps.step07_machine_model.step07_machine_model import fit_machine_model
from osat_edge.roadmap.pre_steps.pre01_common.tests.support import identity


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
        self.assertEqual(13, len(DATASET_ORDER))
        self.assertEqual(("st-awfd-d1", "st-awfd-d2", "tuhh-dad3350-surface"), DATASET_ORDER[:3])
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

    def test_r2r_headline_coverage_uses_all_classified_physical_fields(self) -> None:
        mapped = {
            "Film Tension #1 (kg)",
            "Film Tension #2 (kg)",
            "Film Tension #3 (kg)",
            "Web Current Speed (mm/sec)",
        }
        schema = (
            "Date",
            "Model",
            "Trigger",
            "Film kind",
            "OutFeeder-Control: Kp",
            *sorted(mapped),
            "Film width (mm)",
            "Master roll speed (mm/sec)",
        )
        headline, source_fields = _r2r_source_field_coverage(schema, mapped)
        self.assertEqual({"mapped": 4, "total": 6, "fraction": 4 / 6}, headline)
        self.assertEqual(11, source_fields["inspected_source_fields"])
        self.assertEqual(4, source_fields["metadata_or_label_fields_excluded"])
        self.assertEqual(1, source_fields["controller_configuration_fields_excluded"])
        self.assertNotEqual(1.0, source_fields["fraction"])

    def test_benchmark_nominal_fit_is_numerically_equivalent_to_step07(self) -> None:
        machine = identity()
        start = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
        regular = np.arange(12, dtype=np.float64)
        std_fallback = np.asarray([0.0] * 11 + [10.0])
        floor_from_center = np.full(12, 2.0)
        absolute_floor = np.full(12, 1e-8)
        rows: list[FeatureSet] = []
        for index in range(12):
            window_start = start + dt.timedelta(minutes=index)
            window_end = window_start + dt.timedelta(seconds=30)
            rows.append(
                FeatureSet(
                    machine,
                    window_end,
                    EquipmentState.PROCESSING,
                    window_start,
                    window_end,
                    (
                        Feature("regular", float(regular[index]), "spindle", "location"),
                        Feature("std_fallback", float(std_fallback[index]), "spindle", "spread"),
                        Feature("floor_from_center", float(floor_from_center[index]), "spindle", "location"),
                        Feature("absolute_floor", float(absolute_floor[index]), "spindle", "location"),
                    ),
                )
            )
        interval = HealthyInterval(
            machine.machine_id,
            start - dt.timedelta(seconds=1),
            rows[-1].window_end + dt.timedelta(seconds=1),
        )
        operational_model = fit_machine_model(
            MachineHistory(machine, DataOrigin.SYNTHETIC, tuple(rows), (interval,))
        )
        self.assertIs(DataOrigin.SYNTHETIC, operational_model.origin)
        operational = operational_model.contexts[EquipmentState.PROCESSING]
        benchmark = _fit_nominal_benchmark_model(
            machine, rows
        ).contexts[EquipmentState.PROCESSING]
        self.assertEqual(operational.feature_names, benchmark.feature_names)
        np.testing.assert_array_equal(operational.center, benchmark.center)
        np.testing.assert_array_equal(operational.scale, benchmark.scale)
        self.assertEqual(0.02, operational.scale[2])
        self.assertEqual(0.0001, operational.scale[3])

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
        self.assertEqual(12, report["summary"]["unavailable"])

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
        self.assertEqual(13, report["summary"]["attempted"])
        self.assertEqual(13, report["summary"]["unavailable"])
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

    def test_committed_evidence_verifier_is_offline_and_detects_drift(self) -> None:
        report = {
            "version": VERSION,
            "origin": DataOrigin.EXTERNAL_BENCHMARK.value,
            "dataset_order": ["fixture"],
            "datasets": [
                {
                    "dataset": "fixture",
                    "status": "UNAVAILABLE",
                    "source_sha256": None,
                    "channel_coverage": {"mapped": 0, "total": 0, "fraction": None},
                }
            ],
            "summary": {"operational_tickets": 0},
        }
        committed = current_real_data_evidence_record(report)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            path.write_text(json.dumps(committed), encoding="utf-8")
            with patch(
                "osat_edge.roadmap.post_steps.post04_real_data_evaluation.post04_real_data_evaluation.evaluate_all_real_data",
                return_value=report,
            ):
                verified = verify_committed_real_data_evidence(Path(directory), path)
                self.assertEqual("PASS", verified["status"])
                committed["deterministic_comparison_report_sha256"] = "f" * 64
                path.write_text(json.dumps(committed), encoding="utf-8")
                with self.assertRaisesRegex(RealDataEvaluationError, "DRIFT"):
                    verify_committed_real_data_evidence(Path(directory), path)

    def test_extracted_directory_resource_limits_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_kuka(root)
            with patch(
                "osat_edge.roadmap.post_steps.post04_real_data_evaluation.datasets.kuka.MAXIMUM_KUKA_MEMBERS",
                1,
            ):
                with self.assertRaisesRegex(RealDataEvaluationError, "too many files"):
                    evaluate_real_dataset("kuka-kr3", root)

    def test_cli_requires_a_path_for_one_dataset(self) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = main(["evaluate-real", "--dataset", "kuka-kr3"])
        self.assertEqual(2, result)
        self.assertIn("requires --path", stderr.getvalue())

    def test_committed_release_result_is_small_deterministic_and_code_pinned(self) -> None:
        result_path = HISTORICAL_EVIDENCE_PATH
        result = json.loads(result_path.read_text(encoding="utf-8"))
        self.assertLess(result_path.stat().st_size, 20_000)
        self.assertEqual("0.2.4-real-data.json", result_path.name)
        self.assertEqual("0.2.4", result["release_version"])
        self.assertEqual(
            "7c8fc2c86679227b95bafafcfe2e83a421e3098cb64cc4b50d21a05089de27b9",
            result["evaluator_sha256"],
        )
        self.assertEqual(
            "371b9f6c40f2185a5d505f373483973f7f5974c276890d0616b9a715706014b3",
            hashlib.sha256(result_path.read_bytes()).hexdigest(),
        )
        serialized = json.dumps(result)
        self.assertNotIn('"runtime"', serialized)
        kuka = next(item for item in result["results"] if item["dataset"] == "kuka-kr3")
        self.assertFalse(kuka["step09_health_used"])
        self.assertFalse(kuka["step10_evidence_used"])

    def test_external_evaluator_has_no_step15_dependency(self) -> None:
        root = Path(__file__).resolve().parents[1]
        source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((root / "core").glob("*.py"))
            + sorted((root / "datasets").glob("*.py"))
            + [root / "post04_real_data_evaluation.py"]
        )
        self.assertNotIn("step15_maintenance_ticket", source)
        self.assertNotIn("create_or_update_ticket", source)
        self.assertNotIn("step09_health_risk", source)
        self.assertNotIn("step10_fault_evidence", source)
        self.assertNotIn("step06_machine_history", source)


if __name__ == "__main__":
    unittest.main()
