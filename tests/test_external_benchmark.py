from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
from scipy.io import savemat

from osat_edge.benchmark import (
    BenchmarkDatasetNotFound,
    BenchmarkError,
    REQUIRED_FIELDS,
    analyze_nasa_milling,
    write_benchmark_report,
)
from osat_edge.cli import main
from osat_edge.common import DataOrigin


def _write_mat(path: Path, *, nonfinite: bool = False, omit: str | None = None) -> None:
    fields = tuple(field for field in REQUIRED_FIELDS if field != omit)
    records = np.empty((1, 4), dtype=[(field, "O") for field in fields])
    for index in range(4):
        values = {
            "case": 1,
            "run": index + 1,
            "VB": np.nan if index == 1 else 0.1 * index,
            "time": index * 5,
            "DOC": 0.75,
            "feed": 0.25,
            "material": 1,
            "smcAC": np.asarray([1.0, 2.0 + index, 3.0]),
            "smcDC": np.asarray([4.0, 5.0 + index, 6.0]),
            "vib_table": np.asarray([0.1, 0.2, 0.3]),
            "vib_spindle": np.asarray([0.4, 0.5 - index * 0.02, 0.6]),
            "AE_table": np.asarray([0.1, 0.2, 0.3]),
            "AE_spindle": np.asarray([0.1, 0.2, 0.3]),
        }
        if nonfinite:
            values["smcAC"] = np.asarray([1.0, np.inf, 3.0])
        for field in fields:
            records[field][0, index] = values[field]
    savemat(path, {"mill": records})


class ExternalBenchmarkTests(unittest.TestCase):
    def test_tiny_mat_fixture_is_parsed_descriptively(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mill.mat"
            _write_mat(path)
            report = analyze_nasa_milling(path)
        self.assertEqual(DataOrigin.EXTERNAL_BENCHMARK.value, report["origin"])
        self.assertEqual(1, report["cases"])
        self.assertEqual(4, report["runs"])
        self.assertEqual(3, report["runs_with_measured_vb"])
        self.assertEqual(1, report["operating_conditions"])
        first = report["run_summaries"][0]["signals"]
        self.assertNotEqual(first["smcAC"]["median"], first["smcDC"]["median"])
        self.assertFalse(report["spindle_speed"]["compatible_time_series_present"])
        self.assertNotIn("health_state", report)
        self.assertNotIn("tickets", report)

    def test_missing_dataset_has_clean_cli_failure(self) -> None:
        missing = Path("definitely-missing-nasa-milling.mat")
        with self.assertRaisesRegex(BenchmarkDatasetNotFound, "NASA MILLING DATASET NOT FOUND"):
            analyze_nasa_milling(missing)
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = main(["benchmark-nasa-milling", "--dataset", str(missing)])
        self.assertEqual(2, result)
        self.assertEqual("NASA MILLING DATASET NOT FOUND", stderr.getvalue().strip())

    def test_malformed_structure_and_nonfinite_signal_fail_closed(self) -> None:
        for omit, nonfinite, message in (
            ("VB", False, "missing fields"),
            (None, True, "finite signal"),
        ):
            with self.subTest(message=message), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "mill.mat"
                _write_mat(path, omit=omit, nonfinite=nonfinite)
                with self.assertRaisesRegex(BenchmarkError, message):
                    analyze_nasa_milling(path)

    def test_full_report_is_written_only_when_explicitly_requested(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset = root / "mill.mat"
            output = root / "report.json"
            _write_mat(dataset)
            report = analyze_nasa_milling(dataset)
            self.assertFalse(output.exists())
            self.assertEqual(output, write_benchmark_report(report, output))
            stored = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(4, len(stored["run_summaries"]))

    def test_canonical_mat_hash_is_stable_across_direct_and_zip_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset = root / "mill.mat"
            archive = root / "dataset.zip"
            _write_mat(dataset)
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as output:
                output.write(dataset, arcname="nested/mill.mat")
            direct = analyze_nasa_milling(dataset)
            zipped = analyze_nasa_milling(archive)
            serialized = json.dumps(zipped)
        self.assertEqual(direct["mill_mat_sha256"], zipped["mill_mat_sha256"])
        self.assertEqual(
            direct["mill_mat_sha256"], direct["source_artifact_sha256"]
        )
        self.assertNotEqual(
            zipped["mill_mat_sha256"], zipped["source_artifact_sha256"]
        )
        self.assertEqual("mill.mat", direct["requested_dataset"])
        self.assertEqual("mill.mat", direct["selected_mat_source"])
        self.assertEqual("dataset.zip", zipped["requested_dataset"])
        self.assertEqual("dataset.zip!nested/mill.mat", zipped["selected_mat_source"])
        self.assertNotIn(str(root.resolve()), serialized)

    def test_dataset_resource_limits_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset = root / "mill.mat"
            archive = root / "dataset.zip"
            _write_mat(dataset)
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as output:
                output.write(dataset, arcname="mill.mat")

            with patch("osat_edge.benchmark.MAXIMUM_RECORDS", 3), self.assertRaisesRegex(
                BenchmarkError, "too many records"
            ):
                analyze_nasa_milling(dataset)
            with patch(
                "osat_edge.benchmark.MAXIMUM_SIGNAL_SAMPLES", 2
            ), self.assertRaisesRegex(BenchmarkError, "signal-length"):
                analyze_nasa_milling(dataset)
            with patch("osat_edge.benchmark.MAXIMUM_MAT_BYTES", 1), self.assertRaisesRegex(
                BenchmarkError, "member exceeds"
            ):
                analyze_nasa_milling(archive)

            deepest = io.BytesIO()
            with zipfile.ZipFile(deepest, "w") as output:
                output.write(dataset, arcname="mill.mat")
            middle = io.BytesIO()
            with zipfile.ZipFile(middle, "w") as output:
                output.writestr("deeper.zip", deepest.getvalue())
            over_nested = root / "over-nested.zip"
            with zipfile.ZipFile(over_nested, "w") as output:
                output.writestr("middle.zip", middle.getvalue())
            with self.assertRaisesRegex(BenchmarkError, "nesting"):
                analyze_nasa_milling(over_nested)

    def test_benchmark_module_is_isolated_from_osat_inference(self) -> None:
        source = (Path(__file__).resolve().parents[1] / "osat_edge" / "benchmark.py").read_text(
            encoding="utf-8"
        )
        for forbidden in (".pipeline", ".roadmap", ".machines", ".ui"):
            self.assertNotIn(forbidden, source)

    def test_benchmark_dependency_is_optional_and_core_pins_are_unchanged(self) -> None:
        root = Path(__file__).resolve().parents[1]
        core = [
            line
            for line in (root / "requirements.txt").read_text(encoding="utf-8").splitlines()
            if line and not line.startswith("#")
        ]
        optional = (root / "requirements-benchmarks.txt").read_text(encoding="utf-8")
        self.assertEqual(
            ["numpy==2.5.1", "scikit-learn==1.9.0", "PyQt6==6.11.0"], core
        )
        self.assertIn("scipy==1.18.1", optional)

    @unittest.skipUnless(
        os.environ.get("NASA_MILLING_DATASET"),
        "Set NASA_MILLING_DATASET for optional official-data integration",
    )
    def test_optional_official_dataset_integration(self) -> None:
        report = analyze_nasa_milling(os.environ["NASA_MILLING_DATASET"])
        self.assertEqual(167, report["runs"])
        self.assertEqual(16, report["cases"])
        self.assertEqual(146, report["runs_with_measured_vb"])


if __name__ == "__main__":
    unittest.main()
