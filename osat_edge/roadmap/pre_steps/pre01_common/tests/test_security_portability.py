from __future__ import annotations

import ast
import hashlib
import importlib
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest

from osat_edge.roadmap.pre_steps.pre01_common.pre01_common import VERSION, utc
from osat_edge.roadmap.post_steps.post02_reference_replay.post02_reference_replay import DEFAULT_REFERENCE_DIRECTORY
from osat_edge.roadmap.post_steps.post04_real_data_evaluation.post04_real_data_evaluation import (
    COMMITTED_EVIDENCE_PATH,
    DEFAULT_EXTERNAL_DATA_ROOT,
)
from osat_edge.roadmap.steps.step11b_oem_manuals.step11b_oem_manuals import DEFAULT_MANUALS_PATH


ROOT = pathlib.Path(__file__).resolve().parents[5]


class SecurityPortabilityTests(unittest.TestCase):
    def test_repository_organization_is_enforced(self) -> None:
        package_root = ROOT / "osat_edge"
        self.assertEqual(
            {
                ".artifacts", ".gitignore", ".venv", "AGENTS.md", "README.md",
                "STUDENT_GUIDE.md", "benchmarks", "osat_edge", "requirements.txt",
            },
            {path.name for path in ROOT.iterdir()},
        )
        self.assertEqual(
            {"__init__.py", "pipeline.py"},
            {path.name for path in package_root.glob("*.py")},
        )
        self.assertTrue((ROOT / "STUDENT_GUIDE.md").is_file())
        self.assertFalse(
            any("_assets" in path.name for path in package_root.rglob("*")),
            "Stage assets must live directly under their owning stage folder",
        )
        for obsolete_root in ("config", "docs", "examples", "knowledge", "tests", "tools"):
            self.assertFalse(
                (ROOT / obsolete_root).exists(),
                f"The obsolete root {obsolete_root}/ must not be recreated",
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
        stage_groups = {
            package_root / "roadmap" / "pre_steps": (
                "pre01_common", "pre02_machine_registry", "pre03_data_provenance",
            ),
            package_root / "roadmap" / "steps": (
                "step01_physics_library", "step02_physical_features",
                "step03_physical_residuals", "step04_family_data",
                "step05_family_model", "step06_machine_history",
                "step07_machine_model", "step08_live_telemetry",
                "step09_health_risk", "step10_fault_evidence",
                "step11a_maintenance_db", "step11b_oem_manuals", "step12_rag",
                "step13_local_llm", "step14_json_validation",
                "step15_maintenance_ticket",
            ),
            package_root / "roadmap" / "post_steps": (
                "post01_demo", "post02_reference_replay",
                "post03_external_benchmark", "post04_real_data_evaluation",
            ),
        }
        for parent, stages in stage_groups.items():
            self.assertEqual(
                set(stages),
                {
                    path.name
                    for path in parent.iterdir()
                    if path.is_dir() and path.name != "__pycache__"
                },
            )
            self.assertEqual(["__init__.py"], sorted(path.name for path in parent.glob("*.py")))
            for stage in stages:
                with self.subTest(stage=stage):
                    self.assertTrue((parent / stage / f"{stage}.py").is_file())
                    self.assertTrue((parent / stage / "__init__.py").is_file())
                    self.assertEqual(
                        {"__init__.py", f"{stage}.py"},
                        {path.name for path in (parent / stage).glob("*.py")},
                    )
        self.assertEqual("0.2.4", VERSION)

    def test_stage_owned_research_resources_and_readmes_are_not_byte_duplicates(self) -> None:
        package_root = ROOT / "osat_edge"
        owned = [
            path
            for path in package_root.rglob("*")
            if path.is_file()
            and (
                path.name == "README.md"
                or any(part in {"research", "resources"} for part in path.parts)
            )
        ]
        by_digest: dict[str, list[pathlib.Path]] = {}
        for path in owned:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            by_digest.setdefault(digest, []).append(path)
        duplicates = [paths for paths in by_digest.values() if len(paths) > 1]
        self.assertEqual([], duplicates)

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
            if re.search(
                r"^STATIONS\s*[:=]", path.read_text(encoding="utf-8"), re.MULTILINE
            ):
                station_definitions.append(path)
        self.assertEqual(
            [
                package_root
                / "roadmap"
                / "pre_steps"
                / "pre02_machine_registry"
                / "pre02_machine_registry.py"
            ],
            station_definitions,
        )

    def test_every_runtime_module_imports_without_a_cycle(self) -> None:
        package_root = ROOT / "osat_edge"
        modules = []
        for path in package_root.rglob("*.py"):
            if any(part in {"tests", "research", "resources"} for part in path.parts):
                continue
            relative = path.relative_to(ROOT).with_suffix("")
            parts = relative.parts[:-1] if relative.name == "__init__" else relative.parts
            modules.append(".".join(parts))
        for module in sorted(modules):
            with self.subTest(module=module):
                importlib.import_module(module)

    def test_cli_package_import_does_not_initialize_pyqt(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys; import osat_edge.ui.cli; "
                "raise SystemExit(any(name.startswith('PyQt6') for name in sys.modules))",
            ],
            cwd=ROOT,
            check=False,
        )
        self.assertEqual(0, result.returncode)

        ui_init = ROOT / "osat_edge" / "ui" / "__init__.py"
        tree = ast.parse(ui_init.read_text(encoding="utf-8"))
        self.assertFalse(
            any(isinstance(node, (ast.Import, ast.ImportFrom)) for node in ast.walk(tree))
        )

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
            / "step13_local_llm"
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
