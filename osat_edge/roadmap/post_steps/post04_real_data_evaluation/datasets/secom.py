"""UCI SECOM provenance and schema inspection."""
from __future__ import annotations
from pathlib import Path
import time
from typing import Any
from ..core.dataset_context import RealDataEvaluationError, _base_report, _unverified_input
from ..core.source_files import _zip_members
SECOM_OFFICIAL_ARCHIVE_SHA256 = "eea568baf3c2229096d7d294cf0b096b5502bd96d92c0b80a65b84714059be8e"
SECOM_OFFICIAL_FILE_SET_SHA256 = "29c8312b075821292d52eb8e3e20fbe6a4943272de3aa3900c6b9b19026dd927"
def _evaluate_secom(path: Path) -> dict[str, Any]:
    started = time.perf_counter()
    source_hash, content_hash, members = _zip_members(path)
    data_items = [(name, value) for name, value in members.items() if name.lower().endswith("secom.data")]
    label_items = [(name, value) for name, value in members.items() if name.lower().endswith("secom_labels.data")]
    if len(data_items) != 1 or len(label_items) != 1:
        raise RealDataEvaluationError("SECOM input must contain one data and one label file")
    try:
        data_lines = data_items[0][1].decode("utf-8").splitlines()
        label_lines = label_items[0][1].decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise RealDataEvaluationError("SECOM files must be UTF-8 text") from exc
    if not data_lines or len(data_lines) != len(label_lines):
        raise RealDataEvaluationError("SECOM data and labels must contain aligned nonempty rows")
    widths = {len(line.split()) for line in data_lines}
    if len(widths) != 1:
        raise RealDataEvaluationError("SECOM rows must have one feature width")
    labels: list[int] = []
    for line in label_lines:
        parts = line.split(maxsplit=1)
        if not parts or parts[0] not in {"-1", "1"}:
            raise RealDataEvaluationError("SECOM labels must be -1 or 1")
        labels.append(int(parts[0]))
    verified = (
        source_hash == SECOM_OFFICIAL_ARCHIVE_SHA256
        or content_hash == SECOM_OFFICIAL_FILE_SET_SHA256
    )
    if not verified:
        return _unverified_input(
            "uci-secom",
            source_hash,
            "The files are SECOM-compatible, but neither the source archive nor canonical file-set hash matches the pinned official dataset.",
            samples=len(data_lines),
            observed_variable_count=next(iter(widths)),
            observed_label_counts={"pass": labels.count(-1), "fail": labels.count(1)},
            canonical_content_sha256=content_hash,
        )
    report = _base_report(
        "uci-secom",
        source_hash,
        provenance_verified=True,
        provenance_method=(
            "pinned official archive SHA-256"
            if source_hash == SECOM_OFFICIAL_ARCHIVE_SHA256
            else "pinned canonical official file-set SHA-256"
        ),
    )
    report.update(
        {
            "status": "INSPECTED_NOT_EXECUTABLE",
            "mapped_channels": [],
            "channel_coverage": {"mapped": 0, "total": next(iter(widths)), "fraction": 0.0},
            "full_station_representation": False,
            "samples": len(data_lines),
            "runs": None,
            "machines": None,
            "label_counts": {"pass": labels.count(-1), "fail": labels.count(1)},
            "classification_metrics": None,
            "runtime": {"elapsed_seconds": time.perf_counter() - started},
            "limitations": [
                "Evidence class B other semiconductor process/yield data; not equipment-health or OSAT plant validation.",
                "All sensor variables are anonymized and have no physical names or units, so zero channels can be mapped exactly.",
                "Pass/fail yield labels cannot be relabeled as equipment health or maintenance faults.",
                "No accuracy is reported because the unchanged PHM pipeline cannot execute without fabricated channel semantics.",
            ],
        }
    )
    return report
