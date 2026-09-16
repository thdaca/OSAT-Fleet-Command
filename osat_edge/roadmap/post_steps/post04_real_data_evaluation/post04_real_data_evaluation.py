"""Public orchestration API for isolated external real-data evaluation.

Dataset-specific parsing and calculations live under the datasets package.
Shared metrics, reporting, and evidence lifecycle live under the core package.
This module only dispatches datasets and re-exports the supported POST04 API.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ...pre_steps.pre01_common.pre01_common import DataOrigin, VERSION
from .core.dataset_context import (
    DATASET_ORDER,
    DATASETS,
    DEFAULT_EXTERNAL_DATA_ROOT,
    RealDataEvaluationError,
    RealDataNotFound,
    _rejected_invalid,
    _unavailable,
)
from .core.model_bridge import _fit_nominal_benchmark_model
from .core.reporting import (
    deterministic_scientific_bytes,
    deterministic_scientific_report,
    deterministic_scientific_sha256,
    real_data_summary,
    write_real_data_report,
)
from .datasets.forinfpro_himd import _evaluate_forinfpro
from .datasets.kuka import _evaluate_kuka
from .datasets.nasa_milling import _evaluate_nasa
from .datasets.r2r import _evaluate_r2r, _r2r_source_field_coverage
from .datasets.secom import _evaluate_secom
from .datasets.st_awfd import (
    ST_AWFD_SPECS,
    ST_THRESHOLD_PROBES,
    _evaluate_st_awfd,
    _st_feature_sets_for_step,
    _st_identity,
    _validate_st_awfd_matrix,
)
from .datasets.tuhh_dad3350 import (
    KEYENCE_PARSER_COMMIT,
    TUHH_FEED_FILES,
    _evaluate_tuhh_surface,
    _surface_statistics,
)
from .datasets.unmapped import _inspect_unmapped


def evaluate_real_dataset(dataset_id: str, path: str | Path) -> dict[str, Any]:
    """Evaluate one explicit local external dataset without operational authority."""

    if dataset_id not in DATASETS:
        raise RealDataEvaluationError(f"Unknown external dataset {dataset_id!r}")
    selected = Path(path)
    if not selected.exists():
        raise RealDataNotFound(f"Dataset path not found: {selected.name}")
    if dataset_id in ST_AWFD_SPECS:
        return _evaluate_st_awfd(selected, dataset_id)
    if dataset_id == "tuhh-dad3350-surface":
        return _evaluate_tuhh_surface(selected)
    if dataset_id == "kuka-kr3":
        return _evaluate_kuka(selected)
    if dataset_id == "nasa-milling":
        return _evaluate_nasa(selected)
    if dataset_id == "uci-secom":
        return _evaluate_secom(selected)
    if dataset_id == "forinfpro-himd":
        return _evaluate_forinfpro(selected)
    if dataset_id == "r2r-web-tension":
        return _evaluate_r2r(selected)
    return _inspect_unmapped(dataset_id, selected)


def evaluate_all_real_data(root: str | Path) -> dict[str, Any]:
    """Attempt every registered dataset in the specified ignored/local root."""

    external = Path(root)
    results: list[dict[str, Any]] = []
    for dataset_id in DATASET_ORDER:
        path = external / dataset_id
        if not path.exists():
            results.append(_unavailable(dataset_id, "No local dataset artifact was present."))
            continue
        try:
            results.append(evaluate_real_dataset(dataset_id, path))
        except RealDataNotFound as exc:
            results.append(_unavailable(dataset_id, str(exc)))
        except RealDataEvaluationError as exc:
            results.append(_rejected_invalid(dataset_id, None, str(exc)))
    return {
        "version": VERSION,
        "origin": DataOrigin.EXTERNAL_BENCHMARK.value,
        "dataset_order": list(DATASET_ORDER),
        "datasets": results,
        "summary": {
            "attempted": len(results),
            "executed": sum(item["status"].startswith("EXECUTED") for item in results),
            "inspected_not_executable": sum(
                item["status"] == "INSPECTED_NOT_EXECUTABLE"
                for item in results
            ),
            "unavailable": sum(item["status"] == "UNAVAILABLE" for item in results),
            "rejected_invalid": sum(
                item["status"] == "REJECTED_INVALID" for item in results
            ),
            "unverified_external_input": sum(
                item["status"] == "UNVERIFIED_EXTERNAL_INPUT" for item in results
            ),
            "operational_tickets": 0,
        },
        "claims": [
            "EXTERNAL-DATA RESEARCH EVALUATION; REAL-DATA STATUS REQUIRES PINNED PROVENANCE",
            "NO PUBLIC DATASET RESULT IS OSAT PLANT VALIDATION",
            "NO EXTERNAL BENCHMARK HAS OPERATIONAL OR TICKET AUTHORITY",
            "NO STEP-05 FAMILY MODEL IS FIT FROM EXTERNAL DATA",
        ],
    }


from .core.evidence_lifecycle import (
    COMMITTED_EVIDENCE_PATH,
    CURRENT_EVIDENCE_PATH,
    HISTORICAL_EVIDENCE_PATH,
    HISTORICAL_EVIDENCE_SHA256,
    SNAPSHOT4_EVIDENCE_ARTIFACT_SHA256,
    SNAPSHOT4_SCIENTIFIC_PAYLOAD_SHA256,
    THIRD_PARTY_DATA_USE_PATH,
    current_real_data_evidence_record,
    evaluator_source_sha256,
    snapshot4_result_sha256,
    snapshot4_scientific_payload_sha256,
    verify_committed_real_data_evidence,
    verify_historical_real_data_artifact,
    write_current_real_data_evidence,
)


__all__ = (
    "COMMITTED_EVIDENCE_PATH",
    "CURRENT_EVIDENCE_PATH",
    "DATASET_ORDER",
    "DATASETS",
    "DEFAULT_EXTERNAL_DATA_ROOT",
    "HISTORICAL_EVIDENCE_PATH",
    "HISTORICAL_EVIDENCE_SHA256",
    "SNAPSHOT4_EVIDENCE_ARTIFACT_SHA256",
    "SNAPSHOT4_SCIENTIFIC_PAYLOAD_SHA256",
    "THIRD_PARTY_DATA_USE_PATH",
    "RealDataEvaluationError",
    "RealDataNotFound",
    "current_real_data_evidence_record",
    "deterministic_scientific_bytes",
    "deterministic_scientific_report",
    "deterministic_scientific_sha256",
    "evaluate_all_real_data",
    "evaluate_real_dataset",
    "evaluator_source_sha256",
    "real_data_summary",
    "snapshot4_result_sha256",
    "snapshot4_scientific_payload_sha256",
    "verify_committed_real_data_evidence",
    "verify_historical_real_data_artifact",
    "write_current_real_data_evidence",
    "write_real_data_report",
)
