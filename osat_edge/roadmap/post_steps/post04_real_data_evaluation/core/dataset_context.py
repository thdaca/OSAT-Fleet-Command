"""Dataset registry, errors, and common fail-closed report context."""
from __future__ import annotations
from pathlib import Path
from typing import Any
from ....pre_steps.pre01_common.pre01_common import DataOrigin, FROZEN_EXTERNAL_EVIDENCE_VERSION as VERSION
DATASET_ORDER = (
    "st-awfd-d1",
    "st-awfd-d2",
    "tuhh-dad3350-surface",
    "wafer-dicing-chang-2024",
    "phm-2018-ion-mill",
    "phm-2016-cmp",
    "forinfpro-himd",
    "r2r-web-tension",
    "me-ad",
    "kuka-kr3",
    "rddac",
    "nasa-milling",
    "uci-secom",
)
POST04_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXTERNAL_DATA_ROOT = POST04_ROOT.parents[3] / "benchmarks" / "_external"
DATASETS: dict[str, dict[str, str]] = {
    "st-awfd-d1": {
        "title": "STMicroelectronics Automatic Wafer Fault Detection D1",
        "source": "https://github.com/STMicroelectronics/ST-AWFD",
        "evidence_class": "B",
        "domain": "semiconductor wafer-production process sequences",
    },
    "st-awfd-d2": {
        "title": "STMicroelectronics Automatic Wafer Fault Detection D2",
        "source": "https://github.com/STMicroelectronics/ST-AWFD",
        "evidence_class": "B",
        "domain": "semiconductor wafer-production process sequences",
    },
    "tuhh-dad3350-surface": {
        "title": "TUHH DISCO DAD3350 diced-surface profilometry",
        "source": "https://doi.org/10.15480/882.15763",
        "evidence_class": "A",
        "domain": "wafer-dicing surface metrology",
    },
    "wafer-dicing-chang-2024": {
        "title": "Chang/Tsai/Mo wafer-dicing study data",
        "source": "https://doi.org/10.3390/electronics13101802",
        "evidence_class": "A",
        "domain": "wafer dicing / chipping",
    },
    "phm-2018-ion-mill": {
        "title": "PHM Society 2018 Ion Mill Etch Data Challenge",
        "source": "https://phmsociety.org/conference/annual-conference-of-the-phm-society/annual-conference-of-the-prognostics-and-health-management-society-2018-b/phm-data-challenge-6/",
        "evidence_class": "B",
        "domain": "wafer-fabrication ion mill etch",
    },
    "phm-2016-cmp": {
        "title": "PHM Society 2016 Wafer CMP Data Challenge",
        "source": "https://phmsociety.org/conference/annual-conference-of-the-phm-society/annual-conference-of-the-prognostics-and-health-management-society-2016/phm-data-challenge-4/",
        "evidence_class": "B",
        "domain": "wafer-fabrication chemical-mechanical planarization",
    },
    "forinfpro-himd": {
        "title": "FORinFPRO-HIMD",
        "source": "https://doi.org/10.5281/zenodo.20744054",
        "evidence_class": "C",
        "domain": "hybrid injection molding",
    },
    "r2r-web-tension": {
        "title": "R2R Web Tension",
        "source": "https://doi.org/10.17632/gz3rzw6xgf.2",
        "evidence_class": "C",
        "domain": "roll-to-roll web transport",
    },
    "me-ad": {
        "title": "ME-AD Progressive Robotics Anomaly Detection",
        "source": "https://doi.org/10.5281/zenodo.20817531",
        "evidence_class": "C",
        "domain": "industrial robot progressive actuator degradation",
    },
    "kuka-kr3": {
        "title": "KUKA KR3 Motor-Current Dataset",
        "source": "https://doi.org/10.5281/zenodo.21456277",
        "evidence_class": "D",
        "domain": "industrial robot motor current / payload",
    },
    "rddac": {
        "title": "RDDAC Real Deep Drawing and Cutting Dataset",
        "source": "https://doi.org/10.18419/DARUS-5589",
        "evidence_class": "C",
        "domain": "forming and cutting",
    },
    "nasa-milling": {
        "title": "NASA/UC Berkeley Milling Data Set",
        "source": "https://data.nasa.gov/dataset/milling-wear",
        "evidence_class": "C",
        "domain": "milling / machining",
    },
    "uci-secom": {
        "title": "UCI SECOM",
        "source": "https://doi.org/10.24432/C54305",
        "evidence_class": "B",
        "domain": "semiconductor manufacturing process / yield",
    },
}
MAXIMUM_GENERIC_ARCHIVE_BYTES = 256 * 1024 * 1024
MAXIMUM_GENERIC_MEMBERS = 1_000
MAXIMUM_GENERIC_MEMBER_BYTES = 64 * 1024 * 1024
MAXIMUM_GENERIC_TOTAL_BYTES = 256 * 1024 * 1024
class RealDataEvaluationError(ValueError):
    pass


