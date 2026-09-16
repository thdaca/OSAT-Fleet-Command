"""Fail-closed inspection for cataloged datasets with no executable mapping."""
from __future__ import annotations
from pathlib import Path
from typing import Any
from ....pre_steps.pre03_data_provenance.pre03_data_provenance import legacy_external_directory_hash as _directory_hash, sha256_file as _sha256_file
from ..core.dataset_context import MAXIMUM_GENERIC_ARCHIVE_BYTES, RealDataEvaluationError, RealDataNotFound, _bounded_directory_files, _unverified_input
def _inspect_unmapped(dataset_id: str, path: Path) -> dict[str, Any]:
    if not path.exists():
        raise RealDataNotFound(f"Dataset path not found: {path.name}")
    if path.is_file():
        if path.stat().st_size > MAXIMUM_GENERIC_ARCHIVE_BYTES:
            raise RealDataEvaluationError("Dataset artifact exceeds the inspection size limit")
        files = [path]
    else:
        files = _bounded_directory_files(path)
    if not files:
        raise RealDataNotFound("No local dataset artifact was present.")
    source_hash = _sha256_file(path) if path.is_file() else _directory_hash(path, files)
    return _unverified_input(
        dataset_id,
        source_hash,
        "No pinned official artifact or canonical-content identity is registered for this dataset; local bytes cannot be declared verified real data.",
        files=len(files),
    )
