"""FORinFPRO-HIMD provenance and source-schema inspection."""
from __future__ import annotations
import csv
from pathlib import Path
import time
from typing import Any
from ....pre_steps.pre03_data_provenance.pre03_data_provenance import legacy_external_directory_hash as _directory_hash, md5_file as _md5_file, sha256_file as _sha256_file
from ..core.dataset_context import MAXIMUM_GENERIC_MEMBER_BYTES, RealDataEvaluationError, RealDataNotFound, _base_report, _bounded_directory_files, _unverified_input
FORINFPRO_OFFICIAL_MD5 = {
    "cycle_001_machine_data.csv": "d2a7d96d133f3d7b43a5089ad4bf0b09",
    "cycle_001_pt.csv": "40d8511c11e8e0575dc3930ddd258c19",
    "cycle_001_us_rms.csv": "c767196cfd1b6dec0d09ed0a2dba2551",
}
def _evaluate_forinfpro(path: Path) -> dict[str, Any]:
    started = time.perf_counter()
    if path.is_dir():
        bounded = _bounded_directory_files(path)
        files = [item for item in bounded if item.suffix.lower() == ".csv"]
    else:
        if path.stat().st_size > MAXIMUM_GENERIC_MEMBER_BYTES:
            raise RealDataEvaluationError("FORinFPRO file exceeds the size limit")
        files = [path]
    if not files or any(not item.exists() for item in files):
        raise RealDataNotFound("FORinFPRO-HIMD CSV files not found")
    schemas: list[dict[str, Any]] = []
    for item in files:
        with item.open("r", encoding="utf-8-sig", newline="") as stream:
            first = stream.readline()
            delimiter = ";" if first.count(";") > first.count(",") else ","
            stream.seek(0)
            reader = csv.reader(stream, delimiter=delimiter)
            header = tuple(value.strip() for value in (next(reader, None) or ()) if value.strip())
            count = sum(1 for _row in reader)
        signals = tuple(
            value
            for value in header
            if value.casefold() not in {"time", "datum/zeit", "maschinennummer"}
        )
        schemas.append(
            {
                "file": item.name,
                "declared_columns": len(header),
                "candidate_signal_columns": len(signals),
                "rows": count,
            }
        )
    source_hash = _directory_hash(path, files) if path.is_dir() else _sha256_file(path)
    observed_md5 = {item.name: _md5_file(item) for item in files}
    verified = observed_md5 == FORINFPRO_OFFICIAL_MD5
    if not verified:
        return _unverified_input(
            "forinfpro-himd",
            source_hash,
            "The local files do not match the complete three-file MD5 manifest for official FORinFPRO-HIMD v1.",
            files=schemas,
            observed_file_md5=observed_md5,
            expected_official_file_md5=FORINFPRO_OFFICIAL_MD5,
        )
    report = _base_report(
        "forinfpro-himd",
        source_hash,
        provenance_verified=True,
        provenance_method="complete official v1 three-file MD5 manifest",
    )
    report.update(
        {
            "status": "INSPECTED_NOT_EXECUTABLE",
            "official_version": "v1",
            "official_file_md5": observed_md5,
            "mapped_channels": [],
            "channel_coverage": {
                "mapped": 0,
                "total": sum(item["candidate_signal_columns"] for item in schemas),
                "fraction": 0.0,
            },
            "full_station_representation": False,
            "files": schemas,
            "classification_metrics": None,
            "runtime": {"elapsed_seconds": time.perf_counter() - started},
            "limitations": [
                "Evidence class C industrial mechanism analog; polymer injection molding is not semiconductor transfer molding.",
                "The inspected CSV headers do not declare physical units, so cavity pressure and temperature cannot be mapped to unit-enforced channels without guessing.",
                "Only one published cycle was present locally, so a disjoint exact-machine calibration/evaluation split is unavailable.",
            ],
        }
    )
    return report
