"""Bounded reading and identity calculation for external source containers."""
from __future__ import annotations
from pathlib import Path
import zipfile
from ....pre_steps.pre03_data_provenance.pre03_data_provenance import (
    legacy_external_directory_hash as _directory_hash,
    legacy_external_named_content_hash as _named_content_hash,
    sha256_file as _sha256_file,
)
from .dataset_context import (
    MAXIMUM_GENERIC_ARCHIVE_BYTES, MAXIMUM_GENERIC_MEMBERS,
    MAXIMUM_GENERIC_MEMBER_BYTES, MAXIMUM_GENERIC_TOTAL_BYTES,
    RealDataEvaluationError, RealDataNotFound, _bounded_directory_files,
)
def _zip_members(path: Path) -> tuple[str, str, dict[str, bytes]]:
    if not path.exists():
        raise RealDataNotFound(f"Dataset path not found: {path.name}")
    selected = path
    if path.is_dir():
        archives = sorted(path.glob("*.zip"))
        if len(archives) == 1:
            selected = archives[0]
    if selected.is_file() and selected.suffix.lower() == ".zip":
        if selected.stat().st_size > MAXIMUM_GENERIC_ARCHIVE_BYTES:
            raise RealDataEvaluationError("Dataset ZIP exceeds the evaluation size limit")
        try:
            with zipfile.ZipFile(selected) as archive:
                files = [item for item in archive.infolist() if not item.is_dir()]
                if len(files) > MAXIMUM_GENERIC_MEMBERS:
                    raise RealDataEvaluationError("Dataset ZIP contains too many members")
                if len({item.filename for item in files}) != len(files):
                    raise RealDataEvaluationError("Dataset ZIP contains duplicate member names")
                if any(item.file_size > MAXIMUM_GENERIC_MEMBER_BYTES for item in files):
                    raise RealDataEvaluationError("Dataset ZIP member exceeds the size limit")
                if sum(item.file_size for item in files) > MAXIMUM_GENERIC_TOTAL_BYTES:
                    raise RealDataEvaluationError("Dataset ZIP expands beyond the size limit")
                members = {}
                for item in files:
                    with archive.open(item) as stream:
                        content = stream.read(MAXIMUM_GENERIC_MEMBER_BYTES + 1)
                    if len(content) != item.file_size:
                        raise RealDataEvaluationError("Dataset ZIP member size mismatch")
                    members[item.filename] = content
        except zipfile.BadZipFile as exc:
            raise RealDataEvaluationError("Dataset ZIP is invalid") from exc
        return _sha256_file(selected), _named_content_hash(list(members.items())), members
    if path.is_dir():
        files = _bounded_directory_files(path)
        members = {item.relative_to(path).as_posix(): item.read_bytes() for item in files}
        return _directory_hash(path, files), _named_content_hash(list(members.items())), members
    if path.stat().st_size > MAXIMUM_GENERIC_MEMBER_BYTES:
        raise RealDataEvaluationError("Dataset file exceeds the size limit")
    content = path.read_bytes()
    members = {path.name: content}
    return _sha256_file(path), _named_content_hash(list(members.items())), members
