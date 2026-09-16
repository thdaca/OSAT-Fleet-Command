from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from osat_edge.roadmap.pre_steps.pre01_common.pre01_common import DataOrigin, RuntimeMode
from osat_edge.roadmap.post_steps.post01_demo.post01_demo import _fit_demo_model
from osat_edge.roadmap.pre_steps.pre02_machine_registry.pre02_machine_registry import STATIONS
from osat_edge.pipeline import MachinePipeline
from osat_edge.roadmap.post_steps.post02_reference_replay.post02_reference_replay import (
    DEFAULT_REFERENCE_DIRECTORY,
    ReferenceReplayError,
    load_reference_replay,
    run_reference_replay,
)
from osat_edge.roadmap.steps.step08_live_telemetry.step08_live_telemetry import ReplayTelemetrySource
from osat_edge.roadmap.steps.step11a_maintenance_db.step11a_maintenance_db import MaintenanceRepository


class ReferenceReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dataset = load_reference_replay()
        cls.report = run_reference_replay()

    def _copy_fixture(self, directory: str) -> Path:
        target = Path(directory) / "reference_replay"
        shutil.copytree(DEFAULT_REFERENCE_DIRECTORY, target)
        return target

    def _refresh_checksum(self, directory: Path, filename: str) -> None:
        manifest_path = directory / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["files"][filename] = hashlib.sha256(
            (directory / filename).read_bytes()
        ).hexdigest()
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    def test_frozen_artifact_is_small_human_readable_and_checksum_valid(self) -> None:
        names = {
            path.name
            for path in DEFAULT_REFERENCE_DIRECTORY.iterdir()
            if path.name != "__pycache__"
        }
        self.assertEqual(
            {
                "README.md",
                "manifest.json",
                "telemetry.csv",
                "context.csv",
                "source_mapping.json",
                "expected_checkpoints.json",
                "generate_reference_replay.py",
            },
            names,
        )
        self.assertLess(
            sum(
                path.stat().st_size
                for path in DEFAULT_REFERENCE_DIRECTORY.iterdir()
                if path.is_file()
            ),
            1_000_000,
        )
        self.assertEqual("osat-reference-fleet-001", self.dataset.manifest["dataset_id"])

    def test_generator_is_byte_reproducible_with_lf_on_this_platform(self) -> None:
        root = Path(__file__).resolve().parents[5]
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            committed = temporary / "committed"
            generated = temporary / "generated"
            shutil.copytree(DEFAULT_REFERENCE_DIRECTORY, committed)
            subprocess.run(
                [
                    sys.executable,
                    str(DEFAULT_REFERENCE_DIRECTORY / "generate_reference_replay.py"),
                    "--output",
                    str(generated),
                ],
                cwd=root,
                check=True,
            )
            self.assertEqual(
                {
                    path.name
                    for path in committed.iterdir()
                    if path.name not in {"generate_reference_replay.py", "__pycache__"}
                },
                {path.name for path in generated.iterdir()},
            )
            for expected in committed.iterdir():
                if expected.name in {"generate_reference_replay.py", "__pycache__"}:
                    continue
                with self.subTest(file=expected.name):
                    expected_bytes = expected.read_bytes()
                    self.assertEqual(expected_bytes, (generated / expected.name).read_bytes())
                    self.assertNotIn(b"\r\n", expected_bytes)
                    self.assertIn(b"\n", expected_bytes)

    def test_runtime_mode_and_data_origin_are_independent(self) -> None:
        self.assertIs(RuntimeMode.REAL_REPLAY, self.dataset.source.runtime_mode)
        self.assertIs(DataOrigin.SYNTHETIC, self.dataset.source.origin)
        self.assertEqual("DEMO-WS-01", self.dataset.identity.machine_id)
        self.assertEqual("wafer_saw", self.dataset.identity.family)

    def test_replay_uses_actual_pipeline_and_observed_checkpoints_match(self) -> None:
        expected = {
            row["name"]: row["expected"]
            for row in self.dataset.expected_checkpoints["checkpoints"]
        }
        observed = self.report["checkpoint_observations"]
        for name, fields in expected.items():
            with self.subTest(checkpoint=name):
                for key, value in fields.items():
                    self.assertEqual(value, observed[name][key])
        self.assertEqual(1, len(self.report["tickets"]))
        self.assertTrue(self.report["tickets"][0]["demo_only"])
        self.assertEqual("URGENT", self.report["tickets"][0]["priority"])
        self.assertEqual("CRITICAL", self.report["final_health"])
        self.assertEqual(1509, self.report["input_telemetry_rows"])
        self.assertEqual(1509, self.report["accepted_telemetry_rows"])
        self.assertEqual(0, self.report["rejected_telemetry_rows"])
        self.assertEqual(251, self.report["accepted_context_rows"])
        self.assertEqual(0, self.report["rejected_context_rows"])
        self.assertTrue(
            {"NORMAL", "WATCH", "DEGRADED", "CRITICAL", "UNKNOWN"}
            .issubset(self.report["health_counts"])
        )

    def test_reference_trace_includes_stale_unknown_and_physics_abstention(self) -> None:
        stale = self.report["checkpoint_observations"]["required_stale"]
        abstains = self.report["checkpoint_observations"]["physics_abstains"]
        resumes = self.report["checkpoint_observations"]["physics_resumes"]
        self.assertFalse(stale["telemetry_valid"])
        self.assertEqual("UNKNOWN", stale["health"])
        self.assertFalse(abstains["physics_residual_present"])
        self.assertTrue(resumes["physics_residual_present"])
        self.assertGreater(self.report["physics_abstention_ticks"], 0)
        self.assertGreater(self.report["maximum_positive_residual_a"], 0.0)

    def test_expected_results_do_not_control_inference(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = self._copy_fixture(directory)
            path = fixture / "expected_checkpoints.json"
            value = json.loads(path.read_text(encoding="utf-8"))
            value["checkpoints"][-1]["expected"]["health"] = "NORMAL"
            path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            self._refresh_checksum(fixture, path.name)
            report = run_reference_replay(fixture)
        self.assertEqual("CRITICAL", report["final_health"])

    def test_checksum_tampering_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = self._copy_fixture(directory)
            path = fixture / "telemetry.csv"
            path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ReferenceReplayError, "Checksum mismatch"):
                load_reference_replay(fixture)

    def test_manifest_claims_and_classification_are_internally_consistent(self) -> None:
        mutations = (
            (lambda value: value.update(production_qualified=True), "production_qualified"),
            (
                lambda value: value.update(claims=["REAL OSAT DATA", "PLANT VALIDATION"]),
                "manifest.claims",
            ),
            (lambda value: value.update(classification=["FROZEN"]), "classification"),
        )
        for mutate, message in mutations:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as directory:
                fixture = self._copy_fixture(directory)
                path = fixture / "manifest.json"
                value = json.loads(path.read_text(encoding="utf-8"))
                mutate(value)
                path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                with self.assertRaisesRegex(ReferenceReplayError, message):
                    load_reference_replay(fixture)

    def test_manifest_timeline_and_phases_match_actual_records(self) -> None:
        mutations = (
            (
                lambda value: value["timeline"].update(start_utc="2026-02-02T14:00:01Z"),
                "timeline",
            ),
            (
                lambda value: value["phases"][0].update(end_seconds=251),
                "inside the dataset interval",
            ),
            (
                lambda value: value["phases"][1].update(name="healthy_stable"),
                "known and unique",
            ),
        )
        for mutate, message in mutations:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as directory:
                fixture = self._copy_fixture(directory)
                path = fixture / "manifest.json"
                value = json.loads(path.read_text(encoding="utf-8"))
                mutate(value)
                path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                with self.assertRaisesRegex(ReferenceReplayError, message):
                    load_reference_replay(fixture)

    def test_json_objects_reject_unknown_structural_fields(self) -> None:
        mutations = (
            (
                "manifest.json",
                lambda value: value.update(real_osat_validation=True),
                "manifest has unknown fields",
                False,
            ),
            (
                "manifest.json",
                lambda value: value["machine"].update(lot_id="SECRET"),
                "manifest.machine has unknown fields",
                False,
            ),
            (
                "manifest.json",
                lambda value: value["timeline"].update(customer="SECRET"),
                "manifest.timeline has unknown fields",
                False,
            ),
            (
                "manifest.json",
                lambda value: value["phases"][0].update(process_window="SECRET"),
                r"manifest.phases\[0\] has unknown fields",
                False,
            ),
            (
                "source_mapping.json",
                lambda value: value.update(real_osat_validation=True),
                "source_mapping has unknown fields",
                True,
            ),
            (
                "source_mapping.json",
                lambda value: value["mappings"][0].update(lot_id="SECRET"),
                r"mappings\[0\] has unknown fields",
                True,
            ),
            (
                "expected_checkpoints.json",
                lambda value: value.update(customer="SECRET"),
                "expected_checkpoints has unknown fields",
                True,
            ),
            (
                "expected_checkpoints.json",
                lambda value: value["checkpoints"][0].update(lot_id="SECRET"),
                r"checkpoints\[0\] has unknown fields",
                True,
            ),
            (
                "expected_checkpoints.json",
                lambda value: value["checkpoints"][0]["expected"].update(
                    real_osat_validation=True
                ),
                "unknown expected fields",
                True,
            ),
        )
        for filename, mutate, message, refresh in mutations:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as directory:
                fixture = self._copy_fixture(directory)
                path = fixture / filename
                value = json.loads(path.read_text(encoding="utf-8"))
                mutate(value)
                path.write_text(
                    json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                if refresh:
                    self._refresh_checksum(fixture, filename)
                with self.assertRaisesRegex(ReferenceReplayError, message):
                    load_reference_replay(fixture)

    def test_reference_directory_rejects_unexpected_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = self._copy_fixture(directory)
            (fixture / "secret_recipe.txt").write_text("SECRET", encoding="utf-8")
            with self.assertRaisesRegex(ReferenceReplayError, "exactly the six"):
                load_reference_replay(fixture)

    def test_top_level_expected_summary_is_checked_after_replay(self) -> None:
        mutations = (
            ("expected_final_state", "NORMAL"),
            ("expected_subsystem", "cooling"),
            ("expected_ticket_priority", "HIGH"),
        )
        for field, replacement in mutations:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                fixture = self._copy_fixture(directory)
                path = fixture / "expected_checkpoints.json"
                value = json.loads(path.read_text(encoding="utf-8"))
                value[field] = replacement
                path.write_text(
                    json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                self._refresh_checksum(fixture, path.name)
                with self.assertRaisesRegex(ReferenceReplayError, field):
                    run_reference_replay(fixture)

    def test_csv_rows_reject_surplus_and_missing_values(self) -> None:
        for filename, surplus, message in (
            ("telemetry.csv", True, "surplus fields"),
            ("telemetry.csv", False, "missing fields"),
            ("context.csv", True, "surplus fields"),
            ("context.csv", False, "missing fields"),
        ):
            with self.subTest(file=filename, surplus=surplus), tempfile.TemporaryDirectory() as directory:
                fixture = self._copy_fixture(directory)
                path = fixture / filename
                lines = path.read_text(encoding="utf-8").splitlines()
                lines[1] = (
                    f"{lines[1]},SECRET_PROCESS_IP"
                    if surplus
                    else ",".join(lines[1].split(",")[:-1])
                )
                path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                self._refresh_checksum(fixture, filename)
                with self.assertRaisesRegex(ReferenceReplayError, message):
                    load_reference_replay(fixture)

    def test_fail_closed_schema_and_data_validation(self) -> None:
        mutations = (
            (
                "source_mapping.json",
                lambda value: value["mappings"][0].update(source_id="UNAPPROVED"),
                "unapproved source_id",
                "telemetry.csv",
                lambda text: text,
            ),
            (
                "source_mapping.json",
                lambda value: value["mappings"][0].update(unit="V"),
                "unit",
                None,
                None,
            ),
        )
        for filename, mutate, message, second_name, second_mutate in mutations:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as directory:
                fixture = self._copy_fixture(directory)
                path = fixture / filename
                value = json.loads(path.read_text(encoding="utf-8"))
                mutate(value)
                path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                self._refresh_checksum(fixture, filename)
                if second_name is not None:
                    second = fixture / second_name
                    second.write_text(second_mutate(second.read_text(encoding="utf-8")), encoding="utf-8")
                    self._refresh_checksum(fixture, second_name)
                with self.assertRaisesRegex(ReferenceReplayError, message):
                    load_reference_replay(fixture)

    def test_nonfinite_and_duplicate_channel_records_are_rejected(self) -> None:
        for replacement, message in ((",nan,A", "finite"), (None, "Duplicate")):
            with self.subTest(message=message), tempfile.TemporaryDirectory() as directory:
                fixture = self._copy_fixture(directory)
                path = fixture / "telemetry.csv"
                lines = path.read_text(encoding="utf-8").splitlines()
                if replacement is None:
                    lines.insert(2, lines[1])
                else:
                    parts = lines[1].split(",")
                    parts[3] = "nan"
                    lines[1] = ",".join(parts)
                path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                self._refresh_checksum(fixture, path.name)
                with self.assertRaisesRegex(ReferenceReplayError, message):
                    load_reference_replay(fixture)

    def test_real_osat_replay_still_rejects_synthetic_machine_model(self) -> None:
        source = ReplayTelemetrySource(
            self.dataset.identity,
            self.dataset.station,
            self.dataset.source._batches,
            origin=DataOrigin.REAL_OSAT,
        )
        with tempfile.TemporaryDirectory() as directory, self.assertRaisesRegex(
            ValueError, "reject synthetic exact-machine"
        ):
            MachinePipeline(
                identity=self.dataset.identity,
                station=self.dataset.station,
                source=source,
                repository=MaintenanceRepository(Path(directory) / "tickets.sqlite"),
                machine_model=_fit_demo_model(self.dataset.identity, self.dataset.station),
            )

    def test_unvalidated_synthetic_replay_cannot_create_a_demo_ticket(self) -> None:
        source = ReplayTelemetrySource(
            self.dataset.identity,
            self.dataset.station,
            self.dataset.source._batches,
            origin=DataOrigin.SYNTHETIC,
        )
        with tempfile.TemporaryDirectory() as directory:
            repository = MaintenanceRepository(Path(directory) / "tickets.sqlite")
            pipeline = MachinePipeline(
                identity=self.dataset.identity,
                station=self.dataset.station,
                source=source,
                repository=repository,
                machine_model=_fit_demo_model(self.dataset.identity, self.dataset.station),
            )
            while pipeline.tick() is not None:
                pass
            self.assertEqual([], repository.list_tickets())

    def test_replay_source_requires_explicit_origin(self) -> None:
        with self.assertRaises(TypeError):
            ReplayTelemetrySource(  # type: ignore[call-arg]
                self.dataset.identity,
                STATIONS["wafer_saw"],
                self.dataset.source._batches,
            )


if __name__ == "__main__":
    unittest.main()
