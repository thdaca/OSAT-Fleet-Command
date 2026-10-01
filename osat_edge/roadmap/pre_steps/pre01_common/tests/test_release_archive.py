from __future__ import annotations

from pathlib import Path, PurePosixPath
import tempfile
import unittest
import zipfile

from osat_edge.roadmap.pre_steps.pre01_common.resources.build_release import (
    ReleaseArchiveError,
    build_release_archive,
    validate_member_names,
    validate_release_archive,
)


class ReleaseArchiveTests(unittest.TestCase):
    def _project_fixture(self, parent: Path) -> Path:
        root = parent / "PortableProject"
        (root / "osat_edge" / "roadmap").mkdir(parents=True)
        for name in (
            ".gitignore", "AGENTS.md", "README.md", "STUDENT_GUIDE.md",
            "requirements.txt",
        ):
            (root / name).write_text(f"{name}\n", encoding="utf-8")
        (root / "osat_edge" / "__init__.py").write_text("", encoding="utf-8")
        (root / "osat_edge" / "pipeline.py").write_text("VALUE = 1\n", encoding="utf-8")
        (root / "osat_edge" / "roadmap" / "README.md").write_text(
            "roadmap\n", encoding="utf-8"
        )
        (root / "docs" / "teams").mkdir(parents=True)
        (root / "docs" / "teams" / "README.md").write_text("Team entry points\n", encoding="utf-8")
        (root / "osat_edge" / "__pycache__").mkdir()
        (root / "osat_edge" / "__pycache__" / "ignored.pyc").write_bytes(b"cache")
        (root / "osat_edge" / "runtime.sqlite-wal").write_bytes(b"runtime")
        (root / ".venv").mkdir()
        (root / ".venv" / "ignored.txt").write_text("local", encoding="utf-8")
        (root / ".artifacts").mkdir()
        (root / ".artifacts" / "ignored.json").write_text("{}", encoding="utf-8")
        (root / "benchmarks" / "_external").mkdir(parents=True)
        (root / "benchmarks" / "_external" / "ignored.csv").write_text(
            "external", encoding="utf-8"
        )
        return root

    def test_built_archive_is_portable_clean_and_extractable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            root = self._project_fixture(parent)
            archive_path = parent / "release.zip"
            names = build_release_archive(root, archive_path)
            self.assertEqual(names, validate_release_archive(archive_path, root.name))
            self.assertTrue(all("\\" not in name and "/" in name for name in names))
            self.assertEqual({root.name}, {PurePosixPath(name).parts[0] for name in names})
            self.assertEqual(len(names), len(set(names)))
            serialized = "\n".join(names)
            for excluded in (
                ".venv", ".artifacts", "__pycache__", ".pyc",
                "benchmarks/_external", ".sqlite-wal", "/build/", "/dist/",
            ):
                self.assertNotIn(excluded, serialized)

            extracted = parent / "extracted"
            with zipfile.ZipFile(archive_path, "r") as archive:
                archive.extractall(extracted)
            extracted_root = extracted / root.name
            self.assertTrue((extracted_root / "README.md").is_file())
            self.assertTrue((extracted_root / "osat_edge" / "pipeline.py").is_file())
            self.assertTrue(
                (extracted_root / "osat_edge" / "roadmap" / "README.md").is_file()
            )
            self.assertTrue((extracted_root / "docs" / "teams" / "README.md").is_file())

    def test_member_validation_rejects_nonportable_or_escaping_names(self) -> None:
        invalid = (
            "PortableProject\\osat_edge\\pipeline.py",
            "/PortableProject/osat_edge/pipeline.py",
            "PortableProject/../escape.py",
            "PortableProject/osat_edge/../../escape.py",
            "OtherProject/osat_edge/pipeline.py",
            "PortableProject/.venv/ignored.py",
        )
        for name in invalid:
            with self.subTest(name=name), self.assertRaises(ReleaseArchiveError):
                validate_member_names((name,), "PortableProject")
        with self.assertRaisesRegex(ReleaseArchiveError, "Duplicate"):
            validate_member_names(
                ("PortableProject/README.md", "PortableProject/README.md"),
                "PortableProject",
            )

if __name__ == "__main__":
    unittest.main()
