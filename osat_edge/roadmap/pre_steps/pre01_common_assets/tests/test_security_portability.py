from __future__ import annotations

import ast
import importlib
import pathlib
import re
import tempfile
import unittest

from osat_edge.roadmap.pre_steps.pre01_common import VERSION, utc
from osat_edge.roadmap.post_steps.post02_reference_replay import DEFAULT_REFERENCE_DIRECTORY
from osat_edge.roadmap.post_steps.post04_real_data_evaluation import (
    COMMITTED_EVIDENCE_PATH,
    DEFAULT_EXTERNAL_DATA_ROOT,
)
from osat_edge.roadmap.steps.step11b_oem_manuals import DEFAULT_MANUALS_PATH


ROOT = pathlib.Path(__file__).resolve().parents[5]


class SecurityPortabilityTests(unittest.TestCase):
    def test_repository_organization_is_enforced(self) -> None:
        package_root = ROOT / "osat_edge"
        self.assertEqual(
            {"__init__.py", "pipeline.py"},
            {path.name for path in package_root.glob("*.py")},
        )
        self.assertFalse(any((ROOT / "tests").glob("*.py")))
        self.assertFalse(any((ROOT / "tools").glob("*.py")))
        for generic in ("config", "examples", "knowledge"):
            directory = ROOT / generic
            self.assertFalse(
                any(path.is_file() for path in directory.rglob("*") if "__pycache__" not in path.parts),
                f"Stage-owned resources must not return to {generic}/",
            )
        self.assertEqual(
            {"STUDENT_GUIDE.md"},
            {path.name for path in (ROOT / "docs").glob("*") if path.is_file()},
        )
        old = {
            "artifacts.py", "baseline.py", "contracts.py", "data_quality.py",
            "evaluation.py", "features.py", "health.py", "historical.py",
            "ingestion.py", "maintenance.py", "offline.py", "physics.py",
            "qualification.py", "rag.py", "registry.py", "risk.py", "runtime.py",
            "simulation.py", "telemetry.py", "theme.py",
            "common.py", "machines.py", "demo.py", "benchmark.py", "real_data.py",
            "reference_replay.py", "ui.py",
        }
        present = {path.name for path in package_root.rglob("*.py")}
        self.assertTrue(old.isdisjoint(present))
        self.assertEqual("0.2.4", VERSION)

    def test_no_old_import_paths_or_duplicate_station_registry(self) -> None:
        package_root = ROOT / "osat_edge"
        banned = {
            "osat_edge.common", "osat_edge.machines", "osat_edge.demo",
            "osat_edge.benchmark", "osat_edge.real_data",
            "osat_edge.reference_replay", "osat_edge.cli",
        }
        station_definitions: list[pathlib.Path] = []
        for path in package_root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    self.assertNotIn(node.module, banned, str(path))
                    self.assertIsNone(
                        re.fullmatch(r"osat_edge\.roadmap\.step[0-9].*", node.module),
                        str(path),
                    )
                elif isinstance(node, ast.Import):
                    for name in node.names:
                        self.assertNotIn(name.name, banned, str(path))
            if "_assets" not in path.as_posix() and re.search(
                r"^STATIONS\s*[:=]", path.read_text(encoding="utf-8"), re.MULTILINE
            ):
                station_definitions.append(path)
        self.assertEqual(
            [package_root / "roadmap" / "pre_steps" / "pre02_machine_registry.py"],
            station_definitions,
        )

    def test_every_runtime_module_imports_without_a_cycle(self) -> None:
        package_root = ROOT / "osat_edge"
        modules = []
        for path in package_root.rglob("*.py"):
            if "_assets" in path.as_posix():
                continue
            relative = path.relative_to(ROOT).with_suffix("")
            parts = relative.parts[:-1] if relative.name == "__init__" else relative.parts
            modules.append(".".join(parts))
        for module in sorted(modules):
            with self.subTest(module=module):
                importlib.import_module(module)

    def test_bundled_resource_paths_are_absolute_and_cwd_independent(self) -> None:
        for path in (
            DEFAULT_MANUALS_PATH,
            DEFAULT_REFERENCE_DIRECTORY,
            COMMITTED_EVIDENCE_PATH,
            DEFAULT_EXTERNAL_DATA_ROOT,
        ):
            self.assertTrue(path.is_absolute())
        self.assertTrue(DEFAULT_MANUALS_PATH.is_file())
        self.assertTrue(DEFAULT_REFERENCE_DIRECTORY.is_dir())
        self.assertTrue(COMMITTED_EVIDENCE_PATH.is_file())

    def test_source_uses_no_eval_or_hard_coded_unix_temp_path(self) -> None:
        source = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "osat_edge").rglob("*.py"))
        self.assertNotIn("eval" + "(", source)
        self.assertNotIn(chr(34) + "/" + "tmp", source)
        self.assertNotIn(chr(39) + "/" + "tmp", source)

    def test_dependency_files_list_only_direct_core_and_optional_llm(self) -> None:
        core = [line for line in (ROOT / "requirements.txt").read_text().splitlines() if line and not line.startswith("#")]
        optional = (
            ROOT
            / "osat_edge"
            / "roadmap"
            / "steps"
            / "step13_local_llm_assets"
            / "resources"
            / "requirements-llm.txt"
        ).read_text()
        self.assertEqual(["numpy==2.5.1", "scikit-learn==1.9.0", "PyQt6==6.11.0"], core)
        self.assertIn("llama-cpp-python", optional)
        self.assertNotIn("llama-cpp-python", "\n".join(core))

    def test_windows_safe_temporary_paths_and_aware_time(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "portable.sqlite"
            path.touch()
            self.assertTrue(path.is_file())
        import datetime as dt
        with self.assertRaises(ValueError):
            utc(dt.datetime(2026, 1, 1))


if __name__ == "__main__":
    unittest.main()
