"""NASA/UC Berkeley milling descriptive evaluation for POST04."""
from __future__ import annotations
from pathlib import Path
import time
from typing import Any
from ...post03_external_benchmark.benchmark import (
    BenchmarkError,
    NASA_OFFICIAL_ARCHIVE_SHA256,
    NASA_OFFICIAL_MAT_SHA256,
    analyze_nasa_milling,
)
from ..core.dataset_context import RealDataEvaluationError, _base_report, _unverified_input
def _evaluate_nasa(path: Path) -> dict[str, Any]:
    started = time.perf_counter()
    selected = path
    if path.is_dir():
        archives = sorted(path.glob("*.zip"))
        mats = sorted(path.rglob("mill.mat"))
        if len(archives) == 1 and not mats:
            selected = archives[0]
    try:
        source = analyze_nasa_milling(selected)
    except BenchmarkError as exc:
        raise RealDataEvaluationError(str(exc)) from exc
    verified = (
        source["source_artifact_sha256"] == NASA_OFFICIAL_ARCHIVE_SHA256
        or source["mill_mat_sha256"] == NASA_OFFICIAL_MAT_SHA256
    )
    if not verified:
        return _unverified_input(
            "nasa-milling",
            source["source_artifact_sha256"],
            "The input is structurally compatible with NASA Milling, but neither its source artifact nor canonical mill.mat hash matches the pinned official dataset.",
            observed_runs=source["runs"],
            canonical_mat_sha256=source["mill_mat_sha256"],
        )
    report = _base_report(
        "nasa-milling",
        source["source_artifact_sha256"],
        provenance_verified=True,
        provenance_method=(
            "pinned official archive SHA-256"
            if source["source_artifact_sha256"] == NASA_OFFICIAL_ARCHIVE_SHA256
            else "pinned canonical official mill.mat SHA-256"
        ),
    )
    report.update(
        {
            "status": "EXECUTED_DESCRIPTIVE",
            "canonical_mat_sha256": source["mill_mat_sha256"],
            "mapped_channels": [],
            "channel_coverage": {"mapped": 0, "total": 3, "fraction": 0.0},
            "full_station_representation": False,
            "samples": None,
            "runs": source["runs"],
            "machines": None,
            "split": "none; descriptive association only",
            "metrics_supported": ["continuous wear rank association", "runtime"],
            "classification_metrics": None,
            "continuous_metrics": source["overall_descriptive_association"],
            "runtime": {"elapsed_seconds": time.perf_counter() - started},
            "limitations": [
                "Evidence class C machining analog; not semiconductor or OSAT validation.",
                "Signal output units are not documented and no spindle-speed time series exists, so Step 02/03/07/09 cannot be entered without fabrication.",
                "Wear correlations are descriptive associations and not failure probabilities, health labels, or causal effects.",
            ],
        }
    )
    return report