class RealDataNotFound(RealDataEvaluationError):
    pass


def _bounded_directory_files(
    path: Path,
    *,
    maximum_members: int = MAXIMUM_GENERIC_MEMBERS,
    maximum_file_bytes: int = MAXIMUM_GENERIC_MEMBER_BYTES,
    maximum_total_bytes: int = MAXIMUM_GENERIC_TOTAL_BYTES,
) -> list[Path]:
    if not path.is_dir():
        raise RealDataEvaluationError("Expected a dataset directory")
    files: list[Path] = []
    total = 0
    for item in sorted(path.rglob("*")):
        if item.is_symlink():
            raise RealDataEvaluationError("Dataset directories may not contain symbolic links")
        if not item.is_file():
            continue
        files.append(item)
        if len(files) > maximum_members:
            raise RealDataEvaluationError("Dataset directory contains too many files")
        size = item.stat().st_size
        if size > maximum_file_bytes:
            raise RealDataEvaluationError("Dataset directory file exceeds the size limit")
        total += size
        if total > maximum_total_bytes:
            raise RealDataEvaluationError("Dataset directory exceeds the total size limit")
    return files


def _base_report(
    dataset_id: str,
    source_hash: str | None,
    *,
    provenance_verified: bool = False,
    provenance_method: str | None = None,
) -> dict[str, Any]:
    metadata = DATASETS[dataset_id]
    return {
        "version": VERSION,
        "dataset": dataset_id,
        "title": metadata["title"],
        "source": metadata["source"] if provenance_verified else None,
        "source_reference": metadata["source"],
        "source_sha256": source_hash,
        "origin": DataOrigin.EXTERNAL_BENCHMARK.value,
        "real_data": True if provenance_verified else None,
        "synthetic_data": False if provenance_verified else None,
        "provenance_verified": provenance_verified,
        "provenance_status": (
            "VERIFIED_OFFICIAL_ARTIFACT"
            if provenance_verified
            else "UNVERIFIED_OR_NOT_EVALUATED"
        ),
        "provenance_method": provenance_method,
        "evidence_class": metadata["evidence_class"],
        "domain": metadata["domain"],
        "osat_plant_validation": False,
        "production_qualified": False,
        "ticket_authority": False,
        "operational_ticket_count": 0,
        "step15_called": False,
    }


def _unavailable(dataset_id: str, reason: str) -> dict[str, Any]:
    report = _base_report(dataset_id, None)
    report.update(
        {
            "status": "UNAVAILABLE",
            "mapped_channels": [],
            "channel_coverage": {"mapped": 0, "total": 0, "fraction": None},
            "full_station_representation": False,
            "limitations": [reason],
        }
    )
    return report


def _rejected_invalid(dataset_id: str, source_hash: str | None, reason: str) -> dict[str, Any]:
    report = _base_report(dataset_id, source_hash)
    report.update(
        {
            "status": "REJECTED_INVALID",
            "mapped_channels": [],
            "channel_coverage": {"mapped": 0, "total": 0, "fraction": None},
            "full_station_representation": False,
            "limitations": [reason],
        }
    )
    return report


def _unverified_input(
    dataset_id: str,
    source_hash: str,
    reason: str,
    **observed: Any,
) -> dict[str, Any]:
    report = _base_report(dataset_id, source_hash)
    report.update(
        {
            "status": "UNVERIFIED_EXTERNAL_INPUT",
            "mapped_channels": [],
            "channel_coverage": {"mapped": 0, "total": 0, "fraction": None},
            "full_station_representation": False,
            "limitations": [reason],
            **observed,
        }
    )
    return report
