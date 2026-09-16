from __future__ import annotations

import pathlib
import tempfile
import unittest

from osat_edge.common import VERSION, utc


ROOT = pathlib.Path(__file__).resolve().parents[1]


class SecurityPortabilityTests(unittest.TestCase):
    def test_core_has_only_the_numbered_minimum_modules(self) -> None:
        old = {
            "artifacts.py", "baseline.py", "contracts.py", "data_quality.py",
            "evaluation.py", "features.py", "health.py", "historical.py",
            "ingestion.py", "maintenance.py", "offline.py", "physics.py",
            "qualification.py", "rag.py", "registry.py", "risk.py", "runtime.py",
            "simulation.py", "telemetry.py", "theme.py",
        }
        present = {path.name for path in (ROOT / "osat_edge").glob("*.py")}
        self.assertTrue(old.isdisjoint(present))
        self.assertEqual("0.2.3", VERSION)

    def test_source_uses_no_eval_or_hard_coded_unix_temp_path(self) -> None:
        source = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "osat_edge").rglob("*.py"))
        self.assertNotIn("eval" + "(", source)
        self.assertNotIn('"/tmp', source)
        self.assertNotIn("'/tmp", source)

    def test_dependency_files_list_only_direct_core_and_optional_llm(self) -> None:
        core = [line for line in (ROOT / "requirements.txt").read_text().splitlines() if line and not line.startswith("#")]
        optional = (ROOT / "requirements-llm.txt").read_text()
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
