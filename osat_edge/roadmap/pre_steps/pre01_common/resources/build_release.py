"""Build and validate the portable OSAT SemiGuard release archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
from typing import Iterable, Sequence
import zipfile


REQUIRED_ROOT_FILES = (
    ".gitignore",
    "AGENTS.md",
    "README.md",
    "STUDENT_GUIDE.md",
    "requirements.txt",
)
EXCLUDED_DIRECTORY_NAMES = {
    ".artifacts",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
}
EXCLUDED_FILE_ENDINGS = (
    ".db",
    ".pyc",
    ".sqlite",
    ".sqlite-shm",
    ".sqlite-wal",
    ".sqlite3",
    ".temp",
    ".tmp",
    "~",
)


class ReleaseArchiveError(ValueError):
    """Raised when a project tree or ZIP member violates release rules."""


def _is_excluded(relative_path: PurePosixPath) -> bool:
    parts = relative_path.parts
    if any(part in EXCLUDED_DIRECTORY_NAMES for part in parts):
        return True
    if len(parts) >= 2 and parts[0] == "benchmarks" and parts[1] == "_external":
        return True
    return relative_path.name.lower().endswith(EXCLUDED_FILE_ENDINGS)


def release_files(project_root: Path) -> tuple[Path, ...]:
    """Return the sorted committed files allowed in a clean release."""

    root = project_root.resolve()
    missing = [name for name in REQUIRED_ROOT_FILES if not (root / name).is_file()]
    if not (root / "osat_edge").is_dir():
        missing.append("osat_edge/")
    if missing:
        raise ReleaseArchiveError(f"Release root is missing required entries: {missing}")

    candidates = [*(root / name for name in REQUIRED_ROOT_FILES)]
    for directory in (root / "osat_edge", root / "docs"):
        candidates.extend(path for path in directory.rglob("*") if path.is_file())
    included = []
    for path in candidates:
        relative = PurePosixPath(*path.relative_to(root).parts)
        if not _is_excluded(relative):
            included.append(path)
    return tuple(sorted(included, key=lambda path: path.relative_to(root).as_posix()))


def archive_member_name(project_root: Path, source: Path) -> str:
    """Return one project-rooted ZIP member using POSIX separators only."""

    root = project_root.resolve()
    try:
        relative = source.resolve().relative_to(root)
    except ValueError as error:
        raise ReleaseArchiveError("Release files must remain inside the project root") from error
    return PurePosixPath(root.name, *relative.parts).as_posix()


def validate_member_names(names: Iterable[str], project_root_name: str) -> tuple[str, ...]:
    """Validate portable, unique members beneath exactly one project root."""

    checked: list[str] = []
    seen: set[str] = set()
    for name in names:
        if not isinstance(name, str) or not name:
            raise ReleaseArchiveError("ZIP member names must be nonempty strings")
        if "\\" in name:
            raise ReleaseArchiveError(f"ZIP member contains a backslash: {name!r}")
        if name in seen:
            raise ReleaseArchiveError(f"Duplicate ZIP member: {name!r}")
        seen.add(name)
        if any(part in {"", ".", ".."} for part in name.split("/")):
            raise ReleaseArchiveError(f"ZIP member is empty or contains traversal: {name!r}")
        path = PurePosixPath(name)
        if path.is_absolute():
            raise ReleaseArchiveError(f"ZIP member must be relative: {name!r}")
        if len(path.parts) < 2 or path.parts[0] != project_root_name:
            raise ReleaseArchiveError(
                f"ZIP member escapes the single project root {project_root_name!r}: {name!r}"
            )
        relative = PurePosixPath(*path.parts[1:])
        if _is_excluded(relative):
            raise ReleaseArchiveError(f"ZIP member is excluded generated/local data: {name!r}")
        checked.append(name)
    if not checked:
        raise ReleaseArchiveError("Release archive is empty")
    return tuple(checked)


def validate_release_archive(archive_path: Path, project_root_name: str) -> tuple[str, ...]:
    """Open every member and validate names, boundaries, duplicates, and CRCs."""

    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            names = validate_member_names(
                (member.filename for member in archive.infolist()), project_root_name
            )
            for member in archive.infolist():
                with archive.open(member, "r") as stream:
                    for _block in iter(lambda: stream.read(1024 * 1024), b""):
                        pass
    except (OSError, zipfile.BadZipFile) as error:
        raise ReleaseArchiveError(f"Release ZIP cannot be read: {error}") from error
    return names


def build_release_archive(project_root: Path, destination: Path) -> tuple[str, ...]:
    """Build to a temporary ZIP, validate it, then atomically replace destination."""

    root = project_root.resolve()
    target = destination.resolve()
    temporary = target.with_name(f"{target.name}.tmp")
    files = release_files(root)
    names = tuple(archive_member_name(root, path) for path in files)
    validate_member_names(names, root.name)
    target.parent.mkdir(parents=True, exist_ok=True)
    if temporary.exists():
        temporary.unlink()
    try:
        with zipfile.ZipFile(
            temporary, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as archive:
            for source, member_name in zip(files, names, strict=True):
                archive.write(source, member_name)
        verified = validate_release_archive(temporary, root.name)
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()
    validate_release_archive(target, root.name)
    return verified


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    default_root = Path(__file__).resolve().parents[5]
    parser.add_argument("--project-root", type=Path, default=default_root)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args(argv)
    output = arguments.output or arguments.project_root.resolve().parent / "snapshots" / "0.2.6 (snapshot 2).zip"
    members = build_release_archive(arguments.project_root, output)
    print(
        json.dumps(
            {
                "archive": str(output.resolve()),
                "file_count": len(members),
                "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "size_bytes": output.stat().st_size,
                "verification": "PASS",
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
